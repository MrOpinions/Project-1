# Frontend (React + Tailwind + shadcn/ui)

Source for the two pages Flask serves: the landing page (`index.html` ->
`src/App.tsx` -> `src/pages/Landing.tsx`) and the workspace tool
(`app.html` -> `src/workspace-main.tsx` -> `src/pages/Workspace.tsx`).

Styling is shadcn/ui's `neutral` ("Nova") preset - a pure black-to-grey
scale, dark mode locked - plus a small, separately-validated status
palette (good/warning/serious/critical) used only for urgency/risk, since
that's meaning, not decoration.

**The built output in `dist/` is committed and is what Flask actually
serves** (see `app.py` at the repo root). Node.js is only needed if you
want to change the UI and rebuild - a judge running `python app.py` never
needs it.

## Rebuilding after a change

```bash
npm install
npm run build
```

This regenerates `dist/`, which `app.py` serves at `/` and `/app`.

## Dev server (optional, for iterating on the UI)

```bash
npm run dev
```

This runs Vite's dev server on its own port with hot reload. The
`/api/*` calls will fail unless you also run `python app.py` and proxy
requests, or just use `npm run build` and reload the Flask-served page -
simplest for this project's size.
