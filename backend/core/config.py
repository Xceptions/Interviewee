import os
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class Settings(BaseSettings):
    chroma_db_path: str = os.getenv("CHROMA_DB_PATH", "./chroma_db")
    chroma_collection_name: str = os.getenv("CHROMA_COLLECTION_NAME", "resumes")
    ollama_url: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    ollama_model: str = os.getenv("OLLAMA_MODEL", "llama3.2")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not os.path.isabs(self.chroma_db_path):
            core_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(core_dir)
            self.chroma_db_path = os.path.abspath(os.path.join(backend_dir, self.chroma_db_path))

settings = Settings()
