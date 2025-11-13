"""
Phase 7: Streamlit Frontend

Interactive UI for querying the Shakespearean Scholar RAG system
"""

import streamlit as st
import requests
import json
import os
from typing import Dict, Any

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8002")


def init_session_state():
    """Initialize session state variables"""
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []


def call_api(endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
    """Call the FastAPI backend"""
    url = f"{API_URL}{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, params=data, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, timeout=30)
        
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {str(e)}")
        return None


def format_source(source: Dict, index: int) -> str:
    """Format a source citation"""
    metadata = source.get('metadata', {})
    act = metadata.get('act', '?')
    scene = metadata.get('scene', '?')
    speaker = metadata.get('speaker', '')
    chunk_type = metadata.get('type', '')
    
    citation = f"**Source {index + 1}: Act {act}, Scene {scene}"
    if speaker:
        citation += f" - {speaker}**"
    else:
        citation += "**"
    
    if chunk_type:
        citation += f" _{chunk_type}_"
    
    return citation


def main():
    """Main Streamlit application"""
    init_session_state()
    
    # Page config
    st.set_page_config(
        page_title="Shakespearean Scholar",
        page_icon="📚",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
    <style>
    .main {
        padding: 2rem;
    }
    .stAlert {
        margin-top: 1rem;
    }
    .source-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.title("📚 The Shakespearean Scholar")
    st.markdown("*An Expert AI Tutor on Julius Caesar by William Shakespeare*")
    st.divider()
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Settings")
        
        # Number of sources
        n_results = st.slider(
            "Number of sources to retrieve",
            min_value=1,
            max_value=10,
            value=5,
            help="More sources = more context but slower"
        )
        
        st.divider()
        
        # Health check
        st.subheader("🔍 System Status")
        if st.button("Check Health"):
            with st.spinner("Checking..."):
                health = call_api("/health")
                if health:
                    if health['status'] == 'healthy':
                        st.success(f"✅ {health['message']}")
                        st.info(f"Database: {health.get('db_count', 0)} chunks")
                    else:
                        st.warning(f"⚠️ {health['message']}")
        
        st.divider()
        
        # Stats
        st.subheader("📊 Database Stats")
        if st.button("View Stats"):
            with st.spinner("Loading stats..."):
                stats = call_api("/stats")
                if stats:
                    st.metric("Total Chunks", stats['total_chunks'])
                    st.write("**Chunks by Act:**")
                    for act, count in stats['chunks_by_act'].items():
                        st.write(f"Act {act}: {count}")
        
        st.divider()
        
        # Sample questions
        st.subheader("💡 Sample Questions")
        sample_questions = [
            "What does the Soothsayer say to Caesar?",
            "Why does Brutus decide to join the conspiracy?",
            "Describe Antony's funeral speech",
            "What is Brutus's internal conflict?",
            "How does Caesar respond to warnings?"
        ]
        
        for i, question in enumerate(sample_questions):
            if st.button(question, key=f"sample_{i}"):
                st.session_state.current_query = question
        
        st.divider()
        
        # Clear history
        if st.button("🗑️ Clear History"):
            st.session_state.chat_history = []
            st.rerun()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🎓 Ask Your Question")
        
        # Check if we have a sample question
        default_query = st.session_state.get('current_query', '')
        
        # Query input
        query = st.text_area(
            "Enter your question about Julius Caesar:",
            value=default_query,
            height=100,
            placeholder="e.g., What warning does the Soothsayer give to Caesar?",
            key="query_input"
        )
        
        # Clear the current_query after using it
        if 'current_query' in st.session_state:
            del st.session_state.current_query
        
        col_btn1, col_btn2 = st.columns([1, 4])
        with col_btn1:
            submit_button = st.button("🔍 Ask Scholar", type="primary", use_container_width=True)
        
        # Process query
        if submit_button and query.strip():
            with st.spinner("🤔 The Scholar is thinking..."):
                # Call API
                result = call_api(
                    "/query",
                    method="POST",
                    data={"query": query, "n_results": n_results}
                )
                
                if result:
                    # Add to chat history
                    st.session_state.chat_history.append({
                        'query': query,
                        'result': result
                    })
                    
                    # Display answer
                    st.success("✅ Answer Generated!")
                    st.divider()
                    
                    # Answer
                    st.subheader("📖 Scholar's Answer")
                    st.markdown(result['answer'])
                    
                    st.divider()
                    
                    # Sources
                    st.subheader("📚 Textual Evidence")
                    st.caption("Retrieved sources from Julius Caesar:")
                    
                    for i, source in enumerate(result['sources']):
                        with st.expander(format_source(source, i), expanded=(i < 2)):
                            st.markdown(f"```\n{source['chunk']}\n```")
                            if source.get('distance'):
                                st.caption(f"Similarity score: {1 - source['distance']:.4f}")
    
    with col2:
        st.subheader("📜 Query History")
        
        if st.session_state.chat_history:
            for i, item in enumerate(reversed(st.session_state.chat_history)):
                with st.expander(f"Q{len(st.session_state.chat_history) - i}: {item['query'][:50]}...", expanded=False):
                    st.write("**Question:**")
                    st.write(item['query'])
                    st.write("**Answer:**")
                    st.write(item['result']['answer'][:200] + "...")
        else:
            st.info("No queries yet. Ask a question to get started!")
    
    # Footer
    st.divider()
    st.caption("🎭 The Shakespearean Scholar | Built with Streamlit & FastAPI | Powered by Google Gemini")


if __name__ == "__main__":
    main()
