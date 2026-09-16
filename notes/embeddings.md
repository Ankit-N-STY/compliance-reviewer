# Embeddings, Vector Similarity & Semantic Retrieval

## What it is

Vector embeddings map text (words, sentences, or transcript turns) into dense numerical vectors in a high-dimensional space. Sentences with similar meanings end up close to each other in vector space, allowing **semantic search** rather than exact keyword matching.

In Session 3, we built a 100% free local vector embedding engine (`sentence-transformers` using `all-MiniLM-L6-v2`), a vector retriever using Cosine Similarity, and a local database layer (`core/storage/db.py`) to persist compliance reviews and cached turn embeddings.

---

## Key Concepts

### 1. Vector Space & Embeddings
- `all-MiniLM-L6-v2` maps any input text into a **384-dimensional dense float vector**.
- Example:
  - `"I am not interested, stop calling me"` $\rightarrow$ `[0.0115, 0.0251, -0.0367, ...]` (384 float numbers).

### 2. Cosine Similarity Formula
Cosine similarity measures the angle between two vectors, ranging from `-1.0` (opposite) to `1.0` (identical direction):

$$\text{Cosine Similarity}(\vec{u}, \vec{v}) = \frac{\vec{u} \cdot \vec{v}}{\|\vec{u}\| \|\vec{v}\|} = \frac{\sum_{i=1}^n u_i v_i}{\sqrt{\sum_{i=1}^n u_i^2} \sqrt{\sum_{i=1}^n v_i^2}}$$

### 3. Keyword Search vs. Vector Search for Compliance
- **Keyword Search**: Looks for exact words like `"refuse"`. If a customer says *"I said NO, stop calling me!"*, exact keyword search for `"refuse"` misses it!
- **Vector Semantic Search**: Captures the *meaning* of refusal. Both `"I said NO, stop calling me!"` and `"Please do not call me again"` score **> 0.60** against the rule query *"Customer refuses offer or says stop calling"*.

---

## Benchmark Results: "No Pressure After Refusal" Rule

Target Query: `"Customer refuses offer, says no, stop calling, or not interested"`

### Top Relevant Matches (High Vector Similarity):
1. **Score: 0.6434** $\rightarrow$ `CUSTOMER: "I said NO, stop calling me!"`
2. **Score: 0.6028** $\rightarrow$ `CUSTOMER: "No, I am not interested. Please do not call me again."`
3. **Score: 0.4150** $\rightarrow$ `CUSTOMER: "[Call Disconnected]"`

### Top Irrelevant Matches (Low Vector Similarity):
1. **Score: 0.0620** $\rightarrow$ `BOT: "Yes, I have sent a tracking link via SMS..."`
2. **Score: 0.0869** $\rightarrow$ `BOT: "Awesome! I have scheduled your interview..."`
3. **Score: 0.1004** $\rightarrow$ `BOT: "Is there anything else I can help you with?"`

---

## Storage & API Architecture (`FastAPI` & `LocalDatabase`)

- **`core/storage/db.py`**: Local MongoDB connector (`compliance_reviewer_db`) with fallback to local JSON files (`data/db/`). Persists reviews and cached turn embeddings.
- **FastAPI Endpoints**:
  - `POST /api/v1/embeddings/embed`: Generates 384d vector embedding.
  - `POST /api/v1/embeddings/retrieve`: Semantic vector search over candidate turns.
  - `POST /api/v1/embeddings/reviews`: Saves audit results into local storage.
  - `GET /api/v1/embeddings/reviews`: Fetches stored audit reviews for dashboard.
