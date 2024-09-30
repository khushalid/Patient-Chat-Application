import os
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from dotenv import load_dotenv
from django.conf import settings
from langchain_google_genai import GoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import asyncio
import pickle
import google.generativeai as genai
import chromadb
from typing import List
import google.generativeai as genai
import re
import pdb
from langchain_community.document_loaders import UnstructuredPDFLoader
import tiktoken
from langchain_elasticsearch import ElasticsearchStore
from elasticsearch import Elasticsearch
from langchain.vectorstores import Chroma
import dill

def load_pdf(folder_path, pkl_path="./vector_db/health_docs.pkl"):
    health_docs = []
    if os.path.exists(pkl_path):
        with open(pkl_path, 'rb') as f:
            health_docs = dill.load(f)
    else:
        for f in os.listdir(folder_path):
            if f.endswith('.pdf'):
                pdf_path = os.path.join(folder_path, f)
                loader = UnstructuredPDFLoader(pdf_path)
                health_docs.extend(loader.load())
        with open(pkl_path, 'wb') as f:
            dill.dump(health_docs, f)

    return health_docs


def tiktoken_len(text):
    tokenizer = tiktoken.get_encoding('cl100k_base')
    tokens = tokenizer.encode(
        text,
        disallowed_special=()
    )
    return len(tokens)

def get_text_chunks(health_docs):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1800,
        chunk_overlap=180,
        length_function=tiktoken_len,
        separators=["\n\n", "\n", " ", ""]
    )
    chunks = text_splitter.split_documents(health_docs)
    
    return chunks

def query_elasticsearch(query, es_store):
    retriever = es_store.as_retriever(search_kwargs={"k": 5})
    results = retriever.get_relevant_documents(query)
    return results

def create_or_load_vector_store(health_docs):
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=settings.GEMINI_API_KEY
    )
    db = Chroma.from_documents(health_docs, embeddings)
    return db

def query_vector_store(query, vector_store, k=3):
    results = vector_store.similarity_search(query, k=k)
    return results

def make_rag_prompt(query, relevant_docs):
  prompt = ("""You are a helpful and informative bot that answers questions using text from the reference passage included below. \
  Be sure to respond in a complete sentence, or if needed bullet points, being comprehensive, including all relevant background information. \
  However, you are talking to a non-technical audience, so be sure to break down complicated concepts and \
  strike a friendly and converstional tone. \
  If the passage is irrelevant to the answer, you may ignore the passage and give the answer from your understanding. The answer should be around 500 words.
  QUESTION: '{query}'
  Relevant Information: {relevant_docs}

  ANSWER:
  """).format(query=query, relevant_docs=relevant_docs)

  return prompt

def rag_pipeline(query):
    pdf_folder_path = './RAGData'
    health_docs = load_pdf(pdf_folder_path)
    chunked_docs = get_text_chunks(health_docs)
    vector_store = create_or_load_vector_store(chunked_docs)

    relevant_docs = query_vector_store(query, vector_store)
    prompt = make_rag_prompt(query, relevant_docs)
    return prompt
