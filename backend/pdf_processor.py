"""
PDF Processing Helper for LlamaIndex integration

This module provides functions for extracting text from PDF files,
using either pypdf or PyPDF2 depending on availability.
"""

import os
import tempfile
import traceback

def extract_text_from_pdf(file_content):
    """
    Extract text from a PDF file using available PDF libraries.
    
    Args:
        file_content (bytes): The binary content of the PDF file
        
    Returns:
        str: The extracted text from the PDF
        
    Raises:
        Exception: If PDF processing fails
    """
    # Try to import PDF libraries - first pypdf (newer) then PyPDF2
    pdf_reader_lib = None
    pdf_reader_name = None
    
    try:
        from pypdf import PdfReader
        pdf_reader_lib = PdfReader
        pdf_reader_name = "pypdf"
        print("Using pypdf for PDF processing")
    except ImportError:
        try:
            from PyPDF2 import PdfReader
            pdf_reader_lib = PdfReader
            pdf_reader_name = "PyPDF2"
            print("Using PyPDF2 for PDF processing")
        except ImportError:
            raise ImportError(
                "PDF processing failed: Neither pypdf nor PyPDF2 are installed. "
                "Please install one of these packages with 'pip install pypdf' or 'pip install PyPDF2'."
            )
    
    # Create a temporary file to save the PDF
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(file_content)
            print(f"PDF content written to temp file: {temp_path}")
        
        # Extract text from PDF
        print(f"Attempting to read PDF with {pdf_reader_name}")
        pdf_reader = pdf_reader_lib(temp_path)
        print(f"PDF loaded successfully: {len(pdf_reader.pages)} pages")
        
        pdf_texts = []
        # Extract text from each page
        for page_num in range(len(pdf_reader.pages)):
            print(f"Processing PDF page {page_num+1}/{len(pdf_reader.pages)}")
            page = pdf_reader.pages[page_num]
            page_text = page.extract_text()
            pdf_texts.append(page_text or f"[Empty page {page_num+1}]")
        
        # Join all the pages together
        file_text = "\n\n".join(pdf_texts)
        print(f"PDF text extraction complete: {len(file_text)} characters extracted")
        
        return file_text
    
    except Exception as e:
        print(f"ERROR: PDF processing failed: {str(e)}")
        print(traceback.format_exc())
        raise Exception(f"PDF processing error: {str(e)}")
    
    finally:
        # Clean up temp file
        if temp_path and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
                print(f"Temporary PDF file removed: {temp_path}")
            except Exception as cleanup_error:
                print(f"WARNING: Failed to remove temporary file {temp_path}: {str(cleanup_error)}")
