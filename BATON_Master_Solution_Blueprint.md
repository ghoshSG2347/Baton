# BATON — MASTER SOLUTION BLUEPRINT

> **Mission Control for AI-Assisted Development Teams**
>
> GitHub stores the code. Baton prepares the right context for the right teammate and their AI.

---

## DOCUMENT PURPOSE

This document is the consolidated solution specification for **Baton**.

It combines:

- the original problem understanding;
- the user's original product vision;
- the Mission Control / gatekeeper operating model;
- the recommended simplicity-first architecture;
- the zero-cost / zero-server / zero-Baton-AI philosophy;
- the team-duty and ownership system;
- branch- and folder-specific context generation;
- `context.md` generation;
- the ChatGPT / Claude → Antigravity / Cursor workflow;
- the repository skeleton initialization concept;
- the `contracts/` and `OWNER.md` ideas;
- conflict and integration checking;
- token budgeting;
- deployment-aware project structure;
- and the recommended MVP and future roadmap.

This is intended to be the **single source of product truth** before implementation begins.

---

# 0. CORE PRODUCT PHILOSOPHY

## The central idea

> **Do not build another tool. Connect the tools people already use in a simpler way.**

Baton should not try to replace:

- GitHub
- Git
- ChatGPT
- Claude
- Gemini
- Antigravity
- Cursor
- Vercel
- Render

Instead, Baton provides the missing coordination layer between them.

### Existing tools do the heavy lifting

| Need | Existing tool | Baton contributes |
|---|---|---|
| Source control | GitHub / Git | Simple beginner-facing interpretation |
| Identity | GitHub | Team/member presentation |
| Repository state | GitHub API | Relevant selection and organization |
| AI reasoning | ChatGPT / Claude / Gemini | Structured handoff |
| AI coding | Antigravity / Cursor | Focused implementation prompt |
| Hosting | Vercel / Render / equivalent | Deployment-aware rules |
| Token estimation | Tokenizer library | Context budget and visibility |

### Rule

> **Own the decisions. Rent the plumbing.**

Baton's value is the shape it gives to existing infrastructure.

---

# 1. EXECUTIVE SUMMARY

## Product

**Baton** is a lightweight Mission Control system for small teams building software with AI-assisted development tools.

The Mission Control operator configures the team, repository structure, roles, branches, folder ownership, dependencies, and project rules. Baton reads the actual repository state from GitHub and generates a focused Markdown context packet for whichever teammate needs it.

The teammate then takes that context into an existing ChatGPT/Claude conversation containing the PRD. The chat AI converts the project context + the teammate's job into a precise prompt for Antigravity/Cursor. The coding AI then implements the work.

Baton does **not** need its own AI API in the core version.

## Core promise

> **Give each teammate and their AI exactly the project context they need — not the whole project.**

## Operating model

Baton is currently **gatekept by Mission Control**.

The team does not need Baton accounts.

The Mission Control operator:

1. connects/configures the repository;
2. defines team members and responsibilities;
3. initializes the project architecture;
4. selects branches/folders when context is needed;
5. generates Markdown context;
6. generates prompts;
7. distributes the result to teammates.

This deliberately removes:

- user authentication;
- team databases;
- account management;
- social features;
- persistent cloud state;
- unnecessary backend infrastructure.

---

# 2. PROBLEM UNDERSTANDING

## 2.1 The actual problem

The problem is not simply that beginners do not understand Git.

The deeper problem is:

> **Different teammates and their AI sessions maintain different private pictures of the same project.**

That causes:

- duplicated work;
- accidental edits outside ownership;
- inconsistent API assumptions;
- repeated explanations;
- late integration problems;
- unnecessary AI context consumption;
- Git conflicts;
- and wasted development time.

Git synchronizes the code.

It does **not automatically synchronize the team's understanding of the code**.

---

## 2.2 Primary users

### Team

Small 2–4 person development teams, especially beginners or early-stage developers using AI-assisted IDEs.

### Mission Control

The person coordinating the team's context and project structure.

### Teammates

Each member receives a focused context packet for their work instead of needing to understand the entire repository.

---

## 2.3 Why the problem exists

### Fragmented knowledge

Important project knowledge lives inside:

- PRD documents;
- ChatGPT/Claude chats;
- Discord/WhatsApp conversations;
- people's memory;
- README files;
- commit messages;
- source code;
- task lists.

### AI context fragmentation

An AI coding session may repeatedly re-explore the same repository and infer different assumptions.

### Beginner Git limitations

Many beginners know:

- clone;
- push;
- pull;

but struggle with:

- branching;
- merging;
- conflict resolution;
- rebasing;
- understanding ownership boundaries.

### Poor handoffs

A teammate may say:

> "Frontend is mostly done."

That is far less useful than:

> `GET /api/books/:id` expects `{ id, title, author, chapters[] }`, mock data lives at `src/mocks/books.json`, and error states remain unfinished.

Baton converts vague handoffs into structured, source-backed context.

---

## 2.4 Current workflow and failure

| Current approach | Friction | Consequence |
|---|---|---|
| "I'll do frontend" | No explicit ownership | Overlapping edits |
| Each developer asks their own AI | AI must rediscover context | Token/time waste |
| Knowledge shared in chat | Gets buried | Re-explanation |
| Backend guesses frontend needs | Contract is implicit | Integration bugs |
| Everyone works until the final merge | Problems surface late | Panic and rework |
| Whole repo given to AI | Too much irrelevant context | Slower/expensive reasoning |
| Manual context document | Becomes stale | AI follows outdated rules |

---

# 3. EXISTING APPROACHES & WHY THEY ARE NOT ENOUGH

## Manual chat + shared docs

Good at communication.

Weak at:

- freshness;
- structure;
- repository-grounded truth.

## GitHub

Excellent source-control infrastructure.

Weakness for Baton users:

- too much Git terminology;
- doesn't automatically prepare role-specific context;
- doesn't solve the AI handoff problem.

## Project boards

Good for task tracking.

Weak at:

- understanding actual code state;
- extracting contracts from code;
- preparing AI-ready context.

## Repo-to-AI / codebase-packaging tools

Good at representing repositories.

Weak at:

- team ownership;
- role-specific context;
- branch-specific handoff;
- integration coordination.

## Static context files

Good as standing instructions.

Weak because:

- manually maintained files become stale;
- they don't automatically reflect current branch/commit state.

## Generic AI project planners

Typical pattern:

> Idea → AI → PRD → tasks → dashboard

This is likely to be crowded in hackathons.

