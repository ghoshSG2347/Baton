# Baton Frontend Architecture & Implementation Contract

> Current implementation reference (2026-10-06): [PROJECT_CONTEXT.md](../PROJECT_CONTEXT.md) and [PROJECT_AUDIT.md](../PROJECT_AUDIT.md). This historical document contains older descriptions: Conflict Radar compares inventory presence, not changed files; standalone Context Builder purpose/member/budget controls are not sent to the backend; Overview metrics include placeholders. Consult the canonical context before relying on those claims.

> **Authoritative Frontend Context & Source of Truth**  
> **Repository:** `baton-frontend/`  
> **Date:** October 2026  
> **Status:** Implementation-Grounded Audit & Reference Document

---

## 1. Executive Summary & Purpose

`FRONTEND_CONTEXT.md` serves as the authoritative, permanent implementation reference for the **Baton Mission Control Frontend**.

Baton is a Mission Control and coordination interface for AI-assisted software development teams. The frontend was built with React, Vite, TypeScript, and Tailwind CSS. It is designed to work in two operational modes:
1. **Demo Mode**: Standalone interactive demonstration using pre-configured mock fixtures for all repository, analysis, context, prompt, conflict, and integration features.
2. **Backend-Connected Mode**: Live integration with the FastAPI stateless backend (`baton-backend-v1`), orchestrating repository validation, tree inspection, code analysis, context synthesis, prompt assembly, branch conflict detection, and cross-branch integration comparison.

This document captures the exact reality of the frontend implementation as it exists in the codebase today, preventing regressions, avoiding mistaken architectural assumptions, and serving as the primary guide for future AI coding agents.

---

## 2. Frontend Architecture & Technology Stack

### 2.1 Core Technologies

| Layer | Technology | Version | Purpose |
|---|---|---|---|
| **UI Framework** | React | `^18.3.1` | Component-based view rendering with StrictMode |
| **Language** | TypeScript | `^5.5.3` | Type safety and domain interface definitions |
| **Build Tool & Dev Server** | Vite | `^5.4.2` | Rapid HMR and optimized production bundling |
| **Styling** | Tailwind CSS + PostCSS | `^3.4.1` / `^8.4.35` | Utility-first styling with custom Baton design tokens |
| **Animation Engine** | Framer Motion | `^14.0.0` | Layout transitions, entrance animations, gesture taps |
| **Smooth Scrolling** | Lenis | `^1.3.26` | Inertia-based smooth wheel scrolling on the landing page |
| **Iconography** | Lucide React | `^0.446.0` | Monochromatic technical and operational icons |
| **HTTP Client** | Native `fetch` API | Built-in | Typed HTTP client in `src/lib/api/batonApi.ts` |
| **Unused Dependency** | `@supabase/supabase-js` | `^2.57.4` | Present in `package.json`, but not imported or used anywhere |

### 2.2 Runtime Flow & Application Hierarchy

```text
Browser
  ↓
index.html (Mount point #root, fonts, metadata)
  ↓
src/main.tsx (React DOM createRoot + StrictMode)
  ↓
src/App.tsx (Top-level orchestrator: 'landing' vs 'workspace' state)
  │
  ├── CustomCursor (Global pointer tracker & trailing ring)
  │
  ├── [page === 'landing']
  │     ↓
  │   LandingPage.tsx (Lenis smooth scroll, fixed SignalField canvas)
  │     ├── LandingHeader (Sticky blur navbar with navigation & CTA)
  │     ├── HeroSection (Headline, live telemetry strip, CTA buttons)
  │     ├── ProblemSection (02 — Typographic statement, SVG fork visual, 6 problem cards)
  │     ├── BatonLoopSection (03 — 9-stage vertical pipeline rail)
  │     ├── ContextSection (04 — Token comparison & budget progress meter)
  │     ├── OwnershipSection (05 — Team ownership cards & violation alert)
  │     ├── HandoffSection (06 — Terminal execution log simulation)
  │     ├── ConflictRadarSection (07 — Multi-branch lane convergence visual)
  │     ├── IntegrationSection (08 — Route matching matrix)
  │     ├── PhilosophySection (09 — 4-tool operational roles)
  │     ├── FinalCTASection (Closing CTA)
  │     └── LandingFooter (Logo & legal / links)
  │
  └── [page === 'workspace']
        ↓
      WorkspaceShell.tsx (Header, repo status, demo controls, sidebar nav)
        ↓
      Active Workspace Section (Driven by useWorkspaceState hook)
        ├── Overview.tsx (Standby empty state OR 5 KPI metrics + project flow)
        ├── Repository.tsx (Repo validation form, branch selector, file tree & preview)
        ├── Team.tsx (Team member CRUD form, ownership cards, load demo team)
        ├── Analysis.tsx (Folder analysis, 10 pattern categories, handoffs, warnings)
        ├── ContextBuilder.tsx (Folder/budget context packet generation & download)
        ├── PromptBuilder.tsx (Chat-first / Direct prompt generation & starter rules)
        ├── ConflictRadar.tsx (Branch file collision detection & lane tags)
        └── Integration.tsx (Frontend vs Backend branch route comparison matrix)
```

### 2.3 Directory Structure & Responsibilities

