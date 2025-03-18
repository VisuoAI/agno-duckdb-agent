import streamlit as st
import duckdb
import os
from agno.agent import Agent
from agno.tools.duckdb import DuckDbTools
from agno.models.anthropic import Claude

# Streamlit UI Setup
st.set_page_config(page_title="DuckDB Chat Agent", layout="wide")

# Sidebar - File Upload and Database Setup
st.sidebar.header("Upload CSV and Create Database")
# Allow multiple CSV files to be uploaded
uploaded_files = st.sidebar.file_uploader("Upload CSV Files", type=["csv"], accept_multiple_files=True)
db_filename = "data_db.duckdb"  # Changed to a more generic name

def save_uploaded_file(uploaded_file):
    file_path = os.path.join("./", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Create or recreate the database if CSV files are uploaded
if uploaded_files:
    conn = duckdb.connect(db_filename)
    # Drop existing table to avoid duplication
    conn.execute("DROP TABLE IF EXISTS data")
    first_file = True
    for uploaded_file in uploaded_files:
        csv_path = save_uploaded_file(uploaded_file)
        if first_file:
            # Create table from the first CSV
            conn.execute(f"CREATE TABLE data AS SELECT * FROM read_csv_auto('{csv_path}')")
            first_file = False
        else:
            # Append data from subsequent CSV files
            conn.execute(f"INSERT INTO data SELECT * FROM read_csv_auto('{csv_path}')")
    conn.close()
    st.sidebar.success(f"Database Created: {db_filename}")

# Check if the database exists before initializing the agent and chat interface
if os.path.exists(db_filename):
    # Initialize the agent using the created database
    agent = Agent(
        model=Claude(id="claude-3-5-sonnet-20240620", api_key="your_api_key_here"),
        tools=[DuckDbTools(db_path=db_filename)],
        system_message="Use this data for any queries you have related to the uploaded CSV files.",
    )
else:
    st.error("Database not found. Please upload CSV file(s) to create the database.")

# Main Area - Chat Interface
st.title("DuckDB Chat Agent")
st.write("Enter your query below and press Enter to get a response.")

if os.path.exists(db_filename):
    # Initialize session state for messages if not present
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    # Render previous messages
    for message in st.session_state["messages"]:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input box
    user_input = st.chat_input("Ask me anything about the uploaded data...")

    if user_input:
        st.session_state["messages"].append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)
        
        # Get the response from the agent
        response = agent.run(user_input, markdown=True, stream=False)
    
        with st.chat_message("assistant"):
            st.markdown(response)
        st.session_state["messages"].append({"role": "assistant", "content": response})


#TODO - add graphs also
