from rag.ingestion.chunking import chunk_text


def test_chunk_text_non_empty():
    text = "python azure fastapi docker " * 200
    chunks = chunk_text(text, chunk_size=50, overlap=10)
    assert len(chunks) > 1
    assert all(chunks)
