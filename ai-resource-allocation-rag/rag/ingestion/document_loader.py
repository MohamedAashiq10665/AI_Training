from __future__ import annotations

from typing import List

import pandas as pd


def load_employee_documents(csv_path: str) -> List[dict]:
    df = pd.read_csv(csv_path)
    docs = []
    for _, row in df.iterrows():
        text = (
            f"Employee ID: {row['employee_id']}. Name: {row['name']}. "
            f"Primary Skill: {row['primary_skill']}. Secondary Skill: {row['secondary_skill']}. "
            f"Experience: {row['years_experience']} years. Certifications: {row['certifications']}. "
            f"Availability: {row['availability_status']}. Utilization: {row['current_utilization']}. "
            f"Role: {row['role']}. Location: {row['location']}. Resume: {row['resume_text']}"
        )
        docs.append(
            {
                "text": text,
                "metadata": {
                    "employee_id": str(row["employee_id"]),
                    "primary_skill": row["primary_skill"],
                    "availability_status": row["availability_status"],
                    "years_experience": int(row["years_experience"]),
                    "role": row["role"],
                },
            }
        )
    return docs


def build_employee_documents_from_records(records: List[dict]) -> List[dict]:
    docs = []
    for row in records:
        text = (
            f"Employee ID: {row['employee_id']}. Name: {row['name']}. "
            f"Primary Skill: {row['primary_skill']}. Secondary Skill: {row['secondary_skill']}. "
            f"Experience: {row['years_experience']} years. Certifications: {row['certifications']}. "
            f"Availability: {row['availability_status']}. Utilization: {row['current_utilization']}. "
            f"Role: {row['role']}. Location: {row['location']}. Resume: {row['resume_text']}"
        )
        docs.append(
            {
                "text": text,
                "metadata": {
                    "employee_id": str(row["employee_id"]),
                    "primary_skill": row["primary_skill"],
                    "availability_status": row["availability_status"],
                    "years_experience": int(row["years_experience"]),
                    "role": row["role"],
                },
            }
        )
    return docs