Baton instead focuses on the **live build process** and the handoff between teammates and AI tools.

---

# 4. PROPOSED SOLUTION

## Project Name

# BATON

## One-line pitch

> **GitHub stores your code; Baton gives every teammate and their AI the exact context they need to continue the work safely.**

## Elevator pitch

Baton is a Mission Control layer for AI-assisted development teams. The operator defines the project structure, team responsibilities, branch ownership, and development rules. When a teammate needs another teammate's completed work, Baton reads the relevant branch and folder from GitHub, extracts useful project facts, and generates a detailed Markdown handoff. That handoff is inserted into the team's existing planning chat, which creates a focused prompt for Antigravity/Cursor. Baton itself stays lightweight, deterministic, and free of paid AI dependencies.

---

# 5. WHAT BATON ACTUALLY OWNS

Baton should own **four signature decisions**:

## 5.1 Context selection

What information is relevant to the requested task?

## 5.2 Context structure

How should that information be organized so both humans and AI can understand it?

## 5.3 Ownership boundaries

Who owns which branch/folder and what should their AI be allowed to touch?

## 5.4 Handoff format

How should one teammate's completed work be transferred to another teammate with minimal explanation?

These are the product.

Everything else is supporting infrastructure.

---

# 6. MISSION CONTROL MODEL

## 6.1 Operating philosophy

Baton is currently a **Mission Control console**, not a multi-user SaaS platform.

The operator is the gatekeeper.

The operator can:

- add the repository;
- create the team configuration;
- define roles;
- define folders;
- define branches;
- define dependencies;
- define Team Rules;
- initialize the repository structure;
- select whose completed work is needed;
- generate a context packet;
- generate a prompt;
- review warnings;
- distribute the Markdown manually.

## 6.2 What teammates need to do

Ideally almost nothing inside Baton.

Their workflow is:

```text
Receive Markdown
      ↓
Paste into existing ChatGPT / Claude conversation
      ↓
Add job / request
      ↓
Receive coding-agent prompt
      ↓
Paste into Antigravity / Cursor
      ↓
Code
      ↓
Push
```

This keeps the team learning burden very low.

---

# 7. INITIAL PROJECT SETUP

One of the most important additions is **project initialization**.

Before parallel development begins, Mission Control should initialize a predictable project skeleton.

## 7.1 Setup flow

```text
Repository
    ↓
Team roles + duties
    ↓
Deployment target / stack preset
    ↓
Generate project skeleton
    ↓
Mission Control reviews
    ↓
Commit initial structure once
    ↓
Team starts parallel work
```

An empty repository is acceptable, but it needs an initial commit before ordinary branching workflows become useful.

---

## 7.2 Recommended deployment-ready project structure

Baton should initialize the **target project repository** with a clean monorepo-style structure. The goal is simple:

- `frontend/` contains **only frontend code** and is independently deployable to **Vercel**.
- `backend/` contains **only backend code** and is independently deployable to **Render**.
- `contracts/` contains the interface agreed between them.
- `docs/` contains human/AI project knowledge that is not runtime code.
- `scripts/` contains optional repository-level tooling.
- root-level deployment files configure infrastructure without mixing frontend and backend source code.

This is the **recommended default preset for Baton: React + Vite frontend + FastAPI backend + Vercel + Render**. Other stacks can have presets later, but Baton should not force one framework's conventions onto another framework.

### Recommended repository tree

```text
project-root/
│
├── frontend/                         # Vercel application root
│   ├── public/                       # Static public assets
│   ├── src/
│   │   ├── assets/                   # Imported images/icons/fonts
│   │   ├── components/               # Reusable UI components
│   │   ├── features/                 # Feature-level modules
│   │   ├── hooks/                    # Custom React hooks
│   │   ├── lib/                      # Frontend libraries/configuration
│   │   ├── pages/                    # Page-level components/routes
│   │   ├── services/                 # API clients and external services
│   │   ├── types/                    # Frontend TypeScript types
│   │   ├── utils/                    # Pure frontend utilities
│   │   ├── App.tsx
│   │   └── main.tsx
│   │
│   ├── .env.example                  # Frontend variable names only
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   ├── OWNER.md
│   └── README.md
│
├── backend/                          # Render application root
│   ├── app/
│   │   ├── api/
│   │   │   ├── routes/               # HTTP/API route modules
│   │   │   └── deps.py               # Shared FastAPI dependencies
│   │   ├── core/                      # Configuration, security, constants
│   │   ├── database/                  # DB engine/session/base + migrations link
│   │   ├── models/                    # Database models
│   │   ├── schemas/                   # Request/response validation models
│   │   ├── services/                  # Business logic/use-cases
│   │   └── main.py                    # FastAPI application entry point
│   │
│   ├── tests/                         # Backend tests
│   ├── .env.example                   # Backend variable names only
│   ├── requirements.txt
│   ├── OWNER.md
│   └── README.md
│
├── contracts/                        # Shared interface; read by both sides
│   ├── api.md                         # Endpoints + request/response shapes
│   └── data.md                        # Shared entities + field definitions
│
├── docs/                             # Project knowledge, not runtime code
│   ├── PRD_DIGEST.md
│   ├── ARCHITECTURE.md
│   ├── DECISIONS.md
│   └── DEPLOYMENT.md
│
├── scripts/                          # Optional repo-level scripts
│   └── README.md
│
├── render.yaml                       # Render Blueprint for the backend
├── .gitignore
└── README.md
```

### Why this structure is intentionally clean

The repository has **one obvious home for each kind of thing**.

```text
frontend/   → browser application
backend/    → server/API application
contracts/  → agreed interfaces

docs/       → project knowledge
scripts/    → repository tooling
```

There should not be a random `api/`, `server/`, `client/`, or `components/` directory sitting beside `frontend/` and `backend/` unless the chosen stack genuinely requires it.

### What must NOT happen

Do not allow a teammate or AI agent to create structures like:

```text
project-root/
├── frontend/
├── backend/
├── api/
├── server/
├── database/
├── components/
├── utils/
├── src/
└── random-feature/
```

That recreates the exact structural confusion Baton is supposed to prevent.

The rule is:

> **Runtime code belongs inside its deployable application. Shared knowledge belongs at the root.**

---

## 7.3 Frontend — Vercel-ready structure

The `frontend/` directory is treated as a **stand-alone Vercel project**.

For the default React + Vite preset:

