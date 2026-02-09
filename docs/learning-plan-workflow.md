# Learning Plan: Workflow & User Behavior

This doc explains how learning plans are **generated**, how the **API and UI** work, and how **users are meant to use** them. It also calls out likely failure points when "something isn't working."

---

## 1. How learning plans are generated

### Data source

- Plans are built from **your content** in the app.
- Content comes from **user_materials** (processed uploads) joined with **content_items** (title, topics, word_count, etc.).
- If you have **no processed materials** for your `user_id`, generation will fail with a message like *"No content available to generate plans from"* or *"No plans could be generated. Make sure you have content uploaded."*

### Generation flow

1. **User** goes to **Learning Plan** page (`/plan`) and clicks **"Generate Suggested Plans"**.
2. **Frontend** calls:
   - `POST /api/v1/learning-plans/generate-suggested?user_id=...&context_mode=growth&max_plans=3`
3. **Gateway** (`gateway/app/api/v1/learning_plans.py`):
   - Calls the **Planner Agent** (A2A) with a message like: *"Call the generate_learning_plan tool with user_id=..., context_mode=growth, max_plans=3. Return the plans result."*
4. **Planner Agent** (`agents/planner/agent.py` + `agents/planner/tools.py`):
   - Runs **generate_learning_plan** tool, which:
     - Loads **user profile goals** (optional).
     - Gets **prioritized content** via **get_adaptive_priority** (from `user_materials` + `content_items`, status `PROCESSED`).
     - If **no content** → returns `{"status": "error", "error": "No content available to generate plans from"}`.
     - Runs **semantic clustering** on that content.
     - Sends a **prompt + content summary** to the **LLM** (e.g. Gemini) to produce several plans (title, description, goal, difficulty, category, modules with content_ids, order, estimated_minutes).
     - Returns **validated plans** in the shape: `{"status": "success", "plans": [...], "count": N}`.
5. **Gateway**:
   - Parses the agent response (from `function_responses` / `parts` / or JSON in text).
   - If it **cannot find** a `plans` array → 500 with *"Could not parse plans from planner agent response"*.
   - For each plan: builds **learning_plan** rows and **learning_plan_items** (modules), then calls **create_learning_plan**.
   - All created plans get **status = `proposed`**.
6. **Frontend**:
   - On success: calls **loadPlans** again so the new **proposed** plans show in the carousel and lists.

So: **generation depends on (1) Planner Agent being reachable, (2) LLM and DB being available, and (3) the user having at least one processed material.**

---

## 2. User workflow (how users should use it)

### Intended steps

1. **Have content**
   - Upload / process materials so **user_materials** has rows with **status = PROCESSED** for your `user_id`.

2. **Open Learning Plan**
   - Go to **Learning Plan** in the app (sidebar → "Learning Plan", route `/plan`).

3. **Get suggestions**
   - Click **"Generate Suggested Plans"**.
   - Wait for the request (Planner Agent + LLM). New **proposed** plans appear in the **"New Study Plans Designed for You"** carousel.

4. **Review a proposed plan**
   - Click a proposed plan card (or its "Details").
   - **Intended:** See title, description, timeline (modules), duration, difficulty; then **Approve** or **Customize** / **Regenerate** (customize/regenerate may be placeholders).

5. **Approve**
   - In the details modal, click **Approve**.
   - The plan’s **status** changes from `proposed` → `active`. It appears under **"Currently Active Plan"** and in the **All / Active** list.

6. **Use the active plan**
   - **View details** → navigate to **Plan detail** page (`/plans/:id`).
   - **Pause** / **Resume** / **Edit** / **Delete** from the card or detail page.
   - Start **study sessions** from the plan (e.g. from plan detail or session flow that uses plan items).

7. **Optional**
   - **Create New Plan** creates a blank plan (no AI, no modules) with status **active**.
   - **Filters:** All / Active / Paused / Completed for the non‑proposed plans list.

---

## 3. API & data shape (quick reference)

| Action | Endpoint | Notes |
|--------|----------|--------|
| List proposed | `GET /learning-plans/proposed?user_id=...` | Only `status = 'proposed'`. Returns plan rows **without** items. |
| List all/active/paused/completed | `GET /learning-plans?user_id=...&status=...` | Returns plan rows **without** items. |
| Get one plan (with modules) | `GET /learning-plans/:id?user_id=...&include_items=true` | Use this when you need **items** (timeline/modules). |
| Generate suggested | `POST /learning-plans/generate-suggested?user_id=...&context_mode=growth&max_plans=3` | Calls Planner Agent; creates plans with status `proposed`. |
| Approve | `POST /learning-plans/:id/approve?user_id=...` | `proposed` → `active`. |
| Pause / Resume | `POST /learning-plans/:id/pause|resume?user_id=...` | For active plans. |
| Create (manual) | `POST /learning-plans` (body: user_id, title, ...) | No items unless you send them. |
| Update / Delete | `PATCH /learning-plans/:id`, `DELETE /learning-plans/:id` | Standard CRUD. |