```text
baton-frontend/
├── .bolt/
│   ├── config.json                 # Bolt configuration
│   └── prompt                      # Original Bolt setup prompt guidelines
├── public/                         # Static assets
├── src/
│   ├── components/
│   │   ├── landing/                # Landing page presentation components
│   │   │   ├── BatonLoopSection.tsx       # 9-stage pipeline animation
│   │   │   ├── ConflictRadarSection.tsx   # Visual branch lane convergence
│   │   │   ├── ContextSection.tsx         # Full repo vs Baton context token comparison
│   │   │   ├── FinalCTASection.tsx        # Call-to-action bottom banner
│   │   │   ├── HandoffSection.tsx         # Simulated terminal log
│   │   │   ├── HeroSection.tsx            # Hero typography, signal field, telemetry
│   │   │   ├── IntegrationSection.tsx     # Route match preview
│   │   │   ├── LandingFooter.tsx          # Footer navigation and copyright
│   │   │   ├── LandingHeader.tsx          # Fixed glassmorphism navigation header
│   │   │   ├── LandingPage.tsx            # Full landing wrapper + Lenis scroll
│   │   │   ├── OwnershipSection.tsx       # Ownership cards & cross-boundary alert
│   │   │   ├── PhilosophySection.tsx      # Tool hierarchy statements
│   │   │   └── ProblemSection.tsx         # Problem cards & diverging curves SVG
│   │   ├── ui/                     # Shared UI primitives and background canvases
│   │   │   ├── CustomCursor.tsx           # Dual-element mouse pointer and hover detection
│   │   │   ├── primitives.tsx             # StatusIndicator, MonoLabel, Panel, Button, SectionLabel, CopyButton, TelemetryLine
│   │   │   └── SignalField.tsx            # HTML5 2D Canvas animated ambient wave field
│   │   └── workspace/              # Mission Control workspace application
│   │       ├── WorkspaceShell.tsx         # Layout shell, top bar, sidebar navigation, reset modals
│   │       └── sections/                  # 8 workspace view modules
│   │           ├── Analysis.tsx           # Repository and folder deterministic analysis view
│   │           ├── ConflictRadar.tsx      # Branch conflict detection view
│   │           ├── ContextBuilder.tsx     # Token-budgeted context packet generator
│   │           ├── Integration.tsx        # Route comparison and compatibility view
│   │           ├── Overview.tsx           # Mission status and project state visualization
│   │           ├── PromptBuilder.tsx      # Chat-first / Direct coding prompt generator
│   │           ├── Repository.tsx         # Repo connect, branch picker, file tree, file preview
│   │           └── Team.tsx               # Member ownership and dependency mapping
│   ├── hooks/
│   │   ├── useSmoothScroll.ts      # Lenis smooth scroll initialization hook
│   │   └── useWorkspaceState.ts    # Centralized state management & localStorage persistence
│   ├── lib/
│   │   ├── api/
│   │   │   └── batonApi.ts         # Typed fetch client mapping to Baton Backend V1 endpoints
│   │   ├── demo/
│   │   │   └── index.ts            # Complete static demo fixtures and mock datasets
│   │   └── utils/
│   │       └── index.ts            # Formatting helpers (cn, formatTimestamp, shortSha, formatNumber, generateId)
│   ├── types/
│   │   └── index.ts                # TypeScript data interfaces and types
│   ├── App.tsx                     # Root application state & page switcher
│   ├── index.css                   # Global styles, fonts, scrollbar, scanlines, responsive cursor rules
│   ├── main.tsx                    # React root entry point
│   └── vite-env.d.ts               # Vite client type definitions
├── eslint.config.js                # ESLint 9 configuration
├── index.html                      # HTML5 entry with preconnects & SEO metadata
├── package.json                    # Dependencies and scripts
├── postcss.config.js               # PostCSS with Tailwind & Autoprefixer
├── tailwind.config.js              # Baton design tokens (colors, fonts, radius, animations)
├── tsconfig.app.json               # App TypeScript config with `@/` path alias
├── tsconfig.json                   # Solution TypeScript reference
├── tsconfig.node.json              # Node TypeScript config
└── vite.config.ts                  # Vite build config with `@/` path alias mapping to `src/`
```

---

## 3. Design System & Visual Specification

Baton implements a high-precision, technical aesthetic inspired by a mission-control server room after dark: pure black canvas, crisp contrast, 4px rectangular containment, electric green accents, warning amber/reds, and monospace technical labels.

### 3.1 Color Palette

All color tokens are configured in `tailwind.config.js` and `src/index.css`:

| Token | Hex Value | Semantic Role |
|---|---|---|
| `baton-black` | `#000000` | Global background canvas |
| `baton-near-black` | `#0a0a0b` | Panels, card containers, headers, sidebars |
| `baton-layer-1` | `#151617` | Active navigation tabs, table row hover highlights |
| `baton-layer-2` | `#242628` | Elevated element surfaces |
| `baton-layer-3` | `#303236` | High-contrast borders |
| `baton-accent` | `#34d59a` | Primary electric green accent, success indicators, CTAs |
| `baton-accent-dim` | `#285d49` | Subdued green borders and secondary badges |
| `baton-warning` | `#ff3621` | Warning alerts, conflict notices, unmatched routes |
| `baton-white` | `#ffffff` | Primary text and major headlines |
| `baton-text-highlight` | `#c9cbcf` | Monospace code paths, active values, high-contrast labels |
| `baton-text-tertiary` | `#94979e` | Secondary body text, timestamps, neutral metadata |
| `baton-text-secondary` | `#797d86` | Inactive navigation links, subtle descriptions |
| `baton-border` | `#303236` | Panel borders, dividers, subtle grid lines |

### 3.2 Typography

- **Primary Sans Font**: `Inter`, system-ui, sans-serif (imported via Google Fonts in `src/index.css` with weights 400 through 900).
- **Technical Monospace Font**: `Geist Mono`, `Fira Code`, `Source Code Pro`, `SF Mono`, `Monaco`, `Cascadia Code`, `monospace`.
- **Typographic Scale**:
  - Hero Headings: `text-5xl` to `text-8xl` (`font-bold`, `tracking-tight`, `leading-[0.95]`).
  - Section Headings: `text-3xl` to `text-5xl` (`font-bold`, `tracking-tight`).
  - Panel Headers / Labels: `font-mono text-[10px]` (`tracking-[0.15em]` or `tracking-[0.3em]`, `uppercase`).
  - Code & Paths: `font-mono text-[11px]` or `text-[12px]`.
  - Body Text: `text-sm` (`leading-relaxed`).

### 3.3 Geometry, Borders, and Radii

- **Cards / Panels / Inputs**: `rounded-baton` (`4px`) with `border border-baton-border` (`#303236`).
- **Action Buttons**: `rounded-full` (pill shape, e.g., `px-5 py-2` or `px-8 py-3`).
- **Status Indicator Dots**: `rounded-full` (`w-1.5 h-1.5` or `w-2 h-2`).
- **Telemetry Lines**: `h-px` or `h-0.5` linear dividers with moving pulse beams.

### 3.4 Shared UI Primitives (`src/components/ui/primitives.tsx`)

1. **`StatusIndicator`**:
   - States: `connected` (green), `fresh` (green), `stale` (grey), `analyzing` (green), `attention` (warning red), `idle` (secondary grey), `matched` (green), `unmatched` (warning red).
   - Features animated opacity pulsing (`[1, 0.4, 1]` over 2s).
2. **`MonoLabel`**:
   - Monospace tracking text with variants: `default` (`#797d86`), `accent` (`#34d59a`), `warning` (`#ff3621`), `dim` (`#94979e`).
3. **`Panel`**:
   - Standard 4px-radius container with dark background (`#0a0a0b`), 1px border (`#303236`), and optional header label strip.
4. **`Button`**:
   - Pill-shaped button supporting `primary` (green fill, black text), `secondary` (dark background with border), and `ghost` (text only). Includes Framer Motion tap feedback (`scale: 0.97`).
5. **`SectionLabel`**:
   - Horizontal decorative green line (`w-8 h-px`) paired with uppercase monospace accent text.
6. **`CopyButton`**:
   - Interactive button with `navigator.clipboard.writeText`, switching to `COPIED` with check icon for 1.5s.
