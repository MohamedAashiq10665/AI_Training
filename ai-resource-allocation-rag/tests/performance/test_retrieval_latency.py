import time

from rag.pipelines.employee_rag_pipeline import EmployeeRAGPipeline


def test_retrieval_under_five_seconds():
    pipeline = EmployeeRAGPipeline("data/employees.csv")
    pipeline.build_index()
    start = time.time()
    _ = pipeline.retrieve_candidates("Python Azure healthcare", top_k=5)
    elapsed = time.time() - start
    assert elapsed < 5.0