```text
frontend/
├── public/
├── src/
│   ├── assets/
│   ├── components/
│   ├── features/
│   ├── hooks/
│   ├── lib/
│   ├── pages/
│   ├── services/
│   ├── types/
│   ├── utils/
│   ├── App.tsx
│   └── main.tsx
├── .env.example
├── package.json
├── tsconfig.json
├── vite.config.ts
├── OWNER.md
└── README.md
```

The Vercel project should use:

```text
Root Directory: frontend
Framework: Vite / detected framework
Build Command: npm run build
Output Directory: dist
```

Vercel supports setting a project's Root Directory to a subdirectory inside a repository, which is exactly what makes this monorepo layout practical. Vercel's current documentation also supports separate Vercel Projects for directories in the same repository. citeturn702720search0turn702720search2

### Frontend rules

- Frontend may call the backend through HTTP/API contracts.
- Frontend must not import backend implementation files.
- Frontend owns its own `package.json`.
- Frontend owns its own `.env.example`.
- Browser-visible environment variables must follow the chosen frontend framework's naming rules.
- API base URL is configuration, not hard-coded production code.

Example:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Production value is configured in Vercel rather than committed to Git.

---

## 7.4 Backend — Render-ready structure

The `backend/` directory is treated as a **stand-alone Render Web Service**.

For the default FastAPI preset:

```text
backend/
├── app/
│   ├── api/
│   │   ├── routes/
│   │   └── deps.py
│   ├── core/
│   ├── database/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── tests/
├── .env.example
├── requirements.txt
├── OWNER.md
└── README.md
```

Recommended Render configuration:

```text
Service Type: Web Service
Runtime: Python
Root Directory: backend
Build Command: pip install -r requirements.txt
Start Command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
Health Check: /api/health
```

Render's current monorepo documentation supports a `rootDir` such as `backend`, with build and start commands evaluated relative to that directory. Render's FastAPI deployment documentation uses Uvicorn with `--host 0.0.0.0 --port $PORT`. citeturn510696search1turn389406search4

### Backend rules

- `app/main.py` is the API entry point.
- API route modules live under `app/api/routes/`.
- Database-specific implementation stays under `app/database/`.
- Pydantic request/response models live under `app/schemas/`.
- Business logic lives under `app/services/`.
- ORM/database models live under `app/models/`.
- Secrets are never committed.
- The server binds to the platform-provided `PORT`.
- Backend CORS configuration is explicit and reads allowed origins from environment configuration.

Render Web Services must listen on `0.0.0.0` and use the service port; the current Render documentation recommends using the `PORT` environment variable. citeturn389406search3

---

## 7.5 Root-level deployment files

### `render.yaml`

The recommended Render Blueprint lives at the **repository root**, while the service itself uses `backend/` as its root directory.

Example default configuration:

```yaml
services:
  - type: web
    name: project-backend
    runtime: python
    rootDir: backend
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn app.main:app --host 0.0.0.0 --port $PORT
    healthCheckPath: /api/health
```

Render's current Blueprint specification places `render.yaml` at the repository root by default and supports `rootDir` for monorepo services. citeturn510696search0turn510696search4

### Vercel configuration

Do **not** add unnecessary Vercel configuration files just because the project is using Vercel.

For the default setup, configure the Vercel Project's **Root Directory** as:

```text
frontend
```

A `frontend/vercel.json` should only be added when the selected framework actually requires custom Vercel behavior such as rewrites or another explicit configuration override. Vercel documents `vercel.json` as an override mechanism rather than a requirement for every project. citeturn702720search3turn702720search7

---

## 7.6 Contracts stay outside both applications

The shared contract is deliberately **not** placed inside `frontend/` or `backend/`.

```text
contracts/
├── api.md
└── data.md
```

Why?

Because the contract belongs to the **boundary**, not to one implementation.

```text
frontend  ───────→ contracts/api.md ←─────── backend
```

Both teams read it.

The owner of a contract may be the backend member, but everyone treats the agreed interface as a controlled shared artifact.

This prevents the common mistake of allowing frontend code to import backend internals just because both happen to exist in the same Git repository.

---

## 7.7 Deployment-aware environment structure

Each deployable application owns its own environment template.

```text
frontend/.env.example
backend/.env.example
```

Example frontend:

```env
VITE_API_BASE_URL=http://localhost:8000
```

Example backend:

```env
DATABASE_URL=
ALLOWED_ORIGINS=http://localhost:5173
```

Only variable **names and safe development defaults** belong in `.env.example`.

Real secrets belong in Vercel/Render environment configuration, never in Git.

---

## 7.8 Deployment contract Baton should initialize

When Mission Control selects the **Vercel + Render preset**, Baton should automatically encode these rules into the generated project configuration:

```text
DEPLOYMENT

Frontend:
- Directory: /frontend
- Platform: Vercel
- Build root: /frontend

Backend:
- Directory: /backend
- Platform: Render
- Service type: Web Service
- Runtime: Python / FastAPI

Boundary:
- Frontend talks to backend only through HTTP/API contracts.
- Frontend never imports backend implementation files.
- Backend never imports frontend source files.
- Shared interfaces live in /contracts.
- Environment variables remain application-specific.
- CORS must allow the deployed frontend origin.
```

This deployment contract becomes part of the **static half** of every generated `context.md`.

That means an AI agent does not have to rediscover deployment architecture every time it starts a task.

---

## 7.9 Stack presets instead of one giant universal template

Baton should not try to support every framework in the first implementation.

The first preset should be:

```text
React + Vite + TypeScript
        +
FastAPI + Python
        +
Vercel + Render
```

Later presets can include:

```text
Next.js + FastAPI
React/Vite + Node/Express
Next.js full-stack + Vercel
Django + React/Vite
```

The **repository philosophy stays the same** while framework-specific files and commands change.

This keeps the initializer reliable instead of pretending that all frameworks share the same folder conventions.

# 8. OWNER.md

Each owned area should contain an extremely small `OWNER.md`.

Example:

```markdown
# Folder Ownership

Folder: backend/
Owner: Member 2
Branch: member2-backend
Purpose: API and database

Allowed:
- Edit files in this folder

Not allowed:
- Modify another member's owned folder without explicit instruction

Depends on:
- contracts/api.md

Provides:
- The backend endpoints described by contracts/api.md
```

These files exist because AI agents frequently drift outside intended boundaries.

They cost almost no context while providing explicit local rules.

---

# 9. CONTRACTS — THE MOST IMPORTANT STRUCTURAL ADDITION

The `contracts/` directory represents the project's agreed interfaces.

## `contracts/api.md`

Contains:

- endpoint;
- method;
- request shape;
- response shape;
- errors;
- auth expectations;
- ownership of the contract.

## `contracts/data.md`

