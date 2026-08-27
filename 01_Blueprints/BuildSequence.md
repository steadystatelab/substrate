Friday, 14 August 2026 - 2:13 PM BST

```markdown
# SUBSTRATE - Core Build Sequence & Technical Strategy
**Document Classification:** Source of Truth / Strategy[cite: 1]  
**Last Updated:** Friday, 14 August 2026[cite: 1]  

---

## 1. Architectural Principles (The Constraints)
* **Local-First Privacy:** Document ingestion, state evaluation, and raw telemetry stay strictly on local hardware.[cite: 1] Zero external calls without passing through the Gateway.[cite: 1]
* **Low-Footprint Runtime:** Optimised for constrained hardware (<500 MB RAM baseline, <1 GB storage).[cite: 1]
* **Polyglot Blast-Radius Isolation:** Inter-process communication (IPC) limited to plain-text JSON payloads over standard I/O (`stdin`/`stdout`) or local Unix domain sockets.[cite: 1]
* **Asynchronous Delegation:** Mechanical coding and repetitive unit test scaffolding are delegated to asynchronous agents (e.g., Jules) using strict, bounded briefs.[cite: 1]

---

## 2. Sequential Build Pipeline


```

+-------------------------------------------------------------+
| Step 1: Local Telemetry Foundation (SQLite Baseline)        |
+-------------------------------------------------------------+
|
v
+-------------------------------------------------------------+
| Step 2: State Evaluator & Blank-Mind Task Selector          |
+-------------------------------------------------------------+
|
v
+-------------------------------------------------------------+
| Step 3: Mechanical Nudge & Interruption Sequence            |
+-------------------------------------------------------------+
|
v
+-------------------------------------------------------------+
| Step 4: Hardened Gateway & Anonymised Cloud Inference       |
+-------------------------------------------------------------+
|
v
+-------------------------------------------------------------+
| Step 5: Intent Ingestion & High-Level Strategy Sessions     |
+-------------------------------------------------------------+

```

---

### Step 1: Local Telemetry Foundation
* **Structural Purpose:** Establish an uncorrupted, local-only baseline of user activity and system state without cloud dependencies.[cite: 1]
* **Implementation Actions:**
  * Import legacy Antigravity telemetry scripts into `/legacy_telemetry` or `/prototypes`.[cite: 1]
  * Refactor scripts into a standalone local daemon.[cite: 1]
  * Log raw local metrics (active window title, idle timestamps, session durations) directly to an unencrypted local SQLite database.[cite: 1]
* **Exit Criteria:** Daemon runs continuously with zero network activity and sub-50 MB RAM consumption.[cite: 1]

---

### Step 2: State Evaluator & Blank-Mind Task Selector
* **Structural Purpose:** Provide deterministic detection of executive drift and serve an immediate decision scaffold when working memory/initiation drops.[cite: 1]
* **Implementation Actions:**
  * Evaluate local telemetry streams for drift patterns (e.g., rapid window switching, prolonged unproductive idle periods).[cite: 1]
  * Build the local Task Selector: reads a static, priority-ranked local Markdown checklist or SQLite task table.[cite: 1]
  * When triggered (or when blank-mind state is flagged), present **exactly one** concrete, low-friction micro-task rather than an open-ended list.[cite: 1]
* **Exit Criteria:** System can output a single actionable next step via CLI/minimal UI without requiring network inference.[cite: 1]

---

### Step 3: Mechanical Nudge & Interruption Sequence
* **Structural Purpose:** Non-punitive, gentle mechanical redirection to disrupt executive paralysis and time blindness.[cite: 1]
* **Implementation Actions:**
  * Define tiered intervention levels:[cite: 1]
    1. *Level 1 (Subtle):* Soft audio tone / unobtrusive system tray indicator.[cite: 1]
    2. *Level 2 (Active):* Minimal non-modal desktop prompt displaying the current active focus block.[cite: 1]
    3. *Level 3 (Reset):* Mandatory micro-break / screen dimming overlay.[cite: 1]
  * Connect triggers directly to Step 2 State Evaluator output.[cite: 1]
* **Exit Criteria:** Configurable interval triggers that can be snoozed or acknowledged with a single keystroke.[cite: 1]

---

### Step 4: Hardened Gateway & Anonymised Cloud Inference
* **Structural Purpose:** Secure perimeter allowing cloud LLM reasoning while preventing data leakage of personal identifiers or raw logs.[cite: 1]
* **Implementation Actions:**
  * Construct a local sanitisation proxy/broker.[cite: 1]
  * Deterministic PII scrubbing (paths, usernames, project pseudonyms, health descriptors).[cite: 1]
  * Encapsulate outbound payload into a generic, abstract task prompt serialised as standard JSON over HTTPS.[cite: 1]
* **Exit Criteria:** All outbound packets cryptographically audited to guarantee zero unmasked local paths or raw telemetry transmission.[cite: 1]

---

### Step 5: Intent Ingestion & Strategy Sessions
* **Structural Purpose:** Synthesise long-term goals into atomic tasks and integrate them into daily pacing loops.[cite: 1]
* **Implementation Actions:**
  * Connect the anonymised cloud proxy to daily intake workflows (morning planning / evening reviews).[cite: 1]
  * Ingest unstructured strategy brain-dumps and run an automated Task Atomizer pipeline.[cite: 1]
  * Output atomised micro-beats back into the Step 2 Task Selector local database.[cite: 1]
* **Exit Criteria:** Full end-to-end loop operating from conversational intent capture down to local step execution.[cite: 1]

---

## 3. Immediate Next Actions
1. **Repository Clean-up:** Commit legacy Antigravity telemetry scripts into the Substrate Git repository under `/legacy_telemetry`.[cite: 1]
2. **Scaffold Brief:** Prepare the bounded brief for Jules to refactor the telemetry scripts into a clean SQLite logging daemon.[cite: 1]

``` 