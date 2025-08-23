# Observability and Monitoring Documentation

This document describes the comprehensive observability and monitoring features implemented in the Context-Aware Research ChatApp.

## 🔍 LangSmith Integration

### Configuration
The application is integrated with LangSmith for comprehensive tracing of LangGraph executions:

```bash
# Environment Variables
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_PROJECT=context-aware-research-app
LANGSMITH_API_KEY=your_langsmith_api_key_here
```

### Trace Links
Every research brief generation creates a trace that can be viewed in LangSmith:
- **Project URL**: https://smith.langchain.com/o/your-org/projects/p/context-aware-research-app
- **Individual Trace**: Each request includes a `trace_url` in the response metadata

### Example Trace Information
```json
{
  "metadata": {
    "execution_time_seconds": 12.45,
    "total_tokens_used": 3456,
    "request_id": "uuid-123-456",
    "trace_url": "https://smith.langchain.com/o/your-org/projects/p/context-aware-research-app/r/uuid-123-456",
    "node_breakdown": {
      "context_summarization": {"duration_seconds": 0.5, "tokens_used": 150},
      "research_planning": {"duration_seconds": 2.1, "tokens_used": 800},
      "web_search": {"duration_seconds": 3.2, "tokens_used": 0},
      "content_fetching": {"duration_seconds": 4.5, "tokens_used": 0},
      "source_summarization": {"duration_seconds": 1.8, "tokens_used": 1200},
      "brief_generation": {"duration_seconds": 2.3, "tokens_used": 1306}
    }
  }
}
```

## 📊 Token Usage Tracking

### Implementation
- **Service**: [`app/services/monitoring.py`](../app/services/monitoring.py)
- **Integration**: All LLM calls are tracked automatically
- **Estimation**: Token usage is estimated using a 4 characters ≈ 1 token ratio

### Token Breakdown
The system tracks tokens at multiple levels:
1. **Per Node**: Individual node token consumption
2. **Per LLM Call**: Input and output tokens for each model interaction
3. **Total Usage**: Aggregate tokens across the entire request

### Example Token Report
```json
{
  "total_tokens": 3456,
  "token_breakdown": {
    "context_summarization": 150,
    "research_planning": 800,
    "source_summarization": 1200,
    "brief_generation": 1306
  },
  "node_metrics": {
    "context_summarization": {
      "duration_seconds": 0.5,
      "tokens_used": 150,
      "timestamp": "2025-08-23T10:30:45.123Z"
    }
  }
}
```

## ⏱️ Latency Monitoring

### Execution Metrics
The system tracks execution time at multiple granularities:

1. **Total Request Latency**: End-to-end execution time
2. **Node-Level Latency**: Individual node execution duration
3. **LLM Call Latency**: Time spent in language model interactions

### Performance Monitoring API
```bash
# Get current metrics
GET /metrics

# Get specific execution metrics
GET /execution/{request_id}
```

### Example Performance Data
```json
{
  "request_id": "uuid-123-456",
  "duration_seconds": 12.45,
  "node_metrics": {
    "context_summarization": {
      "duration_seconds": 0.5,
      "tokens_used": 150
    },
    "research_planning": {
      "duration_seconds": 2.1,
      "tokens_used": 800
    },
    "web_search": {
      "duration_seconds": 3.2,
      "tokens_used": 0
    },
    "content_fetching": {
      "duration_seconds": 4.5,
      "tokens_used": 0
    },
    "source_summarization": {
      "duration_seconds": 1.8,
      "tokens_used": 1200
    },
    "brief_generation": {
      "duration_seconds": 2.3,
      "tokens_used": 1306
    }
  }
}
```

## 📈 Monitoring Endpoints

