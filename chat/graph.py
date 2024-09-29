import json
import os
from langchain_core.documents import Document
from langchain_community.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
import google.generativeai as genai
from neo4j import GraphDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from django.conf import settings
from .graph_schema import NODES, RELATIONSHIPS
from langchain_google_genai import GoogleGenerativeAI
from langchain_core.documents import Document
import re

# Neo4j setup
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# graph_db = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
graph_db = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# LLM setup - for Gemini (you'll need to write a custom LLM wrapper for Gemini if not done yet)
# genai.configure(api_key=settings.GEMINI_API_KEY)
# llm = genai.GenerativeModel("gemini-pro")

# llm = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.2, verbose=True, google_api_key=settings.GEMINI_API_KEY)

llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.2, google_api_key=settings.GEMINI_API_KEY)

# llm_transformer = LLMGraphTransformer(llm=llm)

# llm_transformer = LLMGraphTransformer(
#     llm=llm,
#     allowed_nodes=list(NODES.keys()),
#     allowed_relationships=[rel for rels in RELATIONSHIPS.values() for rel in rels],
#     node_properties=list(set([prop for props in NODES.values() for prop in props]))
# )


def store_graph_in_neo4j(graph_db, graph_documents):
    with graph_db.session() as session:
        # Clear existing data (optional)
        session.run("MATCH (n) DETACH DELETE n")
        
        # Create nodes
        for node in graph_documents['nodes']:
            properties = ', '.join([f"{k}: ${k}" for k in node['properties']])
            query = f"CREATE (n:{node['type']} {{id: $id, {properties}}})"
            session.run(query, id=node['id'], **node['properties'])
        
        # Create relationships
        for rel in graph_documents['relationships']:
            query = f"""
            MATCH (a {{id: $source_id}}), (b {{id: $target_id}})
            CREATE (a)-[:{rel['type']}]->(b)
            """
            session.run(query, source_id=rel['source'], target_id=rel['target'])


# # def get_graph_data(username):
# #     # Example function to query the graph
# #     query = f"""
# #     MATCH (a:Appointment {{user: '{username}'}})
# #     RETURN a.details, a.status
# #     """
# #     result = graph_db.run_query(query)

# #     # Format the result for easy reading
# #     appointments = [f"{record['a.details']} - Status: {record['a.status']}" for record in result]
# #     return appointments



def extract_json_from_response(response):
    # Use regex to find content between ```json and ``` markers
    json_match = re.search(r'```json\n(.*?)\n```', response, re.DOTALL)
    if json_match:
        return json_match.group(1)
    else:
        # If no markers found, assume the entire response is JSON
        return response

def convert_to_graph_document(prompt, username):
    try:
        print("Starting conversion process...")
        extraction_prompt = f"""
        Extract the following information from the text, if present:
        - Patient Name
        - Doctor Name
        - Appointment Date
        - Appointment Time
        - Medical Condition (if mentioned)
        - Medication (if mentioned)

        Text: {prompt}

        Format the output as a JSON object with these keys: PatientName, DoctorName, AppointmentDate, AppointmentTime, MedicalCondition, Medication.
        If any information is not present, leave the corresponding field empty.
        """
        
        response = llm.invoke(extraction_prompt)
        print("Extraction completed.")
        
        try:
            json_content = extract_json_from_response(response)
            info = json.loads(json_content)
            print(f"Extracted info: {info}")
        except json.JSONDecodeError:
            print(f"Failed to parse JSON: {response}")
            info = {}
        
        nodes, patient_name = create_nodes_from_info(info, username)
        relationships = create_relationships_from_info(info, patient_name)
        
        print(f"Nodes: {nodes}")
        print(f"Relationships: {relationships}")
        
        return [Document(page_content=prompt, metadata={'nodes': nodes, 'relationships': relationships})]
    except Exception as e:
        print(f"An error occurred in convert_to_graph_document: {str(e)}")
        return None


def create_nodes_from_info(info, username):
    nodes = []

    patient_name = info.get('PatientName') or username
    print(patient_name)

    if patient_name:
        nodes.append({
            'id': f"Patient_{patient_name}",
            'type': 'Patient',
            'properties': {'Name': info['PatientName']}  
        })

    if info.get('DoctorName'):
        nodes.append({
            'id': f"Doctor_{info['DoctorName']}",
            'type': 'Doctor',
            'properties': {'Name': info['DoctorName']}  
        })

    if info.get('MedicalCondition'):
        nodes.append({
            'id': f"Condition_{info['MedicalCondition']}",
            'type': 'MedicalCondition',
            'properties': {'Name': info['MedicalCondition']}  
        })

    if info.get('Medication'):
        nodes.append({
            'id': f"Medication_{info['Medication']}",
            'type': 'Medication',
            'properties': {'Name': info['Medication']}  
        })

    if info.get('AppointmentDate') and info.get('AppointmentTime'):
        nodes.append({
            'id': f"Appointment_{info['AppointmentDate']}_{info['AppointmentTime']}",
            'type': 'Appointment',
            'properties': {'Date': info['AppointmentDate'], 'Time': info['AppointmentTime']}
        })

    return nodes, patient_name

def create_relationships_from_info(info, patient_name):
    relationships = []

    if patient_name and info.get('DoctorName'):
        relationships.append({
            'source': f"Patient_{patient_name}",
            'target': f"Doctor_{info['DoctorName']}",
            'type': 'TREATS'
        })

    if patient_name and info.get('AppointmentDate') and info.get('AppointmentTime'):
        appointment_id = f"Appointment_{info['AppointmentDate']}_{info['AppointmentTime']}"
        relationships.append({
            'source': f"Patient_{patient_name}",
            'target': appointment_id,
            'type': 'HAS_APPOINTMENT'
        })
        if info.get('DoctorName'):
            relationships.append({
                'source': appointment_id,
                'target': f"Doctor_{info['DoctorName']}",
                'type': 'WITH_DOCTOR'
            })

    if patient_name and info.get('MedicalCondition'):
        relationships.append({
            'source': f"Patient_{patient_name}",
            'target': f"Condition_{info['MedicalCondition']}",
            'type': 'HAS_CONDITION'
        })

    if patient_name and info.get('Medication'):
        relationships.append({
            'source': f"Patient_{patient_name}",
            'target': f"Medication_{info['Medication']}",
            'type': 'TAKES_MEDICATION'
        })

    return relationships
