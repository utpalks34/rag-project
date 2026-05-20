"""
Streamlit frontend for the AI Study Notes Assistant.
User-friendly interface for document upload and question answering.
"""

import streamlit as st
import requests
import json
from datetime import datetime
import os
from typing import Optional
import base64

# Page configuration
st.set_page_config(
    page_title="AI Study Notes Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main {
        padding: 0rem 0rem;
    }
    
    .stTabs [data-baseweb="tab-list"] button {
        font-size: 16px;
        font-weight: bold;
    }
    
    .source-citation {
        padding: 10px;
        margin: 5px 0;
        border-left: 4px solid #1f77b4;
        background-color: #f0f7ff;
        border-radius: 4px;
    }
    
    .confidence-score {
        display: inline-block;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin-left: 5px;
    }
    
    .high-confidence {
        background-color: #d4edda;
        color: #155724;
    }
    
    .medium-confidence {
        background-color: #fff3cd;
        color: #856404;
    }
    
    .low-confidence {
        background-color: #f8d7da;
        color: #721c24;
    }
</style>
""", unsafe_allow_html=True)


# Initialize session state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

if "api_endpoint" not in st.session_state:
    st.session_state.api_endpoint = os.getenv("BACKEND_URL", "http://localhost:8000")


# API utilities
def check_backend_health():
    """Check if backend is running."""
    try:
        response = requests.get(
            f"{st.session_state.api_endpoint}/health",
            timeout=5
        )
        return response.status_code == 200
    except Exception:
        return False


def upload_document(file):
    """Upload document to backend."""
    try:
        files = {"file": (file.name, file, "application/pdf")}
        response = requests.post(
            f"{st.session_state.api_endpoint}/api/upload",
            files=files,
            timeout=120
        )
        
        if response.status_code == 200:
            return response.json(), True
        else:
            return response.json(), False
    except Exception as e:
        return {"error": str(e)}, False


def query_documents(query: str, top_k: int = 5):
    """Send query to backend."""
    try:
        data = {
            "query": query,
            "top_k": top_k,
            "include_sources": True
        }
        
        response = requests.post(
            f"{st.session_state.api_endpoint}/api/query",
            json=data,
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json(), True
        else:
            return response.json(), False
    except Exception as e:
        return {"error": str(e)}, False


def get_chat_history():
    """Fetch chat history from backend."""
    try:
        response = requests.get(
            f"{st.session_state.api_endpoint}/api/chat/history",
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()["messages"]
        return []
    except Exception:
        return []


def clear_chat():
    """Clear chat history on backend."""
    try:
        requests.post(
            f"{st.session_state.api_endpoint}/api/chat/clear",
            timeout=10
        )
        st.session_state.chat_history = []
    except Exception as e:
        st.error(f"Error clearing chat: {str(e)}")


def get_confidence_badge(score: float) -> str:
    """Get HTML badge for confidence score."""
    if score >= 0.7:
        css_class = "high-confidence"
        label = "High"
    elif score >= 0.5:
        css_class = "medium-confidence"
        label = "Medium"
    else:
        css_class = "low-confidence"
        label = "Low"
    
    return f"""<span class="confidence-score {css_class}">{label} ({score:.2%})</span>"""


# Main UI
def main():
    """Main application logic."""
    
    # Header
    st.markdown("# 📚 AI Study Notes Assistant")
    st.markdown(
        "*Your intelligent study companion powered by RAG (Retrieval-Augmented Generation)*"
    )
    
    # Check backend
    if not check_backend_health():
        st.error(
            "⚠️ Backend is not running. Please ensure the FastAPI server is running on "
            f"{st.session_state.api_endpoint}"
        )
        st.stop()
    
    # Sidebar
    with st.sidebar:
        st.markdown("## ⚙️ Settings")
        
        # API Endpoint
        st.session_state.api_endpoint = st.text_input(
            "Backend API Endpoint",
            value=st.session_state.api_endpoint,
            help="URL of the FastAPI backend"
        )
        
        # Theme
        theme = st.radio("Theme", ["Light", "Dark"])
        
        # Top K setting
        top_k = st.slider(
            "Top K Results",
            min_value=1,
            max_value=20,
            value=5,
            help="Number of source documents to retrieve"
        )
        
        st.markdown("---")
        
        # Stats
        st.markdown("## 📊 Statistics")
        try:
            response = requests.get(
                f"{st.session_state.api_endpoint}/stats",
                timeout=5
            )
            if response.status_code == 200:
                stats = response.json()
                
                st.metric(
                    "Documents in Index",
                    stats.get("pipeline_stats", {}).get("vector_store", {}).get("document_count", 0)
                )
                
                if "metrics" in stats:
                    if stats["metrics"].get("response_time_avg_ms"):
                        st.metric(
                            "Avg Response Time",
                            f"{stats['metrics']['response_time_avg_ms']:.0f}ms"
                        )
        except Exception:
            pass
        
        # Chat controls
        st.markdown("---")
        if st.button("🗑️ Clear Chat History", use_container_width=True):
            clear_chat()
            st.rerun()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📤 Upload", "💬 Chat", "📖 Sources"])
    
    # ==================== UPLOAD TAB ====================
    with tab1:
        st.markdown("## Upload Study Materials")
        st.markdown("Upload PDF files to add them to your study database.")
        
        uploaded_files = st.file_uploader(
            "Choose PDF files",
            type=["pdf"],
            accept_multiple_files=True,
            help="Max 50MB per file"
        )
        
        if uploaded_files:
            progress_bar = st.progress(0)
            
            for idx, file in enumerate(uploaded_files):
                st.info(f"Processing: {file.name}")
                
                result, success = upload_document(file)
                
                if success:
                    st.success(
                        f"✅ Uploaded successfully\n"
                        f"- Pages: {result.get('total_pages', 'N/A')}\n"
                        f"- Chunks created: {result.get('chunks_created', 'N/A')}\n"
                        f"- Upload time: {result.get('upload_time', 'N/A')}"
                    )
                    st.session_state.uploaded_files.append(file.name)
                else:
                    st.error(f"❌ Error uploading file: {result.get('detail', 'Unknown error')}")
                
                progress_bar.progress((idx + 1) / len(uploaded_files))
    
    # ==================== CHAT TAB ====================
    with tab2:
        st.markdown("## Chat with Your Study Materials")
        
        # Display chat history
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                if message["role"] == "user":
                    with st.chat_message("user"):
                        st.markdown(message["content"])
                else:
                    with st.chat_message("assistant"):
                        st.markdown(message["content"])
                        
                        # Display sources if available
                        if message.get("sources"):
                            with st.expander("📚 Sources"):
                                for source in message["sources"]:
                                    st.markdown(f"- {source}")
        
        # Query input
        st.markdown("---")
        
        col1, col2 = st.columns([4, 1])
        
        with col1:
            user_query = st.text_input(
                "Ask a question about your study materials",
                placeholder="e.g., What is photosynthesis?",
                label_visibility="collapsed"
            )
        
        with col2:
            send_button = st.button("Send", use_container_width=True, key="send_button")
        
        if send_button and user_query:
            # Add user message
            st.session_state.chat_history.append({
                "role": "user",
                "content": user_query
            })
            
            # Get response
            with st.spinner("🤔 Thinking..."):
                response, success = query_documents(user_query, top_k)
            
            if success:
                answer = response.get("answer", "No answer generated")
                source_chunks = response.get("source_chunks", [])
                confidence_scores = response.get("confidence_scores", [])
                response_time = response.get("response_time_ms", 0)
                
                # Add assistant message
                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer,
                    "sources": [chunk["source_file"] for chunk in source_chunks]
                })
                
                # Display response
                with st.chat_message("assistant"):
                    st.markdown(answer)
                    
                    st.markdown(f"⏱️ Response time: {response_time:.0f}ms")
                    
                    # Display sources
                    if source_chunks:
                        with st.expander(f"📚 Sources ({len(source_chunks)} results)"):
                            for i, chunk in enumerate(source_chunks):
                                confidence = confidence_scores[i] if i < len(confidence_scores) else 0
                                
                                st.markdown(f"""
                                <div class="source-citation">
                                    <b>Source: {chunk['source_file']}</b> (Page {chunk['page_num']})
                                    {get_confidence_badge(confidence)}
                                    <br><br>
                                    {chunk['text']}
                                </div>
                                """, unsafe_allow_html=True)
            else:
                st.error(f"Error: {response.get('detail', 'Unknown error')}")
            
            st.rerun()
    
    # ==================== SOURCES TAB ====================
    with tab3:
        st.markdown("## Uploaded Sources")
        
        if st.session_state.uploaded_files:
            for filename in st.session_state.uploaded_files:
                st.markdown(f"✓ {filename}")
        else:
            st.info("No files uploaded yet. Upload PDF files in the Upload tab to get started.")


if __name__ == "__main__":
    main()
