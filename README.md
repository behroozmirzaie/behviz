# Beh AI - Natural Language to SQL Visualization

An intelligent AI-powered application that converts natural language questions into SQL queries and automatically generates interactive visualizations from the results.

## 🎯 Project Overview

Beh AI is a sophisticated data analytics tool that bridges the gap between business users and database analytics. Users can ask questions in plain English, and the system automatically:

1. **Translates** natural language to SQL queries
2. **Validates** queries against the database schema  
3. **Executes** queries safely on PostgreSQL
4. **Generates** interactive visualizations using Plotly
5. **Self-corrects** common issues automatically

## 🤖 Understanding AI Agents

### What's an AI Agent?
Think of an AI Agent as a **smart digital assistant** that can understand what you want and automatically figure out how to do it. Unlike regular software that needs specific instructions, our AI Agent can:

- 🧠 **Think**: Understands your questions in plain English
- 🔍 **Explore**: Investigates your database to understand its structure  
- 🛠️ **Execute**: Writes and runs SQL queries automatically
- 📊 **Create**: Builds beautiful charts from the results
- 🔧 **Fix**: Corrects mistakes on its own

### Simple Example: From Question to Answer

**You ask**: *"Which products sell the most?"*

**Behind the scenes, our AI Agent**:
```
🧠 Thinks: "User wants top-selling products"
🔍 Explores: "Found 'products' and 'sales' tables"  
🛠️ Writes: "SELECT product_name, SUM(quantity) FROM..."
✅ Validates: "Query looks correct, tables exist"
🚀 Executes: Runs the query on your database
📊 Visualizes: Creates a bar chart automatically
```

**You get**: Interactive chart showing top products in 15 seconds! ⚡

### Why This Matters
- **No SQL Knowledge Needed**: Just ask questions naturally
- **No Manual Work**: Everything happens automatically
- **Always Accurate**: Validates against your actual database
- **Self-Healing**: Fixes common errors without bothering you

*This turns complex data analysis into simple conversations!* 💬➡️📊

## 🚀 Features

- **Natural Language Processing**: Ask questions like "Show me the number of users per email domain"
- **Intelligent SQL Generation**: Powered by Ollama's Llama 3.2 model
- **Schema Validation**: Ensures generated queries are valid against your database structure
- **Auto-correction**: Handles dialect differences and column name mismatches
- **Interactive Visualizations**: Automatic chart generation (bar, line, scatter, pie charts)
- **Database Schema Explorer**: View your database structure within the app
- **Robust Error Handling**: Graceful handling of database connection issues

## 🏗️ Architecture

### System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │    Ollama       │    │   PostgreSQL    │
│   Frontend      │◄──►│   LLM Server    │    │   Database      │
│                 │    │  (Llama 3.2)    │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Docker      │    │    SQLAlchemy   │    │     Plotly      │
│   Container     │    │   ORM Layer     │    │  Visualization  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### AI Agent Architecture

The core AI agent follows a sophisticated multi-stage pipeline:

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           AI Agent Pipeline                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌───────────────┐                │
│  │   Input     │    │   Schema    │    │    LLM        │                │
│  │ Processing  │───►│  Analysis   │───►│ SQL Generation│                │
│  └─────────────┘    └─────────────┘    └───────────────┘                │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │ Natural     │    │ Database    │    │ Structured  │                  │
│  │ Language    │    │ Schema      │    │ JSON        │                  │
│  │ Question    │    │ Context     │    │ Response    │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│                                                │                        │
│                                                ▼                        │
│  ┌───────────────┐    ┌─────────────┐    ┌───────────────┐              │
│  │ Visualization │◄───│   Query     │◄───│    SQL        │              │
│  │ Generation    │    │ Execution   │    │ Validation.   │              │
│  └───────────────┘    └─────────────┘    └───────────────┘              │
│         │                   │                   │                       │
│         ▼                   ▼                   ▼                       │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                  │
│  │ Interactive │    │ Pandas      │    │ SQLGlot     │                  │
│  │ Charts      │    │ DataFrame   │    │ Parser      │                  │
│  │ (Plotly)    │    │ Results     │    │ Validator   │                  │
│  └─────────────┘    └─────────────┘    └─────────────┘                  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### AI Agent Components

#### 1. **Natural Language Processor**
- **Input**: User questions in plain English
- **Processing**: Context-aware prompt engineering
- **Output**: Structured prompts for the LLM

#### 2. **Schema Intelligence Module**
- **Function**: Dynamically inspects database schema
- **Capabilities**: 
  - Table and column discovery
  - Relationship inference
  - Constraint validation
- **Caching**: Schema information cached for performance

#### 3. **LLM Query Generator** (Ollama Llama 3.2)
- **Model**: Llama 3.2 running locally via Ollama
- **Configuration**: 
  - Temperature: 0 (deterministic output)
  - Format: JSON (structured responses)
- **Output**: JSON containing SQL query and visualization metadata