### Health Check
```bash
GET /metrics
```
Response:
```json
{
  "status": "healthy",
  "features": {
    "langsmith_tracing": true,
    "token_tracking": true,
    "latency_monitoring": true,
    "node_level_metrics": true
  },
  "monitoring": {
    "active_executions": 3,
    "langsmith_project": "context-aware-research-app",
    "trace_endpoint": "https://smith.langchain.com"
  }
}
```

### Execution Tracking
```bash
GET /execution/{request_id}
```
Returns detailed metrics for a specific execution.

## 🔍 LangGraph Node Monitoring

### Monitored Nodes
1. **context_summarization**: Session-based context analysis
2. **research_planning**: Research strategy generation
3. **web_search**: Multi-source information gathering
4. **content_fetching**: Detailed content retrieval
5. **source_summarization**: Content processing and analysis
6. **brief_generation**: Final research brief compilation

### Node Performance Metrics
Each node execution is tracked with:
- **Duration**: Execution time in seconds
- **Token Usage**: Estimated tokens consumed
- **Status**: Success/failure status
- **Timestamp**: Execution timestamp
- **Error Information**: Detailed error messages if applicable

## 📝 Logging

### Log Levels
- **INFO**: Successful operations and metrics
- **WARNING**: Non-critical issues
- **ERROR**: Failed operations with details

### Example Log Output
```
INFO:monitoring:Started tracking execution uuid-123-456
INFO:llm_tracking:LLM Call - Request: uuid-123-456, Node: research_planning, Model: gemini, Input Tokens: 450, Output Tokens: 350, Total: 800
INFO:monitoring:Node Metrics - research_planning: Duration: 2.10s, Tokens: 800
INFO:monitoring:Performance Metrics - Request: uuid-123-456, Duration: 12.45s, Total Tokens: 3456
INFO:monitoring:Execution uuid-123-456 completed successfully
```

## 🎯 Performance Benchmarks

### Typical Performance Ranges

| Operation | Duration Range | Token Range |
|-----------|---------------|-------------|
| Context Summarization | 0.3-0.8s | 100-300 tokens |
| Research Planning | 1.5-3.0s | 600-1200 tokens |
| Web Search | 2.0-5.0s | 0 tokens |
| Content Fetching | 3.0-8.0s | 0 tokens |
| Source Summarization | 1.0-3.0s | 800-2000 tokens |
| Brief Generation | 2.0-4.0s | 1000-2000 tokens |
| **Total Request** | **8-25s** | **2500-5500 tokens** |

### Factors Affecting Performance
- **Search Complexity**: More complex queries require additional processing
- **Content Volume**: Larger amounts of fetched content increase processing time
- **LLM Provider**: Different models have varying response times
- **Network Latency**: External API calls for search and content fetching

## 🔧 Configuration

### Monitoring Service Configuration
```python
# app/services/monitoring.py
monitoring_service = MonitoringService()

# Track execution
metrics = monitoring_service.start_execution(request_id)
monitoring_service.add_node_metrics(request_id, "node_name", duration, tokens)
monitoring_service.finish_execution(request_id)
```

### LangSmith Configuration
```python
# app/config.py
langsmith_api_key: Optional[str] = Field(None, description="LangSmith API key for tracing")
langchain_tracing_v2: bool = Field(True, description="Enable LangChain tracing")
langchain_endpoint: str = Field("https://api.smith.langchain.com", description="LangSmith endpoint")
langchain_project: str = Field("context-aware-research-app", description="LangSmith project name")
```

## 📊 Accessing Traces

### LangSmith Dashboard
1. **Login** to [LangSmith](https://smith.langchain.com)
2. **Navigate** to project: `context-aware-research-app`
3. **View Traces** by request ID or timestamp
4. **Analyze** node-by-node execution flow
5. **Debug** performance bottlenecks

### Programmatic Access
```python
# Get trace URL from response metadata
trace_url = response.metadata["trace_url"]
# Open in browser for detailed analysis
```

This comprehensive monitoring setup provides full visibility into the application's performance, token usage, and execution flow, enabling effective debugging and optimization.