Contains:

- entities;
- fields;
- relationships;
- important constraints.

## Why this matters

The original problem is ultimately about parallel pieces not fitting together.

Contracts become the explicit boundary between those pieces.

Baton can later compare:

```text
Frontend expectation
        ↕
contracts/api.md
        ↕
Backend implementation
```

and detect possible drift.

---

# 10. TEAM CONFIGURATION

Mission Control should have one compact configuration file in Baton's own project.

Do **not** store it inside the application repository being analyzed unless the team explicitly wants that behavior.

Example:

```yaml
project:
  repo: owner/project-name
  default_branch: main

team_rules:
  - "Only edit files inside your owned folders unless explicitly instructed."
  - "Match agreed contracts exactly."
  - "Do not silently invent API shapes."
  - "State assumptions explicitly."

members:
  - name: Asha
    github: asha
    branch: member1-asha
    role: frontend
    folders:
      - frontend
    job: "Build the user interface and frontend API integration."
    depends_on: []
    provides_to:
      - Ravi

  - name: Ravi
    github: ravi
    branch: member2-ravi
    role: backend
    folders:
      - backend
    job: "Build the API and database required by the frontend."
    depends_on:
      - Asha
    provides_to:
      - Asha
```

### Structured fields

Keep these structured:

- name;
- GitHub username;
- branch;
- role;
- folders;
- dependencies;
- provided-to relationships.

Keep `job` mostly free-form.

Do not ask an LLM to interpret configuration that ordinary code can handle.

---

# 11. USER FLOW

## 11.1 Initial setup

```text
Mission Control
    ↓
Provide GitHub repo
    ↓
Select / configure stack
    ↓
Generate folder architecture
    ↓
Assign team roles
    ↓
Assign branches
    ↓
Assign folders
    ↓
Add Team Rules
    ↓
Commit starter structure
```

## 11.2 During development

Suppose:

- Member 1 owns `/frontend`;
- Member 2 owns `/backend`.

Member 1 pushes their completed frontend work.

Mission Control then selects:

```text
Source member: Member 1
Branch: member1-frontend
Folder: /frontend
Target member: Member 2
Purpose: Backend integration
```

Baton reads Member 1's branch directly.

No merge is necessary just to inspect completed work.

---

# 12. REPOSITORY ANALYSIS

Baton should analyze only what is needed.

## 12.1 First-level facts

Extract without AI:

- repository name;
- active branch;
- commit SHA;
- file tree;
- stack from package/dependency manifests;
- important configuration files;
- environment variable names;
- route patterns;
- API client calls;
- type/interface definitions;
- mock data;
- TODOs;
- recent commit subjects;
- Handoff lines;
- stray files;
- shared files.

## 12.2 Prioritization

When context is limited, prioritize:

1. Team Rules;
2. role / ownership;
3. requested folder;
4. relevant contracts;
5. API client and type files;
6. entry points / routes;
7. mocks;
8. recent handoff;
9. relevant config;
10. only then additional implementation files.

Skip or deprioritize:

- lockfiles;
- generated assets;
- binaries;
- images;
- unrelated folders;
- huge vendor output.

---

# 13. `context.md` DESIGN

`context.md` is the primary Baton deliverable.

## It should have two halves.

### Static half — derived from configuration

Always include:

- project identity;
- stack;
- folder structure;
- ownership;
- role of requester;
- role rules;
- do-not-touch boundaries;
- deployment constraints;
- contract rules.

### Dynamic half — derived from GitHub

Regenerate every time:

- current state;
- completed work;
- relevant files;
- API expectations;
- routes;
- mocks;
- TODOs;
- handoff;
- shared-file warnings;
- possible mismatches;
- freshness stamp.

---

## 13.1 `context.md` standard template

```markdown
# Baton Context

## Source
- Repository: owner/project
- Branch: member1-frontend
- Commit: a1b2c3d
- Generated: YYYY-MM-DD HH:MM

## Requesting Member
- Name: Member 2
- Role: Backend
- Owns: /backend

## Do Not Touch
- /frontend
- /ai

## Project Stack
- Frontend: ...
- Backend: ...
- Database: ...
- Deployment: ...

## Project Structure
...

## Team Rules
...

## Source Member
- Name: Member 1
- Role: Frontend
- Branch: member1-frontend
- Folder: /frontend

## Completed Work
...

## Detected Frontend Expectations
...

## Routes
...

## API Calls
...

## Types / Data Shapes
...

## Mock Data
...

## Environment Variables
Names only.

## Handoff
...

## Shared Files
...

## Possible Integration Issues
...

## Stray / Out-of-structure Files
...

## Not Detected
Anything Baton could not safely determine.

## Files Included for Verification
...
```

---

# 14. CONTEXT BUDGETING

Detailed context is useful.

Unlimited context is not.

Baton therefore needs explicit size presets:

## Small

Use when the recipient only needs the most important interfaces and state.

## Medium

Recommended default.

Includes relevant code excerpts and broader context.

## Large

Use for unusually complex handoffs.

### Every context generation should show:

```text
Estimated tokens: 2,140
Budget: 2,500
Files included: 13
Files omitted: 7
```

And:

> **What was cut**

should be visible.

Never pretend a context is complete when it was compressed.

---

# 15. PROMPT BUILDER

The Prompt Builder is a core feature.

The user should not need to remember how to construct the perfect prompt.

## Input

```text
My identity
My role
My job
Target teammate / source
Generated context
Team rules
Target AI
```

## Chat-first mode

Recommended default:

```text
PRD
+
Baton context
+
My job
+
Team rules
        ↓
ChatGPT / Claude
        ↓
Focused coding prompt
        ↓
Antigravity / Cursor
```

## Direct mode

A quick option that skips the planning chat and outputs a direct coding-agent prompt.

This is useful when the user already understands the task.

---

# 16. STARTER PROMPT

Baton should offer a reusable starter instruction such as:

```text
Read the Baton context before beginning.

Follow the ownership rules.
Only create or edit files inside your owned folders unless explicitly instructed.
Use existing contracts exactly.
Do not silently invent interfaces.
State assumptions before implementing uncertain behavior.

When the task is complete, provide a concise Handoff containing:
- what was completed;
- what it depends on;
- what remains;
- any important assumptions.
```

The coding AI can place a concise Handoff into the commit message when practical.

A human can also enter the Handoff manually.

---

# 17. ROLE-SPECIFIC BRIEFS

Do not mutate one shared `context.md` into multiple incompatible versions.

Instead use:

```text
context.md
brief-member-1.md
brief-member-2.md
...
```

