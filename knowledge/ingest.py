import os
import json
import glob
import re
from typing import List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv

# Try importing PDF reader
try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

# Try importing OpenAI client for dense embeddings
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DOCS_DIR = BASE_DIR / "documents"
INDEX_FILE = BASE_DIR / "knowledge_store.json"

def clean_text(text: str) -> str:
    """Normalize whitespace and clean extracted text."""
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def clean_markdown(text: str) -> str:
    """Tidy markdown but keep its line breaks, so bullets and headings stay readable."""
    lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
    return "\n".join(line for line in lines if line)

def extract_from_pdf(filepath: Path) -> List[Dict[str, Any]]:
    """Extract text from a PDF file page by page."""
    if PdfReader is None:
        print(f"[Warning] pypdf not installed. Skipping PDF: {filepath.name}")
        return []
    
    chunks = []
    try:
        reader = PdfReader(str(filepath))
        for page_idx, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 30:
                chunks.append({
                    "source": filepath.name,
                    "page": page_idx + 1,
                    "title": f"{filepath.stem} (Page {page_idx + 1})",
                    "content": clean_text(text)
                })
    except Exception as e:
        print(f"[Error] Failed to read PDF {filepath.name}: {e}")
    return chunks

def extract_from_text(filepath: Path) -> List[Dict[str, Any]]:
    """Extract and split markdown/text documents into semantic sections."""
    chunks = []
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Split markdown by H2 headers (## ) or double linebreaks
        sections = re.split(r"\n(?=##\s|\n\n)", content)
        for idx, section in enumerate(sections):
            cleaned = clean_markdown(section)
            if len(cleaned) > 40:
                # Extract first line as section title if possible
                first_line = section.strip().split("\n")[0].replace("#", "").strip()
                title = first_line if first_line else f"{filepath.stem} Part {idx+1}"
                chunks.append({
                    "source": filepath.name,
                    "page": 1,
                    "title": title,
                    "content": cleaned
                })
    except Exception as e:
        print(f"[Error] Failed to read text file {filepath.name}: {e}")
    return chunks

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Generate dense embeddings using OpenAI if key exists, else return empty."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return []
    try:
        client = OpenAI(api_key=api_key)
        response = client.embeddings.create(
            input=texts,
            model="text-embedding-3-small"
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        print(f"[Warning] OpenAI embedding failed ({e}). Falling back to lexical search.")
        return []

def build_knowledge_index():
    print("📚 Agrova Knowledge Base Ingestion Pipeline")
    print(f"📂 Scanning directory: {DOCS_DIR}")
    
    if not DOCS_DIR.exists():
        DOCS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created documents directory: {DOCS_DIR}")

    all_chunks: List[Dict[str, Any]] = []
    
    # Process all PDF, MD, and TXT files
    doc_files = list(DOCS_DIR.glob("*.*"))
    if not doc_files:
        print("⚠️ No documents found in knowledge/documents! Drop your PDFs or MD files there.")
        return

    for doc_path in doc_files:
        ext = doc_path.suffix.lower()
        if ext == ".pdf":
            print(f"📄 Ingesting PDF: {doc_path.name}...")
            chunks = extract_from_pdf(doc_path)
            all_chunks.extend(chunks)
        elif ext in [".md", ".txt"]:
            print(f"📝 Ingesting Text/Markdown: {doc_path.name}...")
            chunks = extract_from_text(doc_path)
            all_chunks.extend(chunks)

    print(f"\n🧩 Total knowledge chunks extracted: {len(all_chunks)}")

    if not all_chunks:
        print("No content could be extracted.")
        return

    # Attempt embedding generation
    print("🧠 Generating vector embeddings...")
    texts = [c["content"] for c in all_chunks]
    embeddings = get_embeddings(texts)

    # Attach embeddings to chunks
    for idx, chunk in enumerate(all_chunks):
        chunk["id"] = f"chunk_{idx+1}"
        if embeddings and idx < len(embeddings):
            chunk["embedding"] = embeddings[idx]
        else:
            chunk["embedding"] = None

    # Save to disk
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump({
            "total_chunks": len(all_chunks),
            "has_embeddings": bool(embeddings),
            "chunks": all_chunks
        }, f, indent=2)

    print(f"💾 Knowledge index successfully saved to: {INDEX_FILE}")
    print(f"✅ Ingestion complete! {len(all_chunks)} chunks ready for RAG.")

if __name__ == "__main__":
    build_knowledge_index()