#### 4. **SQL Validation Engine** (SQLGlot)
- **Parser**: Advanced SQL parsing and validation
- **Dialect Translation**: MySQL → PostgreSQL conversion
- **Schema Compliance**: Validates tables, columns, and joins
- **Business Rules**: Enforces specific join requirements (e.g., sales.product_id = products.id)

#### 5. **Query Execution Layer** (SQLAlchemy)
- **Connection Management**: Robust PostgreSQL connectivity
- **Retry Logic**: Handles database startup delays
- **Error Handling**: Graceful failure management
- **Security**: Parameterized query execution

#### 6. **Visualization Intelligence**
- **Chart Selection**: Automatic chart type determination
- **Axis Mapping**: Smart column-to-axis mapping
- **Self-Correction**: Handles column name mismatches
- **Rendering**: Interactive Plotly visualizations

#### 7. **Self-Healing Mechanisms**
- **Column Resolution**: Automatically corrects column name issues
- **Retry Logic**: Database connection resilience
- **Fallback Options**: Default visualization when primary fails
- **Error Recovery**: Graceful degradation with user feedback

## 🛠️ Technology Stack

### Backend
- **Python 3.12**: Core application runtime
- **Streamlit**: Web application framework
- **SQLAlchemy**: Database ORM and connection management
- **Pandas**: Data manipulation and analysis
- **SQLGlot**: SQL parsing, validation, and dialect translation

### AI/ML
- **Ollama**: Local LLM server
- **Llama 3.2**: Large language model for SQL generation
- **LangChain**: LLM integration framework

### Database
- **PostgreSQL 15**: Primary database engine
- **Adminer**: Database administration interface

### Visualization
- **Plotly Express**: Interactive chart generation
- **Streamlit Components**: UI components and layout

### Infrastructure
- **Docker**: Containerization and orchestration
- **Docker Compose**: Multi-service deployment

## 📋 Prerequisites

- Docker and Docker Compose installed
- Ollama running locally with Llama 3.2 model
- At least 8GB RAM (recommended for LLM operations)

### Setting up Ollama

1. Install Ollama from [https://ollama.ai](https://ollama.ai)
2. Pull the Llama 3.2 model:
   ```bash
   ollama pull llama3.2:latest
   ```
3. Ensure Ollama is running on the default port (11434)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd beh-ai
```

### 2. Start the Application
```bash
docker-compose up --build
```

### 3. Access the Application
- **Main App**: http://localhost:8501
- **Database Admin**: http://localhost:8080
- **PostgreSQL**: localhost:5432

### 4. Database Setup
The PostgreSQL database will be automatically initialized with sample data from `init-db/backup.sql`.

## 💡 Usage Examples

### Example Queries

1. **User Distribution**: "Show me the number of users per email domain"
2. **Sales Analysis**: "What are the top 10 products by total sales?"
3. **Time Series**: "Show monthly sales trends for the last year"
4. **Geographic**: "Display user distribution by country"

### Expected Workflow

1. Enter your question in natural language
2. Click "Generate Visualization"
3. Review the generated SQL query
4. Examine the query results
5. Interact with the generated visualization

## 🔧 Configuration

### Environment Variables

- **Database**: Configured in `docker-compose.yml`
  - User: `user`
  - Password: `password`
  - Database: `mydatabase`
  - Port: `5432`

- **Ollama**: 
  - Base URL: `http://host.docker.internal:11434`
  - Model: `llama3.2:latest`

### Customization

- **Database Schema**: Replace `init-db/backup.sql` with your data
- **LLM Model**: Change model in `main.py` line 98
- **UI Styling**: Modify Streamlit configuration in `main.py`

## 🏢 Database Schema

The application automatically discovers your database schema and uses it for:
- Query validation
- Table relationship inference
- Column existence checking
- Join requirement enforcement

## 🔒 Security Considerations

- Database credentials are configured for development use
- SQL queries are validated before execution
- Parameterized queries prevent SQL injection
- Local LLM execution ensures data privacy

## 🐛 Troubleshooting

### Common Issues

1. **Ollama Connection Failed**
   - Ensure Ollama is running: `ollama serve`
   - Check model availability: `ollama list`

2. **Database Connection Issues**
   - Wait for PostgreSQL initialization (up to 30 seconds)
   - Check Docker container status: `docker-compose ps`

3. **Out of Memory**
   - Increase Docker memory allocation
   - Use a smaller LLM model

## 🔮 Future Enhancements

- [ ] Support for multiple database types (MySQL, SQLite)
- [ ] Advanced chart customization options
- [ ] Query result caching
- [ ] User authentication and query history
- [ ] Advanced analytics and insights
- [ ] Natural language explanations of results
- [ ] Integration with cloud LLM providers

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting section
- Review Docker logs: `docker-compose logs`

---

**Beh AI** - Transforming natural language into actionable data insights! 🚀📊
