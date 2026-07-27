# Exercise04 - Login API Security Hardening

This exercise demonstrates an iterative Copilot workflow:

1. Generate a basic login API from a weak prompt.
2. Improve it with a stronger prompt.
3. Run a security review.
4. Apply production-grade fixes.
5. Generate and run unit tests.
6. Validate Copilot limitations.

## Step 1 - Basic Prompt

Prompt used:

```text
Create a login API with username and password
```

Observed likely output characteristics:

- Plaintext password storage
- Basic string comparison
- No schema validation
- User enumeration through different error messages
- No token-based auth flow

Reference snapshot: `docs/step1_insecure_login_api.py`

## Step 2 - Better Prompt

Prompt used:

```text
Add input validation, password hashing (bcrypt), and error handling
```

Observed improvements:

- Pydantic request schema
- Bcrypt-based password verification
- More structured error handling

Still missing:

- JWT-based auth/session flow
- Account status checks
- Brute-force protection / rate limiting
- Secret management discipline and token controls

Reference snapshot: `docs/step2_improved_login_api.py`

## Step 3 - Security Review Findings

Prompt used:

```text
Find security issues in this code
```

Findings:

1. Step 1 stores plaintext passwords and compares raw strings.
2. Step 1 leaks authentication state (user exists vs wrong password).
3. Step 1 has no input constraints, allowing malformed payloads.
4. Step 2 still has no JWT auth flow for downstream authorization.
5. Step 2 uses an in-memory user store and has no lockout/rate limit controls.
6. Step 2 can still be weak in secret/key management depending on deployment defaults.

## Step 4 - Applied Fixes

Implemented in this exercise codebase:

- Bcrypt password hashing + verify helper
- Strict request validation (username pattern, min/max lengths)
- Proper auth flow with JWT access token (`HS256`, expiry, subject claim)
- Generic invalid-credential response to reduce user enumeration
- Inactive-account check

Final API endpoints:

- `POST /auth/register`
- `POST /auth/login`

## Step 5 - Unit Tests

Generated tests with edge cases cover:

- Valid login returns JWT token
- Wrong password
- Unknown username
- Empty fields
- Invalid username format
- Too-short password
- Inactive account

## Step 6 - Copilot Limitation Check

Human review findings:

- Copilot often starts with insecure defaults unless security requirements are explicit.
- Copilot-generated auth samples may omit operational controls (rate limiting, lockout, audit logs).
- In-memory examples are useful for learning but not production persistence.
- JWT examples often need manual hardening (key rotation strategy, refresh token flow, revocation).

## Run

```bash
pip install -r requirements.txt
pytest
uvicorn app.main:app --reload
```

Open docs:

- `http://127.0.0.1:8000/docs`
