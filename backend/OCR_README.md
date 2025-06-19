# OCR Support for LlamaIndex Backend

This backend now includes OCR (Optical Character Recognition) capabilities for processing scanned PDFs. This allows the system to extract text from images or scanned documents that don't have a machine-readable text layer.

## Features

- **Automatic OCR Detection**: The system automatically detects when a PDF might be scanned or image-based and applies OCR as needed
- **Fallback Processing**: First attempts standard text extraction, falls back to OCR if needed
- **Quality Analysis**: Evaluates extracted text to ensure it's meaningful before returning results

## Requirements

The OCR system requires:

1. **Python Libraries**:
   - `pdf2image`: For converting PDF pages to images
   - `pytesseract`: Python wrapper for Tesseract OCR
   - `Pillow`: For image processing

2. **System Dependencies**:
   - Tesseract OCR engine
   - Poppler utilities (for PDF to image conversion)

## Deployment

For Railway deployment, the Dockerfile already includes the necessary system dependencies.

For local development:
- **Ubuntu/Debian**: `sudo apt-get install tesseract-ocr poppler-utils`
- **macOS**: `brew install tesseract poppler`
- **Windows**: Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and ensure it's in your PATH

## Configuration

No additional configuration is required. The OCR system will automatically process PDFs as needed.

## Troubleshooting

If OCR processing is failing:

1. Check that Tesseract is properly installed and in the PATH
2. Ensure PDF files are valid and not corrupted
3. For poor quality scans, results may be limited - consider pre-processing the images

## Future Improvements

Potential enhancements:

1. Language detection for non-English documents
2. Image preprocessing for better OCR results
3. Support for additional OCR engines
4. Custom OCR settings based on document types
