# Context-Aware Research ChatApp

A sophisticated AI-powered research assistant that provides comprehensive, context-aware research briefs using advanced language models and web search capabilities.

## 🌟 Features

- **Context-Aware Conversations**: Automatically detects follow-up questions and maintains conversation context
- **Intelligent Research Depth**: Auto-detects or manually set research depth (Quick, Medium, Deep)
- **Multi-Source Research**: Integrates Google Search, Tavily API, and web scraping for comprehensive data gathering
- **Structured Output**: Provides well-formatted research briefs with executive summaries, key findings, and sources
- **Real-time Processing**: Live updates during research with status indicators
- **Beautiful UI**: Modern dark-themed interface with responsive design
- **CORS-Enabled**: Separate frontend and backend deployment ready

## 🏗️ Architecture

### System Architecture
```
┌─────────────────┐    HTTP/REST    ┌─────────────────┐
│   Frontend      │ ────────────── │    Backend      │
│   (Streamlit)   │                │   (FastAPI)     │
│   Port: 8501    │                │   Port: 8000    │
└─────────────────┘                └─────────────────┘
                                            │
                                            │
                                   ┌─────────────────┐
                                   │   LangGraph     │
                                   │   Workflow      │
                                   └─────────────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        │                   │                   │
              ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
              │   Google APIs   │ │   Tavily API    │ │   Together AI   │
              │   (Gemini +     │ │   (Web Search)  │ │   (Llama)      │
              │    Search)      │ │                 │ │                 │
              └─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Component Flow
```
User Query → Frontend → Backend API → LangGraph Workflow
    ↓
Research Node → Web Search → Content Extraction → Analysis Node
    ↓
Synthesis Node → Source Compilation → Final Brief Generation
    ↓
Response → Frontend Display → User Interface
```

## 🛠️ Tech Stack

### Frontend
- **Streamlit**: Modern web UI framework
- **Python**: Core programming language
- **CSS**: Custom styling for dark theme
- **Requests**: HTTP client for API communication

### Backend
- **FastAPI**: High-performance web framework
- **LangGraph**: Workflow orchestration for AI agents
- **LangChain**: LLM integration and tooling
- **Uvicorn**: ASGI server for production

### AI & APIs
- **Google Gemini**: Primary language model
- **Together AI**: Alternative LLM provider (Llama models)
- **Google Custom Search**: Web search capabilities
- **Tavily API**: Enhanced web search and scraping
- **LangSmith**: Observability and tracing

### Infrastructure
- **Docker**: Containerization
- **Hugging Face Spaces**: Backend deployment
- **Streamlit Cloud**: Frontend deployment
- **CORS**: Cross-origin resource sharing

## 📁 Project Structure

```
Context-Aware-Research-ChatApp/
├── backend/                    # Backend API service
│   ├── app/
│   │   ├── config.py          # Configuration management
│   │   ├── main.py            # FastAPI application
│   │   ├── graph/             # LangGraph workflow definitions
│   │   ├── nodes/             # Individual workflow nodes
│   │   ├── routes/            # API route handlers
│   │   ├── services/          # Business logic services
│   │   ├── structure/         # Data models and schemas
│   │   └── tools/             # External API integrations
│   ├── app.py                 # Entry point for deployment
│   ├── requirements.txt       # Backend dependencies
│   ├── Dockerfile            # Backend containerization
│   └── .env.example          # Environment template
├── frontend/                  # Frontend Streamlit app
│   ├── streamlit_app.py      # Main Streamlit application
│   ├── requirements.txt      # Frontend dependencies
│   ├── Dockerfile           # Frontend containerization
│   └── .env.example         # Frontend environment template
├── docs/                     # Documentation
│   └── OBSERVABILITY.md     # Monitoring and observability
├── docker-compose.yml       # Local development setup
└── README.md                # This file
```

## 🚀 Quick Start

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/Context-Aware-Research-ChatApp.git
   cd Context-Aware-Research-ChatApp
   ```

2. **Set up environment variables**
   ```bash
   # Backend
   cp backend/.env.example backend/.env
   # Add your API keys to backend/.env
   
   # Frontend
   cp frontend/.env.example frontend/.env
   # Set API_URL=http://localhost:8000
   ```

3. **Run with Docker Compose**
   ```bash
   docker-compose up --build
   ```

4. **Or run manually**
   ```bash
   # Terminal 1 - Backend
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   
   # Terminal 2 - Frontend
   cd frontend
   pip install -r requirements.txt
   streamlit run streamlit_app.py
   ```

### Cloud Deployment

#### Backend (Hugging Face Spaces)
1. Create new Space with Docker SDK
2. Upload `backend/` folder contents
3. Add environment variables in Space secrets
4. Deploy automatically

#### Frontend (Streamlit Cloud)
1. Push `frontend/` folder to GitHub
2. Connect to Streamlit Cloud
3. Set `API_URL` to your Hugging Face Space URL
4. Deploy

## 🔧 Configuration

### Required Environment Variables

**Backend (.env):**
```env
GOOGLE_API_KEY=your_google_api_key
TOGETHER_API_KEY=your_together_api_key
LANGSMITH_API_KEY=your_langsmith_api_key  # Optional
TAVILY_API_KEY=your_tavily_api_key        # Optional
```

**Frontend (.env):**
```env
API_URL=http://localhost:8000  # For local development
# API_URL=https://your-space.hf.space  # For production
```

## 🎯 Usage

1. **Start a conversation**: Type any research question
2. **Auto-depth detection**: Use words like "quick" or "detailed" to set research depth
3. **Follow-up questions**: The system automatically detects and maintains context
4. **View sources**: Copy URLs from the sources section to visit original content
5. **Adjust settings**: Use sidebar to configure backend URL and view conversation history

## 🔍 Key Features in Detail

### Context Awareness
- Automatically detects follow-up questions using NLP patterns
- Maintains conversation history for relevant context
- Builds upon previous research in subsequent queries

### Research Depth Intelligence
- **Quick (1)**: Fast overview with essential information
- **Medium (2)**: Balanced analysis with key insights
- **Deep (3)**: Comprehensive research with detailed analysis

### Multi-Source Integration
- Google Custom Search for broad web coverage
- Tavily API for enhanced content extraction
- Multiple LLM providers for robust processing
- Real-time web scraping and content analysis

## 📊 Monitoring & Observability

- **LangSmith Integration**: Complete workflow tracing
- **Health Checks**: Real-time backend status monitoring
- **Error Handling**: Graceful degradation with user feedback
- **Performance Metrics**: Request timing and success rates

## 🔗 Deployment URLs

- **Frontend Demo**: https://context-aware-chatbott.streamlit.app/
- **Backend API**: https://huggingface.co/spaces/bhoomika19/context-aware-research-bott
- **Documentation**: https://docs.google.com/document/d/1rYhy2MA-_YoCIEFTwRxHkHdymQxdhFeKz0WQXRc3yxg/edit?usp=sharing
