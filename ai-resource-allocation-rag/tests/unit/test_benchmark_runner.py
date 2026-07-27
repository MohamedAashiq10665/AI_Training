from pathlib import Path

from analytics import model_benchmark_runner as runner


class DummyResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {"eval_count": 100, "prompt_eval_count": 40}


class DummyClient:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def post(self, *args, **kwargs):
        return DummyResponse()


def test_benchmark_runner_writes_artifacts(monkeypatch, tmp_path):
    monkeypatch.setattr(runner.httpx, "Client", DummyClient)
    monkeypatch.setattr(runner, "CSV_OUTPUT", tmp_path / "results.csv")
    monkeypatch.setattr(runner, "JSON_OUTPUT", tmp_path / "results.json")
    monkeypatch.setattr(runner, "MARKDOWN_OUTPUT", tmp_path / "results.md")
    monkeypatch.setattr(
        runner,
        "PROMPTS_PATH",
        tmp_path / "prompts.json",
    )
    (tmp_path / "prompts.json").write_text('["prompt one", "prompt two"]', encoding="utf-8")

    df = runner.run_benchmark()

    assert len(df) == len(runner.MODELS) * 2
    assert Path(runner.CSV_OUTPUT).exists()
    assert Path(runner.JSON_OUTPUT).exists()
    assert Path(runner.MARKDOWN_OUTPUT).exists()