7. **`TelemetryLine`**:
   - 1px divider with an animated green light beam translating horizontally across the container.

---

## 4. Landing Page Architecture & Interactions

The landing page is a single-page marketing and product showcase located at `src/components/landing/LandingPage.tsx`.

### 4.1 Visual & Interactive Elements

- **Lenis Smooth Scrolling**: Initialized via `useSmoothScroll()`, applying smooth easing to mouse wheel events. Automatically disabled when `prefers-reduced-motion` is detected.
- **Ambient Signal Field**: Fullscreen fixed Canvas 2D background (`SignalField.tsx`) simulating 50–80 oscillating vertical data bars with wave interference and mouse proximity reactions.
- **Scanline Effect**: Fixed 2px overlay translating from top to bottom over 8 seconds.
- **Parallax Hero**: The hero section fades and scales down on scroll via Framer Motion's `useScroll` and `useTransform`.
- **Page Transition**: Clicking any workspace entry button triggers a full-screen blackout overlay with a sliding green accent line (400ms duration) before mounting the workspace.

### 4.2 Landing Page Interaction Registry

| Section | Element / Button | Visual Label | Action Performed | Destination | Conditions |
|---|---|---|---|---|---|
| **Header** | Link | `Product` | Smooth scroll anchor | `#problem` | Always |
| **Header** | Link | `Workflow` | Smooth scroll anchor | `#workflow` | Always |
| **Header** | Link | `Why Baton` | Smooth scroll anchor | `#philosophy` | Always |
| **Header** | Link | `Docs` | Smooth scroll anchor | `#workflow` | Visible on `sm+` screens |
| **Header** | Button (Primary) | `Enter Mission Control` | Triggers transition & page switch | Workspace (`App.tsx: page = 'workspace'`) | Always |
| **Hero** | Button (Primary) | `ENTER MISSION CONTROL` | Triggers transition & page switch | Workspace (`App.tsx: page = 'workspace'`) | Always |
| **Hero** | Link (Ghost) | `SEE HOW BATON WORKS` | Smooth scroll anchor | `#workflow` | Always |
| **Problem** | Visual Cards | 6 problem tags | Hover / scroll inspection | In-place | Display only |
| **Baton Loop** | Pipeline Rail | 9-stage sequence | Scroll-triggered sequential activation | In-place | Animated |
| **Context** | Token Meter | Budget progress bar | Animated fill to 41% | In-place | Demonstration |
| **Ownership** | Warning Box | `POSSIBLE OWNERSHIP VIOLATION` | Highlights boundary collision | In-place | Demonstration |
| **Handoff** | Terminal Log | 13-line log sequence | Staggered entrance + blinking cursor | In-place | Animated |
| **Conflict Radar**| Lane visual | Branch lanes convergence | Staggered path lines to `src/api/client.ts` | In-place | Demonstration |
| **Integration** | Route List | Matched/unmatched routes | Shows route comparison matrix | In-place | Demonstration |
| **Final CTA** | Button (Primary) | `ENTER MISSION CONTROL` | Triggers transition & page switch | Workspace (`App.tsx: page = 'workspace'`) | Always |
| **Footer** | Nav items | `GITHUB`, `DOCS`, `PRIVACY` | Text labels | `#` | Static presentation |

---

## 5. Workspace Architecture & Shell Navigation

The Workspace environment provides the mission control interface for inspecting repositories and generating handoff context.

### 5.1 Workspace Shell Layout (`WorkspaceShell.tsx`)

The workspace consists of:
1. **Top Bar (56px / `h-14`)**:
   - Mobile hamburger button (`< 1024px`).
   - Baton logo button (calls `onBackToLanding` to return to marketing page).
   - Demo Mode indicator pill (`Demo Data` button) with a dropdown to trigger the **Clear Demo Data** confirmation modal.
   - Active repository display (`owner/repo` or `No repository`).
   - Active branch display (`BRANCH <name>`).
   - Global status indicator (`CONNECTED` vs `IDLE`).
   - Quick action buttons: **Refresh** (`window.location.reload()`), **Mission Overview** (`setActiveSection('overview')`), **Workspace Settings** (`Reset local workspace` menu).
2. **Collapsible Sidebar (`w-60`)**:
   - Fixed left sidebar on desktop; off-canvas slide-out drawer on mobile/tablet.
   - Organized into 3 functional groups with 8 navigation items.
   - Uses Framer Motion `layoutId="sidebar-active"` for active indicator line transitions.
3. **Main Content Viewport**:
   - Independent vertical scroll area (`overflow-y-auto bg-baton-black`).
   - Smooth entrance animation on section change (`opacity: 0, y: 8` → `opacity: 1, y: 0`).

### 5.2 Sidebar Navigation Structure

| Group | Navigation Item | Section ID | Icon | Purpose | Initial State |
|---|---|---|---|---|---|
| **MISSION CONTROL** | Overview | `overview` | `Activity` | Mission summary, 5 KPI metrics, project state visual | Active by default |
| **MISSION CONTROL** | Repository | `repository` | `GitBranch` | GitHub repository validation, branch list, file tree, preview | Available |
| **MISSION CONTROL** | Team & Ownership | `team` | `Users` | Team member directory, folder ownership, dependencies | Available |
| **MISSION CONTROL** | Analysis | `analysis` | `BarChart3` | Deterministic structural & contract analysis | Available |
| **CONTEXT** | Context Builder | `context` | `FileText` | Focused markdown context generator with token budget | Available |
| **CONTEXT** | Prompt Builder | `prompt` | `Terminal` | Chat-first & Direct prompt generator with Baton starter rules | Available |
| **COORDINATION** | Conflict Radar | `conflicts` | `Radar` | Multi-branch file overlap collision detector | Available |
| **COORDINATION** | Integration | `integration` | `GitMerge` | Dual-branch route comparison and compatibility matrix | Available |

---

## 6. Workspace State & Persistence Model

State is managed by the custom hook `useWorkspaceState` (`src/hooks/useWorkspaceState.ts`).

### 6.1 State Variables & Persistence