## Shared context

Contains the common project picture.

## Member brief

Contains:

- person's role;
- owned folders;
- job;
- dependencies;
- what they need from another member;
- what others expect from them;
- shared files to watch.

The Prompt Builder can combine the shared context + one member brief into one copyable block.

---

# 18. OWNERSHIP SYSTEM

Ownership should be explicit.

If:

```text
Member 1 owns /frontend
Member 2 owns /backend
```

then Baton should be able to say:

> Member 2's branch changed `/frontend/api/client.ts`, which is owned by Member 1.

This is an **ownership warning**, not automatically a hard error.

The team may deliberately allow shared edits.

---

# 19. CONFLICT RADAR

Conflict Radar is one of Baton's strongest optional features.

## V1 approach

File-level overlap only.

Example:

```text
⚠ Possible conflict

Member 1 changed:
frontend/api/client.ts

Member 2 also changed:
frontend/api/client.ts

Both changes are on separate branches.
Review before merging.
```

Important wording:

> **“might conflict” / “possible overlap”**

Never:

> “This will definitely conflict.”

Baton cannot guarantee a Git-level conflict unless it actually computes the relevant diff/merge behavior.

---

# 20. INTEGRATION CHECKER

This is the feature most closely connected to the original problem's deeper cause.

Baton can compare:

```text
Frontend expectations
        ↓
contracts/api.md
        ↓
Backend implementation
```

Example:

```text
⚠ POSSIBLE CONTRACT MISMATCH

Frontend:
GET /api/books/:id

Backend:
GET /api/book/:id

Frontend response field:
chapters[]

Backend response field:
sections[]
```

Results must be described as:

> **possible mismatch**

because static detection is best-effort.

---

# 21. PROJECT STRUCTURE VALIDATION

Baton should compare the actual repository tree against the agreed architecture.

## Example

```text
Expected:
frontend/api/
frontend/components/
backend/core/
backend/database/
contracts/

Found:
frontend/utils.js
```

Baton reports:

> `frontend/utils.js` is outside the agreed standard structure.

This catches AI agents that create files in random places.

---

# 22. DEPLOYMENT-AWARE STRUCTURE

Deployment is not an afterthought. The initializer must generate a repository whose boundaries already match the deployment boundaries.

## 22.1 Default deployment model

```text
GitHub Repository
│
├── frontend/  ───────────→ Vercel Project
│
├── backend/   ───────────→ Render Web Service
│
├── contracts/              Shared API/data agreement
├── docs/                   Project knowledge
└── render.yaml             Render infrastructure definition
```

Vercel can deploy a subdirectory of a repository by setting the project's **Root Directory** to `frontend`. Render supports the same monorepo pattern by setting the service `rootDir` to `backend`, after which build/start commands are evaluated relative to that directory. citeturn702720search0turn702720search2turn510696search1

## 22.2 Deployment rules Baton must encode

- `frontend/` is the only home for browser/frontend runtime code.
- `backend/` is the only home for server/API runtime code.
- `contracts/` is the boundary between them.
- Frontend must communicate with backend through HTTP/API contracts, never backend imports.
- Backend must never import frontend source files.
- Each deployable application owns its own dependency manifest.
- Each deployable application owns its own `.env.example`.
- Secrets never enter Git.
- CORS is configured explicitly for the deployed frontend origin.
- Backend binds to `0.0.0.0` and the platform-provided `PORT`.
- Deployment configuration belongs at the appropriate infrastructure boundary instead of being mixed into application source code.

## 22.3 What Baton should generate

For the default React + Vite + FastAPI preset, the initializer should generate at minimum:

```text
project-root/
├── frontend/
├── backend/
├── contracts/
├── docs/
├── scripts/
├── render.yaml
├── .gitignore
└── README.md
```

The generated frontend and backend directories must already contain their framework-specific starter files, ownership metadata, environment templates, and deployment instructions.

## 22.4 Deployment validation

Before allowing the team to start parallel implementation, Baton should validate:

```text
✓ frontend/ exists
✓ backend/ exists
✓ frontend has dependency manifest
✓ backend has dependency manifest
✓ frontend .env.example exists
✓ backend .env.example exists
✓ contracts/api.md exists
✓ contracts/data.md exists
✓ render.yaml points to backend
✓ backend exposes a health endpoint
✓ no runtime source folder exists outside frontend/backend
```

This makes deployment structure part of the project's **initial contract**, rather than something the team discovers near the end.

For the exact current platform settings and free-tier behavior, Baton should treat official Vercel and Render documentation as the source of truth at deployment time. citeturn702720search2turn389406search3

# 23. TOKEN ECONOMY

Baton should be designed around the user's core principle:

> **AI can write thousands of lines now. Therefore the bottleneck shifts toward giving AI the right information efficiently.**

## Baton should not consume AI tokens for:

- file trees;
- commit lists;
- ownership;
- branch state;
- overlap detection;
- token estimates;
- route patterns;
- environment variable names;
- repository metadata.

## Baton should minimize what is passed to external AI

The ideal context is:

```text
Project rules
+
My role
+
What I own
+
What I need
+
Relevant teammate's completed work
+
Relevant interfaces
+
Current state
+
Important warnings
```

not:

```text
Entire repository
+ thousands of irrelevant files
```

---

# 24. AI STRATEGY

## Baton itself

### No AI by default.

This is a deliberate product decision.

## External AI

AI is useful for:

- interpreting the PRD;
- planning work;
- deciding implementation steps;
- writing code;
- explaining difficult concepts.

## Deterministic code is preferable for:

- GitHub metadata;
- branch state;
- ownership;
- file trees;
- token counting;
- comparisons;
- known static patterns;
- context formatting.

This makes the system:

- cheaper;
- more predictable;
- more explainable;
- easier to debug.

---

# 25. SECURITY & PRIVACY

## Read-only access

Use a narrowly scoped, read-only GitHub credential.

## Token handling

Do not hard-code the token.

Prefer local/in-memory handling in the Mission Control model.

## Secrets

Never put secret values into generated context.

Allowed:

```text
DATABASE_URL detected
```

Forbidden:

```text
DATABASE_URL=actual-secret-value
```

## Untrusted repository content

Commit messages, comments, README text and source text may contain malicious or instruction-like content.

Treat repository-derived text as **data**, not as Baton instructions.

## Privacy

Because Baton is gatekept:

- distribute context manually;
- expose only the branch/folder information actually required;
- never reveal secrets;
- avoid emails where GitHub username is sufficient.

---

# 26. SYSTEM ARCHITECTURE

