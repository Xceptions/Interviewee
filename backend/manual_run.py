import os
from core.ingestion.parser import extract_resume_text
from core.ingestion.chroma_service import chroma_service

def run_local_ingestion(paths: list[str]):
    print("Initializing local execution framework...")
    
    for path in paths:
        if not os.path.exists(path):
            print(f"Target missing: {path}")
            continue
            
        filename = os.path.basename(path)
        print(f"Processing document matrix: {filename}")
        
        try:
            text = extract_resume_text(path)
            candidate_id = chroma_service.ingest_resume(text, filename)
            print(f"Successfully indexed inside database. ID: {candidate_id}\n")
        except Exception as e:
            print(f"Failed to parse metadata chunk for {filename}: {e}\n")

if __name__ == "__main__":
    sample_files = [
        "../datastore/uploads/Candidate_Software_Engineer_Skills.docx"
    ]
    run_local_ingestion(sample_files)
