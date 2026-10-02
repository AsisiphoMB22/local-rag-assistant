import json
import sqlite3

import ollama
import streamlit as st

from pypdf import PdfReader
from styles import load_css

load_css()

DB_PATH = "research.db"
EMBED_MODEL = "granite-embedding:30m"
CHAT_MODEL = "gemma3:1b"
CHUNK_SIZE = 900
CHUNK_OVERLAP = 150
TOP_K = 4
DEFAULT_QUESTION = "What helps distributed teams stay productive?"

def extract_documents(uploaded_files):
    pages = []
    for uploaded_file in uploaded_files:
        uploaded_file.seek(0)
        source = uploaded_file.name
        if source.lower().endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            for page_number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                if text:
                    pages.append({"source": source, "page": page_number, "text": text})
        else:
            text = uploaded_file.getvalue().decode("utf-8", errors="replace").strip()
            if text:
                pages.append({"source": source, "page": 1, "text": text})
    return pages

def chunk_pages(pages):
    chunks = []
    for page in pages:
        text = page["text"]
        start = 0
        chunk_index = 0
        while start < len(text):
            end = min(start + CHUNK_SIZE, len(text))
            content = text[start:end].strip()
            if content:
                chunks.append({
                    "id": f"{page['source']}|{page['page']}|{chunk_index}",
                    "source": page["source"],
                    "page": page["page"],
                    "chunk_index": chunk_index,
                    "content": content,
                })
            if end == len(text):
                break
            start = end - CHUNK_OVERLAP
            chunk_index += 1
    return chunks

def literal_phrase_search(chunks, question):
    normalized_question = question.strip().lower()
    if not normalized_question:
        return []
    return [chunk for chunk in chunks if normalized_question in chunk["content"].lower()]

def store_chunks(chunks):
    texts = [chunk["content"] for chunk in chunks]
    embeddings = ollama.embed(model=EMBED_MODEL, input=texts).embeddings
    rows = [
        (chunk["id"], chunk["source"], chunk["page"], chunk["chunk_index"], chunk["content"], json.dumps(embedding))
        for chunk, embedding in zip(chunks, embeddings)
    ]
    sources = sorted({chunk["source"] for chunk in chunks})
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.executemany("DELETE FROM chunks WHERE source = ?", [(source,) for source in sources])
        connection.executemany(
            "INSERT INTO chunks (id, source, page, chunk_index, content, embedding) VALUES (?, ?, ?, ?, ?, ?)",
            rows,
        )
        connection.commit()
    finally:
        connection.close()

def count_stored_chunks():
    connection = sqlite3.connect(DB_PATH)
    try:
        return connection.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    finally:
        connection.close()

def load_sources():
    connection = sqlite3.connect(DB_PATH)
    try:
        return [row[0] for row in connection.execute("SELECT DISTINCT source FROM chunks ORDER BY source").fetchall()]
    finally:
        connection.close()

def load_rows(selected_sources=None):
    connection = sqlite3.connect(DB_PATH)
    try:
        if selected_sources:
            placeholders = ", ".join("?" for _ in selected_sources)
            sql = "SELECT source, page, chunk_index, content, embedding " + f"FROM chunks WHERE source IN ({placeholders})"
            return connection.execute(sql, tuple(selected_sources)).fetchall()
        return connection.execute("SELECT source, page, chunk_index, content, embedding FROM chunks").fetchall()
    finally:
        connection.close()

def cosine_similarity(left, right):
    dot_product = sum(a * b for a, b in zip(left, right))
    left_magnitude = sum(value * value for value in left) ** 0.5
    right_magnitude = sum(value * value for value in right) ** 0.5
    if left_magnitude == 0 or right_magnitude == 0:
        return 0.0
    return dot_product / (left_magnitude * right_magnitude)

