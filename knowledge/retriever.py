import os
import json
import re
import math
from pathlib import Path
from typing import List, Dict, Any
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
INDEX_FILE = BASE_DIR / "knowledge_store.json"

# Common Nigerian Pidgin to Agricultural terms dictionary
PIDGIN_AGRI_MAP = {
    r"\bno dey chop\b": "reduced feed intake appetite loss not eating",
    r"\bdey chop\b": "eating feed consumption",
    r"\bdey stool\b": "diarrhea watery droppings loose feces",
    r"\bdey stool blood\b": "bloody diarrhea coccidiosis feces with blood",
    r"\bdey shit\b": "droppings feces excretion",
    r"\bdem dey die\b": "mortality dying death spike",
    r"\bdey weak\b": "lethargy droopiness ruffled feathers weakness",
    r"\bdey breath hard\b": "respiratory distress panting gasping",
    r"\begg drop\b": "reduced egg production drop in laying",
    r"\bdey huddle\b": "huddling together chilling cold stress",
    r"\bfowl\b": "poultry chicken broiler layer bird",
    r"\be dey hot\b": "heat stress high ambient temperature",
    # Goats, sheep, cattle, pigs, fish
    r"\bgoat\b|\bgoats\b|\bshaki\b": "goat sheep small ruminant",
    r"\bram\b|\bewe\b|\blamb\b": "sheep small ruminant",
    r"\bcow\b|\bcows\b|\bbull\b|\bmaiwa\b": "cattle cow calf",
    r"\bkid\b|\bkids\b": "goat kid young small ruminant",
    r"\bpig\b|\bpigs\b|\bpiglet\b|\bhog\b": "pig swine piglet",
    r"\bcatfish\b|\bclarias\b": "catfish clarias fish pond",
    r"\btilapia\b": "tilapia fish pond",
    r"\bfish\b|\bpond\b": "fish pond aquaculture water",
    r"\bdey cough\b": "coughing respiratory pneumonia",
    r"\bnose dey run\b|\beye dey water\b": "nasal discharge ocular discharge",
    r"\bdey vomit\b": "vomiting",
    r"\bdey limp\b|\bleg dey pain\b": "lameness limping",
    r"\bdey thin\b|\be dey lose weight\b": "weight loss emaciation thin",
    r"\beye dey white\b|\bdey pale\b": "anaemia pale eyelids mucous membranes",
    r"\bdey drool\b|\bmouth dey sore\b": "drooling mouth lesions blisters",
    r"\bdey gasp\b|\bdey float\b": "low dissolved oxygen gasping surface",
    r"\bwater dey green\b": "algae bloom plankton water quality",
    r"\bdey stool water\b": "diarrhoea watery",
    r"\bdem dey die\b|\bdey die\b|\bplenty die\b": "mortality deaths outbreak",
}

def normalize_pidgin_query(query: str) -> str:
    """Expand Nigerian Pidgin expressions into technical and common agricultural keywords."""
    expanded_query = query.lower()
    for pattern, replacement in PIDGIN_AGRI_MAP.items():
        if re.search(pattern, expanded_query):
            expanded_query += f" {replacement}"
    return expanded_query

def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot / (mag1 * mag2)

# Filler words (English + Pidgin) that carry no topic meaning and would otherwise match every chunk
STOPWORDS = {
    "a", "an", "the", "and", "or", "of", "to", "in", "on", "for", "with", "is", "are", "was", "be", "it", "its",
    "my", "me", "i", "we", "you", "your", "this", "that", "at", "as", "by", "from", "do", "does", "can", "how",
    "what", "when", "why", "should", "some", "them", "they", "he", "she", "has", "have", "had", "not", "no",
    "dey", "na", "e", "dem", "wey", "wetin", "abeg", "make", "una", "sef", "don", "fit", "get", "very", "too",
    "much", "many", "more", "about", "if", "so", "but", "up", "out", "all", "any", "one", "per",
}

# Query words that tell us which animal the farmer is asking about
SPECIES_QUERY_WORDS = {
    "small_ruminant": {"goat", "goats", "sheep", "ram", "rams", "ewe", "ewes", "lamb", "lambs", "kid", "kids", "doe", "buck", "ruminant"},
    "cattle": {"cattle", "cow", "cows", "bull", "bulls", "calf", "calves", "heifer", "heifers", "ox", "oxen", "milk", "dairy"},
    "pig": {"pig", "pigs", "piglet", "piglets", "sow", "sows", "boar", "hog", "hogs", "swine", "pork"},
    "fish": {"fish", "catfish", "tilapia", "clarias", "pond", "ponds", "fingerling", "fingerlings", "aquaculture", "fry"},
    "poultry": {"broiler", "broilers", "layer", "layers", "chicken", "chickens", "fowl", "fowls", "poultry", "bird", "birds",
               "hen", "hens", "cockerel", "chick", "chicks", "egg", "eggs", "flock"},
}

# Substrings of a chunk's source file name / title that tell us which animal it covers
SPECIES_SOURCE_MARKERS = {
    "small_ruminant": ("goat", "sheep"),
    "cattle": ("cattle", "cow", "bunaji"),
    "pig": ("pig", "swine"),
    "fish": ("fish", "tilapia", "catfish"),
    "poultry": ("poultry", "broiler", "aviagen", "layer", "chicken"),
}

