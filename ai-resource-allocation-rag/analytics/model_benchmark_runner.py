from __future__ import annotations

import json
import time
from pathlib import Path

import httpx
import pandas as pd
import psutil

OLLAMA_URL = "http://localhost:11434"
MODELS = ["llama3:8b", "phi3:mini"]
PROMPTS_PATH = Path("prompts/benchmark_prompts.json")
CSV_OUTPUT = Path("data/model_benchmark_results.csv")
JSON_OUTPUT = Path("data/model_benchmark_results.json")
MARKDOWN_OUTPUT = Path("docs/model_benchmark_results.md")


def _to_markdown_table(df: pd.DataFrame) -> str:
    headers = [str(c) for c in df.columns]
    rows = [headers]
    rows.append(["---" for _ in headers])
    for row in df.itertuples(index=False):
        rows.append([str(v) for v in row])
    return "\n".join(["| " + " | ".join(r) + " |" for r in rows])


def _load_prompts() -> list[str]:
    if PROMPTS_PATH.exists():
        return json.loads(PROMPTS_PATH.read_text(encoding="utf-8"))
    return ["Recommend available Python developers for a healthcare project."]


def _run_single(model: str, prompt: str) -> dict:
    payload = {"model": model, "prompt": prompt, "stream": False}
    process = psutil.Process()
    mem_before = process.memory_info().rss
    started = time.perf_counter()

    with httpx.Client(timeout=120.0) as client:
        response = client.post(f"{OLLAMA_URL}/api/generate", json=payload)
        response.raise_for_status()
        body = response.json()

    elapsed = time.perf_counter() - started
    mem_after = process.memory_info().rss
    mem_delta_mb = (mem_after - mem_before) / (1024 * 1024)

    return {
        "model": model,
        "prompt": prompt,
        "latency_seconds": round(elapsed, 3),
        "memory_delta_mb": round(mem_delta_mb, 3),
        "prompt_eval_count": int(body.get("prompt_eval_count", 0) or 0),
        "eval_count": int(body.get("eval_count", 0) or 0),
        "success": True,
    }


def run_benchmark() -> pd.DataFrame:
    prompts = _load_prompts()
    rows: list[dict] = []

    for model in MODELS:
        for prompt in prompts:
            try:
                rows.append(_run_single(model, prompt))
            except Exception as exc:
                rows.append(
                    {
                        "model": model,
                        "prompt": prompt,
                        "latency_seconds": None,
                        "memory_delta_mb": None,
                        "prompt_eval_count": 0,
                        "eval_count": 0,
                        "success": False,
                        "error": str(exc),
                    }
                )

    df = pd.DataFrame(rows)
    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    JSON_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    MARKDOWN_OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    df.to_csv(CSV_OUTPUT, index=False)
    JSON_OUTPUT.write_text(df.to_json(orient="records", indent=2), encoding="utf-8")

    summary = (
        df.groupby("model")
        .agg(
            avg_latency_seconds=("latency_seconds", "mean"),
            avg_memory_delta_mb=("memory_delta_mb", "mean"),
            avg_eval_count=("eval_count", "mean"),
            success_rate=("success", "mean"),
        )
        .reset_index()
    )

    markdown = ["# Automated Model Benchmark Results", "", "## Summary"]
    markdown.append(_to_markdown_table(summary))
    markdown.append("")
    markdown.append("## Raw Results")
    markdown.append(_to_markdown_table(df))
    MARKDOWN_OUTPUT.write_text("\n".join(markdown), encoding="utf-8")

    return df


if __name__ == "__main__":
    results = run_benchmark()
    print(f"Benchmark complete. Rows: {len(results)}")
    print(f"CSV: {CSV_OUTPUT}")
    print(f"JSON: {JSON_OUTPUT}")
    print(f"Markdown: {MARKDOWN_OUTPUT}")
