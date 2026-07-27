# Demo Video Talk Track

This script is written for screen recording. Read it naturally, keep a steady pace, and follow the on-screen cues.

## 1. Opening (30 to 45 seconds)

### On screen
- Project title slide or README open in editor.

### Presenter dialogue
Hi everyone, in this demo I am presenting my capstone project, AI-Powered Resource Allocation and Bench Management with RAG.

The core business problem is simple: staffing decisions are often slow, manual, and hard to explain in review meetings.

This solution combines secure APIs, analytics, and AI recommendations so managers can staff projects faster, with clear reasoning and measurable impact.

## 2. What I Built (45 to 60 seconds)

### On screen
- Architecture or docs overview.

### Presenter dialogue
This system has three layers working together.

First, a FastAPI backend with authentication, role-based access, workforce analytics, and project allocation workflows.

Second, a React-based command center with dashboard insights and an operational workforce directory.

Third, an AI recommendation layer that combines retrieval and weighted scoring to produce explainable fit-candidate results.

## 3. Demo Roadmap (15 seconds)

### Presenter dialogue
In the next few minutes, I will show login and security, dashboard analytics, staffing recommendations with validation, project allocation actions, cross-project AI recommendation chat, and finally quality evidence from testing and benchmarking.

## 4. Live Walkthrough (8 to 10 minutes)

### Part A: Login and Access Control (1 minute)

### On screen
- Login page.

### Presenter dialogue
I am logging in as a manager.

Notice that access is role-aware. Sensitive operations such as recommendation and allocation actions are restricted, while read-only visibility is still available for viewer roles.

This is important because enterprise staffing tools must enforce permissions at both UI and API layers.

### Part B: Dashboard Analytics (2 minutes)

### On screen
- Dashboard KPIs and charts.

### Presenter dialogue
This is the workforce command center.

At the top we have KPIs: total employees, available employees, bench percentage, and utilization.

Now let us read the charts quickly:
- Bench by skill tells us where idle capacity exists.
- Historical allocation trend shows staffing movement over time.
- Skill demand trend indicates which capabilities are in demand.
- Upcoming project demand highlights domain pressure.

So before staffing anyone, we already have a data-backed view of supply versus demand.

### Part C: AI Staffing Recommendation with Validation (2 minutes)

### On screen
- AI Staffing Recommendation panel.

### Presenter dialogue
Now I will use the AI Staffing Recommendation panel.

First, I will intentionally type unrelated free-text input to show validation.

You can see the system blocks the request and asks for a proper skill-list format.

Now I enter a valid input, for example Python, Azure, Data Engineering, and run recommendation.

The output is ranked and explainable, including match score, matched skills, missing skills, availability, and recommendation reason.

This demonstrates two things: strong user guidance and reliable recommendation quality.

### Part D: Workforce Directory Operations (2.5 minutes)

### On screen
- Switch to Employees page, then Projects tab.

### Presenter dialogue
Next I move to the Workforce Directory.

In Employees tab, we have searchable and paginated employee data with profile context.

In Projects tab, I open project details.

Inside this view, we can see allocated members and AI-driven fit candidates.

Now I perform an assign action for a fit candidate.

And now I perform unassign for an allocated member.

These actions prove this is not a static dashboard. It supports real staffing operations with utilization recalculation.

### Part E: Cross-Project AI Recommendation Chat (1 minute)

### On screen
- Project details AI Recommendation Chat section.

### Presenter dialogue
Now I will use cross-project AI recommendation chat.

This feature suggests who can be moved from other projects, with context like source project, skill overlap, experience, and utilization.

It is useful when managers must balance delivery risk across multiple projects, not just fill a single role.

### Part F: Optional API Proof (45 to 60 seconds)

### On screen
- Swagger or API client.

### Presenter dialogue
If needed, I can quickly validate API behavior.

Recommendation requests with unrelated non-skill input now return clear validation errors.

Valid recommendation requests return ranked candidates.

Project details and allocation endpoints reflect assignment changes immediately.

This confirms backend and frontend behavior are aligned.

### Part G: Quality Evidence (1 minute)

### On screen
- Test report, benchmark artifacts, docs folder.

### Presenter dialogue
To close the technical walkthrough, here is quality evidence.

We have automated tests for core workflows and role behavior.

We also have benchmark artifacts in CSV, JSON, and Markdown for model comparison and reproducibility.

## 5. Architecture Summary (1.5 to 2 minutes)

### On screen
- Architecture doc or diagram.

### Presenter dialogue
At a high level, requests flow from React UI to FastAPI services.

The backend validates auth and role permissions, reads workforce and project data, retrieves relevant candidate context, then applies recommendation scoring.

For project staffing operations, assign and unassign endpoints update allocations and utilization state.

The design emphasizes explainability, maintainability, and operational safety.

## 6. Business Impact (45 to 60 seconds)

### Presenter dialogue
Business value comes in five areas:
- faster staffing cycles,
- better bench utilization,
- better project control through direct assignment workflows,
- higher recommendation quality with explainability,
- and better governance through transparent decision support.

## 7. Limitations and Next Steps (45 to 60 seconds)

### Presenter dialogue
Current limitations are mostly around data freshness and model tuning.

Next steps include feedback-driven ranking improvements, scenario simulation for future demand, and stronger production hardening with CI/CD and managed deployment.

## 8. Closing (20 to 30 seconds)

### Presenter dialogue
To summarize, this capstone delivers an end-to-end staffing intelligence platform that combines security, analytics, AI recommendations, and operational workflows.

Thank you for watching. I am happy to take questions.

## Quick Delivery Tips for Recording

- Keep cursor movement slow and intentional.
- Pause for one second before each section transition.
- When showing validation, narrate expected versus actual behavior.
- Keep the total video length around 10 to 12 minutes.
