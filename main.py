import streamlit as st
import os
from pathlib import Path
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.agents import initialize_agent
from langchain_community.callbacks.streamlit import StreamlitCallbackHandler
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

st.set_page_config(page_title="LangChain: Chat with SQL DB", page_icon="🦜")
st.title("🦜 LangChain: Chat with Student Database")

LOCALDB = "USE_LOCALDB"
MYSQL = "USE_MYSQL"

# Initialize session state for API key
if "groq_api_key" not in st.session_state:
    # Try to load from environment variable first
    env_api_key = os.getenv("GROQ_API_KEY", "")
    st.session_state.groq_api_key = env_api_key

radio_opt = ["Use SQLite Database (student.db)", "Connect to MySQL Database"]

selected_opt = st.sidebar.radio(label="Choose the database you want to chat with", options=radio_opt)

if radio_opt.index(selected_opt) == 1:
    db_uri = MYSQL
    mysql_host = st.sidebar.text_input("Provide MySQL Host", value=os.getenv("MYSQL_HOST", "localhost"))
    mysql_user = st.sidebar.text_input("MySQL User", value=os.getenv("MYSQL_USER", "root"))
    mysql_password = st.sidebar.text_input("MySQL password", type="password", value=os.getenv("MYSQL_PASSWORD", ""))
    mysql_db = st.sidebar.text_input("MySQL database", value=os.getenv("MYSQL_DATABASE", "student_management"))
else:
    db_uri = LOCALDB

# API Key section with persistence
st.sidebar.markdown("### 🔑 Groq API Key Configuration")

# If API key is already set, show it and provide option to change
if st.session_state.groq_api_key:
    st.sidebar.success("✅ API Key is configured")
    if st.sidebar.button("Change API Key"):
        st.session_state.groq_api_key = ""
        st.rerun()
else:
    # First time setup or key was cleared
    api_key = st.sidebar.text_input(
        label="Enter your Groq API Key", 
        type="password", 
        placeholder="Enter your Groq API key",
        value=os.getenv("GROQ_API_KEY", ""),
        key="api_key_input"
    )
    
    if api_key:
        st.session_state.groq_api_key = api_key
        st.sidebar.success("✅ API Key saved!")
        st.rerun()
    else:
        st.info("Please add your Groq API key to continue")
        st.stop()

## LLM model - Use the persisted API key
llm = ChatGroq(groq_api_key=st.session_state.groq_api_key, model_name="llama-3.1-8b-instant", streaming=True)

@st.cache_resource(ttl="2h")
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None):
    if db_uri == LOCALDB:
        # Use the student.db file in the same directory
        dbfilepath = (Path(__file__).parent / "student.db").absolute()
        
        # Check if database file exists
        if not dbfilepath.exists():
            st.error(f"SQLite database file not found at: {dbfilepath}")
            st.info("Please make sure you've run sqlite.py to create the student.db file")
            st.stop()
            
        st.success(f"✅ Connected to SQLite database: {dbfilepath.name}")
        
        # Create SQLAlchemy engine for SQLite
        engine = create_engine(f"sqlite:///{dbfilepath}")
        return SQLDatabase(engine)
        
    elif db_uri == MYSQL:
        if not (mysql_host and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()
        
        # MySQL connection string  
        mysql_port = os.getenv("MYSQL_PORT", "3306")
        
        # Clean the host value if it contains a port
        if ':' in mysql_host:
            mysql_host = mysql_host.split(':')[0]
            st.warning(f"⚠️ Removed port from host. Using host: '{mysql_host}'")
        
        connection_string = f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
        
        try:
            engine = create_engine(connection_string)
            # Test the connection
            with engine.connect() as conn:
                from sqlalchemy import text
                conn.execute(text("SELECT 1"))
            st.success("✅ Successfully connected to MySQL database!")
            return SQLDatabase(engine)
        except Exception as e:
            st.error(f"❌ Failed to connect to MySQL: {str(e)}")
            st.stop()

# Configure database based on user selection
try:
    if db_uri == MYSQL:
        db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db)
    else:
        db = configure_db(db_uri)
        
    # Display database info
    with st.sidebar.expander("📊 Database Info"):
        st.write(f"Connected to: {'MySQL' if db_uri == MYSQL else 'SQLite'}")
        if db_uri == LOCALDB:
            st.write("Database: student.db")
            st.write("Table: STUDENT")
            st.write("Columns: NAME, CLASS, SECTION, MARKS")
        
except Exception as e:
    st.error(f"Database configuration failed: {e}")
    st.stop()

## Create toolkit and agent
try:
    # Create the toolkit
    toolkit = SQLDatabaseToolkit(db=db, llm=llm)
    
    # Use create_sql_agent with minimal configuration to prevent loops
    agent = create_sql_agent(
        llm=llm,
        toolkit=toolkit,
        verbose=False,  # Disable verbose to reduce overhead
        agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
        handle_parsing_errors=True,
        max_iterations=1,  # Only 1 attempt - force immediate execution
        max_execution_time=8,  # Very short timeout
        return_intermediate_steps=False,
    )
    
except Exception as e:
    st.error(f"Failed to create SQL agent: {e}")
    st.stop()

# Display sample data
with st.expander("📋 View Sample Data"):
    try:
        sample_data = db.run("SELECT * FROM STUDENT LIMIT 5;")
        st.write(sample_data)
    except Exception as e:
        st.error(f"Could not fetch sample data: {e}")

# Initialize chat history
if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "Hi! I can help you query the student database. Ask me anything about the students, their classes, or marks!"}]

