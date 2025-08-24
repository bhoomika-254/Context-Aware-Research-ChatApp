# Hugging Face Spaces Deployment Guide

## Required Environment Variables

Set these in your Hugging Face Space's Settings → Repository secrets:

### Required (Core functionality):
- `GOOGLE_API_KEY`: Your Google Cloud API key for Gemini
- `GOOGLE_CSE_ID`: Your Google Custom Search Engine ID

### Optional (Enhanced features):
- `TOGETHER_API_KEY`: Together AI API key for additional LLM options
- `TAVILY_API_KEY`: Tavily API key for enhanced web search
- `LANGSMITH_API_KEY`: LangSmith API key for monitoring (optional)
- `LANGCHAIN_TRACING_V2`: Set to "true" to enable LangSmith tracing
- `LANGCHAIN_PROJECT`: Project name for LangSmith (default: "context-aware-research-app")

### Database (Optional):
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon key
- `SUPABASE_SERVICE_KEY`: Supabase service role key

## Deployment Steps

1. **Fork this repository** to your GitHub account

2. **Create a new Hugging Face Space**:
   - Go to https://huggingface.co/new-space
   - Choose "Streamlit" as the SDK
   - Link your forked repository

3. **Set Environment Variables**:
   - Go to your Space's Settings
   - Add the required environment variables in the "Repository secrets" section

4. **Deploy**:
   - Your Space will automatically build and deploy
   - The app will be available at your Space URL

## API Key Setup

### Google API Key & Custom Search Engine:
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable "Custom Search API" and "Generative Language API"
4. Create credentials (API Key)
5. Create a Custom Search Engine at [Google CSE](https://cse.google.com/)
6. Get your Search Engine ID

### Together AI (Optional):
1. Sign up at [Together AI](https://together.ai/)
2. Generate an API key from your dashboard

### Tavily (Optional):
1. Sign up at [Tavily](https://tavily.com/)
2. Get your API key from the dashboard

## Troubleshooting

- **Import Errors**: Ensure all dependencies are in requirements.txt
- **API Errors**: Check that your API keys are correctly set
- **Search Issues**: Verify Google CSE is properly configured
- **Memory Issues**: The app uses async processing to handle memory efficiently

## Local Development

For local development, copy `.env.example` to `.env` and fill in your API keys.