## V1 architecture

```text
                  ┌───────────────────────┐
                  │    Mission Control    │
                  │      React UI         │
                  └───────────┬───────────┘
                              │
                              ▼
                  ┌───────────────────────┐
                  │     Baton Core        │
                  │                       │
                  │ Team Config           │
                  │ Ownership             │
                  │ Repo Analyzer         │
                  │ Context Builder       │
                  │ Contract Checker      │
                  │ Conflict Radar        │
                  │ Prompt Builder        │
                  │ Token Budget          │
                  └───────────┬───────────┘
                              │
                              ▼
                       ┌────────────┐
                       │ GitHub API │
                       └─────┬──────┘
                             │
                             ▼
                  ┌──────────────────────┐
                  │ Generated Artifacts  │
                  │                      │
                  │ context.md           │
                  │ member brief         │
                  │ prompt.md            │
                  │ warnings             │
                  └──────────┬───────────┘
                             │
                    ┌────────┴────────┐
                    ▼                 ▼
               ChatGPT/Claude    Direct Prompt
                    │                 │
                    └────────┬────────┘
                             ▼
                     Antigravity/Cursor
                             │
                             ▼
                           GitHub
```

## No backend in V1

The browser performs the orchestration.

This is the major complexity reduction.

---

# 27. TECH STACK

## Frontend

Recommended:

- React
- Vite
- TypeScript
- Tailwind CSS
- shadcn/ui

## GitHub integration

- GitHub REST API
- Octokit or equivalent maintained GitHub SDK

## State

- local application state;
- local storage only where genuinely useful.

## Backend

None in V1.

## Database

None in V1.

## AI

None in Baton V1.

## Deployment

Local-first.

Optional static hosting later if the token model remains safe.

---

# 28. UI / UX STRATEGY

## Visual direction

Baton should feel like:

> **Mission Control for developers**

not:

> **another generic AI dashboard.**

Use:

- calm editorial structure;
- clear typography;
- restrained accent color;
- strong whitespace;
- obvious primary actions;
- little jargon.

## Essential screens

### 1. Mission Control Home

Shows:

- project;
- repository;
- team;
- roles;
- ownership;
- recent activity;
- warnings.

### 2. Project Initialization

Shows:

- stack preset;
- folder architecture;
- role assignments;
- generated starter structure;
- download ZIP.

### 3. Team Configuration

Shows:

- members;
- branches;
- roles;
- folders;
- dependencies;
- Team Rules.

### 4. Context Builder

Primary controls:

```text
Source member
Branch
Folder
Target member
Purpose
Context size
```

Primary action:

> **Generate Context**

### 5. Context Preview

Shows:

- source commit;
- files analyzed;
- token estimate;
- omitted sections;
- warnings;
- copy/download controls.

### 6. Prompt Builder

Shows:

- target member;
- job;
- context;
- team rules;
- Chat-first mode;
- Direct mode.

---

# 29. FEATURE PRIORITY

## MUST HAVE

1. GitHub repository connection
2. Mission Control dashboard
3. Team configuration
4. Roles / duties
5. Branch selection
6. Folder selection
7. Ownership rules
8. Repository analyzer
9. `context.md` generator
10. Prompt Builder
11. Copy / download
12. Freshness metadata

## SHOULD HAVE

13. Token meter
14. What-was-cut list
15. Project structure validation
16. Conflict radar
17. Integration checker
18. Handoff parsing
19. Starter prompt
20. Polling / manual refresh

## NICE TO HAVE

21. Discord/Slack alerts
22. line-level overlap
23. BYO-key AI summaries
24. public project showcase
25. accounts
26. social feed
27. MCP
28. IDE extension
29. multi-repo
30. automatic PR/issue generation

---

# 30. MVP DEFINITION

## Safe Version

```text
Connect repo
→ configure team
→ select branch/folder
→ analyze
→ generate context.md
→ copy/download
```

## Strong Version — RECOMMENDED

```text
Safe Version
+
Team Rules
+
Ownership
+
Token budget
+
Prompt Builder
+
Conflict Radar
+
Integration Checker
+
Structure validation
+
Freshness metadata
```

## Ambitious Version

```text
Strong Version
+
Webhooks
+
Discord/Slack
+
AI summaries
+
MCP
+
IDE extension
+
Accounts
+
Persistent backend
```

Do not begin with the ambitious version.

---

# 31. THE SINGLE MOST IMPORTANT MVP WORKFLOW

The entire product should survive if everything else is removed.

```text
Mission Control selects:
Member 1
    ↓
Branch: member1-frontend
    ↓
Folder: /frontend
    ↓
Target: Member 2
    ↓
Purpose: backend integration
    ↓
Baton analyzes actual code
    ↓
context.md
    ↓
Member 2 adds PRD + job
    ↓
ChatGPT / Claude
    ↓
Focused Antigravity prompt
    ↓
Backend implementation
```

This is the **golden path**.

Build this first.

---

# 32. DEMO STRATEGY

## Wow Moment #1 — Smart Handoff

Show a completed frontend branch.

Select `/frontend`.

Click:

> **What does the backend developer need to know?**

Baton generates:

- expected endpoints;
- request shapes;
- response shapes;
- types;
- mock data;
- unfinished work;
- project rules;
- freshness information.

Then produce the coding prompt.

---

## Wow Moment #2 — Integration Check

Show:

```text
Frontend expects:
chapters[]

Backend provides:
sections[]

⚠ Possible contract mismatch
```

This shows Baton is not just a Markdown formatter.

---

## 3-minute product story

```text
Problem
  ↓
Two teammates work independently
  ↓
Knowledge becomes fragmented
  ↓
Member 1 pushes frontend
  ↓
Mission Control requests handoff
  ↓
Baton analyzes actual branch + folder
  ↓
Context generated
  ↓
PRD + context + job → ChatGPT/Claude
  ↓
Coding prompt → Antigravity
  ↓
Implementation
  ↓
Baton checks possible integration issues
```

---

# 33. ERROR / EDGE-CASE BEHAVIOR

## Empty repo

Show a clean initializer.

Generate skeleton → review → download ZIP → commit once.

## Empty folder

Show:

> Not started.

Do not create fake content.

## Dependency not ready

Show:

> Member 1's frontend branch currently has no detected API usage.

## Analyzer uncertainty

Show:

> Not detected. Relevant raw files included for verification.

## Context too large

Trim based on priority and show exactly what was omitted.

## Shared file overlap

Show a warning, not a hard block.

## Missing GitHub permission

Explain what permission is missing in plain English.

