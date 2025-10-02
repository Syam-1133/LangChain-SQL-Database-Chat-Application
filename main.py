import streamlit as st
import os
import pandas as pd
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    st.warning("Plotly not available. Install with: pip install plotly")

from pathlib import Path
from langchain_community.agent_toolkits.sql.base import create_sql_agent
from langchain_community.utilities import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain_community.agent_toolkits.sql.toolkit import SQLDatabaseToolkit
from sqlalchemy import create_engine, text
from langchain_groq import ChatGroq
from dotenv import load_dotenv
import time
from datetime import datetime
import io

# Load environment variables from .env file
load_dotenv()

# Enhanced page configuration
st.set_page_config(
    page_title="🦜 SQL Database Chat", 
    page_icon="🤖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        color: white;
    }
    
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    
    .query-suggestion {
        background: #f0f2f6;
        padding: 0.8rem;
        border-radius: 8px;
        border-left: 4px solid #667eea;
        margin: 0.5rem 0;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    
    .query-suggestion:hover {
        background: #e8eaf6;
        transform: translateX(5px);
    }
    
    .status-indicator {
        display: inline-block;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        margin-right: 8px;
    }
    
    .status-connected { background-color: #4CAF50; }
    .status-disconnected { background-color: #f44336; }
    .status-connecting { background-color: #ff9800; }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px 20px;
    }
    
    .result-container {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e0e0e0;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Main header with enhanced styling
st.markdown("""
<div class="main-header">
    <h1>🦜 LangChain SQL Database Chat</h1>
    <p>Transform natural language into powerful SQL queries with AI</p>
</div>
""", unsafe_allow_html=True)

LOCALDB = "USE_LOCALDB"
MYSQL = "USE_MYSQL"

# Initialize session state for API key and query history
if "groq_api_key" not in st.session_state:
    env_api_key = os.getenv("GROQ_API_KEY", "")
    st.session_state.groq_api_key = env_api_key

if "query_history" not in st.session_state:
    st.session_state.query_history = []

if "database_stats" not in st.session_state:
    st.session_state.database_stats = {}

# Enhanced sidebar with tabs
with st.sidebar:
    st.markdown("## ⚙️ Configuration")
    
    # Database selection with enhanced UI
    st.markdown("### 🗄️ Database Selection")
    radio_opt = ["🗃️ SQLite Database (student.db)", "🌐 MySQL Database"]
    selected_opt = st.radio("Choose database:", radio_opt, index=0)
    
    # Connection status indicator
    if "connection_status" not in st.session_state:
        st.session_state.connection_status = "disconnected"
    
    status_color = {
        "connected": "status-connected",
        "connecting": "status-connecting", 
        "disconnected": "status-disconnected"
    }
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; margin: 1rem 0;">
        <span class="status-indicator {status_color[st.session_state.connection_status]}"></span>
        <span>Status: {st.session_state.connection_status.title()}</span>
    </div>
    """, unsafe_allow_html=True)

if radio_opt.index(selected_opt) == 1:
    db_uri = MYSQL
    st.markdown("### 🔧 MySQL Configuration")
    
    with st.expander("📋 Connection Details", expanded=True):
        mysql_host = st.text_input("🏠 Host", value=os.getenv("MYSQL_HOST", "localhost"))
        mysql_user = st.text_input("👤 Username", value=os.getenv("MYSQL_USER", "root"))
        mysql_password = st.text_input("🔐 Password", type="password", value=os.getenv("MYSQL_PASSWORD", ""))
        mysql_db = st.text_input("🗄️ Database", value=os.getenv("MYSQL_DATABASE", "student_management"))
else:
    db_uri = LOCALDB

# Enhanced API Key section
st.markdown("### 🔑 AI Configuration")

if st.session_state.groq_api_key:
    st.success("✅ API Key configured")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔄 Change Key", use_container_width=True):
            st.session_state.groq_api_key = ""
            st.rerun()
    with col2:
        if st.button("🧪 Test Connection", use_container_width=True):
            with st.spinner("Testing..."):
                time.sleep(1)
                st.success("✅ Connection successful!")
else:
    api_key = st.text_input(
        "Enter Groq API Key", 
        type="password", 
        placeholder="gsk_...",
        help="Get your free API key from https://console.groq.com/"
    )
    
    if api_key:
        st.session_state.groq_api_key = api_key
        st.success("✅ API Key saved!")
        st.rerun()
    else:
        st.warning("⚠️ Please add your Groq API key to continue")
        st.stop()

# Quick Actions section
st.markdown("### ⚡ Quick Actions")

col1, col2 = st.columns(2)
with col1:
    if st.button("📊 View Stats", use_container_width=True):
        st.session_state.show_stats = True
        
with col2:
    if st.button("🗑️ Clear History", use_container_width=True):
        st.session_state.query_history = []
        if "messages" in st.session_state:
            st.session_state.messages = [{"role": "assistant", "content": "Hi! I can help you query the student database. Ask me anything!"}]
        st.success("History cleared!")

# Query suggestions
st.markdown("### 💡 Quick Queries")

sample_queries = [
    "Show all students",
    "Students with marks > 80",
    "Average marks by class", 
    "Top 3 performers",
    "Students in section A",
    "Count by class"
]

for query in sample_queries:
    if st.button(f"💬 {query}", key=f"quick_{query}", use_container_width=True):
        # Add to chat
        if "messages" not in st.session_state:
            st.session_state.messages = []
        st.session_state.messages.append({"role": "user", "content": query})
        st.rerun()

## LLM model - Use the persisted API key
llm = ChatGroq(groq_api_key=st.session_state.groq_api_key, model_name="llama-3.1-8b-instant", streaming=True)

# Helper functions for data visualization
def create_visualization(data, query_type, title="Query Results"):
    """Create visualizations based on query type and data"""
    if not PLOTLY_AVAILABLE:
        return None
        
    try:
        # Convert string data to DataFrame if needed
        if isinstance(data, str):
            lines = data.strip().split('\n')
            if len(lines) > 1:
                # Try to parse as table data
                rows = []
                headers = None
                for line in lines:
                    if '|' in line and not line.startswith('|---'):
                        parts = [part.strip() for part in line.split('|') if part.strip()]
                        if headers is None:
                            headers = parts
                        else:
                            rows.append(parts)
                
                if headers and rows:
                    df = pd.DataFrame(rows, columns=headers)
                    
                    # Try to convert numeric columns
                    for col in df.columns:
                        try:
                            df[col] = pd.to_numeric(df[col])
                        except:
                            pass
                    
                    return create_charts(df, query_type, title)
        
        return None
    except Exception as e:
        st.error(f"Visualization error: {e}")
        return None

def create_charts(df, query_type, title):
    """Create different types of charts based on data"""
    charts = []
    
    try:
        # Bar chart for categorical data with numeric values
        numeric_cols = df.select_dtypes(include=['number']).columns
        categorical_cols = df.select_dtypes(include=['object']).columns
        
        if len(numeric_cols) > 0 and len(categorical_cols) > 0 and PLOTLY_AVAILABLE:
            # Bar chart
            fig_bar = px.bar(
                df, 
                x=categorical_cols[0], 
                y=numeric_cols[0],
                title=f"{title} - Bar Chart",
                color=categorical_cols[0] if len(categorical_cols) > 0 else None
            )
            fig_bar.update_layout(height=400)
            charts.append(("bar", fig_bar))
            
            # Pie chart if suitable
            if len(df) <= 10 and PLOTLY_AVAILABLE:  # Only for small datasets
                fig_pie = px.pie(
                    df, 
                    values=numeric_cols[0], 
                    names=categorical_cols[0],
                    title=f"{title} - Distribution"
                )
                charts.append(("pie", fig_pie))
        
        # Line chart for time series or sequential data
        if len(numeric_cols) >= 2 and PLOTLY_AVAILABLE:
            fig_line = px.line(
                df, 
                x=df.columns[0], 
                y=numeric_cols[0],
                title=f"{title} - Trend"
            )
            fig_line.update_layout(height=400)
            charts.append(("line", fig_line))
            
    except Exception as e:
        st.error(f"Chart creation error: {e}")
    
    return charts

def export_data(data, format_type="csv"):
    """Export data in different formats"""
    try:
        if isinstance(data, str):
            # Convert string data to DataFrame
            lines = data.strip().split('\n')
            rows = []
            headers = None
            
            for line in lines:
                if '|' in line and not line.startswith('|---'):
                    parts = [part.strip() for part in line.split('|') if part.strip()]
                    if headers is None:
                        headers = parts
                    else:
                        rows.append(parts)
            
            if headers and rows:
                df = pd.DataFrame(rows, columns=headers)
                
                if format_type == "csv":
                    return df.to_csv(index=False)
                elif format_type == "json":
                    return df.to_json(orient='records', indent=2)
                elif format_type == "excel":
                    buffer = io.BytesIO()
                    df.to_excel(buffer, index=False)
                    return buffer.getvalue()
        
        return None
    except Exception as e:
        st.error(f"Export error: {e}")
        return None

@st.cache_resource(ttl="2h")
def configure_db(db_uri, mysql_host=None, mysql_user=None, mysql_password=None, mysql_db=None):
    st.session_state.connection_status = "connecting"
    
    try:
        if db_uri == LOCALDB:
            # Use the student.db file in the same directory
            dbfilepath = (Path(__file__).parent / "student.db").absolute()
            
            # Check if database file exists
            if not dbfilepath.exists():
                st.session_state.connection_status = "disconnected"
                st.error(f"SQLite database file not found at: {dbfilepath}")
                st.info("Please make sure you've run sqlite.py to create the student.db file")
                st.stop()
                
            # Create SQLAlchemy engine for SQLite
            engine = create_engine(f"sqlite:///{dbfilepath}")
            
            # Test connection and get stats
            with engine.connect() as conn:
                try:
                    result = conn.execute(text("SELECT COUNT(*) FROM STUDENT"))
                    student_count = result.fetchone()[0]
                    
                    # Get class distribution
                    result = conn.execute(text("SELECT CLASS, COUNT(*) FROM STUDENT GROUP BY CLASS"))
                    class_dist = dict(result.fetchall())
                    
                    # Get average marks
                    result = conn.execute(text("SELECT AVG(MARKS) FROM STUDENT"))
                    avg_marks = round(result.fetchone()[0], 2)
                    
                    st.session_state.database_stats = {
                        "total_students": student_count,
                        "class_distribution": class_dist,
                        "average_marks": avg_marks,
                        "database_type": "SQLite"
                    }
                except Exception as e:
                    st.warning(f"Could not fetch database statistics: {e}")
            
            st.session_state.connection_status = "connected"
            st.success(f"✅ Connected to SQLite database: {dbfilepath.name}")
            return SQLDatabase(engine)
            
        elif db_uri == MYSQL:
            if not (mysql_host and mysql_user and mysql_password and mysql_db):
                st.session_state.connection_status = "disconnected"
                st.error("Please provide all MySQL connection details.")
                st.stop()
            
            # MySQL connection string  
            mysql_port = os.getenv("MYSQL_PORT", "3306")
            
            # Clean the host value if it contains a port
            if ':' in mysql_host:
                mysql_host = mysql_host.split(':')[0]
                st.warning(f"⚠️ Removed port from host. Using host: '{mysql_host}'")
            
            connection_string = f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}:{mysql_port}/{mysql_db}"
            
            engine = create_engine(connection_string)
            # Test the connection
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                
                # Try to get some basic stats if possible
                try:
                    tables_result = conn.execute(text("SHOW TABLES"))
                    tables = [row[0] for row in tables_result.fetchall()]
                    st.session_state.database_stats = {
                        "tables": tables,
                        "database_type": "MySQL"
                    }
                except:
                    pass
            
            st.session_state.connection_status = "connected"
            st.success("✅ Successfully connected to MySQL database!")
            return SQLDatabase(engine)
            
    except Exception as e:
        st.session_state.connection_status = "disconnected"
        st.error(f"❌ Database connection failed: {str(e)}")
        st.stop()

# Configure database based on user selection
try:
    if db_uri == MYSQL:
        db = configure_db(db_uri, mysql_host, mysql_user, mysql_password, mysql_db)
    else:
        db = configure_db(db_uri)
        
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

# Main content area with tabs
tab1, tab2, tab3, tab4 = st.tabs(["💬 Chat", "📊 Analytics", "🗄️ Database Info", "📚 History"])

with tab1:
    # Chat interface
    st.markdown("### � Chat with Database")
    
    # Initialize chat history
    if "messages" not in st.session_state or st.button("🗑️ Clear Chat", key="clear_main"):
        st.session_state["messages"] = [{"role": "assistant", "content": "Hi! I can help you query the student database. Ask me anything about the students, their classes, or marks!"}]

    # Display chat messages with enhanced styling
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])
            
            # Add visualization if available
            if msg["role"] == "assistant" and "visualization" in msg and PLOTLY_AVAILABLE:
                for chart_type, chart in msg["visualization"]:
                    st.plotly_chart(chart, use_container_width=True)

    # Chat input with suggestions
    st.markdown("#### 💡 Try these queries:")
    cols = st.columns(3)
    
    with cols[0]:
        if st.button("📊 Show all students", key="suggest1"):
            user_query = "Show all students"
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.rerun()
    
    with cols[1]:
        if st.button("🏆 Top performers", key="suggest2"):
            user_query = "Who has the highest marks?"
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.rerun()
    
    with cols[2]:
        if st.button("📈 Class averages", key="suggest3"):
            user_query = "What's the average marks by class?"
            st.session_state.messages.append({"role": "user", "content": user_query})
            st.rerun()

    # Enhanced chat input
    user_query = st.chat_input(placeholder="Ask about students, classes, marks, or type SQL queries...")

with tab2:
    # Analytics dashboard
    st.markdown("### 📊 Database Analytics")
    
    if st.session_state.database_stats:
        stats = st.session_state.database_stats
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.markdown("""
            <div class="metric-container">
                <h3>👥 Total Students</h3>
                <h2>{}</h2>
            </div>
            """.format(stats.get('total_students', 'N/A')), unsafe_allow_html=True)
        
        with col2:
            st.markdown("""
            <div class="metric-container">
                <h3>📈 Avg Marks</h3>
                <h2>{}</h2>
            </div>
            """.format(stats.get('average_marks', 'N/A')), unsafe_allow_html=True)
        
        with col3:
            st.markdown("""
            <div class="metric-container">
                <h3>🗄️ Database</h3>
                <h2>{}</h2>
            </div>
            """.format(stats.get('database_type', 'N/A')), unsafe_allow_html=True)
        
        with col4:
            class_count = len(stats.get('class_distribution', {}))
            st.markdown("""
            <div class="metric-container">
                <h3>📚 Classes</h3>
                <h2>{}</h2>
            </div>
            """.format(class_count), unsafe_allow_html=True)
        
        # Charts
        if 'class_distribution' in stats and PLOTLY_AVAILABLE:
            st.markdown("#### 📊 Class Distribution")
            class_df = pd.DataFrame(list(stats['class_distribution'].items()), 
                                  columns=['Class', 'Students'])
            
            col1, col2 = st.columns(2)
            with col1:
                fig_bar = px.bar(class_df, x='Class', y='Students', 
                               title="Students per Class")
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col2:
                fig_pie = px.pie(class_df, values='Students', names='Class',
                               title="Class Distribution")
                st.plotly_chart(fig_pie, use_container_width=True)
        elif 'class_distribution' in stats:
            st.markdown("#### 📊 Class Distribution")
            class_df = pd.DataFrame(list(stats['class_distribution'].items()), 
                                  columns=['Class', 'Students'])
            st.dataframe(class_df)
    
    else:
        st.info("📊 Connect to database to view analytics")

with tab3:
    # Database info
    st.markdown("### 🗄️ Database Information")
    
    # Connection info
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🔗 Connection Status")
        status = st.session_state.connection_status
        if status == "connected":
            st.success(f"✅ Connected ({status})")
        elif status == "connecting":
            st.warning(f"⏳ Connecting...")
        else:
            st.error(f"❌ Disconnected")
    
    with col2:
        st.markdown("#### 📊 Quick Stats")
        if st.session_state.database_stats:
            stats = st.session_state.database_stats
            if 'total_students' in stats:
                st.metric("Students", stats['total_students'])
            if 'average_marks' in stats:
                st.metric("Avg Marks", f"{stats['average_marks']}")
    
    # Sample data
    if st.button("🔄 Refresh Sample Data"):
        try:
            sample_data = db.run("SELECT * FROM STUDENT LIMIT 10;")
            st.markdown("#### 📋 Sample Data")
            st.code(sample_data)
        except Exception as e:
            st.error(f"Could not fetch sample data: {e}")
    
    # Schema info
    st.markdown("#### 🏗️ Database Schema")
    st.markdown("""
    **STUDENT Table:**
    - `NAME` (VARCHAR): Student's full name
    - `CLASS` (VARCHAR): Course/Class name  
    - `SECTION` (VARCHAR): Class section
    - `MARKS` (INT): Student's marks/score
    """)

with tab4:
    # Query history
    st.markdown("### 📚 Query History")
    
    if st.session_state.query_history:
        for i, query in enumerate(reversed(st.session_state.query_history[-10:])):
            with st.expander(f"🕒 {query.get('timestamp', '')} - {query.get('query', '')[:50]}..."):
                st.markdown(f"**Query:** {query.get('query', '')}")
                st.markdown(f"**Response:** {query.get('response', '')}")
                
                if st.button(f"🔄 Re-run", key=f"rerun_{i}"):
                    st.session_state.messages.append({"role": "user", "content": query.get('query', '')})
                    st.rerun()
    else:
        st.info("📝 No query history yet. Start chatting to see your queries here!")

if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    
    # Save to history
    st.session_state.query_history.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": user_query,
        "response": ""  # Will be updated after processing
    })

    with st.chat_message("user"):
        st.write(user_query)

    with st.chat_message("assistant"):
        # Enhanced query processing
        query_lower = user_query.lower()
        
        try:
            answer = ""
            charts = []
            
            # Smart pattern matching for immediate SQL execution
            if "show all student" in query_lower or "all student" in query_lower:
                with st.spinner("📊 Fetching all students..."):
                    result = db.run("SELECT * FROM STUDENT LIMIT 10;")
                    answer = f"Here are the students in the database:\n\n{result}"
                    charts = create_visualization(result, "table", "All Students")
                    
            elif "marks above" in query_lower or "marks >" in query_lower:
                with st.spinner("🔍 Finding students with high marks..."):
                    import re
                    numbers = re.findall(r'\d+', user_query)
                    threshold = numbers[0] if numbers else "80"
                    result = db.run(f"SELECT NAME, CLASS, SECTION, MARKS FROM STUDENT WHERE MARKS > {threshold} ORDER BY MARKS DESC;")
                    answer = f"Students with marks above {threshold}:\n\n{result}"
                    charts = create_visualization(result, "marks", f"Students with marks > {threshold}")
                    
            elif "highest mark" in query_lower or "best mark" in query_lower or "top student" in query_lower:
                with st.spinner("🏆 Finding top performers..."):
                    result = db.run("SELECT NAME, CLASS, SECTION, MARKS FROM STUDENT ORDER BY MARKS DESC LIMIT 5;")
                    answer = f"Students with highest marks:\n\n{result}"
                    charts = create_visualization(result, "ranking", "Top Performers")
                    
            elif "lowest mark" in query_lower or "worst mark" in query_lower:
                with st.spinner("📉 Finding students who need help..."):
                    result = db.run("SELECT NAME, CLASS, SECTION, MARKS FROM STUDENT ORDER BY MARKS ASC LIMIT 5;")
                    answer = f"Students with lowest marks:\n\n{result}"
                    charts = create_visualization(result, "ranking", "Students Needing Support")
                    
            elif "count" in query_lower or "how many" in query_lower:
                with st.spinner("🔢 Counting students..."):
                    if "class" in query_lower:
                        result = db.run("SELECT CLASS, COUNT(*) as Student_Count FROM STUDENT GROUP BY CLASS ORDER BY CLASS;")
                        answer = f"Number of students in each class:\n\n{result}"
                        charts = create_visualization(result, "count", "Students per Class")
                    elif "section" in query_lower:
                        result = db.run("SELECT SECTION, COUNT(*) as Student_Count FROM STUDENT GROUP BY SECTION ORDER BY SECTION;")
                        answer = f"Number of students in each section:\n\n{result}"
                        charts = create_visualization(result, "count", "Students per Section")
                    else:
                        result = db.run("SELECT COUNT(*) as Total_Students FROM STUDENT;")
                        answer = f"Total number of students: {result}"
                        
            elif "average" in query_lower:
                with st.spinner("📊 Calculating averages..."):
                    if "section" in query_lower:
                        result = db.run("SELECT SECTION, ROUND(AVG(MARKS), 2) as Average_Marks FROM STUDENT GROUP BY SECTION ORDER BY Average_Marks DESC;")
                        answer = f"Average marks by section:\n\n{result}"
                        charts = create_visualization(result, "average", "Average Marks by Section")
                    elif "class" in query_lower:
                        result = db.run("SELECT CLASS, ROUND(AVG(MARKS), 2) as Average_Marks FROM STUDENT GROUP BY CLASS ORDER BY Average_Marks DESC;")
                        answer = f"Average marks by class:\n\n{result}"
                        charts = create_visualization(result, "average", "Average Marks by Class")
                    else:
                        result = db.run("SELECT ROUND(AVG(MARKS), 2) as Overall_Average FROM STUDENT;")
                        answer = f"Overall average marks: {result}"
                        
            elif any(word in query_lower for word in ['select', 'from', 'where', 'group by', 'order by']):
                with st.spinner("⚙️ Executing SQL query..."):
                    result = db.run(user_query)
                    answer = f"Query result:\n\n{result}"
                    charts = create_visualization(result, "custom", "Custom Query Results")
                    
            else:
                # Try the agent as a last resort
                try:
                    with st.spinner("🤔 Let me try to understand your query..."):
                        response = agent.invoke({"input": user_query})
                        answer = response.get("output", "")
                        
                        if "Final Answer:" in answer:
                            answer = answer.split("Final Answer:")[-1].strip()
                        
                        if not answer or len(answer.strip()) < 10 or "Agent stopped" in answer:
                            raise Exception("Agent response incomplete")
                            
                except:
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
            
            # Display answer
            st.write(answer)
            
            # Display charts if available
            if charts and PLOTLY_AVAILABLE:
                st.markdown("#### 📊 Data Visualization")
                for chart_type, chart in charts:
                    st.plotly_chart(chart, use_container_width=True)
                
                # Export options
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📥 Export CSV"):
                        csv_data = export_data(result, "csv")
                        if csv_data:
                            st.download_button(
                                label="💾 Download CSV",
                                data=csv_data,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                                mime="text/csv"
                            )
                
                with col2:
                    if st.button("📥 Export JSON"):
                        json_data = export_data(result, "json")
                        if json_data:
                            st.download_button(
                                label="💾 Download JSON",
                                data=json_data,
                                file_name=f"query_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                                mime="application/json"
                            )
            
            # Update message history with visualization
            message_content = {"role": "assistant", "content": answer}
            if charts:
                message_content["visualization"] = charts
                
            st.session_state.messages.append(message_content)
            
            # Update query history
            if st.session_state.query_history:
                st.session_state.query_history[-1]["response"] = answer
            
        except Exception as e:
            error_response = f"I'm having trouble accessing the database. Please check the connection.\n\nError: {str(e)}"
            st.error(error_response)
            st.session_state.messages.append({"role": "assistant", "content": error_response})
            
            if st.session_state.query_history:
                st.session_state.query_history[-1]["response"] = error_response

# Enhanced footer with additional info
with st.sidebar:
    st.markdown("---")
    st.markdown("### 📊 App Statistics")
    
    if st.session_state.query_history:
        st.metric("Queries Asked", len(st.session_state.query_history))
    
    if st.session_state.database_stats:
        stats = st.session_state.database_stats
        if 'total_students' in stats:
            st.metric("Students in DB", stats['total_students'])
    
    st.markdown("### ℹ️ About")
    st.markdown("""
    **🦜 LangChain SQL Chat**
    
    Version: 2.0
    
    **Features:**
    - 🤖 AI-powered queries
    - 📊 Data visualization  
    - 📥 Export functionality
    - 📚 Query history
    - 🎨 Modern UI
    
    **Technologies:**
    - Streamlit
    - LangChain
    - Groq AI
    - Plotly
    - SQLAlchemy
    """)
    
    st.markdown("---")
    st.markdown("💾 **Database:** student.db")
    st.markdown("📊 **Table:** STUDENT") 
    st.markdown("🦜 **Powered by:** LangChain + Groq")
    
    # Performance metrics
    if 'performance_stats' in st.session_state:
        st.markdown("### ⚡ Performance")
        perf = st.session_state.performance_stats
        st.metric("Avg Response Time", f"{perf.get('avg_time', 0):.2f}s")

# Add some footer spacing
st.markdown("<br><br>", unsafe_allow_html=True)

# Enhanced footer
st.markdown("""
---
<div style="text-align: center; color: #666; margin: 2rem 0;">
    <p><strong>🦜 LangChain SQL Database Chat v2.0</strong></p>
    <p>Transform your database interactions with the power of AI 🚀</p>
    <p>Built with ❤️ using Streamlit, LangChain, and Groq AI</p>
</div>
""", unsafe_allow_html=True)