def retrieve(question, selected_sources=None):
    rows = load_rows(selected_sources)
    if not rows:
        return []
    query_vector = ollama.embed(model=EMBED_MODEL, input=question).embeddings[0]
    scored = []
    for source, page, chunk_index, content, embedding_json in rows:
        scored.append({"source": source, "page": page, "chunk_index": chunk_index, "content": content, "score": cosine_similarity(query_vector, json.loads(embedding_json))})
    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:TOP_K]

def has_relevant_evidence(evidence, threshold=0.65):
    if not evidence:
        return False

    return any(item["score"] >= threshold for item in evidence)

def answer_question(question, evidence):
    evidence_text = "\n\n".join(
        f"[Source {index}: {item['source']}, page {item['page']}]\n{item['content']}"
        for index, item in enumerate(evidence, start=1)
    )
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {"role": "system", "content": "You are a careful research assistant. Answer only from the provided evidence. Cite claims with the exact bracketed source labels. If the evidence is insufficient, say so clearly."},
            {"role": "user", "content": f"Question:\n{question}\n\nEvidence:\n{evidence_text}"},
        ],
    )
    return response.message.content

def compare_documents(document_a, document_b):
    response = ollama.chat(
        model=CHAT_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a careful research assistant. "
                    "You are given the complete text of two documents. "
                    "Compare the documents using only the text provided. "
                    "Do not ask the user to provide the documents again. "
                    "Do not say that the documents are missing. "
                    "Identify important similarities, differences, and a brief key takeaway."
                )
            },
            {
                "role": "user",
                "content": (
                    "DOCUMENT A CONTENT:\n"
                    + document_a["content"]
                    + "\n\n"
                    "DOCUMENT B CONTENT:\n"
                    + document_b["content"]
                    + "\n\n"
                    "Now compare these two documents.\n\n"
                    "Structure your response as:\n"
                    "### Similarities\n"
                    "### Differences\n"
                    "### Key Takeaway"
                )
            }
        ],
    )

    return response.message.content

def render_evidence(evidence):
    for index, item in enumerate(evidence, start=1):
        with st.expander(f"Source {index}: {item['source']}, page {item['page']}"):
            st.write(f"Cosine similarity: {item['score']:.3f}")
            st.write(item["content"])

