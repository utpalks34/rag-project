AI Study Notes Assistant - Production-Ready RAG Application

A sophisticated Retrieval-Augmented Generation (RAG) system for intelligent question-answering from study materials. Upload PDFs, ask questions, and get accurate answers with source citations.

Key Features

### Core Functionality
-  **PDF Upload & Processing** - Extract text from multiple PDFs with page tracking
- **Semantic Chunking** - RecursiveCharacterTextSplitter with configurable parameters (512 chunks, 50 overlap)
   **Vector Storage** - Persistent ChromaDB with 50,000+ chunk capacity
-  **Semantic Search** - Cosine similarity-based retrieval
-  **RAG Pipeline** - Retrieve context + Generate answers with GPT-4
-  **Source Citations** - Track and display page numbers and source files
-  **Confidence Scores** - Show retrieval similarity metrics

Advanced Features
-  **Hybrid Retrieval** - Combines semantic + keyword search (toggleable)
-  **Query Rewriting** - Automatic query expansion for better results
-  **Chat History** - Persistent conversation memory
-  **Analytics** - Response times, document counts, metrics tracking
- **Dark/Light Themes** - Streamlit UI customization
-  **Performance** - <2 second response times on 50K+ chunks
-  **Docker Support** - Multi-container orchestration with Compose
- **Error Handling** - Comprehensive exception management with request tracking
- **Logging** - Structured logs with rotation and multiple outputs

 