OFF_SPECIES_PENALTY = 0.3  # chunks about another animal keep 30% of their score

def tokenize(text: str) -> List[str]:
    return [t for t in re.findall(r"[a-z0-9]+", text.lower()) if t not in STOPWORDS and len(t) > 1]

def detect_query_species(query: str) -> set:
    tokens = set(re.findall(r"[a-z0-9]+", query.lower()))
    return {sp for sp, words in SPECIES_QUERY_WORDS.items() if tokens & words}

def chunk_species(chunk: Dict[str, Any]) -> str:
    label = f"{chunk.get('source', '')} {chunk.get('title', '')}".lower()
    for sp, markers in SPECIES_SOURCE_MARKERS.items():
        if any(m in label for m in markers):
            return sp
    return ""

class AgrovaRetriever:
    def __init__(self, index_file: Path = INDEX_FILE):
        self.index_file = index_file
        self.chunks = []
        self.has_embeddings = False
        self._doc_tf = []
        self._doc_len = []
        self._avg_len = 1.0
        self._idf = {}
        self.load_index()

    def _build_bm25(self):
        """Pre-compute term frequencies and inverse document frequencies for BM25 scoring."""
        self._doc_tf, self._doc_len, df = [], [], {}
        for chunk in self.chunks:
            tokens = tokenize(chunk.get("content", ""))
            tf = {}
            for t in tokens:
                tf[t] = tf.get(t, 0) + 1
            self._doc_tf.append(tf)
            self._doc_len.append(len(tokens))
            for t in tf:
                df[t] = df.get(t, 0) + 1
        n = max(len(self.chunks), 1)
        self._avg_len = (sum(self._doc_len) / n) or 1.0
        self._idf = {t: math.log(1 + (n - d + 0.5) / (d + 0.5)) for t, d in df.items()}

    def bm25_score(self, query_tokens: set, idx: int, k1: float = 1.5, b: float = 0.75) -> float:
        tf, length = self._doc_tf[idx], self._doc_len[idx]
        score = 0.0
        for t in query_tokens:
            f = tf.get(t)
            if f:
                score += self._idf.get(t, 0.0) * f * (k1 + 1) / (f + k1 * (1 - b + b * length / self._avg_len))
        return score

    def load_index(self):
        if not self.index_file.exists():
            print(f"[Retriever] Index file not found at {self.index_file}. Run ingest.py first.")
            return
        try:
            with open(self.index_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.chunks = data.get("chunks", [])
                self.has_embeddings = data.get("has_embeddings", False)
            self._build_bm25()
            print(f"[Retriever] Loaded {len(self.chunks)} knowledge chunks for retrieval.")
        except Exception as e:
            print(f"[Retriever Error] Failed to load index: {e}")

    def query_embedding(self, query: str) -> List[float]:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key or OpenAI is None:
            return []
        try:
            client = OpenAI(api_key=api_key)
            resp = client.embeddings.create(input=[query], model="text-embedding-3-small")
            return resp.data[0].embedding
        except Exception:
            return []

    def retrieve(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve top K relevant agricultural documents for a farmer's query."""
        if not self.chunks:
            self.load_index()
            if not self.chunks:
                return []

        enriched_query = normalize_pidgin_query(query)
        query_vector = self.query_embedding(enriched_query) if self.has_embeddings else []

        query_tokens = set(tokenize(enriched_query))
        wanted_species = detect_query_species(enriched_query)

        scored_chunks = []
        for idx, chunk in enumerate(self.chunks):
            score = 0.0
            # Dense similarity if available
            if query_vector and chunk.get("embedding"):
                score = cosine_similarity(query_vector, chunk["embedding"])
            else:
                # Lexical scoring fallback (BM25)
                score = self.bm25_score(query_tokens, idx)

            # If the farmer named an animal, keep chunks about it and demote chunks about other animals
            if wanted_species:
                species = chunk_species(chunk)
                if species and species not in wanted_species:
                    score *= OFF_SPECIES_PENALTY

            scored_chunks.append((score, chunk))

        # Sort descending by relevance score
        scored_chunks.sort(key=lambda x: x[0], reverse=True)

        results = []
        for score, chunk in scored_chunks[:top_k]:
            idx = self.chunks.index(chunk)
            matched = sorted(t for t in query_tokens if self._doc_tf[idx].get(t))
            title_tokens = set(tokenize(chunk.get("title") or ""))
            results.append({
                "id": chunk.get("id"),
                "title": chunk.get("title"),
                "source": chunk.get("source"),
                "page": chunk.get("page", 1),
                "content": chunk.get("content"),
                "relevance_score": round(score, 4),
                # Lets callers tell a real match from one stray word (e.g. "today") shared with the text
                "matched_terms": matched,
                "title_hit": bool(title_tokens & set(matched)),
            })
        return results

# Singleton instance
retriever = AgrovaRetriever()

if __name__ == "__main__":
    test_query = "My broilers no dey chop well and some of them dey stool watery droppings"
    print(f"\n🔍 Testing Retrieval for query: '{test_query}'")
    results = retriever.retrieve(test_query, top_k=2)
    for idx, r in enumerate(results):
        print(f"\n[{idx+1}] Source: {r['source']} (Score: {r['relevance_score']}) - {r['title']}")
        print(f"Content: {r['content'][:250]}...")