| State Property | Type | Default Value | Persisted in `localStorage`? | Description |
|---|---|---|---|---|
| `repoUrl` | `string` | `""` | **YES** | URL of the connected GitHub repository |
| `repo` | `RepoValidation \| null` | `null` | **YES** | Validated repo metadata (owner, repo, default branch, visibility) |
| `selectedBranch` | `string` | `""` | **YES** | Currently active Git branch for file browsing & analysis |
| `selectedFolder` | `string` | `""` | **YES** | Scoped folder path for targeted analysis |
| `members` | `TeamMember[]` | `[]` | **YES** | Team member ownership list |
| `isDemoMode` | `boolean` | `false` | **YES** | Flag determining whether mock fixtures or live API calls are used |
| `githubToken` | `string` | `""` | **NO** (explicitly stripped) | Personal access token (kept in-memory for security) |
| `activeSection` | `WorkspaceSection` | `'ai'` | **YES** | Active sidebar navigation section ID |
| `firstRun` | `boolean` | `true` (if no repo) | **YES** | First-run onboarding indicator |
| `firstRunStep` | `number` | `0` | **YES** | Onboarding step index |
| `resetVersion` | `number` | `0` | **NO** | Re-render key for cleanly re-mounting workspace components |

### 6.2 Storage Key & Security Handling

- **Key**: `baton-workspace-state` in browser `localStorage`.
- **Security Rule**: The `saveState` function explicitly strips `githubToken` before writing to `localStorage`:
  ```typescript
  function saveState(state: WorkspaceState) {
    const { githubToken, ...persistable } = state;
    void githubToken;
    localStorage.setItem(STORAGE_KEY, JSON.stringify(persistable));
  }
  ```

### 6.3 Reset & Clear Mechanisms

The frontend provides two distinct reset mechanisms:
1. **Clear Demo Data Modal** (`WorkspaceShell.tsx: lines 114–150`):
   - Accessible via the `Demo Data` button in the top bar.
   - Opens a modal asking for confirmation to clear all loaded data.
   - Invokes `state.reset()`, clearing memory state, bumping `resetVersion`, and calling `localStorage.removeItem('baton-workspace-state')`.
2. **Reset Local Workspace Action** (`WorkspaceShell.tsx: lines 205–218`):
   - Accessible from the Settings gear icon in the top bar.
   - Clears saved repository and team configurations immediately.

---

## 7. Comprehensive Page-by-Page Inventory

### 7.1 Overview (`Overview.tsx`)
- **Route / Section**: `overview`
- **Purpose**: High-level operational dashboard showing connected repository status, branch, file count, estimated context token weight, and recent project activity.
- **Empty State**: When `!repo && !isDemoMode`, renders **"MISSION CONTROL STANDBY"** with an active telemetry line and a **"CONNECT REPOSITORY"** button that redirects to the `repository` section.
- **Loaded State**:
  - 5 KPI metric cards: `REPOSITORY`, `BRANCH`, `ANALYSIS` (`FRESH`), `FILES` (`84`), `CONTEXT` (`3.2K TOKENS`).
  - `PROJECT STATE` diagram: Visual nodes for Frontend, Backend, and Shared with animated pulse connectors.
  - `RECENT ACTIVITY`: 6 recent operational events (time, event text, status dot).
- **Data Source**: Live state for repo/branch + `DEMO_ACTIVITIES` from `src/lib/demo/index.ts`.

### 7.2 Repository (`Repository.tsx`)
- **Route / Section**: `repository`
- **Purpose**: Connect to GitHub, validate repository accessibility, inspect branches, browse file trees, and preview file source code.
- **Input Controls**:
  - `Repository URL` input field (`https://github.com/owner/repo`).
  - `GitHub Token (optional)` password field for private repos or rate limit elevation.
  - `VALIDATE REPOSITORY` button with spinner.
- **Demo Shortcut**: Typing `baton/demo-project` or validating in Demo Mode immediately succeeds and loads `DEMO_BRANCHES`.
- **Live API Integration**:
  - Calls `batonApi.validateRepository(urlInput, tokenInput)`.
  - Calls `batonApi.getBranches(owner, repo, tokenInput)`.
  - Selecting a branch calls `batonApi.getTree(owner, repo, branch, '', tokenInput)`.
- **Components**:
  - 4 metadata cards: Owner, Repository, Default Branch, Visibility.
  - Branch selection list with short SHA tags.
  - Interactive collapsible File Tree browser with folder toggle (`ChevronRight`) and file selection.
  - File Preview panel displaying monospace file contents.

### 7.3 Team & Ownership (`Team.tsx`)
- **Route / Section**: `team`
- **Purpose**: Define and visualize team ownership boundaries, branch assignments, owned folder paths, dependencies, and handoff jobs.
- **Actions**:
  - `ADD MEMBER` button (toggles 8-field entry form).
  - `LOAD DEMO TEAM` button (loads `DEMO_MEMBERS` into state).
- **Form Fields**: Member Name, GitHub Username, Branch, Role, Folders (comma-separated), Job, Depends On (comma-separated), Provides To (comma-separated).
- **Card Display**: Role badge, active branch, owned folders list with folder icons, dependency tags, and delete trash icon.
- **Empty State**: Centered prompt with users icon when no members exist.

### 7.4 Analysis (`Analysis.tsx`)
- **Route / Section**: `analysis`
- **Purpose**: Deterministic inspection of repository structure, routes, types, mock fixtures, environment variables, handoff markers, and contracts.
- **Controls**: Scoped folder input (e.g. `/frontend`) + `ANALYZE PROJECT` / `RE-ANALYZE` button.
- **States**:
  - `idle`: "NO ANALYSIS YET" panel.
  - `loading`: Step-by-step progress telemetry (reading file tree, detecting stack, scanning types).
  - `partial`: Warning banner highlighting skipped files (e.g., large assets) or analysis warnings.
  - `error`: Warning card with error message and `RETRY` button.
  - `success`: 4 metadata headers (Branch, Commit SHA, Generated timestamp, Files Analyzed) + 10 categorized analysis grids + Handoffs panel + Complete file list.
- **10 Categorized Grids**: `STACK`, `LANGUAGES`, `IMPORTANT FILES`, `ROUTES`, `API CALLS`, `TYPES`, `MOCK DATA`, `ENVIRONMENT VARIABLES`, `SHARED FILES`, `STRAY FILES`.

### 7.5 Context Builder (`ContextBuilder.tsx`)
- **Route / Section**: `context`
- **Purpose**: Generate a focused, token-budgeted Markdown context packet ready for injection into AI coding assistants.
- **Configuration Inputs**: Folder input, Purpose/Task textarea, Target Teammate input, Budget token threshold (default: 8,000).
- **Outputs & Actions**:
  - `GENERATE CONTEXT` button with progress telemetry.
  - Estimated token meter bar with percentage calculation.
  - Omitted files warning if budget is exceeded.
  - Markdown output panel with `COPY` button, `DOWNLOAD` button (`context.md`), and `REFRESH` button.
- **Data Source**: In demo mode uses `DEMO_CONTEXT_MARKDOWN`; in live mode calls `batonApi.generateContext`.

