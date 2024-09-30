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
from datetime import datetime, timedelta
import calendar
import pdb

# Neo4j setup
NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

# graph_db = Neo4jGraph(url=NEO4J_URI, username=NEO4J_USERNAME, password=NEO4J_PASSWORD)
graph_db = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

llm = GoogleGenerativeAI(model="gemini-pro", temperature=0.2, google_api_key=settings.GEMINI_API_KEY)

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
            result = session.run(query, source_id=rel['source'], target_id=rel['target'])
            print(f"Relationship creation result for {rel['type']} ({rel['source']} -> {rel['target']}): {result.consume().counters}")




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
        - Medication Frequency (if mentioned)

        Text: {prompt}

        Format the output as a JSON object with these keys: PatientName, DoctorName, AppointmentDate, AppointmentTime, MedicalCondition, Medication, MedicationFrequency.
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

        print(nodes)
        print(relationships)
        
        return [Document(page_content=prompt, metadata={'nodes': nodes, 'relationships': relationships})]
    except Exception as e:
        print(f"An error occurred in convert_to_graph_document: {str(e)}")
        return None


def create_nodes_from_info(info, username):
    nodes = []

    patient_name = info.get('PatientName') or username
    print(patient_name)
    print("creat node info: ", info)

    if patient_name:
        nodes.append({
            'id': f"Patient_{patient_name}",
            'type': 'Patient',
            'properties': {'Name': f"Patient_{patient_name}"}  
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

    if info.get('MedicationFrequency'):
        nodes.append({
            'id': f"MedicationFrequency_{info['MedicationFrequency']}",
            'type': 'Medication_Frequence',
            'properties': {'Name': info['MedicationFrequency']}  
        })

    if info.get('AppointmentDate') and info.get('AppointmentTime'):
        date_time = datetime.strptime(f"{info['AppointmentDate']} {info['AppointmentTime']}", "%m/%d %H:%M")
        nodes.append({
            'id': f"Appointment_{date_time.strftime('%m/%d_%H:%M')}",
            'type': 'Appointment',
            'properties': {
                'Date': date_time.strftime("%m/%d"),  # Format: YYYY-MM-DD
                'Time': date_time.strftime("%H:%M")  # Format: HH:MM
            }
        })

    return nodes, patient_name

def create_relationships_from_info(info, patient_name):
    relationships = []

    if patient_name and info.get('DoctorName'):
        relationships.append({
            'source': f"Doctor_{info['DoctorName']}",
            'target': f"Patient_{patient_name}",
            'type': 'TREATS'
        })

    if patient_name and info.get('AppointmentDate') and info.get('AppointmentTime'):
        date_time = datetime.strptime(f"{info['AppointmentDate']} {info['AppointmentTime']}", "%m/%d %H:%M")
        appointment_id = f"Appointment_{date_time.strftime('%m/%d')}_{date_time.strftime('%H:%M')}"
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
    
    if info.get('MedicationFrequency') and info.get('Medication'):
        relationships.append({
            'source': f"Medication_{info['Medication']}",
            'target': f"MedicationFrequency_{info['MedicationFrequency']}",
            'type': 'MEDICATION_FREQUENCY'
        })

    return relationships

def get_appointment_details(username):
    username = f"Patient_{username}"
    with graph_db.session() as session:
        query = """
        MATCH (p:Patient {id: $username})-[:HAS_APPOINTMENT]->(a:Appointment)-[:WITH_DOCTOR]->(d:Doctor)
        RETURN p.id as PatientName, a.Date as AppointmentDate, a.Time as AppointmentTime, d.Name as DoctorName 
        """
        result = session.run(query, username=username)
        # appointments = [dict(record) for record in result]
        appointments = [{"Date": record["AppointmentDate"], "Time": record["AppointmentTime"], "Doctor": record["DoctorName"]} 
                        for record in result]
        if appointments:
            details = "Your appointments:\n"
            for apt in appointments:
                details += f"Date: {apt['Date']}, Time: {apt['Time']}, Doctor: {apt['Doctor']}\n"
        else:
            details = "You have no scheduled appointments."
        
        return details



def convert_update_query_to_graph_document(prompt, username):
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
        - Medication Frequency (if mentioned)

        Text: {prompt}

        Format the output as a JSON object with these keys: PatientName, DoctorName, AppointmentDate, AppointmentTime, MedicalCondition, Medication, MedicationFrequency.
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

        with graph_db.session() as session:
            get_appointment_query = """
            MATCH (p:Patient {id: $patient_id})-[:HAS_APPOINTMENT]->(a:Appointment)-[:WITH_DOCTOR]->(d:Doctor)
            RETURN a.id as AppointmentId, a.Date as Date, a.Time as Time, d.id as DoctorId, d.Name as DoctorName, p.id as PatientName
            LIMIT 1
            """
            result = session.run(get_appointment_query, patient_id=f"Patient_{username}")
            existing_appointment = result.single()
            print("existing appointment: ", existing_appointment)

            if not existing_appointment:
                return "No existing appointment found for the user."
            
            print("newinfo: ", info)
            # Step 2 & 3: Prepare update data
            update_data = {
                'PatientName': info.get('PatientName') or existing_appointment['PatientName'],
                'AppointmentDate': info.get('AppointmentDate') or existing_appointment['Date'],
                'AppointmentTime': info.get('AppointmentTime').split(' ')[0] if info.get('AppointmentTime') else existing_appointment['Time'],
                'DoctorName': info.get('DoctorName') or existing_appointment['DoctorName'],
                'MedicalCondition': info.get('MedicalCondition') or existing_appointment.get('MedicalCondition') or None,
                'Medication': info.get('Medication') or existing_appointment.get('Medication') or None,
                'MedicationFrequency': info.get('MedicationFrequency') or existing_appointment.get('MedicationFrequency') or None
            }


        nodes, patient_name = create_nodes_from_info(update_data, username)
        relationships = create_relationships_from_info(update_data, patient_name)
        
        return [Document(page_content=prompt, metadata={'nodes': nodes, 'relationships': relationships})]
    except Exception as e:
        print(f"An error occurred in convert_to_graph_document: {str(e)}")
        return None

def update_specific_appointment(graph_db, username, new_info):
    with graph_db.session() as session:
        # Step 1: Get existing appointment data
        appointment_node = next((node for node in new_info['nodes'] if node['type'] == 'Appointment'), None)
        doctor_node = next((node for node in new_info['nodes'] if node['type'] == 'Doctor'), None)
        patient_node = next((node for node in new_info['nodes'] if node['type'] == 'Patient'), None)
        print(appointment_node, doctor_node, patient_node)
        if not appointment_node or not doctor_node or not patient_node:
            return "Failed to extract necessary information from the graph document."

        update_query = """
        MATCH (p:Patient {id: $patient_id})-[:HAS_APPOINTMENT]->(a:Appointment)-[r:WITH_DOCTOR]->(d:Doctor)
        SET a.Date = $new_date, 
            a.Time = $new_time, 
            a.id = $new_appointment_id, 
            d.id = $new_doctor_id,
            d.Name = $new_doctor_name
        RETURN a.Date as NewDate, a.Time as NewTime, d.id as NewDoctor, p.id as PatientName
        """
        
        result = session.run(update_query, 
                             patient_id=f'Patient_{username}',
                             new_appointment_id=appointment_node['id'],
                             new_date=appointment_node['properties']['Date'],
                             new_time=appointment_node['properties']['Time'],
                             new_doctor_id=doctor_node['id'],
                             new_doctor_name=doctor_node['properties']['Name'])
        
        print(result)
        updated = result.single()
        print("updated? ", updated)
        if updated:
            return f"Appointment updated successfully for Patient: {updated['PatientName']}. Date: {updated['NewDate']}, Time: {updated['NewTime']}, Doctor: {updated['NewDoctor']}"
        else:
            return "Failed to update the appointment."