from __future__ import annotations

import random
from pathlib import Path

import pandas as pd
from faker import Faker

fake = Faker()
random.seed(42)
Faker.seed(42)

PRIMARY_SKILLS = [
    "Python",
    "Java",
    "AWS",
    "Azure",
    "GCP",
    "Data Engineering",
    "React",
    "DevOps",
    "SQL",
    "Machine Learning",
]
SECONDARY_SKILLS = ["FastAPI", "Spring", "Docker", "Kubernetes", "Spark", "Node.js", "Terraform"]
CERTIFICATIONS = [
    "AWS-SA",
    "Azure-AZ900",
    "GCP-ACE",
    "CKA",
    "PMP",
    "Databricks-Associate",
    "ScrumMaster",
]
LOCATIONS = ["Cairo", "Dubai", "Riyadh", "Bangalore", "London", "Remote"]
ROLES = ["Software Engineer", "Data Engineer", "Cloud Engineer", "ML Engineer", "QA Engineer"]
DOMAINS = ["Healthcare", "Finance", "Retail", "Telecom", "Public Sector"]


def generate_employees(n: int = 500) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        primary = random.choice(PRIMARY_SKILLS)
        secondary = random.choice([s for s in SECONDARY_SKILLS if s != primary])
        years = random.randint(1, 15)
        certs = ";".join(random.sample(CERTIFICATIONS, k=random.randint(1, 3)))
        availability = random.choices(["Available", "Allocated", "On Leave"], weights=[0.45, 0.5, 0.05])[0]
        utilization = round(random.uniform(0.0, 1.0), 2)
        rows.append(
            {
                "employee_id": f"EMP{i:04d}",
                "name": fake.name(),
                "primary_skill": primary,
                "secondary_skill": secondary,
                "years_experience": years,
                "certifications": certs,
                "availability_status": availability,
                "current_utilization": utilization,
                "location": random.choice(LOCATIONS),
                "role": random.choice(ROLES),
                "resume_text": (
                    f"{years} years working with {primary} and {secondary}, "
                    f"delivered projects in {random.choice(DOMAINS)} domain."
                ),
            }
        )
    return pd.DataFrame(rows)


def generate_projects(n: int = 100) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        req = random.sample(PRIMARY_SKILLS, k=random.randint(2, 4))
        rows.append(
            {
                "project_id": f"PRJ{i:03d}",
                "project_name": f"{random.choice(DOMAINS)} Transformation {i}",
                "required_skills": ";".join(req),
                "preferred_certifications": ";".join(random.sample(CERTIFICATIONS, k=2)),
                "min_experience": random.randint(2, 10),
                "required_headcount": random.randint(2, 8),
                "location": random.choice(LOCATIONS),
                "domain": random.choice(DOMAINS),
            }
        )
    return pd.DataFrame(rows)


def generate_allocations(employees: pd.DataFrame, projects: pd.DataFrame, n: int = 1000) -> pd.DataFrame:
    rows = []
    months = pd.date_range("2025-01-01", "2026-12-01", freq="MS").strftime("%Y-%m").tolist()
    for i in range(1, n + 1):
        emp = employees.sample(1).iloc[0]
        prj = projects.sample(1).iloc[0]
        rows.append(
            {
                "allocation_id": f"ALC{i:05d}",
                "employee_id": emp["employee_id"],
                "project_id": prj["project_id"],
                "allocation_month": random.choice(months),
                "allocation_percentage": random.choice([25, 50, 75, 100]),
                "performance_rating": round(random.uniform(3.0, 5.0), 1),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    data_dir = Path("data")
    data_dir.mkdir(parents=True, exist_ok=True)

    employees = generate_employees(500)
    projects = generate_projects(100)
    allocations = generate_allocations(employees, projects, 1000)

    employees.to_csv(data_dir / "employees.csv", index=False)
    projects.to_csv(data_dir / "projects.csv", index=False)
    allocations.to_csv(data_dir / "historical_allocations.csv", index=False)
    print("Generated data/employees.csv, data/projects.csv, data/historical_allocations.csv")


if __name__ == "__main__":
    main()
