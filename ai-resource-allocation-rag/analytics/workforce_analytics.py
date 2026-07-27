from __future__ import annotations

import pandas as pd


def bench_by_skill(employee_csv: str = "data/employees.csv") -> dict:
    df = pd.read_csv(employee_csv)
    return (
        df[df["current_utilization"] < 0.2]
        .groupby("primary_skill")
        .size()
        .sort_values(ascending=False)
        .to_dict()
    )
