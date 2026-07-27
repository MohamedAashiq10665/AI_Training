from __future__ import annotations

from openai import OpenAI

from app.core.config import Settings
from app.domain.models import MatchResult, QueryResponse
from app.services.openai_embedder import OpenAIEmbedder
from app.services.ssa_faq_scraper import FAQDocument, SSAFAQScraper
from app.services.vector_store import JSONVectorStore


class RAGService:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required.")

        self._scraper = SSAFAQScraper(settings.ssa_faq_seed_url)
        self._embedder = OpenAIEmbedder(settings.openai_api_key, settings.embedding_model)
        self._store = JSONVectorStore(settings.index_path)
        self._chat_client = OpenAI(api_key=settings.openai_api_key)

    def train(self, max_list_pages: int, max_question_pages: int) -> int:
        urls = self._scraper.collect_question_urls(
            max_list_pages=max_list_pages,
            max_question_pages=max_question_pages,
        )
        documents = self._scraper.scrape_questions(urls)
        unique_documents = self._dedupe_by_question(documents)

        if not unique_documents:
            self._store.save([], [])
            return 0

        training_texts = [f"Question: {doc.question}\nAnswer: {doc.answer}" for doc in unique_documents]
        embeddings = self._embedder.embed_texts(training_texts)
        self._store.save(unique_documents, embeddings)
        return len(unique_documents)

    def answer_query(self, query: str, top_k: int, min_similarity: float) -> QueryResponse:
        query_embedding = self._embedder.embed_text(query)
        results = self._store.search(
            query_embedding=query_embedding,
            top_k=top_k,
            min_similarity=min_similarity,
        )

        if not results:
            return QueryResponse(
                query=query,
                answer="No Content",
                url=None,
                matching_percentage=0.0,
                matches=[],
            )

        llm_answer = self._generate_answer_from_matches(query, results)
        top_match = results[0]
        matches = [
            MatchResult(
                question=result.document.question,
                answer=result.document.answer,
                url=result.document.url,
                similarity=round(result.similarity, 4),
                matching_percentage=result.matching_percentage,
            )
            for result in results
        ]

        return QueryResponse(
            query=query,
            answer=llm_answer,
            url=top_match.document.url,
            matching_percentage=top_match.matching_percentage,
            matches=matches,
        )

    def _generate_answer_from_matches(self, query: str, matches: list) -> str:
        context_lines: list[str] = []
        for idx, match in enumerate(matches, start=1):
            context_lines.append(
                "\n".join(
                    [
                        f"[{idx}] Question: {match.document.question}",
                        f"[{idx}] Answer: {match.document.answer}",
                        f"[{idx}] URL: {match.document.url}",
                        f"[{idx}] Similarity: {round(match.similarity, 4)}",
                    ]
                )
            )

        prompt = (
            "Use only the provided SSA FAQ context to answer the user query. "
            "If context is insufficient, reply exactly with 'No Content'.\n\n"
            f"User Query: {query}\n\n"
            "Context:\n"
            f"{'\n\n'.join(context_lines)}"
        )

        try:
            response = self._chat_client.chat.completions.create(
                model=self._settings.answer_model,
                temperature=0,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a factual assistant. Answer only from context and do not invent details.",
                    },
                    {"role": "user", "content": prompt},
                ],
            )
            answer = (response.choices[0].message.content or "").strip()
            return answer if answer else "No Content"
        except Exception:
            return matches[0].document.answer if matches else "No Content"

    @staticmethod
    def _dedupe_by_question(documents: list[FAQDocument]) -> list[FAQDocument]:
        seen: set[str] = set()
        deduped: list[FAQDocument] = []
        for doc in documents:
            key = doc.question.lower().strip()
            if key in seen:
                continue
            seen.add(key)
            deduped.append(doc)
        return deduped
