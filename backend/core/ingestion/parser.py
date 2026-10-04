import os
import pdfplumber
from docx import Document

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file while preserving layout 
    to handle multi-column resumes correctly.
    Args:
        - file_path: the path to the file for uploading
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at: {file_path}")
        
    full_text = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text(layout=True)
            if text:
                full_text.append(text)
                
    return "\n".join(full_text)

def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts text from a Microsoft Word (.docx) resume.
    Args:
        - file_path: the path to the file for uploading
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"DOCX file not found at: {file_path}")
        
    doc = Document(file_path)
    full_text = []
    for paragraph in doc.paragraphs:
        if paragraph.text.strip():
            full_text.append(paragraph.text)
            
    return "\n".join(full_text)

def extract_resume_text(file_path: str) -> str:
    """
    Orchestrator to automatically call the correct parser based on file extension.
    Args:
        - file_path: the path to the file for extraction
    """
    _, ext = os.path.splitext(file_path.lower())
    
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext == ".docx":
        return extract_text_from_docx(file_path)
    else:
        raise ValueError(f"Unsupported file format: {ext}. Only PDF and DOCX are allowed.")
