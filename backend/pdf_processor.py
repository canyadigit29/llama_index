"""
PDF Processing Helper for LlamaIndex integration

This module provides functions for extracting text from PDF files,
using either pypdf or PyPDF2 depending on availability.
It also includes OCR capabilities for scanned PDFs using pdf2image and pytesseract.
"""

import os
import tempfile
import traceback
import re

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
    # Print detailed diagnostic information
    print("="*50)
    print("PDF PROCESSOR DIAGNOSTIC")
    print("="*50)
    print(f"File content type: {type(file_content)}")
    print(f"File content size: {len(file_content) if file_content else 0} bytes")
    if file_content and len(file_content) > 100:
        print(f"First 100 bytes: {file_content[:100]}")
        # Check if it looks like a valid PDF (should start with %PDF)
        print(f"Starts with %PDF: {'Yes' if file_content.startswith(b'%PDF') else 'No'}")
    print("="*50)
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

def is_meaningful_text(text, min_length=50, min_words=10):
    """
    Check if extracted text is meaningful.
    
    Args:
        text (str): The text to check
        min_length (int): Minimum character length to be considered meaningful
        min_words (int): Minimum word count to be considered meaningful
        
    Returns:
        bool: True if the text appears meaningful
    """
    if not text or len(text.strip()) < min_length:
        return False
    
    # Count words (simple approach)
    words = re.findall(r'\w+', text)
    if len(words) < min_words:
        return False
        
    # Look for patterns that might indicate meaningful text
    # (meaningful text typically has spaces, punctuation, etc.)
    if ' ' not in text:  # No spaces usually means garbage text
        return False
        
    return True

def perform_ocr_on_pdf(file_content):
    """
    Extract text from a scanned PDF using OCR.
    
    Args:
        file_content (bytes): The binary content of the PDF file
        
    Returns:
        str: The extracted text from the PDF using OCR
        
    Raises:
        Exception: If OCR processing fails
    """
    try:
        print("="*50)
        print("OCR PROCESSING INITIATED")
        print("="*50)
        
        # Import dependencies for OCR
        try:
            from pdf2image import convert_from_bytes
            import pytesseract
            from PIL import Image
        except ImportError as imp_err:
            print(f"ERROR: Required OCR libraries not installed: {str(imp_err)}")
            print("Install with: pip install pdf2image pytesseract Pillow")
            raise ImportError(f"OCR dependencies not installed: {str(imp_err)}")
        
        # Create a temp file for processing
        temp_pdf = None
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp:
                temp_pdf = temp.name
                temp.write(file_content)
            
            # Convert PDF pages to images
            print("Converting PDF pages to images...")
            images = convert_from_bytes(
                file_content,
                dpi=300,  # Higher DPI for better quality
                thread_count=2,  # Parallel processing
                grayscale=False,  # Color can help OCR in some cases
            )
            print(f"Successfully converted {len(images)} pages to images")
            
            # Process each page with OCR
            all_text = []
            for i, image in enumerate(images):
                print(f"Performing OCR on page {i+1}/{len(images)}...")
                
                # Process with pytesseract
                page_text = pytesseract.image_to_string(image, lang='eng')
                
                if page_text:
                    all_text.append(page_text)
                    char_count = len(page_text)
                    word_count = len(page_text.split())
                    print(f"  Page {i+1}: Extracted {char_count} chars, ~{word_count} words")
                else:
                    print(f"  Page {i+1}: No text extracted")
                    all_text.append(f"[No text could be extracted from page {i+1}]")
            
            # Combine all text from all pages
            result = "\n\n".join(all_text)
            total_length = len(result)
            print(f"OCR completed: Total {total_length} characters extracted")
            
            # Return empty string if no meaningful text was found
            if not result or total_length < 50:
                print("WARNING: OCR process produced little or no text")
                return ""
                
            return result
            
        finally:
            # Clean up temporary files
            if temp_pdf and os.path.exists(temp_pdf):
                os.unlink(temp_pdf)
                print(f"Temporary OCR PDF file cleaned up: {temp_pdf}")
                
    except Exception as e:
        print(f"ERROR during OCR processing: {str(e)}")
        print(traceback.format_exc())
        return ""  # Return empty string on error


def extract_text_with_ocr_fallback(file_content):
    """
    Extract text from PDF with automatic OCR fallback for scanned documents.
    
    This is the main function that should be called from external modules.
    It attempts standard text extraction first and falls back to OCR 
    if the document appears to be scanned/image-based.
    
    Args:
        file_content (bytes): The binary content of the PDF file
        
    Returns:
        str: The extracted text and a boolean indicating if OCR was used
        
    """
    print("="*50)
    print("PDF PROCESSING WITH OCR FALLBACK")
    print("="*50)
    
    # First attempt: try standard text extraction
    standard_text = ""
    used_ocr = False
    error_message = None
    
    try:
        standard_text = extract_text_from_pdf(file_content)
        print(f"Standard extraction yielded {len(standard_text)} characters")
        
        # Check if the standard extraction gave meaningful results
        if is_meaningful_text(standard_text):
            print("Standard text extraction succeeded, no need for OCR")
            return standard_text, False
        else:
            print("Standard text extraction produced insufficient results, will try OCR")
    except Exception as e:
        error_message = str(e)
        print(f"Standard text extraction failed: {error_message}")
        print("Will attempt OCR as fallback")
    
    # Second attempt: OCR-based extraction
    try:
        print("Starting OCR processing...")
        ocr_text = perform_ocr_on_pdf(file_content)
        
        if is_meaningful_text(ocr_text):
            print("OCR extraction succeeded")
            return ocr_text, True
        else:
            print("OCR extraction produced insufficient results")
            
            # If both methods failed to produce meaningful text
            if not is_meaningful_text(standard_text) and not is_meaningful_text(ocr_text):
                print("WARNING: Both standard extraction and OCR failed to extract meaningful text")
                
                # Return the better of the two results, or combine them
                combined = (standard_text or "") + "\n\n" + (ocr_text or "")
                if combined.strip():
                    return combined, True
                    
                # Last resort - return a placeholder with the error
                return f"[PDF processing failed: {error_message or 'No text could be extracted'}]", False
            
            # If we have some standard text, return it even if not ideal
            return standard_text or ocr_text, ocr_text != ""
            
    except Exception as ocr_err:
        print(f"OCR processing also failed: {str(ocr_err)}")
        # If OCR fails but we have some text from standard extraction, return it
        if standard_text:
            return standard_text, False
        return f"[PDF processing failed: {error_message or str(ocr_err)}]", False
