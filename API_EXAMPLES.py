"""
API Usage Examples and Integration Guide
"""

# ============================================================================
# Example 1: Upload a PDF Document
# ============================================================================

import requests
import json

BASE_URL = "http://localhost:8000"

# Upload a PDF file
def upload_document(file_path: str):
    """Upload a PDF document to the system."""
    with open(file_path, 'rb') as f:
        files = {'file': (file_path, f, 'application/pdf')}
        response = requests.post(
            f"{BASE_URL}/api/upload",
            files=files,
            timeout=60
        )
    
    result = response.json()
    print(f"Upload Status: {result['status']}")
    print(f"File ID: {result['file_id']}")
    print(f"Pages: {result['total_pages']}")
    print(f"Chunks Created: {result['chunks_created']}")
    
    return result


# Usage:
# upload_document("study_guide.pdf")


# ============================================================================
# Example 2: Ask a Question
# ============================================================================

def ask_question(query: str, top_k: int = 5):
    """Ask a question about uploaded documents."""
    payload = {
        "query": query,
        "top_k": top_k,
        "include_sources": True
    }
    
    response = requests.post(
        f"{BASE_URL}/api/query",
        json=payload
    )
    
    result = response.json()
    
    print(f"\nQuestion: {query}\n")
    print(f"Answer:\n{result['answer']}\n")
    
    print(f"Response Time: {result['response_time_ms']:.0f}ms")
    print(f"Model Used: {result['model_used']}\n")
    
    print("Sources:")
    for i, chunk in enumerate(result['source_chunks'], 1):
        confidence = result['confidence_scores'][i-1]
        print(f"\n{i}. {chunk['source_file']} (Page {chunk['page_num']})")
        print(f"   Confidence: {confidence:.1%}")
        print(f"   Text: {chunk['text'][:100]}...")
    
    return result


# Usage:
# ask_question("What is photosynthesis?")


# ============================================================================
# Example 3: Chat Conversation with History
# ============================================================================

def get_chat_history():
    """Get the complete chat history."""
    response = requests.get(f"{BASE_URL}/api/chat/history")
    result = response.json()
    
    print(f"Total Messages: {result['total_messages']}\n")
    
    for msg in result['messages']:
        role = msg['role'].upper()
        timestamp = msg['timestamp']
        print(f"[{timestamp}] {role}:")
        print(f"{msg['content']}\n")
        
        if msg.get('sources'):
            print(f"Sources: {', '.join(msg['sources'])}\n")


# Usage:
# get_chat_history()


# ============================================================================
# Example 4: Conversational Flow
# ============================================================================

def conversation_example():
    """Demonstrate a multi-turn conversation."""
    
    questions = [
        "What is photosynthesis?",
        "Can you explain the light-dependent reactions?",
        "How is glucose produced?"
    ]
    
    for question in questions:
        print(f"\nUser: {question}")
        result = ask_question(question)
        print("\n" + "=" * 80)


# Usage:
# conversation_example()


# ============================================================================
# Example 5: Health Check and Statistics
# ============================================================================

def check_system_health():
    """Check system health and statistics."""
    
    # Health check
    response = requests.get(f"{BASE_URL}/health")
    health = response.json()
    
    print("System Health:")
    print(f"Status: {health['status']}")
    print(f"Database Connected: {health['database_connected']}")
    print(f"API Key Configured: {health['api_key_configured']}")
    
    # Statistics
    response = requests.get(f"{BASE_URL}/stats")
    stats = response.json()
    
    print(f"\nStatistics:")
    print(f"Documents in Index: {stats['pipeline_stats']['vector_store']['document_count']}")
    print(f"Average Response Time: {stats['metrics'].get('response_time_avg_ms', 'N/A'):.0f}ms")
    print(f"Total Queries: {stats['metrics'].get('query_count', 0)}")


# Usage:
# check_system_health()


# ============================================================================
# Example 6: Error Handling
# ============================================================================