### 7.6 Prompt Builder (`PromptBuilder.tsx`)
- **Route / Section**: `prompt`
- **Purpose**: Construct standardized coding prompts incorporating Baton context, ownership constraints, and coding agent guidelines.
- **Modes**:
  - `CHAT-FIRST`: Generates planning instructions for reasoning LLMs (ChatGPT / Claude) before implementation.
  - `DIRECT`: Generates direct execution prompts for coding agents (Antigravity / Cursor).
- **Inputs**: Task textarea, Context textarea, Constraints textarea, Ownership input, Target Teammate input.
- **Outputs & Actions**:
  - `BUILD PROMPT` button, `RESET` button.
  - Output preview with `COPY PROMPT` button and `DOWNLOAD` button (`prompt.md`).
  - Automatically appends standard Baton starter rules (ownership boundaries, exact contract compliance, required handoff summary).

### 7.7 Conflict Radar (`ConflictRadar.tsx`)
- **Route / Section**: `conflicts`
- **Purpose**: Scan multiple Git branches to detect overlapping modifications to shared files before merge conflicts occur.
- **Inputs**: Multi-line textarea for branch names (e.g. `member/alex-ui\nmember/sam-api`).
- **Actions**: `SCAN FOR CONFLICTS` button (requires ≥ 2 branches).
- **Visuals**:
  - Status banner (`NO CONFLICTS DETECTED` vs `N POSSIBLE SHARED-FILE CONFLICTS`).
  - Branch Lanes visualization showing individual files modified in each branch lane with warning pill tags on colliding paths.
  - Detailed conflict cards listing affected path, colliding branches, and coordination advisory.

### 7.8 Integration (`Integration.tsx`)
- **Route / Section**: `integration`
- **Purpose**: Cross-reference frontend API calls against backend route handlers across different branches.
- **Inputs**: `Frontend Branch` input (e.g. `member/maya-ui`) and `Backend Branch` input (e.g. `member/arjun-api`).
- **Actions**: `CHECK INTEGRATION` button.
- **Visuals & Status**:
  - Status banner: `INTEGRATION STATUS — READY` (green) vs `INTEGRATION STATUS — ATTENTION REQUIRED` (red).
  - Side-by-side comparison tables: `FRONTEND BRANCH — API CALLS` vs `BACKEND BRANCH — ROUTES`.
  - Route status badges: `MATCH` (green) vs `UNMATCHED` (warning red).
  - Unmatched Endpoints summary card detailing missing routes and orphan endpoints.

---

## 8. Interactive Control & Button Registry

| Section / Component | Element | Label / Icon | Expected Action | Actual Code Behavior | API Call Invoked | Navigation / State Update |
|---|---|---|---|---|---|---|
| `LandingHeader` | Link | `Product` | Scroll to problem | Native anchor `#problem` | None | None |
| `LandingHeader` | Link | `Workflow` | Scroll to workflow | Native anchor `#workflow` | None | None |
| `LandingHeader` | Link | `Why Baton` | Scroll to philosophy | Native anchor `#philosophy` | None | None |
| `LandingHeader` | Button | `Enter Mission Control` | Enter workspace | Sets transition overlay; enters workspace | None | `setPage('workspace')` |
| `HeroSection` | Button | `ENTER MISSION CONTROL` | Enter workspace | Sets transition overlay; enters workspace | None | `setPage('workspace')` |
| `HeroSection` | Link | `SEE HOW BATON WORKS` | Scroll to workflow | Native anchor `#workflow` | None | None |
| `FinalCTASection` | Button | `ENTER MISSION CONTROL` | Enter workspace | Sets transition overlay; enters workspace | None | `setPage('workspace')` |
| `WorkspaceShell` | Button | `BATON` (Logo) | Return to landing | Calls `onBackToLanding` | None | `setPage('landing')` |
| `WorkspaceShell` | Button | `Demo Data` | Open demo dropdown | Toggles `demoMenuOpen` | None | Local state |
| `WorkspaceShell` | Button | `Clear Demo Data` | Open modal | Opens `clearDemoOpen` modal | None | Local state |
| `WorkspaceShell` | Button (Modal)| `CLEAR DEMO DATA` | Reset workspace | Calls `state.reset()` | None | State wiped, version bumped |
| `WorkspaceShell` | Button | `Refresh` (`RefreshCw`) | Reload browser | Invokes `window.location.reload()` | None | Full page reload |
| `WorkspaceShell` | Button | `Overview` (`Activity`) | Go to overview | Calls `state.setActiveSection('overview')` | None | `activeSection = 'overview'` |
| `WorkspaceShell` | Button | `Settings` (`Settings`)| Open settings menu | Toggles `settingsOpen` | None | Local state |
| `WorkspaceShell` | Button | `Reset local workspace`| Reset workspace | Calls `state.reset()` | None | State wiped, version bumped |
| `WorkspaceShell` | Sidebar Items | 9 Nav buttons | Switch active view | Calls `state.setActiveSection(id)` | None | `activeSection = id` |
| `Overview` | Button | `CONNECT REPOSITORY` | Go to repo section | Calls `onConnectRepo` | None | `activeSection = 'repository'` |
| `Repository` | Button | `VALIDATE REPOSITORY` | Validate GitHub URL | Validates repo and loads branches | `POST /api/v1/github/validate-repository`<br>`GET /api/v1/github/branches` | Sets `state.repo`, `state.repoUrl` |
| `Repository` | Button List | Branch rows | Select active branch | Fetches branch file tree | `GET /api/v1/github/tree` | Sets `state.selectedBranch` |
| `Repository` | Tree Items | Directory rows | Expand/collapse | Toggles `expandedDirs` set | None | Local state |
| `Repository` | Tree Items | File rows | View file content | In demo mode, displays fixture code | `GET /api/v1/github/file` (demo only) | `selectedFile` state |
| `Team` | Button | `ADD MEMBER` | Toggle form | Toggles `showForm` | None | Local state |
| `Team` | Button | `LOAD DEMO TEAM` | Load demo members | Loads `DEMO_MEMBERS` into state | None | `state.members = DEMO_MEMBERS` |
| `Team` | Button | `SAVE MEMBER` | Add team member | Calls `state.addMember(member)` | None | Appends to `state.members` |
| `Team` | Button | `Trash` (`Trash2`) | Remove member | Calls `state.removeMember(id)` | None | Removes from `state.members` |
| `Analysis` | Button | `ANALYZE PROJECT` | Run code analysis | Runs folder or repo analysis | `POST /api/v1/analysis/folder` or `repository` | Sets `analysis` state |
| `ContextBuilder` | Button | `GENERATE CONTEXT` | Build context packet | Generates markdown context | `POST /api/v1/context` | Sets `markdown`, `tokens`, `result` |
| `ContextBuilder` | Button | `COPY` | Copy markdown | Copies to system clipboard | None | Clipboard API |
| `ContextBuilder` | Button | `DOWNLOAD` | Download markdown | Triggers download of `context.md` | None | Blob download |
| `ContextBuilder` | Button | `REFRESH` | Re-generate context | Re-invokes `handleGenerate` | `POST /api/v1/context` | Re-fetches context |
| `PromptBuilder` | Button | `CHAT-FIRST` / `DIRECT`| Toggle mode | Toggles `mode` | None | `mode` state |
| `PromptBuilder` | Button | `BUILD PROMPT` | Assemble prompt | Generates formatted prompt | `POST /api/v1/prompt` | Sets `generatedPrompt` |
| `PromptBuilder` | Button | `RESET` | Clear inputs | Clears form & outputs | None | Local state reset |
| `PromptBuilder` | Button | `COPY PROMPT` | Copy prompt text | Copies to system clipboard | None | Clipboard API |
| `PromptBuilder` | Button | `DOWNLOAD` | Download prompt | Triggers download of `prompt.md` | None | Blob download |
| `ConflictRadar` | Button | `SCAN FOR CONFLICTS` | Scan branch files | Fetches trees & checks overlaps | `POST /api/v1/conflicts` | Sets `result` state |
| `Integration` | Button | `CHECK INTEGRATION` | Compare routes | Checks route compatibility | `POST /api/v1/integration` | Sets `result` state |

