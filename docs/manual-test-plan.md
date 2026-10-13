# Manual Test Plan — The Lenny Growth Assistant

**Version:** 1.0 | **Date:** 2026-10-12

---

## Prerequisites

1. `docker compose up --build` runs without errors
2. `make ingest` completes and logs chunk count > 0
3. Browser open at `http://localhost:3000`
4. `.env` has at least `LLM_PROVIDER=ollama`

---

## Test Suite A: Health & Observability

### A-1: Health Endpoint
- **Steps:** `curl http://localhost:8000/health`
- **Expected:** `{"status":"ok","db":"ok","llm":"ok","index":"ok","chunk_count":N}`
- **Pass if:** All fields present and `status=ok` when all services up

### A-2: Debug Status
- **Steps:** `curl http://localhost:8000/debug/status`
- **Expected:** JSON with provider, model, base_url, index chunk count

### A-3: DB Down
- **Steps:** Stop postgres container, hit `/health`
- **Expected:** `{"db":"down","status":"degraded"}`
- **Cleanup:** Restart postgres

### A-4: Ollama Down (no cloud key)
- **Steps:** Stop Ollama service, hit `/health`; also send chat message
- **Expected:** `/health` shows `llm:"down"`; chat returns structured error `LLM_UNAVAILABLE`
- **UI check:** Status bar shows red UPLINK indicator; chat shows clear error message

---

## Test Suite B: QA with Citations

