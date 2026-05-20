"""
PDF processing utilities for extracting text from PDF files.
"""

import os
from pathlib import Path
from typing import List, Dict, Optional
from pypdf import PdfReader
from utils.logger import logger


class PDFProcessor:
    """Handle PDF file operations and text extraction."""
    
    def __init__(self, upload_folder: str):
        """
        Initialize PDF processor.
        
        Args:
            upload_folder: Path to store uploaded PDFs
        """
        self.upload_folder = upload_folder
        Path(upload_folder).mkdir(parents=True, exist_ok=True)
    
    def extract_text_from_pdf(self, file_path: str) -> Dict[str, any]:
        """
        Extract text from a PDF file with page tracking.
        
        Args:
            file_path: Path to the PDF file
            
        Returns:
            Dictionary with extracted text and metadata
        """
        try:
            logger.info(f"Extracting text from PDF: {file_path}")
            
            pdf_reader = PdfReader(file_path)
            extracted_data = {
                "text": "",
                "pages": [],
                "total_pages": len(pdf_reader.pages),
                "filename": Path(file_path).name,
            }
            
            for page_num, page in enumerate(pdf_reader.pages, 1):
                page_text = page.extract_text()
                extracted_data["text"] += f"\n--- Page {page_num} ---\n{page_text}"
                extracted_data["pages"].append({
                    "page_num": page_num,
                    "text": page_text,
                })
            
            logger.info(f"Successfully extracted {extracted_data['total_pages']} pages from {file_path}")
            return extracted_data
            
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {str(e)}")
            raise
    
    def save_uploaded_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded PDF file.
        
        Args:
            file_content: Binary content of the file
            filename: Original filename
            
        Returns:
            Path to saved file
        """
        try:
            # Sanitize filename
            safe_filename = "".join(c for c in filename if c.isalnum() or c in "._- ")
            file_path = os.path.join(self.upload_folder, safe_filename)
            
            with open(file_path, "wb") as f:
                f.write(file_content)
            
            logger.info(f"Saved uploaded file: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Error saving uploaded file {filename}: {str(e)}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file."""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"Deleted file: {file_path}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error deleting file {file_path}: {str(e)}")
            return False