**Important:** List endpoints return only **learning_plans** rows. They do **not** include **learning_plan_items**. To show modules/timeline in the UI, the client must call **get learning plan by id** with `include_items=true` and use the returned `items`.

---

## 4. Where things often break ("something isn’t working")

### A. "No plans could be generated" / "No content available"

- **Cause:** No processed content for this user, or Planner Agent returns "No content available to generate plans from".
- **Check:** Same `user_id` as in the app (e.g. from localStorage); **user_materials** has rows with **status = 'PROCESSED'** and matching **content_items**.

### B. "Could not parse plans from planner agent response"

- **Cause:** Gateway could not find a `plans` array in the Planner Agent response (e.g. ADK response shape changed, or LLM didn’t return valid JSON in the expected place).
- **Check:** Gateway and agent logs; shape of `response.result` (e.g. `function_responses`, `content.parts`, or raw text).

### C. Proposed plan details modal shows no timeline / modules

- **Cause:** On **Details** click, the app uses the **list** payload (proposed plan from carousel). List APIs don’t return **items**, and the normalized carousel object doesn’t have `plan.items` or `plan.details.timeline`, so **proposedTimeline** is empty in the modal.
- **Fix:** When opening the details modal for a **proposed** plan, **fetch the full plan** with `getLearningPlan(planId, userId)` (which uses `include_items=true`), then call the same modal logic with the **fetched** plan so `plan.items` (and optionally `plan.details`) are available and the timeline can be built.

### D. Generate button spins then error

- **Cause:** Planner Agent down, wrong A2A URL, LLM key missing, or DB error inside the agent (e.g. pool, missing tables).
- **Check:** Gateway logs for 500 and agent error message; agent logs for exceptions; env for agent URL and LLM key.

### E. Plans generated but not visible

- **Cause:** Frontend might be using a different `user_id` than the one used for generation (e.g. localStorage vs query param), or list filters.
- **Check:** Same `user_id` in generate-suggested and in list/proposed requests; that plans have `status = 'proposed'` in the DB.

---

## 5. Status flow

- **proposed** → created by "Generate Suggested Plans"; shown in carousel.
- **active** → after user clicks **Approve**; at most one is highlighted as "Currently Active Plan".
- **paused** / **completed** / **archived** → from Pause / completion logic / archiving.

---

## 6. Database schema and agent interaction

**Tables (see `supabase/init.sql`):**

- **learning_plans**: `id` (UUID), `user_id` (TEXT), `title`, `description`, `goal`, `status` (proposed | active | paused | completed | archived), `difficulty`, `category`, `category_color`, `estimated_time`, `module_count`, `progress_percent`, `total_modules`, `completed_modules`, `next_session_at`, `paused_at`, `weeks`, `sessions_per_week`, `details` (JSONB), `metadata` (JSONB), timestamps.
- **learning_plan_items**: `id` (UUID), `plan_id` (FK to learning_plans ON DELETE CASCADE), `user_id`, `title`, `description`, `content_ids` (UUID[]), `status` (pending | scheduled | done | skipped), `order_index`, `estimated_minutes`, `scheduled_at`, timestamps.

**Content check:** `GET /learning-plans/check-content` queries **user_materials** (count where `user_id` and `status = 'PROCESSED'`). It does **not** read learning_plans.

**Agent flow:**

1. Frontend calls `POST /learning-plans/generate-suggested?user_id=...&context_mode=growth&max_plans=3`.
2. Gateway gets A2A client and calls `run_agent(agent_name="planner", message="Call the generate_learning_plan tool with ...")`.
3. Planner Agent (ADK) receives the message and invokes the **generate_learning_plan** tool (in `agents/planner/tools.py`). The tool:
   - Reads **user_profiles** (goals), **user_materials** + **content_items** (PROCESSED), runs clustering and LLM, and returns `{ "status": "success", "plans": [ ... ] }`. It does **not** write to learning_plans or learning_plan_items.
4. Gateway parses the agent response for a `plans` array; for each plan it builds `PlanCreate` (and `PlanItemCreate` for each module) and calls **create_learning_plan**. All DB writes to **learning_plans** and **learning_plan_items** happen in the gateway; the agent is read-only for user/content data and returns structured plan payloads only.

---

## 7. Summary

- **Generation:** User clicks "Generate Suggested Plans" → Gateway calls Planner Agent → Agent uses **user_materials** + **content_items** (and goals/clustering) → LLM returns plans → Gateway creates **learning_plans** + **learning_plan_items** with **status = proposed**.
- **Usage:** User reviews proposed plans → opens **Details** (should load full plan + items for timeline) → **Approve** → plan becomes **active** → user uses Plan detail page and study sessions.
- **Fixes to try first when it “doesn’t work”:** Ensure processed content exists for the user; ensure Details fetches full plan with items for the modal; confirm same `user_id` and Planner Agent/LLM/DB health.
