# Chat2Query Design System Tokens — Enterprise Brutalist Palette

This document defines the reusable design tokens, typography specifications, layout grids, and CSS custom properties for Chat2Query's frontend interface.

---

## 1. Color Palette: "High-Contrast Blueprint & Signal Ink"

Rather than standard near-black/neon cyberpunk templates, the Chat2Query brutalist visual language is grounded in architectural drafting paper, legal-grade audit indexes, and industrial control schematics with high-vibrancy signal accents.

| Token Name | CSS Custom Property | Hex Value | Role & Rationale |
| :--- | :--- | :--- | :--- |
| **Paper Canvas** | `--bg-paper` | `#F8F5EE` | Primary background. Warm unbleached paper tone providing high contrast and legal-drafting feel. |
| **Surface Fill** | `--bg-surface` | `#EDE7DC` | Panel, sidebar, and table header background. Slightly darker paper fill for structural division. |
| **Surface Alt** | `--bg-surface-alt` | `#E2DAD0` | Tab bar background and secondary container highlights. |
| **Iron Gall Ink** | `--ink-dark` | `#0F1419` | Primary text and 2px/3px structural borders. High-density deep blue-black. |
| **Muted Ink** | `--ink-muted` | `#4F5863` | Secondary labels, metadata descriptions, and inactive tabs. |
| **Industrial Canary Yellow** | `--yellow-signal` | `#FFD600` | High-visibility action accent. Primary CTAs, active command buttons, user badges, and receipt tags. |
| **International Cobalt** | `--cobalt-signal` | `#0047AB` | Primary database signal accent. Active navigation view, DB intent pills, and live SQL metrics. |
| **Ultraviolet Hybrid** | `--purple-signal` | `#7C3AED` | Hybrid query intent accent. Multi-source cross-reference synthesis badges and audit execute tags. |
| **Sky Blue Document** | `--cyan-signal` | `#0284C7` | Document retrieval intent accent. Document chunk citations, page-number tags, and PDF file type pills. |
| **Signal Vermilion**| `--rust-warn` | `#DC2626` | High-visibility security pipeline warning accent. Masked column flags, AST syntax errors, and modal close triggers. |
| **Safety Emerald** | `--emerald-pass` | `#16A34A` | Approved execution status, active connection badges, and verified audit logs. |
| **Code Canvas** | `--code-bg` | `#0F172A` | Deep charcoal/slate surface for raw SQL codeblocks, AST nodes, and JSON execution payloads. |

---

## 2. Typography Specifications

| Role | Font Family | Weights | CSS Custom Property | Usage |
| :--- | :--- | :--- | :--- | :--- |
| **Display / Headers** | `Space Grotesk`, sans-serif | 500, 700, 800 | `--font-display` | Navigation labels, page titles (`<h1>`), brand badges, modal headers, primary buttons |
| **Body & Controls** | `Public Sans`, sans-serif | 400, 600, 800 | `--font-body` | Conversational text, table cell contents, form inputs, tooltips |
| **Data / SQL / Metadata** | `JetBrains Mono`, monospace | 400, 500, 700 | `--font-mono` | SQL queries, raw execution payloads, vector scores, page numbers, timestamps, system status tags |

### Typography Scale
- **Display 1 (`.page-title`)**: `24px` / `800` weight / uppercase / `-0.02em` letter-spacing
- **Header 2 (`.card-name`)**: `16px` / `800` weight / uppercase / `0.02em` letter-spacing
- **Navigation (`.nav-item`)**: `13px` / `800` weight / uppercase / `0.03em` letter-spacing
- **Body (`.msg-text`)**: `14px` / `400` weight / `1.5` line-height
- **Monospace Code (`.sql-block`)**: `12px` / `400` weight / `1.4` line-height
- **Metadata Tag (`.mono-cell`)**: `11px` / `600` weight / uppercase

---

## 3. Structural Constraints & Border Rules

```css
:root {
  /* Strict Zero Border Radius — No Rounded Corners Anywhere */
  --border-thick: 3px solid #0F1419;
  --border-med: 2px solid #0F1419;
  --border-thin: 1px solid #0F1419;

  /* Hard-Edged Offset Drop Shadows (No Blur, No Soft Shadows) */
  --shadow-hard: 4px 4px 0px #0F1419;
  --shadow-sm: 2px 2px 0px #0F1419;
  --shadow-yellow: 4px 4px 0px #FFD600;
  --shadow-cobalt: 4px 4px 0px #0047AB;
  --shadow-purple: 4px 4px 0px #7C3AED;
}
```

---

## 4. CSS Custom Property Template (For Next.js / Tailwind Integration)

```css
/* Add to global css (e.g. globals.css) */
@import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Public+Sans:wght@400;600;800&family=Space+Grotesk:wght@500;700;800&display=swap');

@layer base {
  :root {
    --bg-paper: #F8F5EE;
    --bg-surface: #EDE7DC;
    --bg-surface-alt: #E2DAD0;
    --ink-dark: #0F1419;
    --ink-muted: #4F5863;
    
    --yellow-signal: #FFD600;
    --cobalt-signal: #0047AB;
    --purple-signal: #7C3AED;
    --cyan-signal: #0284C7;
    --rust-warn: #DC2626;
    --emerald-pass: #16A34A;
    --code-bg: #0F172A;
    --code-fg: #F8FAFC;

    --font-display: 'Space Grotesk', system-ui, sans-serif;
    --font-body: 'Public Sans', system-ui, sans-serif;
    --font-mono: 'JetBrains Mono', monospace;

    --border-thick: 3px solid #0F1419;
    --border-med: 2px solid #0F1419;
    --shadow-hard: 4px 4px 0px #0F1419;
    --shadow-sm: 2px 2px 0px #0F1419;
  }

  *, *::before, *::after {
    border-radius: 0px !important;
  }
}
```
