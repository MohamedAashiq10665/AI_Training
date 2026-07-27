# API Documentation

## Authentication

### POST /auth/login

Request body:

```json
{
  "username": "manager",
  "password": "manager123"
}
```

Response:

```json
{
  "access_token": "<jwt-token>",
  "token_type": "bearer",
  "role": "manager"
}
```

### GET /auth/me

Requires Bearer token. Returns current user profile and role.

## Authorization

Use header in protected routes:

```text
Authorization: Bearer <access_token>
```

Roles:

- `admin`: all endpoints
- `manager`: recommendation, bench, analytics, utilization, chat, employees
- `viewer`: analytics, utilization, chat, employees

## POST /recommend

Required roles: `admin`, `manager`

Request body:

```json
{
  "project_name": "Healthcare Analytics",
  "required_skills": ["Python", "Azure"],
  "preferred_certifications": ["Azure-AZ900"],
  "min_experience": 4,
  "required_count": 3,
  "location": "Remote",
  "domain": "Healthcare"
}
```

Returns ranked employees with match score, reason, matched/missing skills, and upskilling suggestions.

## POST /chat

Required roles: `admin`, `manager`, `viewer`

Request body:

```json
{
  "query": "Find three available Python developers with Azure experience for a healthcare project.",
  "top_k": 5
}
```

Returns RAG-grounded answer and source employee IDs.

## GET /employees

Required roles: `admin`, `manager`, `viewer`

Returns employee list (paginated by limit query parameter).

## GET /analytics

Required roles: `admin`, `manager`, `viewer`

Returns total employees, available employees, bench percentage, resource utilization, and bench by skill.

## GET /bench

Required roles: `admin`, `manager`

Returns bench population and top bench skills.

## GET /utilization

Required roles: `admin`, `manager`, `viewer`

Returns overall utilization, role utilization, historical allocation trend.