---

## 9. Demo Data System & Fixture Inventory

All mock and demonstration datasets reside in `src/lib/demo/index.ts`.

### 9.1 Fixture Inventory

| Fixture Constant | Target Section(s) | Entity Type | Summary of Data Contents |
|---|---|---|---|
| `DEMO_MEMBERS` | `Team.tsx`, `useWorkspaceState.ts` | `TeamMember[]` | 2 members: Maya (Frontend Lead, `member/maya-ui`, `/frontend`) and Arjun (Backend Lead, `member/arjun-api`, `/backend`). |
| `DEMO_ANALYSIS` | `Analysis.tsx` | `AnalysisResult` | Stack (React, TS, Vite, Tailwind), 9 file trees, 3 API calls (`/api/projects`, `/api/auth`, `/api/tasks`), 4 types, 1 skipped file warning. |
| `DEMO_CONFLICTS` | `ConflictRadar.tsx` | `ConflictResult` | 1 detected conflict on `src/api/client.ts` between `member/alex-ui` and `member/sam-api`. |
| `DEMO_INTEGRATION`| `Integration.tsx` | `IntegrationResult` | 3 frontend routes vs 2 backend routes; `GET /api/tasks` unmatched; `compatible: false`. |
| `DEMO_ACTIVITIES` | `Overview.tsx` | Array | 6 activity timeline entries (analysis, route detected, overlap detected, context generated). |
| `DEMO_BRANCHES` | `Repository.tsx` | `Branch[]` | 6 Git branches (`main`, `member/maya-ui`, `member/arjun-api`, `member/alex-ui`, `member/sam-api`, `feature/auth`). |
| `DEMO_TREE` | `Repository.tsx` | `TreeItem[]` | 25 file and directory nodes spanning frontend, backend, contracts, and docs. |
| `DEMO_FILE_CONTENT`| `Repository.tsx` | `string` | 23-line TypeScript API client implementation with `fetchProjects`, `login`, and `fetchTasks`. |
| `DEMO_CONTEXT_MARKDOWN`| `ContextBuilder.tsx` | `string` | Complete 67-line Baton structured context packet formatted in Markdown. |

### 9.2 Entering, Operating, and Exiting Demo Mode

- **Entering Demo Mode**:
  - Automatically triggered when typing `baton/demo-project` in the repository connect form.
  - Triggered by clicking `LOAD DEMO TEAM` in the Team section.
  - Can be pre-loaded by setting `isDemoMode: true` in state.
- **Operating in Demo Mode**:
  - API calls are bypassed; sections use simulated `setTimeout` delays (600ms–1500ms) to mirror asynchronous backend telemetry.
- **Exiting Demo Mode**:
  - Click `Demo Data` in the top bar → click `Clear Demo Data` → confirm in the modal dialog.
  - Or click the Settings gear icon → click `Reset local workspace`.

---

## 10. Backend API Integration & Contract Status

The frontend API client is located at `src/lib/api/batonApi.ts`.

### 10.1 Environment Variables & Headers

- **API Base URL**: `import.meta.env.VITE_BATON_API_URL || 'http://localhost:8000'`
- **Baton Access Key**: `import.meta.env.VITE_BATON_ACCESS_KEY || ''` (sent via `X-Baton-Key` header)
- **GitHub Token**: Passed dynamically from state or user input (sent via `X-GitHub-Token` header)

### 10.2 Endpoint Integration Matrix

| Frontend Client Method | HTTP | Endpoint Path | Request Body / Params | Status vs Backend V1 | Notes & Discrepancies |
|---|---|---|---|---|---|
| `checkHealth()` | `GET` | `/health` | None | **IMPLEMENTED** | Validates backend availability |
| `validateRepository(url, token)` | `POST` | `/api/v1/github/validate-repository` | `{ repo_url: string }` | **IMPLEMENTED** | Validates owner, repo, and visibility |
| `getBranches(owner, repo, token)` | `GET` | `/api/v1/github/branches` | Query: `owner`, `repo` | **IMPLEMENTED** | Returns list of branches and commit SHAs |
| `getTree(owner, repo, branch, path, token)` | `GET` | `/api/v1/github/tree` | Query: `owner`, `repo`, `branch`, `path` | **IMPLEMENTED** | Returns array of `TreeItem` objects |
| `getFile(owner, repo, branch, path, token)` | `GET` | `/api/v1/github/file` | Query: `owner`, `repo`, `branch`, `path` | **PARTIALLY WIRED** | Method exists in `batonApi.ts`; `Repository.tsx` currently only invokes it in demo mode |
| `analyzeFolder(owner, repo, branch, folder, token)` | `POST` | `/api/v1/analysis/folder` | `{ owner, repo, branch, folder }` | **IMPLEMENTED** | Deterministic folder pattern analysis |
| `analyzeRepository(owner, repo, branch, token)` | `POST` | `/api/v1/analysis/repository` | `{ owner, repo, branch }` | **IMPLEMENTED** | Deterministic repository-wide analysis |
| `generateContext(owner, repo, branch, folder, includeMarkdown, token)` | `POST` | `/api/v1/context` | `{ owner, repo, branch, folder, include_markdown }` | **IMPLEMENTED** | Generates token-budgeted Markdown context |
| `generatePrompt(task, context, constraints, token)` | `POST` | `/api/v1/prompt` | `{ task, context, constraints }` | **IMPLEMENTED** | Formulates structured prompt |
| `detectConflicts(branches, files, token)` | `POST` | `/api/v1/conflicts` | `{ files, branches }` | **IMPLEMENTED** | Frontend passes `Record<string, string[]>` of files per branch |
| `checkIntegration(owner, repo, branch, frontendBranch, backendBranch, token)` | `POST` | `/api/v1/integration` | `{ owner, repo, branch, frontend_branch, backend_branch }` | **IMPLEMENTED** | Compares routes across branches |

