# Frontend Build Plan — Multi-Tenant Text-to-SQL & Document Chat Platform

Companion to `BUILD_PLAN.md` (backend, complete and verified across Phases 1–8). This document
is the frontend's own working brief — same phase-by-phase, verify-don't-assert discipline that
got the backend through eight rounds of honest scrutiny, applied here from the start instead of
after the fact.

## 0. How to use this document

1. Track progress in the existing `PROGRESS.md`, under a new **Frontend** section (F1–F8),
   same format as the backend's Phase 1–8 entries.
2. One phase at a time. Stop at each Definition of Done for review — don't let three phases'
   worth of half-wired screens pile up before anyone looks at them.
3. **The brutalist mockup file is the literal visual source of truth.** Not this document, not
   memory of what was discussed, the actual CSS in the actual file. Every phase that touches
   layout or styling starts by checking against it.
4. **The exported `openapi.json` is the literal API source of truth.** Route paths, request
   bodies, response shapes — read the spec, don't reconstruct them from memory of what
   PROGRESS.md said was built. The API integration map in Section 5 is a starting index, not
   a substitute for reading the actual spec.
5. **Standing rule for the whole build**: the mockup's HTML has hardcoded demo content sitting
   right there — the invoice/contract example, fake connection cards, fake audit rows. Every
   screen from F3 onward renders real data from real API calls against the live backend. If a
   number or string in a component came from the mockup file instead of a fetch response, that's
   the same failure mode as the mocked "integration tests" from the backend build — it looks
   done and isn't.

---

## 1. Prerequisite — real design tokens (do this before F1)

Open the actual brutalist mockup file and pull these directly out of its CSS. Don't reconstruct
from description, don't soften, don't average toward something safer — copy the literal values:

- Full color palette (background, surface, border, text, and the accent color(s)), as hex
- Border width(s) used structurally
- Confirm `border-radius: 0` throughout
- Typeface(s): family names, weights used, where display type vs. body type vs. data/mono type
  apply
- Spacing scale actually used (even if informal — note the values that recur)

Write these into a `tailwind.config.ts` theme extension as the single source every component
pulls from — no inline hex, no inline font-family strings anywhere else in the app.

---

## 2. Tech stack

- **Framework**: Next.js (App Router) + TypeScript
- **Styling**: Tailwind CSS, theme extended with the tokens from Section 1
- **Component primitives**: Radix UI / shadcn, restyled to the token system — don't hand-roll
  dialogs, dropdowns, or toggles; accessibility is easy to get subtly wrong from scratch
- **Server state / data fetching**: TanStack Query for everything except chat streaming
- **Streaming**: native `EventSource`, wrapped in a small typed parser (Section 8)
- **Client/UI state**: Zustand — active view, command palette open/closed, in-flight evidence
  rail contents. Server data does not belong here; TanStack Query owns that.
- **Forms**: `react-hook-form` + `zod` — connection forms and permission edits both need real
  validation, not just HTML5 `required`
- **SQL syntax highlighting**: Shiki or `react-syntax-highlighter`
- **Testing**: Vitest + React Testing Library (unit/component), Playwright (e2e)

---

## 3. Repository layout

