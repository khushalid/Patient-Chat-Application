
from django.contrib.auth.models import User
from chat.models import Chat, Message
from rest_framework.decorators import api_view
from .serializers import MessageSerializer
from rest_framework.response import Response
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import google.generativeai as genai
import json
from django.conf import settings
from chat.graph import *  # Import Neo4j functions
from langchain_core.documents import Document
from chat.healtRAG import rag_pipeline, build_knowledge_base

# Replace OpenAI with Gemini API Key
gemini_api_key = settings.GEMINI_API_KEY  # Update your settings to include GEMINI_API_KEY
# Ensure the API key is configured
genai.configure(api_key=settings.GEMINI_API_KEY)

vector_store = build_knowledge_base('./RAGData')

def classify_prompt(prompt):
    # Define the prompt for classification
    classification_prompt = f"""
    You are a classifier that determines if a question is related to booking an appointment with the doctor, a simple health-related question or a general question. 
    In appointment there are 3 categories that if user is asking to book a new appointment, to check the appointment, or to update an appointment
    Please categorize the following question into 'Book Appointment', 'Check Appointment', 'Update Appointment', 'Health', or 'General:

    Question: "{prompt}"
    """

    # Call the API for classification
    response = genai.GenerativeModel("gemini-pro").generate_content(classification_prompt)

    # Extract classification result
    category = response.text.strip()
    return category

@api_view(['GET'])
def getMessages(request, pk):
    user = User.objects.get(username=request.user.username)
    print(pk)
    chat = Chat.objects.filter(user=user).get(pk=pk)
    messages = Message.objects.filter(chat=chat)
    serializer = MessageSerializer(messages, many=True)
    return Response(serializer.data)


@csrf_exempt
def get_prompt_result(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            prompt = data.get('prompt')
            user = User.objects.get(username=request.user.username)
            chat = Chat.objects.filter(user=user)[0]
            message = Message(message=prompt, is_user=True, chat=chat)
            message.save()
            if not prompt:
                return JsonResponse({'error': 'Prompt is missing in the request'}, status=400)
            
            category = classify_prompt(prompt)
            print(f"Category: {category}")

            if category == "Health":
                try:
                    prompt = rag_pipeline(prompt, vector_store)
                    assistant_reply = llm.invoke(prompt)
                    message = Message(message=assistant_reply, is_user=False, chat=chat)
                    message.save()

                    return JsonResponse(assistant_reply, safe=False)
                
                except Exception as error:
                    error_msg = f"Error: {str(error)}"
                    print(error_msg)
                    return JsonResponse({'error': error_msg}, status=500)
                
            elif category == 'Book Appointment':
                try:
                    graph_documents = convert_to_graph_document(prompt, user)

                    
                    if not graph_documents or not graph_documents[0].metadata['nodes']:
                        assistant_reply = "I'm sorry, I couldn't extract any appointment information from your request. Could you please provide more details?"
                    else:
                        # Store the extracted graph in Neo4j
                        store_graph_in_neo4j(graph_db, graph_documents[0].metadata)

                        # Generate a response based on the extracted graph
                        response_prompt = f"""
                        Based on the following appointment information extracted from the user's query:
                        Nodes: {graph_documents[0].metadata['nodes']}
                        Relationships: {graph_documents[0].metadata['relationships']}
                        
                        Generate a friendly and informative response to the user's request:
                        "{prompt}"
                        
                        Include any relevant details about the appointment and ask for any additional information if needed.
                        If an appointment was requested, confirm the details. If information is missing, ask for it.
                        If the user is checking existing appointments, provide that information.
                        """

                        assistant_reply = llm.invoke(response_prompt)

                    message = Message(message=assistant_reply, is_user=False, chat=chat)
                    message.save()
                    return JsonResponse(assistant_reply, safe=False)
                
                except Exception as error:
                    error_msg = f"Error processing appointment request: {str(error)}"
                    print(error_msg)
                    return JsonResponse({'error': error_msg}, status=500)
                
            elif category == 'Check Appointment':
                try:
                    appointment_details = get_appointment_details(user.username)
                    response_prompt = f"""
                    The user has requested to check their appointment details. Here are the current appointments:
                    {appointment_details}

                    Please provide a friendly and informative response to the user based on this information.
                    If there are no appointments, suggest that they book one.
                    If there are appointments, summarize them briefly and ask if they need any further assistance.
                    """
                    assistant_reply = llm.invoke(response_prompt)
                    message = Message(message=assistant_reply, is_user=False, chat=chat)
                    message.save()
                    return JsonResponse(assistant_reply, safe=False)
                except Exception as error:
                    error_msg = f"Error checking appointment: {str(error)}"
                    print(error_msg)
                    return JsonResponse({'error': error_msg}, status=500)

            elif category == 'Update Appointment':
                try:
                    graph_documents = convert_update_query_to_graph_document(prompt, user)

                    if not graph_documents or not graph_documents[0].metadata['nodes']:
                        assistant_reply = "I'm sorry, I couldn't extract any appointment information from your request. Could you please provide more details?"
                    else:
                        # Store the extracted graph in Neo4j
                        updated_appointment = update_specific_appointment(graph_db, user, graph_documents[0].metadata)
                    
                    response_prompt = f"""
                    Based on the following appointment information extracted from the user's query:
                    Nodes: {graph_documents[0].metadata['nodes']}
                    Relationships: {graph_documents[0].metadata['relationships']}
                        
                    Generate a friendly and informative response to the user's request:
                    "{prompt}"
                    With this updated appointment details:
                    "{updated_appointment}

                    Please provide a friendly and informative response to the user based on this information.
                    If the update was successful, confirm the new appointment details.
                    If the update failed, explain why and suggest alternatives if possible.
                    """
                    assistant_reply = llm.invoke(response_prompt)
                    message = Message(message=assistant_reply, is_user=False, chat=chat)
                    message.save()
                    return JsonResponse(assistant_reply, safe=False)
                except Exception as error:
                    error_msg = f"Error updating appointment: {str(error)}"
                    print(error_msg)
                    return JsonResponse({'error': error_msg}, status=500)

            else:
                assistant_reply = 'I can only respond to health-related questions.'
                message = Message(message=assistant_reply, is_user=False, chat=chat)
                message.save()
                return JsonResponse(assistant_reply, safe=False)
        except Exception as error:
            error_msg = f"Error: {str(error)}"
            print(error_msg)
            return JsonResponse({'error': error_msg}, status=500)

    return JsonResponse({'error': 'Method not allowed'}, status=405)