---

# 34. REAL VS SIMULATED

## Must be real

- repository connection;
- branch selection;
- folder analysis;
- context generation;
- ownership mapping;
- token estimation;
- contract/integration detection;
- conflict detection if shown.

## Can be simulated

- multiple-person demo pushes;
- saved snapshot fallback;
- demo repository scenario.

## Must never be faked

- token savings claims;
- conflict warnings;
- contribution rankings;
- API compatibility claims;
- “Baton understands the entire codebase” claims.

---

# 35. EFFICIENCY & COST STRATEGY

## Goal

> **Baton should add useful context without creating a new AI bill.**

## Target

- no Baton AI API;
- no vector database;
- no embeddings;
- no server-side LLM;
- no database;
- no paid service dependency.

## Performance principle

Fetch and analyze only what is needed.

For a folder-specific request, do not download the entire project if it can be avoided.

## Caching

Use browser-side caching/conditional requests where practical.

## Rate limits

Respect GitHub rate limits.

Show last successful data when refresh cannot be completed.

---

# 36. TECHNICAL RISKS

| Risk | Probability | Impact | Mitigation |
|---|---:|---:|---|
| GitHub rate limits | Medium | Medium | caching, conditional requests, manual refresh |
| Token configuration | Medium | High | local-first, read-only, step-by-step setup |
| Dynamic code patterns | High | Medium | best-effort detection + raw evidence |
| False conflict warnings | Medium | Medium | file-level warnings, cautious wording |
| Unpushed work | Certain | Medium | explicitly show repository freshness |
| Huge context | Medium | Medium | size budgets and trimming |
| AI ignores ownership | Medium | Medium | ownership line in every prompt/context |
| Stale context | Medium | High | commit SHA + timestamp |
| Framework-specific structure | High | Medium | stack-specific presets |
| Prompt injection | Low/Medium | High | treat repo-derived text as untrusted |

---

# 37. DOMAIN KNOWLEDGE REQUIRED

| Concept | Meaning | Why Baton needs it |
|---|---|---|
| Commit | Saved repository change | freshness/activity |
| Branch | Parallel line of development | teammate work |
| Diff | Changed lines/files | overlap detection |
| Folder ownership | Responsible area | AI boundaries |
| API contract | Interface between components | integration safety |
| Handoff | concise work-transfer summary | teammate context |
| Context window | amount of text AI can process | budget |
| GitHub token | credential for repository access | private repository reading |
| ETag / caching | cheaper repeated API checks | refresh efficiency |

---

# 38. REAL-WORLD DEPLOYABILITY

Baton can evolve into a real product for:

- hackathon teams;
- student project teams;
- coding clubs;
- bootcamps;
- small AI-assisted development teams.

## Later production architecture

```text
GitHub App
    ↓
Webhook service
    ↓
Persistent team configuration
    ↓
Cached repository state
    ↓
Baton browser UI
```

Possible future capabilities:

- no manual token entry;
- automatic branch updates;
- persistent team workspaces;
- larger repository support;
- webhooks;
- accounts;
- saved projects;
- integrations.

None of these are required for the current internal Mission Control version.

---

# 39. WHAT TO CUT FIRST

When complexity increases, remove in this order:

1. BYO-key AI summaries
2. social features
3. notifications
4. Discord/Slack
5. line-level conflict analysis
6. public showcase
7. advanced visualizations
8. automatic handoff parsing
9. polling automation

Protect at all costs:

1. repository connection;
2. team configuration;
3. branch/folder selection;
4. ownership;
5. repository analyzer;
6. context generator;
7. prompt builder.

---

# 40. VIBE-CODING STRATEGY

Baton is intentionally suitable for AI-assisted implementation.

## Human owns

- product decisions;
- architecture;
- context format;
- folder structure rules;
- ownership model;
- what must be deterministic;
- what the system must never claim;
- scope control.

## Coding AI owns

- UI implementation;
- GitHub API wrappers;
- parsing utilities;
- Markdown generation code;
- token estimation;
- React components;
- state management;
- tests;
- error handling;
- deployment configuration.

## Rule

> **Vibe-code the implementation. Do not vibe-design the product.**

Do not start by telling an AI:

> “Build Baton.”

Start from the frozen contracts and workflows in this document.

---

# 41. IMPLEMENTATION ORDER

The recommended implementation order is:

## Phase 1 — Foundation

1. Create React/Vite/TypeScript application.
2. Create Mission Control shell.
3. Add GitHub repository configuration.
4. Implement read-only GitHub access.
5. Fetch repository metadata.

## Phase 2 — Team configuration

6. Create team config model.
7. Add members.
8. Add roles.
9. Add branches.
10. Add folder ownership.
11. Add Team Rules.

## Phase 3 — Repository understanding

12. Implement branch picker.
13. Implement folder picker.
14. Implement file-tree retrieval.
15. Implement manifest detection.
16. Implement route/API/type/environment detection.
17. Implement freshness metadata.

## Phase 4 — Context engine

18. Build `context.md` template.
19. Build priority rules.
20. Build token-size budgeting.
21. Build omitted-content reporting.
22. Build raw-evidence fallback.

## Phase 5 — Prompt Builder

23. Build Chat-first prompt.
24. Build Direct prompt.
25. Add Starter prompt.
26. Add ownership line automatically.

## Phase 6 — Coordination intelligence

27. Add structure validation.
28. Add ownership warnings.
29. Add conflict radar.
30. Add integration checker.
31. Add Handoff extraction.

## Phase 7 — Polish

32. Improve Mission Control UI.
33. Improve loading/error states.
34. Improve copy/download flows.
35. Test on a real repository with teammates.

---

# 42. TESTING STRATEGY

The most important testing target is not individual components.

It is the **golden workflow**.

## Test case 1 — Frontend → Backend handoff

Given:

- `/frontend` branch exists;
- frontend calls API endpoints;
- backend is not complete.

Expected:

- Baton detects API calls;
- generates `context.md`;
- includes contracts;
- includes mock data;
- includes freshness;
- produces a focused prompt.

## Test case 2 — Ownership violation

Given a backend branch edits `/frontend`.

Expected:

> possible ownership violation.

## Test case 3 — Shared-file overlap

Given two branches modify `package.json`.

Expected:

> possible shared-file conflict.

## Test case 4 — Context too large

Expected:

- trimming;
- visible budget;
- visible omitted items;
- no false claim of completeness.

## Test case 5 — Empty folder

Expected:

> not started / no relevant files detected.

## Test case 6 — Private repository

Expected:

