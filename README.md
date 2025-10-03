<div align="center">

# 🦜 LangChain SQL Database Chat Application

![LangChain](https://img.shields.io/badge/🦜_LangChain-Framework-blue?style=for-the-badge&logo=chainlink&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)
![Python](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![SQLite](https://img.shields.io/badge/SQLite-07405E?style=for-the-badge&logo=sqlite&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-005C84?style=for-the-badge&logo=mysql&logoColor=white)

![Groq](https://img.shields.io/badge/Groq-AI_Powered-orange?style=for-the-badge&logo=openai&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Stars](https://img.shields.io/github/stars/Syam-1133/AI-Hand-Gesture-Controlled-Mouse?style=for-the-badge&logo=github)
![Forks](https://img.shields.io/github/forks/Syam-1133/AI-Hand-Gesture-Controlled-Mouse?style=for-the-badge&logo=github)

<img src="https://readme-typing-svg.herokuapp.com?font=Fira+Code&pause=1000&color=36BCF7&center=true&vCenter=true&width=435&lines=Chat+with+SQL+Database;Natural+Language+to+SQL;AI+Powered+Database+Queries;Built+with+LangChain+%26+Groq" alt="Typing SVG" />

</div>

---

## 🎯 Overview

A sophisticated Streamlit web application that enables natural language conversations with SQL databases using LangChain and Groq's AI models. This project demonstrates the power of combining Large Language Models (LLMs) with database querying capabilities to create an intuitive database interaction experience.

<div align="center">

### 🚀 **Transform Natural Language into SQL Queries Instantly!**

</div>

## 🌟 Features

<div align="center">

| 🗄️ **Multi-DB Support** | 🤖 **AI Powered** | 💬 **Interactive** | 🔐 **Secure** |
|:---:|:---:|:---:|:---:|
| SQLite & MySQL | Natural Language Processing | Real-time Chat | API Key Management |
| Easy Database Switching | Smart Query Recognition | Persistent History | Secure Connections |

</div>

### 🗄️ **Multi-Database Support**
- **SQLite Integration**: Works with local SQLite databases (default: `student.db`)
- **MySQL Integration**: Connect to remote MySQL databases with full configuration support
- **Dynamic Database Switching**: Easy toggle between database types through the UI

### 🤖 **Intelligent Query Processing**
- **Natural Language to SQL**: Convert plain English questions into SQL queries
- **Smart Pattern Matching**: Optimized query recognition for common database operations
- **Direct SQL Execution**: Support for raw SQL queries for advanced users
- **Error Handling**: Robust error management with fallback mechanisms

### 💬 **Interactive Chat Interface**
- **Persistent Chat History**: Maintains conversation context throughout the session
- **Real-time Responses**: Streaming responses for better user experience
- **Clear Chat Functionality**: Reset conversations when needed
- **Sample Query Suggestions**: Built-in examples to guide users

### 🔐 **Secure Configuration**
- **API Key Management**: Secure handling of Groq API keys with environment variable support
- **Database Credentials**: Safe storage and handling of database connection details
- **Session Persistence**: Maintains API key configuration across sessions

## 🏗️ Project Structure

```
SQL/
├── main.py           # Main Streamlit application
├── sqlite.py         # SQLite database setup and sample data insertion
├── student.db        # SQLite database file (generated)
├── requirements.txt  # Python dependencies
└── README.md         # Project documentation
```

## 📊 Database Schema

The project includes a sample **STUDENT** table with the following structure:

| Column  | Type        | Description           |
|---------|-------------|-----------------------|
| NAME    | VARCHAR(25) | Student's full name   |
| CLASS   | VARCHAR(25) | Course/Class name     |
| SECTION | VARCHAR(25) | Class section         |
| MARKS   | INT         | Student's marks/score |

### Sample Data
```sql
| NAME    | CLASS         | SECTION | MARKS |
|---------|---------------|---------|-------|
| Syam    | ML            | A       | 90    |
| John    | Gen AI        | B       | 100   |
| Mukesh  | Data Science  | A       | 86    |
| Jacob   | DEVOPS        | A       | 50    |
| Dipesh  | DEVOPS        | A       | 35    |
```

## 🚀 Getting Started

### Prerequisites

- Python 3.8 or higher
- Groq API Key ([Get one here](https://console.groq.com/))
- MySQL Server (optional, for MySQL integration)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd SQL
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database**
   ```bash
   python sqlite.py
   ```
   This creates the `student.db` file with sample data.

4. **Configure environment variables** (optional)
   Create a `.env` file in the project root:
   ```env
   GROQ_API_KEY=your_groq_api_key_here
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=student_management
   MYSQL_PORT=3306
   ```

5. **Run the application**
   ```bash
   streamlit run main.py
   ```

6. **Access the application**
   Open your browser and navigate to `http://localhost:8501`

## 🎯 Usage Examples

### Natural Language Queries

Ask questions in plain English:

- **"Show all students"** → Displays all student records
- **"Which students have marks above 80?"** → Filters high-performing students
- **"Who has the highest marks?"** → Shows top performers
- **"How many students are in each class?"** → Groups students by class
- **"What's the average marks by section?"** → Calculates section-wise averages
- **"Show students in Data Science class"** → Filters by specific class

### Advanced Queries

The application also supports:
- Direct SQL query execution
- Complex filtering and aggregations
- Statistical analysis queries
- Custom reporting queries

## 🛠️ Technical Architecture

### Core Components

1. **LangChain Framework**
   - SQL Agent creation and management
   - Database toolkit integration
   - Query optimization and execution

2. **Groq AI Integration**
   - Uses `llama-3.1-8b-instant` model
   - Streaming responses for real-time interaction
   - Natural language processing for query understanding

3. **Database Layer**
   - SQLAlchemy for database abstraction
   - Support for multiple database types
   - Connection pooling and management

4. **Streamlit Frontend**
   - Interactive web interface
   - Real-time chat functionality
   - Configuration management UI

### Key Features Implementation

- **Smart Query Processing**: Pattern matching combined with LLM processing
- **Fallback Mechanisms**: Multiple levels of query handling for reliability
- **Performance Optimization**: Caching and connection management
- **Security**: Secure credential handling and input validation

## 🔧 Configuration Options

### Database Configuration

**SQLite (Default)**
- Automatically uses `student.db` in the project directory
- No additional configuration required
- Perfect for development and testing

**MySQL**
- Configure connection details in the sidebar
- Supports environment variable configuration
- Full SSL and port customization

### AI Model Configuration

- **Model**: `llama-3.1-8b-instant` (Groq)
- **Streaming**: Enabled for real-time responses
- **Max Iterations**: Optimized for quick responses
- **Error Handling**: Comprehensive fallback system

## 📈 Performance Features

- **Query Caching**: Database connections cached for 2 hours
- **Optimized Responses**: Smart pattern matching reduces LLM calls
- **Connection Pooling**: Efficient database connection management
- **Timeout Management**: Prevents hanging queries

## 🔒 Security Considerations

- **API Key Protection**: Secure storage in session state
- **SQL Injection Prevention**: Parameterized queries through SQLAlchemy
- **Input Validation**: Comprehensive input sanitization
- **Error Masking**: Sensitive information hidden from error messages

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangChain**: For the powerful SQL agent framework
- **Groq**: For providing fast and efficient AI models
- **Streamlit**: For the intuitive web framework
- **SQLAlchemy**: For robust database abstraction

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/your-repo/issues) section
2. Review the example queries in the application
3. Ensure your API key and database connections are properly configured

## 🚀 Future Enhancements

- [ ] Support for PostgreSQL databases
- [ ] Advanced visualization features
- [ ] Query history and favorites
- [ ] User authentication and authorization
- [ ] Export functionality for query results
- [ ] Integration with more AI models

---

**Happy Querying! 🎉**