---

## 11. Loading, Error, and Empty State UX Matrix

| View / Action | Trigger Condition | Loading UI | Error UI & Recovery | Empty State UI |
|---|---|---|---|---|
| **Overview** | Initial mount | Instant render | None | "MISSION CONTROL STANDBY" + `CONNECT REPOSITORY` button |
| **Repository Validation** | Click `VALIDATE REPOSITORY` | Spinner on button + `TelemetryLine` | Red error text below button | Connect form with empty inputs |
| **File Tree Browser** | Branch selection | `Loader2` spinner + "Loading tree..." | Error string in parent panel | Tree list or empty directory |
| **File Preview** | File selection | None (synchronous) | None | "Select a file to preview" centered label |
| **Team Management** | Initial mount | Instant render | None | "No team members configured" + `LOAD DEMO TEAM` |
| **Analysis** | Click `ANALYZE PROJECT` | `Loader2` spinner + telemetry line + 4-step checklist | Red warning banner + `RETRY` button | "NO ANALYSIS YET" panel |
| **Context Generation** | Click `GENERATE CONTEXT` | `Loader2` spinner + telemetry line + 5-step checklist | Red warning banner + `RETRY` button | "NO CONTEXT GENERATED" panel |
| **Prompt Builder** | Click `BUILD PROMPT` | `Loader2` spinner + `TelemetryLine` | Red warning banner + `RETRY` button | "NO PROMPT GENERATED" panel |
| **Conflict Radar** | Click `SCAN FOR CONFLICTS` | Pulsing `Radar` icon + `TelemetryLine` | Red warning banner + `RETRY` button | "NO SCAN PERFORMED" panel |
| **Integration Check** | Click `CHECK INTEGRATION` | `GitMerge` icon + telemetry line + 3-step checklist | Red warning banner + `RETRY` button | "NO INTEGRATION CHECK PERFORMED" panel |

---

## 12. Animation, Motion, and Scroll Subsystems

1. **Lenis Smooth Scroll**: Configured in `useSmoothScroll.ts` with `duration: 1.2` and power-10 exponential easing. Automatically bypassed when `prefers-reduced-motion: reduce` is detected.
2. **SignalField Canvas**: HTML5 Canvas rendering in `SignalField.tsx`. Responsive to `devicePixelRatio`, updates dynamically on window resize, renders sine wave bar modulations, and adds interactive orbital particles near the mouse cursor.
3. **Custom Cursor**: Dual-element pointer (`CustomCursor.tsx`). Features an inner 6px white dot following the exact cursor and an outer 24px trailing ring with linear interpolation (`0.15` factor). Hovering over interactive targets (`a, button, input, textarea, select, [role="button"], [data-cursor="interactive"]`) expands and illuminates the ring with the Baton green accent.
4. **Scanline Animation**: 2px horizontal light band translating down the screen via CSS keyframes (`scanline 8s linear infinite`).
5. **Page Transitions**: Full-screen fade and scale effects via Framer Motion's `AnimatePresence mode="wait"`.

---

## 13. Responsive Design & Accessibility Audit

### 13.1 Responsive Breakpoint Behaviors

- **Desktop (≥ 1024px / `lg`)**:
  - Permanent fixed 240px (`w-60`) left sidebar.
  - Multi-column metric grids (`grid-cols-4`, `grid-cols-5`).
  - Side-by-side split layouts in Context Builder, Prompt Builder, Repository, and Integration.
- **Tablet (768px – 1023px / `md`)**:
  - Two-column metric grids.
  - Off-canvas sidebar hidden by default; toggled via header hamburger button.
- **Mobile (< 768px / `sm`)**:
  - Off-canvas sidebar with full-screen backdrop overlay.
  - Single-column stacked layouts for all panels, comparison views, and forms.
  - Top bar repository details collapse down to logo and action icons.
  - Custom cursor automatically hides on touch devices via `@media (pointer: coarse)` in `src/index.css`.

### 13.2 Accessibility Observations & Gaps

- **Reduced Motion**: Full compliance in `src/index.css` (`@media (prefers-reduced-motion: reduce)` disables animations, forces `cursor: auto`, and disables scanlines).
- **ARIA & Modal Dialogs**: `clearDemoOpen` modal includes `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, and `Escape` key listener.
- **Form Labels**: Most form controls use `<label>` with monospace uppercase titles; some inputs rely on `placeholder` attributes.
- **Button Roles**: Interactive elements utilize semantic `<button>` elements with `type="button"` or `type="submit"`.

---

## 14. Confirmed Technical Debt & Implementation Observations

During full codebase inspection, the following exact observations and technical debt items were confirmed:

### 14.1 Low / Technical Debt
1. **Unused Package**: `@supabase/supabase-js` is listed in `package.json` dependencies, but is never imported or referenced in any source file.
2. **File Content Fetch in Live Repository**: In `Repository.tsx` line 81, `handleFileClick` only updates `selectedFile` if `state.isDemoMode` is true. In non-demo mode, clicking a file blob does not yet trigger `batonApi.getFile`.
3. **Conflict Radar Live Lane Tags**: In `ConflictRadar.tsx` line 80, `laneFiles` is assigned from `state.isDemoMode ? DEMO_LANE_FILES : {}`. When running against a live repository, the branch lane tags will not render file pills even though conflict detection API calls succeed.
4. **Lenis Scroll Scope**: Lenis is initialized inside `LandingPage.tsx`, but is not active inside `WorkspaceShell.tsx` (the workspace relies on native browser container scrolling, which is appropriate for data-heavy views).

---

## 15. Frontend ↔ Backend Responsibility Boundary

To prevent logic duplication or misplacement in future development:

```text
┌────────────────────────────────────────────────────────┐
│                     FRONTEND OWNS                      │
├────────────────────────────────────────────────────────┤
│ • UI rendering, typography, styling, and design system │
│ • Navigation, view switching, and page transitions     │
│ • Local state management & localStorage persistence    │
│ • Demo mode state, mock fixture injection, and resets  │
│ • Input collection, form validation, and copy/download │
│ • Invoking API endpoints and displaying error/loading  │
└────────────────────────────────────────────────────────┘
                           ↕ HTTP / JSON
