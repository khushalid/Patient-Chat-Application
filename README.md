# Patient Chat Application
### GenAI chatbot implementation using Gemini API


## Project Overview

This Django application allows patients to interact with an AI bot regarding their health and care plan. The AI bot handles health-related conversations, detects patient requests for changes to their treatment or appointments, and filters out irrelevant or sensitive topics.

## Setup and Installation

1. Clone the repository: 
```python
git clone [your-repo-url]
cd [your-repo-name]
```

2. Create and activate a virtual environment:
```python
python -m venv env
source env/bin/activate # On Windows use `env\Scripts\activate`
```

3. Install dependencies:
```python
pip install -r requirements.txt
```

4. Set up the database:
- Install PostgreSQL if not already installed
- Create a new database for the project
- Update the PostgreSQL configuration in `.env file`

- Install Neo4j if not already installed
- Create a new database for the project
- Update the Neo4j configuration in `.env file`
- In your virtual environment enter these commands to configure Neo4j:
```python
export NEO4J_HOME= <Path-To-Your-Neo4j-Folder>
echo $NEO4J_HOME
brew services start neo4j
```
5. Set up environment variables:
- Create a `.env` file in the project folder chatbot/chatbot
- Add the following line and their respective configuration data:
```python
SECRET_KEY = 'YOUR-SECRET-KEY'
GEMINI_API_KEY = Your-Gemini-API-Key

#DATABASES
ENGINE   = 'django.db.backends.postgresql' #change it to your database engine
NAME     = Your-Database-Name #change it to name of your database

#address of your database server and user data
#delete these rows if you going to use sqlite3
USER     = Your-Database-User
PASSWORD = Your-Datavase-Password
HOST     = '127.0.0.1' # change if host address is different
PORT     = '5432'  # change if port is different


# new4j configurations
NEO4J_URI = "bolt://localhost:7687"  # change if your Neo4j URL if different
NEO4J_USERNAME = Your-Neo4j-Username
NEO4J_PASSWORD = Your-Neo4j-Password

LANGCHAIN_API_KEY = Your-Langchain-API-Key
```

6. Apply migrations:
```python
python manage.py makemigrations
python manage.py migrate
```

7. Run the development server:
```python
python manage.py runserver
```

## Usage

1. Access the application at: `http://127.0.0.1:8000/`
2. Register yourself as a user (Enter Name, Email, Password)
3. Start a conversation with the AI bot
4. Ask health-related questions or make appointment requests

## Main Features

- Patient interaction with AI bot
- Health-related inquiries and care plan information
- Appointment and treatment protocol request handling
- Conversation history with timestamps
- Entity extraction and knowledge graph storage (Bonus)

## Technology Stack

- Backend: Django
- Database: PostgreSQL, Neo4j
- LLM: Gemini API
- Additional Libraries: Langchain, Langgraph (for LLM and RAG)

## Interface Images:
1. Health Related Question using RAG and Langchain
<img src="https://github.com/khushalid/Patient-Chat-Application/blob/2596f53a48561886da5ac85519ddc94137576041/Images/Screenshot%202024-09-30%20at%207.16.07%E2%80%AFPM.png" width="800">
<br>
2. Creating Appointment using Neo4j database
<img src="https://github.com/khushalid/Patient-Chat-Application/blob/2596f53a48561886da5ac85519ddc94137576041/Images/Screenshot%202024-09-30%20at%207.25.03%E2%80%AFPM.png" width="800">
<br>
3. Neo4j Knowledge Graph
<img src="https://github.com/khushalid/Patient-Chat-Application/blob/2596f53a48561886da5ac85519ddc94137576041/Images/Screenshot%202024-09-30%20at%207.25.17%E2%80%AFPM.png" width="800">
<br>
4. Updating an appointment
<img src="https://github.com/khushalid/Patient-Chat-Application/blob/2596f53a48561886da5ac85519ddc94137576041/Images/Screenshot%202024-09-30%20at%207.26.04%E2%80%AFPM.png" width="800">
<br>
5. Updated Neo4j Graph
<img src="https://github.com/khushalid/Patient-Chat-Application/blob/2596f53a48561886da5ac85519ddc94137576041/Images/Screenshot%202024-09-30%20at%207.26.17%E2%80%AFPM.png" width="800">
<br>
6. Chat history
<img src="https://github.com/khushalid/Patient-Chat-Application/blob/2596f53a48561886da5ac85519ddc94137576041/Images/Screenshot%202024-09-30%20at%207.26.54%E2%80%AFPM.png" width="800">
<br>
7. General (Non-Health) Queries
<img src="https://github.com/khushalid/Patient-Chat-Application/blob/2596f53a48561886da5ac85519ddc94137576041/Images/Screenshot%202024-09-30%20at%207.36.24%E2%80%AFPM.png" width="800">
<br>


## Assumptions and Limitations

- Single patient mode (no authentication required)
- Limited to health-related topics
- If a new appointment is created, old appointments are deleted.
- ChatBot Turn around time is slow because of mutliple LLM callbacks

## Future Improvements

- Implement multi-user authentication
- Improve time taken to answer user's queries
- Enhance entity extraction and knowledge graph utilization
- Improve conversation memory management for longer dialogues
  - Since I am using Gemini, I have limited tokens to generate response 
- Integrate with actual medical systems for real-time appointment updates
- Improve ChatBot Turn around time using better compute/ faster LLMs/ reducing LLM callbacks


## Some Debugging commands:
To install postgres
```python
brew install postgresql
psql -U postgres -d postgres
pass: <your password>
```

If you face error while importing of pysocgp2
```python
python -m pip install psycopg2-binary
python -c "import psycopg2"
```

If brew is not in your environment, run the following commands:
```python
echo 'export PATH=/opt/homebrew/bin:$PATH' >> ~/.zshrc
source ~/.zshrc
```
