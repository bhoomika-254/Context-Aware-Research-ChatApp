"""
Streamlit Research Assistant Chatbot - Hugging Face Spaces Version
Direct integration without FastAPI backend
"""
import streamlit as st
import asyncio
import os
from datetime import datetime
import uuid
from typing import Dict, Any
import sys
import traceback
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
app_dir = os.path.join(current_dir, "app")
if app_dir not in sys.path:
    sys.path.insert(0, app_dir)

# Import the research functionality directly
try:
    from app.config import settings
    from app.graph.main import research_graph
    from app.structure.pydantic import BriefRequest, BriefResponse
except ImportError as e:
    st.error(f"Import error: {e}")
    st.error("Please ensure all dependencies are installed correctly.")
    st.stop()

# Configure page
st.set_page_config(
    page_title="🔬 Research Brief Generator",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main {
        padding-top: 1rem;
    }
    .stAlert {
        padding: 0.5rem;
        margin: 0.5rem 0;
    }
    .research-card {
        background: #f8fafc;
        padding: 1.5rem;
        border-radius: 10px;
        border-left: 4px solid #6366f1;
        margin: 1rem 0;
    }
    .source-card {
        background: #fefefe;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        margin: 0.5rem 0;
    }
    .insight-card {
        background: #f0f9ff;
        padding: 1rem;
        border-radius: 8px;
        border-left: 3px solid #0ea5e9;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def check_environment():
    """Check if required environment variables are set."""
    required_vars = [
        "GOOGLE_API_KEY",
        "GOOGLE_CSE_ID"
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        st.error(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        st.info("Please set these in your Hugging Face Space secrets.")
        return False
    return True

async def generate_research_brief(query: str, focus_areas: list = None) -> Dict[str, Any]:
    """Generate research brief using the direct graph integration."""
    try:
        # Create request
        request = BriefRequest(
            query=query,
            focus_areas=focus_areas or [],
            user_id=str(uuid.uuid4()),
            session_id=str(uuid.uuid4())
        )
        
        # Run the research graph
        result = await research_graph.ainvoke({
            "query": request.query,
            "focus_areas": request.focus_areas,
            "user_id": request.user_id,
            "session_id": request.session_id
        })
        
        return result
        
    except Exception as e:
        st.error(f"Error generating research brief: {str(e)}")
        st.error(f"Traceback: {traceback.format_exc()}")
        return None

def display_research_results(result: Dict[str, Any]):
    """Display the research results in a structured format."""
    if not result:
        return
    
    # Display main brief
    if "synthesis" in result and result["synthesis"]:
        synthesis = result["synthesis"]
        
        st.markdown("## 📋 Research Brief")
        st.markdown(f"<div class='research-card'>{synthesis.get('content', 'No content available')}</div>", unsafe_allow_html=True)
        
        # Display insights
        if "insights" in synthesis and synthesis["insights"]:
            st.markdown("### 💡 Key Insights")
            for i, insight in enumerate(synthesis["insights"], 1):
                insight_content = insight.get('content', 'No content')
                confidence = insight.get('confidence_level', 0)
                st.markdown(f"""
                <div class='insight-card'>
                    <strong>Insight {i}</strong> (Confidence: {confidence}%)<br/>
                    {insight_content}
                </div>
                """, unsafe_allow_html=True)
    
    # Display sources
    if "sources" in result and result["sources"]:
        st.markdown("### 📚 Sources")
        
        for i, source in enumerate(result["sources"], 1):
            # Handle both old and new source formats
            if isinstance(source, dict):
                title = source.get('title', f'Source {i}')
                url = source.get('url', '#')
                summary = source.get('summary', 'No summary available')
            else:
                # Handle source objects
                title = getattr(source, 'title', f'Source {i}')
                url = getattr(source, 'url', '#')
                summary = getattr(source, 'summary', 'No summary available')
            
            st.markdown(f"""
            <div class='source-card'>
                <strong><a href="{url}" target="_blank">{title}</a></strong><br/>
                {summary}
            </div>
            """, unsafe_allow_html=True)

def main():
    """Main application function."""
    # Header
    st.title("🔬 Context-Aware Research Brief Generator")
    st.markdown("Generate comprehensive research briefs on any topic using AI-powered analysis and real-time data sources.")
    
    # Check environment
    if not check_environment():
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.header("🔧 Configuration")
        
        # Focus areas
        st.subheader("Focus Areas (Optional)")
        focus_areas_text = st.text_area(
            "Enter focus areas (one per line):",
            placeholder="e.g.\nMarket trends\nTechnical analysis\nCompetitive landscape",
            height=100
        )
        
        focus_areas = [area.strip() for area in focus_areas_text.split('\n') if area.strip()] if focus_areas_text else []
        
        if focus_areas:
            st.write("**Selected Focus Areas:**")
            for area in focus_areas:
                st.write(f"• {area}")
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        query = st.text_input(
            "🔍 **Enter your research query:**",
            placeholder="e.g., Latest developments in artificial intelligence for healthcare",
            help="Enter a topic or question you'd like to research"
        )
    
    with col2:
        st.markdown("<br/>", unsafe_allow_html=True)  # Add some spacing
        generate_button = st.button("🚀 Generate Brief", type="primary", use_container_width=True)
    
    # Generate research brief
    if generate_button and query:
        if len(query.strip()) < 10:
            st.warning("⚠️ Please enter a more detailed research query (at least 10 characters).")
        else:
            with st.spinner("🔍 Researching and generating brief..."):
                # Progress indicators
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                status_text.text("🔍 Searching for relevant sources...")
                progress_bar.progress(25)
                
                # Run the research
                try:
                    result = asyncio.run(generate_research_brief(query, focus_areas))
                    
                    progress_bar.progress(75)
                    status_text.text("📝 Generating comprehensive brief...")
                    
                    progress_bar.progress(100)
                    status_text.text("✅ Research brief generated successfully!")
                    
                    # Clear progress indicators
                    progress_bar.empty()
                    status_text.empty()
                    
                    # Display results
                    if result:
                        display_research_results(result)
                        
                        # Store in session state for download
                        st.session_state['last_result'] = result
                        st.session_state['last_query'] = query
                        
                        st.success("✅ Research brief generated successfully!")
                    else:
                        st.error("❌ Failed to generate research brief. Please try again.")
                        
                except Exception as e:
                    progress_bar.empty()
                    status_text.empty()
                    st.error(f"❌ Error: {str(e)}")
                    st.error("Please check your API keys and try again.")
    
    elif generate_button and not query:
        st.warning("⚠️ Please enter a research query first.")
    
    # Example queries
    with st.expander("💡 Example Research Queries"):
        examples = [
            "Latest developments in quantum computing applications",
            "Impact of remote work on employee productivity and well-being",
            "Sustainable energy solutions for urban environments",
            "Artificial intelligence in healthcare diagnostics",
            "Blockchain technology adoption in supply chain management",
            "Climate change effects on global agriculture",
            "Cybersecurity trends and threats in 2024"
        ]
        
        for example in examples:
            if st.button(example, key=f"example_{example}", use_container_width=True):
                st.experimental_set_query_params(query=example)
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #6b7280; padding: 1rem;'>
        🔬 <strong>Context-Aware Research Brief Generator</strong><br/>
        Powered by LangGraph, Google Search, and Advanced AI Models<br/>
        <small>Generate comprehensive research briefs with real-time data and AI analysis</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
