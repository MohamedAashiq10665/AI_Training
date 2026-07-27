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
- `manager`: all operational endpoints except admin-only management concerns
- `viewer`: read-only analytics/workforce endpoints and constrained chat endpoints

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

Validation behavior:

- `required_skills` must be a comma-separated or array-style list of skill names.
- Empty skill lists are rejected.
- Skill entries shorter than 2 characters are rejected.
- Natural-language prompts or unrelated non-skill text return HTTP 400 with a skill-format guidance message.

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

Validation behavior:

- Empty queries are rejected.
- Very short queries should be refined on the frontend before submission.
- Chat supports only workforce staffing/allocation queries.
- Unrelated prompts (for example weather, jokes, general trivia) return HTTP 400.
- Error detail clearly states the supported scope.

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

## GET /project-teams

Required roles: `admin`, `manager`, `viewer`

Returns latest allocation month grouped by project and member list.

## GET /projects

Required roles: `admin`, `manager`, `viewer`

Returns projects with:

- required skills
- headcount demand
- allocated member count (latest month)

## GET /projects/{project_id}/details

Required roles: `admin`, `manager`, `viewer`

Returns:

- project metadata
- allocated members
- fit candidates (AI-driven ranking)

Fit candidates include explainability fields such as matched skills, match score, recommendation reason, and missing skills.

## POST /projects/{project_id}/assign

Required roles: `admin`, `manager`

Assigns an employee to a project for current/latest allocation month and updates utilization/availability.

## POST /projects/{project_id}/unassign

Required roles: `admin`, `manager`

Unassigns an employee from a project and recomputes employee utilization from remaining allocations.

## POST /projects/{project_id}/ai-recommend-chat

Required roles: `admin`, `manager`, `viewer`

Returns cross-project transfer suggestions and an AI response narrative.

Validation behavior:

- User-provided query must be staffing/allocation related.
- Unrelated prompts return HTTP 400 with explicit supported-scope detail.
