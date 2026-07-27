from recommendation_engine.scoring import compute_weighted_score


def test_compute_weighted_score_returns_valid_output():
    employee = {
        "employee_id": "EMP0001",
        "primary_skill": "Python",
        "secondary_skill": "Azure",
        "certifications": "Azure-AZ900;PMP",
        "availability_status": "Available",
        "years_experience": 6,
        "current_utilization": 0.6,
    }
    project = {
        "required_skills": ["Python", "Azure"],
        "preferred_certifications": ["Azure-AZ900"],
        "min_experience": 4,
    }

    result = compute_weighted_score(employee, project)
    assert 0 <= result["match_score"] <= 100
    assert "Python" in result["skills_matched"]
