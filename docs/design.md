# Design Document — The Lenny Growth Assistant

**Version:** 1.0 | **Date:** 2026-10-12

---

## 1. Design Principles

1. **Clarity over cleverness** — Every element serves a function. No decorative chrome.
2. **Trust through transparency** — Show the model, provider, retrieval scores, and containment status at all times.
3. **Calm urgency** — SOC Console aesthetic creates focus without alarm. Phosphor green signals life, not danger.
4. **Accessible by default** — WCAG AA contrast, keyboard-navigable, aria-live for streaming, `prefers-reduced-motion` respected.
5. **Mobile-first layout** — Desktop split-pane, mobile tab-switch; no horizontal scroll.

---

## 2. Color System

| Token | Value | Usage |
|---|---|---|
| `--bg-primary` | `#0a0c0f` | App background |
| `--bg-surface` | `#111318` | Chat panel, artifact panel |
| `--bg-elevated` | `#1a1d24` | Cards, message bubbles |
| `--bg-hover` | `#232730` | Hover states |
| `--accent-green` | `#39ff14` | Primary accent, cursor, active indicators |
| `--accent-cyan` | `#00d4ff` | Secondary accent, links, citation chips |
| `--accent-amber` | `#ffb347` | Warnings, fallback notice |
| `--error-red` | `#ff4444` | Errors only |
| `--text-primary` | `#e2e8f0` | Body text |
| `--text-secondary` | `#7a8599` | Metadata, timestamps |
| `--text-muted` | `#4a5568` | Placeholder, disabled |
| `--border` | `#1e2330` | Panel borders |
| `--border-active` | `#39ff14` | Active panel border |

---

## 3. Typography

| Role | Font | Weight | Size |
|---|---|---|---|
| Body text | `Inter` (Google Fonts) | 400 | 14px |
| Headings | `Inter` | 700 | 16-24px |
| Metadata, codes | `JetBrains Mono` | 400 | 12-13px |
| Status labels | `JetBrains Mono` | 600 | 11px uppercase |
| Chat input | `Inter` | 400 | 15px |

---

## 4. Information Architecture

```
App Shell
├── Boot Sequence (skippable, 2s)
├── Status Bar (top)
│   ├── DB: [OK|DOWN]
│   ├── MODEL: [provider/model]
│   ├── INDEX: [N chunks]
│   └── SANDBOX: [ACTIVE]
├── Main Layout (split on desktop, tabs on mobile)
│   ├── LEFT: OPERATIONS Panel
│   │   ├── Session List (sidebar collapsed by default)
│   │   ├── Chat History (message bubbles)
│   │   │   ├── User message
│   │   │   └── Assistant message
│   │   │       ├── Content
│   │   │       ├── EVIDENCE chips [EP // Guest]
│   │   │       └── Retrieval Trace (collapsible)
│   │   └── Input Bar
│   │       ├── Text field + Send
│   │       └── Route hint display
│   └── RIGHT: PAYLOAD VIEWER
│       ├── Artifact header (title, type badge)
│       ├── CONTAINMENT: ACTIVE badge (popover)
│       ├── Tabs: Preview | Source
│       └── Actions: Copy | Download
└── UPLINK indicator (top-right)
    └── LOCAL | CLOUD | FALLBACK
```

---

## 5. Component States

### Chat Message — States
- `streaming`: blinking cursor, content updates character by character
- `complete`: full content, citation chips shown
- `error`: red border, error code shown
- `no_intel`: amber border, "NO INTEL FOUND" in monospace

### Status Bar — States
- `DB: OK` (green) / `DB: DOWN` (red)
- `MODEL: ollama/llama3.2` (green) / `MODEL: FALLBACK anthropic/claude-3-haiku` (amber)
- `INDEX: 12,450 chunks` (green) / `INDEX: EMPTY` (amber)
- `SANDBOX: ACTIVE` (green)

### Citation Chip — States
- `collapsed`: `[EP-123 // Brian Balfour]` pill
- `expanded`: snippet text + episode + guest + file path

### UPLINK Badge — States
- `LOCAL` (green): Ollama responding
- `CLOUD` (cyan): Cloud provider active
- `FALLBACK` (amber): Auto-switched to cloud
- `OFFLINE` (red): No provider reachable

---

## 6. Responsive Design

### Desktop (>= 1024px)
- 45% chat panel | 55% artifact viewer (split pane, resizable)
- Status bar always visible at top
- Session sidebar collapsible at left edge

### Tablet (768-1023px)
- Full width chat
- Artifact viewer in bottom drawer or tab
- Status bar condensed to icons

### Mobile (< 768px)
- Tab navigation: [OPERATIONS] [PAYLOAD]
- Chat full width
- Status bar icons only with tap-to-expand
- Input bar sticky to bottom

---

## 7. Animations & Motion

All animations respect `prefers-reduced-motion: reduce`:

| Animation | Duration | Easing | Reduced Motion |
|---|---|---|---|
| Boot sequence lines appear | 80ms/line | linear | Skip to final state |
| Message bubble slide in | 200ms | ease-out | Instant |
| Streaming cursor blink | 1s cycle | step | Static underscore |
| Citation chip expand | 150ms | ease-in-out | Instant |
| Status indicator pulse | 2s cycle | ease-in-out | Static |
| Panel resize | 0ms (CSS) | — | — |

---

## 8. Boot Sequence

```
[INITIALIZING LENNY GROWTH ASSISTANT v1.0]
[CONNECTING TO DATABASE...          OK]
[LOADING TRANSCRIPT INDEX...        OK — 12,450 chunks]
[ESTABLISHING UPLINK...             LOCAL — ollama/llama3.2]
[SANDBOXING ARTIFACT RENDERER...    ACTIVE]
[ALL SYSTEMS NOMINAL]
> _
```

- Displays for ~2 seconds, each line appears with 80ms delay
- "SKIP" button in top-right appears after 500ms
- Persists `hasBooted` in sessionStorage (no re-show on refresh)

---

## 9. Accessibility

- All interactive elements have `:focus-visible` outline in `--accent-green`
- `aria-live="polite"` on assistant message content during streaming
- `aria-label` on all icon-only buttons
- Citation chip: `role="button"` with keyboard activate (Enter/Space)
- Status bar: `role="status"` with screen-reader text
- Color is never the *sole* indicator of meaning (also use icons + text)
- Minimum contrast: 4.5:1 for normal text, 3:1 for large text (WCAG AA)
- Tab order follows visual layout order