```
frontend/
|-- app/
|   |-- (auth)/login/page.tsx
|   |-- (app)/layout.tsx              # shell: Sidebar + TopBar + CommandPalette
|   |-- (app)/chat/page.tsx
|   |-- (app)/connections/page.tsx
|   |-- (app)/knowledge/page.tsx
|   |-- (app)/permissions/page.tsx
|   `-- (app)/audit/page.tsx
|-- components/
|   |-- layout/          # Sidebar, TopBar, CommandPalette
|   |-- chat/             # MessageThread, MessageRow, Composer, EvidenceRail,
|   |                     # SqlEvidenceCard, CitationEvidenceCard
|   |-- connections/     # ConnectionCard, ConnectionForm, SchemaTree, ConnectionTestButton
|   |-- knowledge/       # FileCard, UploadDropzone, KnowledgeBaseSelector
|   |-- permissions/     # PermissionMatrix, PermissionToggle, RoleSelect
|   |-- audit/           # AuditLogRow, AuditFilterBar
|   `-- shared/          # StatusPill, EmptyState, ErrorState, Skeletons
|-- lib/
|   |-- api/              # one typed client file per resource — see Section 5
|   |   |-- auth.ts, connections.ts, schema.ts, files.ts, knowledgeBases.ts,
|   |   `-- chat.ts, conversations.ts, permissions.ts, auditLogs.ts
|   |-- auth/              # token handling, refresh logic, AuthProvider/TenantContext
|   |-- sse/                # typed EventSource wrapper (Section 8)
|   `-- stores/             # Zustand UI store
|-- styles/globals.css
|-- tailwind.config.ts
`-- tests/
    |-- unit/
    `-- e2e/
```

---

## 4. Design tokens

Populated during Section 1 / Phase F1 from the real mockup file. Not duplicated here to avoid
this document silently going stale the moment the mockup changes — the single source of truth
lives in `tailwind.config.ts` once F1 lands. If you need to reference the palette while reading
this plan, open the mockup file or the config directly.

---

## 5. API integration map

Starting index only — confirm exact paths, request bodies, and response shapes against the real
`openapi.json` before wiring each screen. Where a route wasn't explicitly named in the backend's
PROGRESS.md notes (marked below), that's a flag to go read the spec rather than guess.

| Screen | Endpoints | Notes |
|---|---|---|
| Login | `POST /api/auth/login`, `POST /api/auth/refresh`, `GET /api/auth/me` | Store tokens in an httpOnly cookie, not `localStorage` — this is a real browser app, not a sandboxed artifact, so the more secure option is available and should be used |
| Chat | `POST /api/chat/stream` (SSE, primary path), `POST /api/chat` (sync fallback), `GET /api/conversations`, `GET /api/conversations/{id}`, `DELETE /api/conversations/{id}`, `GET /api/messages/{id}/citations`, `GET /api/messages/{id}/sql` | SSE events are typed: `intent`, `sql_result`, `citation`, `token`, `done` — see Section 8 |
| Connections | `POST/GET/PUT/DELETE /api/database-connections`, `GET /api/database-connections/{id}`, `POST /{id}/test`, `POST /{id}/sync-schema`, `GET /{id}/schemas`, `GET /{id}/tables` | Confirm whether test/sync-schema return synchronously or as a job you need to poll — check the spec, the two behave very differently in the UI (spinner vs. poll loop) |
| Knowledge bases | `POST /api/files/upload`, `GET /api/files`, `GET /api/files/{id}`, `DELETE /api/files/{id}`, `POST /api/files/{id}/reprocess`, `POST/GET /api/knowledge-bases`, `POST /api/knowledge-bases/{id}/files` | Poll `processing_status` on files with any non-terminal status; stop polling once `indexed`/`failed` |
| Permissions | table/column permission CRUD routes | **Not explicitly enumerated in PROGRESS.md — read `openapi.json` directly for exact paths before starting F6, don't assume a shape** |
| Audit | `GET /api/audit-logs` | Admin-gated on the backend — if the logged-in user isn't `is_tenant_admin`, hide the nav item or show a clear "admin only" state, don't let the UI hit a raw 403 |

---

## 6. Information architecture

Unchanged from the mockup: Login → Chat (default) / Connections / Knowledge bases /
Permissions / Audit log, persistent left nav, command palette (Ctrl/Cmd+K) for quick-jump.

---

## 7. Component inventory