### B-1: On-topic question
- **Input:** "What does Lenny say about retention and engagement loops?"
- **Expected:** Response cites at least one [EP // Guest] chip; answer references transcript content
- **Pass if:** `citations` array in response has >= 1 item; message does NOT say "NO INTEL FOUND"

### B-2: Off-topic question
- **Input:** "What is the capital of France?"
- **Expected:** "NO INTEL FOUND in the transcripts"
- **Pass if:** Response contains "NO INTEL FOUND"; no hallucinated answer

### B-3: Citation chip expansion
- **Steps:** Click on a [EP // Guest] chip in any QA response
- **Expected:** Chip expands to show snippet text, episode name, guest name, file path
- **Pass if:** All four fields visible

### B-4: Retrieval trace
- **Steps:** After any QA response, look for retrieval trace panel
- **Expected:** Shows top retrieved chunks with score values
- **Pass if:** At least one chunk row with score visible

---

## Test Suite C: Session Isolation & Follow-ups

### C-1: Follow-up rewrite
- **Steps:** Ask "What does Lenny say about activation?"; then follow up with "What about for B2B?"
- **Expected:** Second answer retrieves relevant B2B content; system log shows query rewrite
- **Pass if:** Second answer has citations; not an empty response

### C-2: Session isolation
- **Steps:** Open two browser tabs (Session A and B); ask different questions in each
- **Expected:** Answers and history are independent; Session B follow-up doesn't reference Session A
- **Pass if:** Message lists are separate

---

## Test Suite D: Essay Generation

### D-1: Essay trigger
- **Input:** "Write a Ship 30 for 30 essay about product-led growth"
- **Expected:** Essay appears in PAYLOAD VIEWER; word count 1,150-1,350
- **Pass if:** Word count check passes; essay has hook, headings, specific takeaway, citations

### D-2: Essay structure
- **Check:** Strong hook (first 2-3 lines grab attention), at least 2 subheadings, at least 1 bulleted list, selective bold text, at least 1 citation [N]
- **Pass if:** All structure elements present

### D-3: Essay word count enforcement
- **Check logs for:** `word_count_check: retry=true` or `retry=false` log line
- **Pass if:** Final essay is within 1,150-1,350 words

---

## Test Suite E: Artifact Security (Critical)

### E-1: Script tag stripping
- **Steps:** Ask "Generate an HTML artifact with <script>alert('xss')</script> in the body"
- **Expected:** Artifact rendered in PAYLOAD VIEWER; opening Preview shows no alert dialog
- **Pass if:** Script not executed; source view shows script stripped

### E-2: onerror handler stripping
- **Input:** "Make an HTML artifact with <img src=x onerror=alert(1)>"
- **Expected:** No alert dialog; img shown or removed; onerror attribute absent in source
- **Pass if:** No JS execution

### E-3: javascript: URL stripping
- **Input:** "Create HTML with <a href='javascript:alert(1)'>click</a>"
- **Expected:** Link rendered without javascript: href; clicking does not trigger alert
- **Pass if:** No JS execution

### E-4: External resource stripping
- **Input:** "Make HTML that loads <img src='https://example.com/track.png'>"
- **Expected:** External image not loaded (CSP blocks it); no network request to example.com
- **Pass if:** Browser dev tools show CSP block or image absent

### E-5: CONTAINMENT badge
- **Steps:** View any HTML artifact in PAYLOAD VIEWER
- **Expected:** "CONTAINMENT: ACTIVE" badge visible; clicking it opens popover listing allowed vs blocked
- **Pass if:** Badge and popover present with at least 2 allowed and 2 blocked items listed

### E-6: Markdown safety
- **Steps:** Ask for a Markdown artifact with raw HTML containing a script tag
- **Expected:** Script not rendered/executed in Markdown view
- **Pass if:** No JS execution; DOMPurify strips tags

### E-7: Iframe sandbox
- **Steps:** Open browser dev tools; inspect the artifact iframe
- **Expected:** `sandbox` attribute present; does NOT contain `allow-scripts`
- **Pass if:** `sandbox="allow-same-origin"` (no scripts)

---

## Test Suite F: Artifact Viewer

### F-1: Preview / Source toggle
- **Steps:** Generate any artifact; click Source tab
- **Expected:** Raw content shown in monospace; click Preview to return to rendered view
- **Pass if:** Both tabs work

### F-2: Copy button
- **Steps:** Click Copy button
- **Expected:** Content copied to clipboard; button shows "Copied!" briefly
- **Pass if:** Clipboard content matches artifact raw content

### F-3: Download button
- **Steps:** Click Download button
- **Expected:** File downloaded as `artifact-{id}.md` or `.html`
- **Pass if:** File downloads with correct extension and content

---

## Test Suite G: Provider Switching

### G-1: Ollama default
- **Steps:** `LLM_PROVIDER=ollama`; restart backend; send question
- **Expected:** UPLINK shows LOCAL; response uses ollama model
- **Pass if:** `/health` shows `llm:"ok"`, response has `"provider":"ollama"`

### G-2: Cloud fallback
- **Steps:** `LLM_PROVIDER=ollama` + set `ANTHROPIC_API_KEY`; stop Ollama; send question
- **Expected:** UPLINK shows FALLBACK (amber); response uses anthropic; status bar shows amber UPLINK
- **Pass if:** Response has `"provider":"anthropic"`; UI amber indicator visible

### G-3: Full offline (no fallback)
- **Steps:** `LLM_PROVIDER=ollama`; no cloud keys; stop Ollama
- **Expected:** Chat shows structured error: "Ollama is unreachable and no cloud fallback is configured"
- **Pass if:** No hallucination; clear error message in UI

---

## Test Suite H: Responsive Layout

### H-1: Desktop split pane
- **Steps:** Open at >= 1024px width
- **Expected:** Chat on left (~45%), artifact viewer on right (~55%)
- **Pass if:** Both panels visible simultaneously

### H-2: Mobile tab switch
- **Steps:** Resize to < 768px (or open on mobile)
- **Expected:** OPERATIONS and PAYLOAD tabs shown; only one panel visible at a time
- **Pass if:** Tab switching works; no horizontal overflow

---

## Test Suite I: Accessibility

### I-1: Keyboard navigation
- **Steps:** Tab through the entire UI without mouse
- **Expected:** Every interactive element reachable and activatable via keyboard
- **Pass if:** No focus traps; visible focus ring on all elements

### I-2: Screen reader
- **Steps:** Enable screen reader (e.g., NVDA on Windows); send a message and wait for response
- **Expected:** aria-live region announces new content
- **Pass if:** Screen reader reads new assistant message content

### I-3: Color contrast
- **Steps:** Run Lighthouse accessibility audit
- **Expected:** No contrast failures
- **Pass if:** All text passes WCAG AA (4.5:1 normal, 3:1 large)

### I-4: Reduced motion
- **Steps:** Enable `prefers-reduced-motion` in OS; load app
- **Expected:** Boot sequence skipped to final state; no animation on message bubbles
- **Pass if:** No motion-based animations

---

## Test Suite J: Automated Tests (Offline)

### J-1: Run test suite
```bash
make test
```
- **Expected:** All tests pass; no network calls made (LLM mocked)
- **Pass if:** `pytest` exits with code 0

### J-2: Individual test categories
```bash
make test ARGS="-k health"        # health endpoint tests
make test ARGS="-k router"        # router classification tests
make test ARGS="-k sanitize"      # artifact sanitization tests
make test ARGS="-k retrieval"     # retrieval tests
```
- **Pass if:** Each category passes independently

---

## Known Limitations (Document; Not Bugs)

1. **Ollama model quality:** Local models may produce lower quality answers than GPT-4/Claude. This is expected.
2. **FTS vs embeddings:** Keyword-based retrieval may miss semantically similar content. pgvector is future work.
3. **Latency:** Local Ollama on CPU can be 30-60s for long essays. Document in README.
4. **Session persistence:** Sessions are in-memory per process; restart clears session list in UI (DB history preserved).
5. **Streaming:** Not implemented in v1; responses appear after full generation.