def safe_query(query: str):
    """Safely handle query with error handling."""
    try:
        if not query or len(query) < 3:
            print("Error: Query must be at least 3 characters")
            return None
        
        response = requests.post(
            f"{BASE_URL}/api/query",
            json={"query": query, "top_k": 5},
            timeout=10
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            error = response.json()
            print(f"API Error: {error.get('error', 'Unknown error')}")
            print(f"Detail: {error.get('detail', 'No details')}")
            return None
    
    except requests.ConnectionError:
        print("Error: Could not connect to backend")
        return None
    except requests.Timeout:
        print("Error: Request timed out")
        return None
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


# Usage:
# safe_query("What is photosynthesis?")


# ============================================================================
# Example 7: Batch Operations
# ============================================================================

import os
from pathlib import Path

def upload_multiple_documents(folder_path: str):
    """Upload multiple PDF files from a folder."""
    results = []
    
    pdf_files = list(Path(folder_path).glob("*.pdf"))
    
    for i, pdf_file in enumerate(pdf_files, 1):
        print(f"Uploading {i}/{len(pdf_files)}: {pdf_file.name}")
        result = upload_document(str(pdf_file))
        results.append(result)
    
    return results


# Usage:
# upload_multiple_documents("./data/uploads")


# ============================================================================
# Example 8: Custom Integration (Python Script)
# ============================================================================

def create_study_assistant():
    """Create a simple study assistant CLI."""
    
    print("AI Study Assistant")
    print("=" * 60)
    
    while True:
        command = input("\n> Enter command (upload/ask/history/health/exit): ").strip().lower()
        
        if command == "upload":
            filepath = input("Enter file path: ").strip()
            if os.path.exists(filepath):
                upload_document(filepath)
            else:
                print(f"File not found: {filepath}")
        
        elif command == "ask":
            query = input("Enter your question: ").strip()
            if query:
                ask_question(query)
        
        elif command == "history":
            get_chat_history()
        
        elif command == "health":
            check_system_health()
        
        elif command == "exit":
            print("Goodbye!")
            break
        
        else:
            print("Unknown command. Try: upload, ask, history, health, or exit")


# Usage:
# create_study_assistant()


# ============================================================================
# Example 9: Advanced - Custom Headers and Tracking
# ============================================================================

def query_with_tracking(query: str, user_id: str = None):
    """Query with custom headers for tracking."""
    
    headers = {
        "X-User-ID": user_id or "anonymous",
        "X-Request-Source": "python-client"
    }
    
    response = requests.post(
        f"{BASE_URL}/api/query",
        json={"query": query, "top_k": 5},
        headers=headers
    )
    
    # Check response headers
    request_id = response.headers.get("X-Request-ID")
    process_time = response.headers.get("X-Process-Time")
    
    print(f"Request ID: {request_id}")
    print(f"Process Time: {process_time} seconds")
    
    return response.json()


# Usage:
# query_with_tracking("What is photosynthesis?", user_id="user123")


# ============================================================================
# Example 10: Testing and Validation
# ============================================================================

def validate_api_endpoints():
    """Validate all API endpoints are working."""
    
    endpoints = [
        ("GET", "/health"),
        ("GET", "/stats"),
        ("GET", "/docs"),
    ]
    
    print("Validating API Endpoints:")
    
    for method, endpoint in endpoints:
        try:
            if method == "GET":
                response = requests.get(f"{BASE_URL}{endpoint}", timeout=5)
            
            status = "✓" if response.status_code == 200 else "✗"
            print(f"{status} {method:4} {endpoint:20} - {response.status_code}")
        
        except Exception as e:
            print(f"✗ {method:4} {endpoint:20} - Error: {str(e)}")


# Usage:
# validate_api_endpoints()


# ============================================================================
# Example 11: Async Integration (Using asyncio)
# ============================================================================

import asyncio
import aiohttp

async def async_query(session, query: str):
    """Async query function."""
    async with session.post(
        f"{BASE_URL}/api/query",
        json={"query": query, "top_k": 5}
    ) as response:
        return await response.json()


async def batch_queries(queries: list):
    """Run multiple queries concurrently."""
    async with aiohttp.ClientSession() as session:
        tasks = [async_query(session, q) for q in queries]
        results = await asyncio.gather(*tasks)
        return results


# Usage:
# queries = ["What is photosynthesis?", "What is cellular respiration?"]
# results = asyncio.run(batch_queries(queries))


# ============================================================================
# Main Example Runner
# ============================================================================

if __name__ == "__main__":
    """
    Run examples:
    
    python examples.py upload <filepath>
    python examples.py ask "<question>"
    python examples.py history
    python examples.py health
    python examples.py validate
    """
    
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python examples.py [command] [args]")
        print("\nCommands:")
        print("  upload <filepath>  - Upload a PDF file")
        print("  ask <question>     - Ask a question")
        print("  history            - Show chat history")
        print("  health             - Check system health")
        print("  validate           - Validate endpoints")
        sys.exit(1)
    
    command = sys.argv[1].lower()
    
    if command == "upload" and len(sys.argv) > 2:
        upload_document(sys.argv[2])
    elif command == "ask" and len(sys.argv) > 2:
        ask_question(sys.argv[2])
    elif command == "history":
        get_chat_history()
    elif command == "health":
        check_system_health()
    elif command == "validate":
        validate_api_endpoints()
    else:
        print(f"Unknown command: {command}")