`Sidebar`, `TopBar`, `CommandPalette`, `MessageThread`, `MessageRow` (variant driven by the
response's `sources_used`), `Composer`, `EvidenceRail`, `SqlEvidenceCard`,
`CitationEvidenceCard`, `ConnectionCard`, `ConnectionForm`, `SchemaTree`,
`ConnectionTestButton` (owns its own pending/success/error state), `FileCard`,
`UploadDropzone`, `PermissionMatrix`, `PermissionToggle`, `RoleSelect`, `AuditLogRow`,
`AuditFilterBar`, `StatusPill` (one component, ok/warn/err variants, used everywhere —
connections, files, audit — not reimplemented per screen), `EmptyState`, `ErrorState`.

---

## 8. State, data-fetching, and streaming conventions

- **TanStack Query owns all server state.** Query key convention: `['connections']`,
  `['connections', id]`, `['files', kbId]`, `['permissions', roleId]`, etc. — consistent enough
  that invalidation after a mutation is predictable (e.g. permission toggle invalidates
  `['permissions', roleId]`, connection test invalidates `['connections', id]`).
- **Zustand only for UI-local state** that has no server counterpart — active view, command
  palette open state, transient "is this message currently streaming" flags.
- **SSE event handling** (typed wrapper in `lib/sse/`):
  - `intent` → sets the message's source framing (db/document/hybrid) before content arrives
  - `sql_result` → prepend/update a `SqlEvidenceCard` in the rail
  - `citation` → prepend/append a `CitationEvidenceCard` in the rail
  - `token` → append to the streaming message's text buffer
  - `done` → finalize the message (stop the streaming-cursor state, enable retry/copy actions)
  - Evidence events populate the rail *as they arrive*, not after `done` — that live-update
    behavior is the actual point of the evidence rail, don't build it as a post-hoc summary
- **Error handling**: no silent failures. A failed connection test shows a real error state on
  the card, not a console.error and a stuck spinner. A failed chat request shows an inline
  error in the thread, not a blank space where the answer should be.

---

## 9. Build phases

### F1 — Shell & design system
- Extract real tokens (Section 1), configure Tailwind
- Next.js scaffold, `Sidebar` + `TopBar` + routing across all 5 views, `CommandPalette`
  (client-only, no backend calls yet)

**DoD**: navigating all 5 sections works; shell is visually consistent with the mockup —
compared side by side, not asserted. Paste the rendered output or a screenshot.

### F2 — Auth & tenant context
- Login page, httpOnly-cookie token storage, silent refresh before expiry
- `AuthProvider`/`TenantContext`, protected route middleware

**DoD**: log in against the real `/api/auth/login`; wrong credentials show an inline error, not
a redirect loop or console error. Force a short token lifetime (or wait one out) and confirm
refresh actually happens before expiry, not just that the endpoint exists. Show the network
trace, not a description of it.

### F3 — Connections
- `ConnectionCard` grid wired to real CRUD, `ConnectionForm` with real validation
- `ConnectionTestButton` wired to `POST /{id}/test`
- `SchemaTree` wired to `/schemas` and `/tables`

**DoD**: create a real connection through the UI, test it, sync its schema, see the real result
in the tree — all against the live backend. Network trace or recording, not a claim.

### F4 — Chat + evidence rail (the core screen, most likely to go wrong)
- `MessageThread`, `Composer`, real SSE wiring per Section 8
- `EvidenceRail` populated from real `sql_result`/`citation` events — **not** the mockup's
  hardcoded invoice/contract text

**DoD**: run a real hybrid question (a genuine equivalent of the invoice/contract example, not
copy-pasted from the mockup) end-to-end through the actual UI against the live backend. Show
the network/SSE trace. If the rendered answer text matches the mockup's demo text exactly,
that's a signal it wasn't actually wired — flag and re-check rather than assume it's a
coincidence.

### F5 — Knowledge bases
- `UploadDropzone` → `POST /api/files/upload`
- `FileCard` reflecting real `processing_status`, polled while non-terminal

**DoD**: upload a real PDF, watch it move pending → processing → indexed in the UI without a
manual page refresh.

### F6 — Permissions
- Read the real permission endpoints from `openapi.json` first (Section 5 flag)
- `PermissionMatrix` + `PermissionToggle` wired to real reads/writes, per role

**DoD**: toggle a permission off in the UI, then run a chat question in F4's chat screen that
would have used that table/column, and confirm the change actually took effect on a real query
— not just that the toggle's UI state persisted on refresh.

### F7 — Audit log
- `AuditLogRow`/`AuditFilterBar` wired to `GET /api/audit-logs`, admin-gated UI state for
  non-admin users

**DoD**: perform an action elsewhere in the app (test a connection, upload a file, send a chat
message), confirm it appears in the audit view within the same session, no full reload needed.

### F8 — Polish & accessibility pass
- Visible keyboard focus everywhere, `prefers-reduced-motion` respected
- Mobile breakpoint: sidebar collapses, evidence rail becomes a slide-over (pattern already in
  the mockup's `@media (max-width: 860px)` block)
- Loading/empty/error states for every list view — no blank screens, ever
- Final side-by-side check against the mockup: seven phases of feature work tends to erode
  initial design fidelity, worth confirming it still looks like what was designed

---

## 10. Testing plan

- **Unit/component** (Vitest + RTL): `SqlEvidenceCard`, `CitationEvidenceCard`, `StatusPill`
  variants, `PermissionToggle` state logic, the SSE event parser (feed it a mock event stream,
  assert correct state transitions)
- **E2E** (Playwright, against the real running backend): login flow, full connection
  create→test→sync cycle, one complete hybrid chat scenario end-to-end, a permission toggle
  that measurably changes what a subsequent chat query can return
- **Accessibility**: automated `axe-core` pass on every screen, plus a manual keyboard-only
  navigation pass (no mouse) through the full app

---

## 11. Deliverables checklist

- [ ] Next.js app source, modular structure per Section 3
- [ ] `tailwind.config.ts` matching the real mockup tokens exactly (Section 1)
- [ ] All 5 screens + login wired to the real backend — zero remaining mock/hardcoded data
- [ ] SSE streaming working with all 5 typed events, evidence rail updating live
- [ ] Unit + e2e suites passing against real infrastructure
- [ ] Accessibility floor met: focus visibility, reduced motion, mobile responsive down to the
  mockup's breakpoint
- [ ] README frontend section: setup (`npm install`, env vars for API base URL), `npm run dev`,
  `npm run test`, `npm run test:e2e`, build/deploy notes

---

## 12. Kickoff prompt — F1

```
Read FRONTEND_BUILD_PLAN.md in full and PROGRESS.md. The backend (Phases 1-8) is complete
and verified — build against the real running API from the start, not mocks.

Before scaffolding anything, open the actual brutalist mockup file and extract its real
design tokens directly from its CSS per Section 1 — exact hex colors, border widths, type
families/weights/scale, spacing, and confirm border-radius is 0 throughout. Write these
into tailwind.config.ts as real theme values. Pull them from the file, don't reconstruct
from memory or soften them.

Then execute Phase F1 exactly as scoped in Section 9:
- Next.js (App Router) + TypeScript scaffold
- Tailwind configured with the extracted tokens — no inline hex or font-family strings
  anywhere in the app
- Sidebar + TopBar + routing across the 5 views, matching the mockup's nav and IA
- CommandPalette, client-only for now

Standing rule for this whole build, starting now: the mockup's HTML has hardcoded demo
content sitting right there to copy — don't. Every screen from F3 onward renders real data
from real API calls. If text or numbers in a component came from the mockup file instead of
a fetch response, stop and wire the fetch instead.

DoD: navigating all 5 sections works, shell is visually consistent with the mockup checked
side by side. Paste the rendered output or a screenshot, not a description.

Add a Frontend section to PROGRESS.md tracking F1-F8, mirroring the backend Phase 1-8
format. Mark F1 complete only once the visual comparison actually holds up, and stop there
for review before F2.
```
