import pytest
from unittest.mock import MagicMock, patch, mock_open
import os
import core
from core.ingestion.parser import extract_text_from_pdf, extract_text_from_docx, extract_resume_text
from core.ingestion.chroma_service import ChromaService

def test_extract_text_from_pdf_file_not_found():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("missing.pdf")

@patch("os.path.exists", return_value=True)
@patch("pdfplumber.open")
def test_extract_text_from_pdf_success(mock_pdf_open, mock_exists):
    mock_page = MagicMock()
    mock_page.extract_text.return_value = "Resume Page Content"
    mock_pdf = MagicMock()
    mock_pdf.pages = [mock_page]
    mock_pdf_open.return_value.__enter__.return_value = mock_pdf

    result = extract_text_from_pdf("sample.pdf")
    assert result == "Resume Page Content"
    mock_page.extract_text.assert_called_once_with(layout=True)

def test_extract_text_from_docx_file_not_found():
    with patch("os.path.exists", return_value=False):
        with pytest.raises(FileNotFoundError):
            extract_text_from_docx("missing.docx")

@patch("os.path.exists", return_value=True)
@patch("core.ingestion.parser.Document")
def test_extract_text_from_docx_success(mock_document, mock_exists):
    mock_para1 = MagicMock(text="John Doe")
    mock_para2 = MagicMock(text="   ")
    mock_para3 = MagicMock(text="Python Developer")
    mock_doc = MagicMock()
    mock_doc.paragraphs = [mock_para1, mock_para2, mock_para3]
    mock_document.return_value = mock_doc

    result = extract_text_from_docx("sample.docx")
    assert result == "John Doe\nPython Developer"

@patch("core.ingestion.parser.extract_text_from_pdf")
def test_extract_resume_text_pdf(mock_pdf_parser):
    mock_pdf_parser.return_value = "PDF Text"
    result = extract_resume_text("test.PDF")
    assert result == "PDF Text"
    mock_pdf_parser.assert_called_once_with("test.PDF")

@patch("core.ingestion.parser.extract_text_from_docx")
def test_extract_resume_text_docx(mock_docx_parser):
    mock_docx_parser.return_value = "DOCX Text"
    result = extract_resume_text("test.DOCX")
    assert result == "DOCX Text"
    mock_docx_parser.assert_called_once_with("test.DOCX")

def test_extract_resume_text_unsupported():
    with pytest.raises(ValueError):
        extract_resume_text("test.txt")

@pytest.fixture
def mock_chroma_setup():
    with patch("chromadb.PersistentClient") as mock_client, \
         patch("chromadb.utils.embedding_functions.OllamaEmbeddingFunction") as mock_ef:
        mock_collection = MagicMock()
        mock_client.return_value.get_or_create_collection.return_value = mock_collection
        service = ChromaService()
        yield service, mock_collection

def test_chunk_text_logic(mock_chroma_setup):
    service, _ = mock_chroma_setup
    text = "abcdefghij"
    chunks = service._chunk_text(text, chunk_size=4, chunk_overlap=2)
    assert chunks == ["abcd", "cdef", "efgh", "ghij", "ij"]

def test_chunk_text_defensive_overlap(mock_chroma_setup):
    service, _ = mock_chroma_setup
    text = "abcdefghij"
    chunks = service._chunk_text(text, chunk_size=4, chunk_overlap=5)
    assert len(chunks) > 0

def test_ingest_resume_success(mock_chroma_setup):
    service, mock_collection = mock_chroma_setup
    file_text = "This is a long resume text for testing ingestion."
    filename = "John Doe Resume.pdf"

    candidate_id = service.ingest_resume(file_text, filename)
    
    assert "John_Doe_Resume_" in candidate_id
    assert mock_collection.add.called
    
    kwargs = mock_collection.add.call_args[1]
    assert len(kwargs["documents"]) > 0
    assert kwargs["ids"][0].startswith(candidate_id)
    assert kwargs["metadatas"][0]["source_file"] == filename

def test_ingest_resume_empty_text(mock_chroma_setup):
    service, mock_collection = mock_chroma_setup
    candidate_id = service.ingest_resume("", "empty.pdf")
    assert not mock_collection.add.called
    assert "empty_" in candidate_id

def test_query_resume_context_success(mock_chroma_setup):
    service, mock_collection = mock_chroma_setup
    mock_collection.query.return_value = {
        "documents": [["Chunk 1 content", "Chunk 2 content"]]
    }

    results = service.query_resume_context("Python", "user_123")
    assert results == ["Chunk 1 content", "Chunk 2 content"]
    mock_collection.query.assert_called_once_with(
        query_texts=["Python"],
        n_results=3,
        where={"candidate_id": "user_123"}
    )

def test_query_resume_context_empty(mock_chroma_setup):
    service, mock_collection = mock_chroma_setup
    mock_collection.query.return_value = {"documents": []}

    results = service.query_resume_context("Python", "user_123")
    assert results == []