def initialize_database():
    connection = sqlite3.connect(DB_PATH)
    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS chunks (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                page INTEGER NOT NULL,
                chunk_index INTEGER NOT NULL,
                content TEXT NOT NULL,
                embedding TEXT NOT NULL
            )
            """
        )
        connection.commit()
    finally:
        connection.close()

initialize_database()
st.markdown(
    '<div class="main-title">Local RAG Research Assistant</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="main-subtitle">'
    'Search your documents, retrieve relevant evidence, and generate grounded answers locally.'
    '</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="status-badge">● Local AI &nbsp;•&nbsp; Ollama Connected</div>',
    unsafe_allow_html=True
)

st.write("Upload PDF or TXT files, compare literal search with semantic retrieval, and generate a cited answer using local Ollama models.")

uploaded_files = st.file_uploader("Upload research documents", type=["pdf", "txt"], accept_multiple_files=True)
pages = extract_documents(uploaded_files)
chunks = chunk_pages(pages)

st.markdown("### Knowledge Base Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        '<div class="metric-card">'
        '<div class="metric-label">📄 Documents</div>'
        '<div class="metric-value">Local</div>'
        '<div class="metric-description">Your uploaded research files</div>'
        '</div>',
        unsafe_allow_html=True
    )

with col2:
    st.markdown(
        '<div class="metric-card">'
        '<div class="metric-label">🧩 Retrieval</div>'
        '<div class="metric-value">Semantic</div>'
        '<div class="metric-description">Meaning-based document search</div>'
        '</div>',
        unsafe_allow_html=True
    )

with col3:
    st.markdown(
        '<div class="metric-card">'
        '<div class="metric-label">🤖 AI Model</div>'
        '<div class="metric-value">Gemma 3</div>'
        '<div class="metric-description">Local answer generation</div>'
        '</div>',
        unsafe_allow_html=True
    )


if uploaded_files:
    st.write(f"Extracted pages: {len(pages)}")
    st.write(f"Prepared chunks: {len(chunks)}")
    if not pages:
        st.write("No readable text was extracted. Scanned PDFs need OCR, which is outside this project.")
    for page in pages[:3]:
        with st.expander(f"Preview: {page['source']}, page {page['page']}"):
            st.write(page["text"][:1000])

st.write("")
st.write("")
st.write("")

# Document comparison
document_text = {}

for page in pages:
    document_text.setdefault(page["source"], []).append(page["text"])

document_text = {
    source: "\n\n".join(texts)
    for source, texts in document_text.items()
}

if uploaded_files and len(document_text) >= 2:

    st.markdown("### 📑 Compare Documents")

    compare_col1, compare_col2 = st.columns(2)

    sources = sorted(document_text.keys())

    with compare_col1:
        document_a = st.selectbox(
            "Document A",
            sources,
            key="document_a"
        )

    with compare_col2:
        document_b = st.selectbox(
            "Document B",
            sources,
            key="document_b"
        )

    if st.button("🔍 Compare Documents"):
        if document_a == document_b:
            st.warning("Please select two different documents.")
        else:
            with st.spinner("Comparing documents with Gemma 3..."):
                comparison = compare_documents(
                    {"content": document_text[document_a]},
                    {"content": document_text[document_b]}
                )

            st.markdown("### 📊 Comparison Result")
            st.markdown(comparison)


st.markdown(
    '<div class="question-title">🔎 Ask Your Research Question</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="question-description">'
    'Search your local knowledge base and generate an evidence-grounded answer.'
    '</div>',
    unsafe_allow_html=True
)

st.write("")
st.write("")
st.write("")
st.write("")

question = st.text_input("Research question", value=DEFAULT_QUESTION)
selected_sources = st.multiselect("Limit retrieval to these sources; leave empty to search all", load_sources())

button_col1, button_col2, button_col3, button_col4 = st.columns(4)

with button_col1:
    literal_search_clicked = st.button(
        "🔎 Literal Search",
        disabled=not chunks
    )

with button_col2:
    index_clicked = st.button(
        "📥 Index Documents",
        disabled=not chunks
    )

with button_col3:
    retrieval_clicked = st.button(
        "🧠 Semantic Retrieval",
        disabled=not question
    )

with button_col4:
    assistant_clicked = st.button(
        "🤖 Ask Assistant",
        disabled=not question
    )

if literal_search_clicked:
    matches = literal_phrase_search(chunks, question)
    st.write(f"Exact phrase matches: {len(matches)}")
    if not matches:
        st.write("The full question is absent even though one document discusses the idea.")

if index_clicked:
    store_chunks(chunks)
    st.write(f"Stored chunks in {DB_PATH}: {count_stored_chunks()}")

if retrieval_clicked:
    if count_stored_chunks() == 0:
        st.write("Index at least one document first.")
    else:
        evidence = retrieve(question, selected_sources)
        st.write("Semantic retrieval results")
        render_evidence(evidence)

if assistant_clicked:
    if count_stored_chunks() == 0:
        st.write("Index at least one document first.")
    else:
        with st.spinner("Researching your documents..."):
            evidence = retrieve(question, selected_sources)

        if not has_relevant_evidence(evidence):
            st.markdown("### 💡 Answer")
            st.warning(
                "I couldn't find enough relevant evidence in the uploaded "
                "documents to answer this question."
            )

        else:
            with st.spinner("Generating answer..."):
                answer = answer_question(question, evidence)

            st.markdown("### 💡 Answer")
            st.markdown(answer)

            st.markdown("### 📚 Sources")

            relevant_evidence = [
                item for item in evidence
                if item["score"] >= 0.65
            ]

            shown_sources = set()

            for item in relevant_evidence:
                source_key = (item["source"], item["page"])

                if source_key not in shown_sources:
                    shown_sources.add(source_key)

                    with st.expander(
                        f"📄 {item['source']} — Page {item['page']}"
                    ):
                        st.write(item["content"])