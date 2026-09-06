# SimUX — POC

A static, click-through visual prototype of SimUX (a multi-persona
LLM-agent UI/UX auditor) built for an FYP-I defense presentation.

**Nothing in this app executes.** No agent runs, no LLM is called, no
backend exists — every screen reads from a local fixture-data seam
(`src/hooks/useDemoRun.ts`). This is a prototype of what the finished
system will look like and do, not a working version of it. See
`POC_SPEC.md` for the full governing spec and `CLAUDE.md` for a complete
technical handoff (architecture, design decisions, known issues,
milestone status).

## Stack

Vite 6 + React 18 + TypeScript 5.7 + Tailwind CSS 3.4 + `motion`
(Framer Motion) + React Router 6 + Radix UI primitives.

## Running locally

```bash
npm install
npm run dev      # http://localhost:5173
npm run build    # production build (tsc -b && vite build) -> dist/
npm run lint     # typecheck only (tsc --noEmit)
```

## Deployment

Deployed on Vercel. `vercel.json` pins the framework preset and adds the
SPA fallback rewrite React Router needs (all paths serve `index.html`
so client-side routing handles the rest). No environment variables are
required.

## Docs

- `POC_SPEC.md` — what this prototype is and isn't, and why
- `DESIGN.md` — the visual design system (colors, type, motion, the
  scroll-pinned section patterns)
- `CLAUDE.md` — full technical handoff for continuing this project in a
  new session