# Display chat messages
for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

# Chat input
user_query = st.chat_input(placeholder="Ask about students, classes, marks...")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        # Skip the problematic agent and go directly to smart SQL execution
        query_lower = user_query.lower()
        
        try:
            # Smart pattern matching for immediate SQL execution
            if "show all student" in query_lower or "all student" in query_lower:
                with st.spinner("📊 Fetching all students..."):
                    result = db.run("SELECT * FROM STUDENT LIMIT 10;")
                    answer = f"Here are the students in the database:\n\n{result}"
                    
            elif "marks above" in query_lower or "marks >" in query_lower:
                with st.spinner("🔍 Finding students with high marks..."):
                    # Extract number from query
                    import re
                    numbers = re.findall(r'\d+', user_query)
                    threshold = numbers[0] if numbers else "80"
                    result = db.run(f"SELECT NAME, CLASS, SECTION, MARKS FROM STUDENT WHERE MARKS > {threshold} ORDER BY MARKS DESC;")
                    answer = f"Students with marks above {threshold}:\n\n{result}"
                    
            elif "highest mark" in query_lower or "best mark" in query_lower or "top student" in query_lower:
                with st.spinner("🏆 Finding top performers..."):
                    result = db.run("SELECT NAME, CLASS, SECTION, MARKS FROM STUDENT ORDER BY MARKS DESC LIMIT 5;")
                    answer = f"Students with highest marks:\n\n{result}"
                    
            elif "lowest mark" in query_lower or "worst mark" in query_lower:
                with st.spinner("📉 Finding students who need help..."):
                    result = db.run("SELECT NAME, CLASS, SECTION, MARKS FROM STUDENT ORDER BY MARKS ASC LIMIT 5;")
                    answer = f"Students with lowest marks:\n\n{result}"
                    
            elif "count" in query_lower or "how many" in query_lower:
                with st.spinner("🔢 Counting students..."):
                    if "class" in query_lower:
                        result = db.run("SELECT CLASS, COUNT(*) as Student_Count FROM STUDENT GROUP BY CLASS ORDER BY CLASS;")
                        answer = f"Number of students in each class:\n\n{result}"
                    elif "section" in query_lower:
                        result = db.run("SELECT SECTION, COUNT(*) as Student_Count FROM STUDENT GROUP BY SECTION ORDER BY SECTION;")
                        answer = f"Number of students in each section:\n\n{result}"
                    else:
                        result = db.run("SELECT COUNT(*) as Total_Students FROM STUDENT;")
                        answer = f"Total number of students: {result}"
                        
            elif "average" in query_lower:
                with st.spinner("📊 Calculating averages..."):
                    if "section" in query_lower:
                        result = db.run("SELECT SECTION, ROUND(AVG(MARKS), 2) as Average_Marks FROM STUDENT GROUP BY SECTION ORDER BY Average_Marks DESC;")
                        answer = f"Average marks by section:\n\n{result}"
                    elif "class" in query_lower:
                        result = db.run("SELECT CLASS, ROUND(AVG(MARKS), 2) as Average_Marks FROM STUDENT GROUP BY CLASS ORDER BY Average_Marks DESC;")
                        answer = f"Average marks by class:\n\n{result}"
                    else:
                        result = db.run("SELECT ROUND(AVG(MARKS), 2) as Overall_Average FROM STUDENT;")
                        answer = f"Overall average marks: {result}"
                        
            elif any(word in query_lower for word in ['select', 'from', 'where', 'group by', 'order by']):
                with st.spinner("⚙️ Executing SQL query..."):
                    # Try to execute as direct SQL
                    result = db.run(user_query)
                    answer = f"Query result:\n\n{result}"
                    
            else:
                # Try the agent as a last resort with immediate fallback
                try:
                    with st.spinner("🤔 Let me try to understand your query..."):
                        response = agent.invoke({"input": user_query})
                        answer = response.get("output", "")
                        
                        # Clean up agent response
                        if "Final Answer:" in answer:
                            answer = answer.split("Final Answer:")[-1].strip()
                        
                        # If agent gives a poor response, fall back to help
                        if not answer or len(answer.strip()) < 10 or "Agent stopped" in answer:
                            raise Exception("Agent response incomplete")
                            
                except:
                    # Final fallback - show help
                    answer = """I couldn't understand that query. Here are some examples of what I can help with:

🔹 **Show all students** - Display all student records
🔹 **Students with marks above 80** - Filter by marks  
🔹 **Who has the highest marks?** - Top performers
🔹 **Who has the lowest marks?** - Students needing help
🔹 **How many students are there?** - Count students
🔹 **How many students in each class?** - Count by class
🔹 **Average marks by class** - Calculate class averages
🔹 **Average marks by section** - Calculate section averages

Try asking one of these questions!"""
            
            st.write(answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
            
        except Exception as e:
            error_response = f"I'm having trouble accessing the database. Please check the connection.\n\nError: {str(e)}"
            st.error(error_response)
            st.session_state.messages.append({"role": "assistant", "content": error_response})

# Add helpful examples in the sidebar
with st.sidebar.expander("💡 Example Queries"):
    st.markdown("""
    **Try asking:**
    - Show all students
    - Which students are in Data Science class?
    - Who has the highest marks?
    - Show students with marks above 80
    - How many students are in each class?
    - What's the average marks by section?
    - List all students in Section A
    - Show students with marks less than 50
    """)

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("💾 Database: student.db")
st.sidebar.markdown("📊 Table: STUDENT")
st.sidebar.markdown("🦜 Powered by LangChain + Streamlit")