- valid read-only access;
- no token leakage;
- useful error message if access fails.

---

# 43. SUCCESS METRICS

Baton's value should be measured by behavior.

Useful internal measurements include:

- time required to generate a handoff;
- size of context packet vs selected repo area;
- time a teammate spends asking for clarification;
- number of ownership warnings caught before merge;
- number of possible integration mismatches found early;
- time needed for a teammate to understand inherited work.

Do not claim direct AI cost savings unless measured using a real baseline.

---

# 44. CORE UX COPY PRINCIPLES

Avoid Git jargon wherever possible.

Prefer:

> “Ravi and Asha both changed this shared file.”

instead of:

> “Branch divergence detected.”

Prefer:

> “This context is based on commit `a1b2c3d`.”

instead of:

> “State may be stale.”

Prefer:

> “We could not detect the API call automatically, so the source file was included for verification.”

instead of:

> “Parser failed.”

Baton should feel like a helpful Mission Control operator, not a Git textbook.

---

# 45. PRODUCT BOUNDARIES

Baton is **not**:

- a Git replacement;
- a GitHub replacement;
- a code editor;
- an AI chatbot;
- an AI coding model;
- a Jira/Trello clone;
- a social network;
- an automatic code-writing agent;
- an enterprise observability platform.

Baton is:

> **A lightweight context and coordination layer for AI-assisted software teams.**

---

# 46. CORE PRODUCT LOOP

The entire philosophy can be reduced to:

```text
UNDERSTAND THE PROJECT
        ↓
DEFINE OWNERSHIP
        ↓
WORK IN PARALLEL
        ↓
CAPTURE REAL PROGRESS IN GITHUB
        ↓
SELECT ONLY RELEVANT WORK
        ↓
GENERATE FRESH CONTEXT
        ↓
HAND CONTEXT TO PLANNING AI
        ↓
HAND PROMPT TO CODING AI
        ↓
PUSH COMPLETED WORK
        ↓
REPEAT
```

---

# 47. WHY THE PRODUCT EXISTS

A few years ago developers manually wrote enormous amounts of code.

Modern AI can generate enormous amounts of code very quickly.

The bottleneck therefore shifts.

It becomes less about:

> “How fast can we type code?”

and more about:

> “How quickly can the team establish the right understanding and give the AI the right information?”

Baton exists to address that second problem.

---

# 48. FINAL PRODUCT BLUEPRINT

## Product

**Baton — Mission Control for AI-Assisted Development**

## Problem

Teammates and their AI sessions maintain different views of the project, causing context waste, ownership mistakes, conflicts, and late integration failures.

## Solution

A lightweight Mission Control application that reads the real project state from GitHub and generates precise, branch/folder/role-specific Markdown context for the teammate who needs it.

## Target Users

Small beginner / early-stage development teams using AI IDEs.

## Primary Operator

Mission Control / team coordinator.

## Core Workflow

```text
GitHub
→ configure team
→ choose member/branch/folder
→ analyze
→ generate context
→ add to PRD chat
→ create coding prompt
→ Antigravity/Cursor
→ push
→ next handoff
```

## MVP

- GitHub connection
- team configuration
- roles
- duties
- branch selection
- folder selection
- ownership
- project initialization
- deterministic analyzer
- `context.md`
- Prompt Builder
- token budget
- freshness metadata
- structure validation

## Strong Enhancements

- conflict radar
- integration checker
- handoff parsing
- starter prompt
- refresh

## AI

No AI inside Baton V1.

External AI handles reasoning and implementation.

## Tech Stack

- React
- Vite
- TypeScript
- Tailwind
- shadcn/ui
- GitHub API / Octokit
- browser state
- static/local deployment

## Architecture

Browser-only in V1.

GitHub is the repository source of truth.

## Key Differentiator

Baton turns **repository state + team rules + ownership + role + purpose** into **small, usable AI context**.

## Innovation

**7/10**

## Complexity

**5/10**

## Feasibility

**9/10**

## Demo Impact

**8/10**

## Biggest Risk

Being perceived as a GitHub/Markdown wrapper.

### Counter

The product must demonstrate:

- role-aware context;
- ownership-aware prompts;
- branch/folder-specific analysis;
- integration checks;
- conflict prevention;
- context budgeting.

## Recommended Scope

# STRONG VERSION

---

# 49. ONE-SENTENCE JUDGE PITCH

> **“Baton is Mission Control for AI-assisted development teams: it reads the real state of a GitHub project and gives each teammate's AI only the context that teammate needs to continue the work safely.”**

---

# 50. FINAL NON-NEGOTIABLES

These are the product's constitutional rules.

### Rule 1 — No unnecessary AI

Do not add AI where deterministic code is more reliable.

### Rule 2 — No unnecessary infrastructure

Do not create a backend/database unless the product genuinely requires it.

### Rule 3 — GitHub remains the code source of truth

Baton interprets GitHub; it does not replace it.

### Rule 4 — Mission Control is the operator

No team authentication is required for the current internal version.

### Rule 5 — Context must be fresh

Every generated context carries:

- branch;
- commit;
- timestamp.

### Rule 6 — Context must be bounded

Every generated packet has a size budget.

### Rule 7 — No confident guessing

If Baton does not know something, say so.

### Rule 8 — Ownership must be explicit

Every coding prompt should tell the AI:

- who it is;
- what it owns;
- what it must not modify.

### Rule 9 — Existing tools remain the heavy infrastructure

GitHub, ChatGPT/Claude, Antigravity/Cursor and deployment platforms should do what they already do well.

### Rule 10 — Build depth, not feature count

> **Five excellent features are better than twenty shallow ones.**

---

# 51. FINAL DECISION

## The project should be built.

Not as:

> “a simpler GitHub.”

Not as:

> “another AI project planner.”

Not as:

> “a chatbot for repositories.”

But as:

# **BATON — THE CONTEXT BRIDGE BETWEEN YOUR TEAM, GITHUB, CHAT AI, AND CODING AI.**

The product's core insight is simple:

> **Code is already synchronized. Understanding is not. Baton synchronizes the useful understanding.**

And the first workflow to make nearly perfect is:

```text
Member 1 finishes work
        ↓
Mission Control selects branch + folder
        ↓
Baton analyzes actual work
        ↓
Baton generates context.md
        ↓
Context + PRD + Member 2's job
        ↓
ChatGPT / Claude
        ↓
Precise Antigravity / Cursor prompt
        ↓
Member 2 continues without rediscovering the project
```

Everything else is an extension of this.

---

# END OF MASTER BLUEPRINT
