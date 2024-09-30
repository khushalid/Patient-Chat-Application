# Patient Chat Application
### Simple chatbot implementation using Gemini API


## Project Overview

This Django application allows patients to interact with an AI bot regarding their health and care plan. The AI bot handles health-related conversations, detects patient requests for changes to their treatment or appointments, and filters out irrelevant or sensitive topics.

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


## Setup and Installation

1. Clone the repository: 
git clone [your-repo-url]
cd [your-repo-name]

2. Create and activate a virtual environment:
python -m venv env
source env/bin/activate # On Windows use `env\Scripts\activate`

3. Install dependencies:
pip install -r requirements.txt

4. Set up the database:
- Install PostgreSQL if not already installed
- Create a new database for the project
- Update the PostgreSQL configuration in `.env file`

- Install Neo4j if not already installed
- Create a new database for the project
- Update the Neo4j configuration in `.env file`
- In your virtual environment enter these commands to configure Neo4j
    - `export NEO4J_HOME= <Path to your neo4j folder>`
    - `echo $NEO4J_HOME`
    - `brew services start neo4j`

5. Apply migrations:
python manage.py makemigrations
python manage.py migrate

6. Set up environment variables:
- Create a `.env` file in the project folder chatbot/chatbot
- Add this line `SECRET_KEY = 'YOUR-SECRET-KEY'`
- Add your Gemini API key: `GEMINI_API_KEY=your_api_key_here`
- DATABASES Postgresql
    - `ENGINE   = <change it to your database engine>`
    - `NAME     = <change it to name of your database>`
    - `USER     = <change it to your database user>`
    - `PASSWORD = <change it to your database password>`
    - `HOST     = 127.0.0.1` # change if differnet
    - `PORT     = 5432` # change if different
- Neo4j configurations
    - `NEO4J_URI = "bolt://localhost:7687" # change it to your Neo4j URL if different`
    - `NEO4J_USERNAME = <change it to your Neo4j name>`
    - `NEO4J_PASSWORD = <change it to your Neo4j password>`
- Add your Langchain API key: `LANGCHAIN_API_KEY = <your_api_key_here>`

7. Run the development server:
python manage.py runserver

## Usage

1. Access the application at: http://127.0.0.1:8000/
2. Register yourself as a user (Enter Name, Email, Password)
3. Start a conversation with the AI bot
4. Ask health-related questions or make appointment requests

## Assumptions and Limitations

- Single patient mode (no authentication required)
- Limited to health-related topics
- If a new appointment is created, old appointments are deleted.

## Future Improvements

- Implement multi-user authentication
- Improve time taken to answer user's queries
- Enhance entity extraction and knowledge graph utilization
- Improve conversation memory management for longer dialogues
- Integrate with actual medical systems for real-time appointment updates


## Some Debugging commands:
To install postgres
1. `brew install postgresql`
2. `psql -U postgres -d postgres`
3. `pass: <your password>`

If you face error while importing of pysocgp2
1. `python -m pip install psycopg2-binary`
2. `python -c "import psycopg2"`