┌────────────────────────────────────────────────────────┐
│                     BACKEND OWNS                       │
├────────────────────────────────────────────────────────┤
│ • Direct communication with GitHub REST API            │
│ • Token resolution & rate limit management             │
│ • Deterministic AST/Regex pattern analysis             │
│ • Stack, language, route, type, and mock detection     │
│ • Markdown context generation & token budget trimming  │
│ • Prompt assembly and starter rule standardization     │
│ • Branch file collision analysis & route comparison    │
└────────────────────────────────────────────────────────┘
```

---

## 16. Future AI Agent Handoff Rules

Any AI coding assistant modifying the Baton repository must strictly follow these rules:

1. **Consult Documentation First**: Always read `FRONTEND_CONTEXT.md` for frontend work and `baton-backend-v1/BACKEND_CONTEXT.md` for backend work before proposing changes.
2. **Preserve the Visual Aesthetic**: Do not replace custom Tailwind tokens, monochromatic palette, 4px border radius, or monospace styling with generic frameworks or component libraries.
3. **Respect State Architecture**: Do not introduce redundant state stores (e.g. Redux, Zustand). All workspace state must flow through `useWorkspaceState`.
4. **Do Not Fake Real APIs**: When integrating live features, call the real endpoints defined in `src/lib/api/batonApi.ts`. Do not embed synthetic mocks inside production API client methods.
5. **Maintain Demo Mode Parity**: Any new feature added to the workspace must have a corresponding mock fixture in `src/lib/demo/index.ts` so that Demo Mode remains completely functional offline.
6. **No Token Persistence**: Never store GitHub Personal Access Tokens in `localStorage`. Keep tokens strictly in-memory during active sessions.
7. **Smallest Necessary Surface**: Patch only the specific component or hook required for the task. Do not perform wholesale refactors.
8. **Verify Before Declaring Complete**: Always run TypeScript typechecks (`npm run typecheck` or `tsc --noEmit`) before completing frontend tasks.


## 17. Part 3 ? Repository AI Workspace

This section supersedes earlier descriptions of the initial workspace view, provider behavior and credential persistence. Existing landing, repository, team, analysis, context, prompt, conflict and integration screens remain available. The default workspace section is now `ai`, loaded lazily to keep the initial bundle smaller.

### Interface

`AIWorkspace.tsx` extends the existing React/TypeScript/Tailwind 3 stack. Its local stylesheet uses quiet charcoal/green surfaces, Geist typography, a central conversation, a restrained context bar and an optional right evidence/artifact/branch panel. No framework migration was made. The existing landing cursor remains confined to the landing page; workspace interaction uses the native cursor. Branded favicon/description replace starter placeholders.

The conversation supports multi-turn questions, canonical Markdown evidence, source references, typed investigation actions, copy/export, new chat, and stop-waiting behavior. Suggestions use actual snapshot availability and do not create demo AI replies. Shift+Enter adds a newline; Enter submits. React Markdown skips raw HTML, suppresses repository-supplied images and renders links as text, avoiding automatic remote content or executable markup.

The evidence panel shows exact repository/branch/commit, analysis timestamp, collection counts, completeness and all omission categories. Ownership/protection/cross-boundary files are reviewable. Artifact types include repository context, developer handoff, PRD evidence draft, implementation plan, review briefing and coding prompt. Preview supports copy/download, focus trapping and Escape; artifacts remain associated with their snapshot identity. Branch review shows inventory/blob/contract differences and protected changes and can export the comparison. Source/hash unknowns remain explicit.

### Scope and state safety

The current branch dropdown uses GitHub branch names; each request includes repository/folder and the inspected commit where appropriate. Team selection maps name/role/job/folders/do_not_touch/team_scope into the existing backend MemberContext. Team creation now exposes protection and team scopes. Additional task/constraints/protection are explicitly applied in scope settings; editing a draft does not trigger a request on each keystroke. Ownership is never inferred from membership alone: only supplied folders establish candidate modification scope.

Branch/folder/auth/applied-scope changes clear conversation IDs, messages, artifacts and comparison output and load a new authorized briefing. Applied role/duties remain when changing only the branch; changing repository resets the component. Async epoch checks prevent old responses from crossing scope changes. Stop aborts browser waiting and clears the conversation handle; server cancellation/quota refund is not promised. Conversations/artifacts are kept in component memory, not localStorage/sessionStorage; navigating away or reloading starts fresh client state. Server conversation storage is separately bounded and transient.

`useWorkspaceState` stores repository/team configuration in `baton-workspace-state`. It strips both `githubToken` and `batonAccessKey` and redacts recognizable credentials/user strings before persistence. Neither credential is restored from storage. The operator access setter updates the in-memory API client before requests resume, so there is no stale-key request race. Full reset clears both memory credentials; repository changes preserve the current GitHub token as before. The public Vite operator-key binding has been removed. Only `VITE_BATON_API_URL` is frontend configuration; provider credentials belong solely to the backend. API error details are no longer printed to the console.

### Availability and states

AI workspace requires an actual authorized snapshot and deliberately does not use the legacy demo fixture as live AI evidence. No repository shows a connect action. Missing/stale snapshots show the explicit refresh-required message. **Refresh analysis** is the only workspace action invoking repository/folder analysis. Provider-unconfigured state disables sending and explains that context/artifact/branch tools remain available. Provider/auth/quota/invalid-evidence errors are inline and retryable by the user; no response is fabricated. Small context budgets are rejected rather than treated as complete.

Mobile navigation is hidden/inaccessible while closed, opens from a labeled button, closes with Escape, and has a backdrop. The evidence panel can be hidden to prioritize the composer. Controls have keyboard focus states, long evidence paths wrap, and reduced-motion preferences are respected.

### API and validation

`batonApi` adds `/api/v1/workspace/inspect`, `/chat`, `/artifacts`, `/compare` with typed WorkspaceRequest/inspection/chat/artifact/comparison responses. The browser communicates only with Baton. No provider SDK, endpoint or provider credential binding exists in frontend source. The sole new UI dependency is `react-markdown` 10.

Run `npm.cmd run typecheck`, `npm.cmd run lint`, and `npm.cmd run build`. Browser regression checks are in `tests/workspace.e2e.cjs`. First generate fixture responses from the backend using `python -B -m tests.export_workspace_fixtures`, start a local Vite preview, and run the browser script with Playwright installed or `BATON_PLAYWRIGHT_PATH` pointing to the bundled package and `BATON_BROWSER_PATH` to a browser executable. Optional `BATON_PREVIEW_URL` changes the preview URL. Fixture/provider responses are test-only network mocks produced through the actual canonical/context/workspace services; production has no mock AI fallback. Screenshots and fixture JSON live in ignored `.test-output`, not repository source.
