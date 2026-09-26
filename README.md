# Lockstep homepage

Product model: a VS Code extension on top of GitHub Copilot. Phases run as `@lockstep` in Copilot Chat using the client's Copilot models, gates are pull request reviews routed by CODEOWNERS and enforced by branch protection, and skill packs are managed centrally and can be client-hosted. Pricing: Dev $9/month, Team $19/developer/month, Enterprise on request (`components/site/pricing-section.tsx`).

Marketing homepage for an ADLC (Agentic Development Lifecycle) extension for VS Code,
built on Spectrum UI's own homepage design. "Lockstep" and the logo are placeholders.

## Run it

Unzip into an empty folder (not over an earlier version), then:

    npm install
    npm run dev

If you see `Module not found: Can't resolve 'react-markdown'` (or any other package), the
dependencies are out of date. This happens when a new version is unzipped over an old
`node_modules`. Fix it with a clean install:

    rm -rf node_modules .next        # Windows PowerShell: rmdir /s /q node_modules .next
    npm install
    npm run dev

Open http://localhost:3000. Deploys to Vercel as-is.

## What comes from Spectrum UI

Source: https://github.com/arihantcodes/spectrum-ui (Apache 2.0, see `LICENSE-spectrum-ui.txt`).

Homepage structure, taken from Spectrum's own site:
- `app/home/HeroContent.tsx`, `HeroStage.tsx`, `CornerBadge.tsx`, `AnimateEnter.tsx`: the hero,
  the panning "camera" canvas of live cards, the corner-bracket badge and entrance animations.
  Only the copy and the cards on the canvas were changed.
- `components/site/site-header.tsx`, `site-footer.tsx`, `faq-section.tsx`: Spectrum's navbar,
  footer and FAQ, with the same classes and your content.
- `app/globals.css`: Spectrum's tokens, chroma headline sweep, container-frame and reveal utilities.
- Fonts match Spectrum: Spectral (headings), Inter (body copy), Geist Sans and Mono.

Components on the hero canvas (`app/home/stage-cards.tsx` holds all their ADLC content):
- AI Chat Card: 01 Intent
- Agent Plan: 02 Level-1 plan
- Agent Steps: 03 Bolts
- Diff View: 04 code review
- Approval Card: human gate (added `approvedMessage` / `rejectedMessage` props)
- Recent Activity: lifecycle agent feed
- Nav List Card: artifacts and governance
- FAQ Tabs Card: security, models, rollout

Also used: Data Table (audit log in the Foundation section), Scramble Text (logo), Button.

## Site structure

The homepage does five things, in order: what it is (hero), why now (the shift), how it works (the lifecycle
animation), why teams trust it (four points), and the one action (book a pilot), followed by a short FAQ.
Pricing is at `/pricing`, packs at `/packs`, and the registry at `/registry`. The main call to action and its
address are set once in `lib/site.ts`; replace the placeholder email before launch.

Earlier sections (the seven questions, foundation, use cases) remain in `components/site/` if you want them back.

## Skill registry

The same project serves a skill registry at `/registry`, behind a login.

- **Packs and skills.** A pack is a whole package, such as a Claude Code project: its skills plus subagents,
  hooks, config, templates, docs and assets, versioned together. A skill is a single SKILL.md folder.
  Two packs are preloaded: `adlc` and `design-agent` (from `packs/`).
- **Browse** with the same viewer as the site, grouped by skill, subagents, hooks, config, context and docs.
  Spreadsheets, images and other binary files are stored as-is, previewed where possible, and downloadable.
- **Register** a pack or skill by uploading its folder, a .zip, or pasting a SKILL.md. Packs take their name
  from `lockstep-pack.json`, or from the form. It's checked against the
  open Agent Skills format (a SKILL.md with `name` and `description` frontmatter), for unsafe paths and
  for obvious secrets. Submitting an existing name adds a new, higher version.
- **Edit in the browser.** Publishers can edit any text file in a pack from its page (**Edit files**). Markdown
  opens in a Notion-style editor (Novel, built on Tiptap): type `/` for headings, lists, to-dos, tables and code
  blocks, or select text to format it. Frontmatter is edited separately as raw YAML, and a Rich/Markdown toggle
  switches to the source. Edits are merged back onto the original file, so untouched parts keep their exact
  formatting; files with syntax the rich editor can't represent open as Markdown. Code and config files open in
  a code editor. Saving creates a new pending version, and its page shows a line-by-line diff for the approver.
- **Approve** before anything is installable. Admins review pending versions and can't approve their own.
- **Tokens and API** for the extension: `GET /api/registry/skills` and
  `GET /api/registry/skills/<name>?version=1.2.3`, with `Authorization: Bearer <token>`.
- **Roles:** viewer (browse approved), publisher (submit), admin (approve, tokens, users).
- **Activity log** of sign-ins, submissions, reviews, tokens and users in Settings.

On first run the registry creates the administrator from `ADMIN_EMAIL` / `ADMIN_PASSWORD` and imports
the packs in `adlc-agent/` and `packs/` as approved version 1.0.0. Uploads are limited to 4 MB, below Vercel's
request limit.

### Deploying on Vercel

1. Import the repository into Vercel.
2. Add Postgres from the Vercel Marketplace (Neon). It sets `DATABASE_URL`; the tables are created
   automatically on first request.
3. Set `ADMIN_EMAIL`, `ADMIN_PASSWORD` and `SESSION_SECRET` (see `.env.example`).
4. Deploy, open `/registry`, and sign in.

Without `DATABASE_URL` on Vercel the registry refuses to start, because Vercel doesn't keep files
written at runtime. Locally, or on your own server, it falls back to a file store in `.data/`.

For client-hosted Enterprise installs, deploy the same project with `REGISTRY_ONLY=true`.

## Dark mode

Light, System and Dark, using Spectrum UI's own theme switch (`components/theme-toggle.tsx`) and
`next-themes`. It follows the operating system by default and remembers the visitor's choice.
The switch sits in the header on larger screens and in the footer on phones. Dark mode uses
Spectrum's dark palette, including its lime accent (`#E1F435`) in place of the orange.

## Phase skills

Each lifecycle card opens the skill that runs that phase, read at build time from `adlc-agent/`
(`lib/skills.ts`), so the site always shows the files that ship. Deep links work:
`/#skill-build-orchestrate`. `npm run build` re-zips the package to `public/adlc-agent.zip`
for the "Skill pack" download. The "Open in VS Code" button uses a placeholder URI
(`vscode://lockstep.adlc/open`); set it to your extension id in `components/site/skill-viewer.tsx`.

## Sections

`components/site/sections.tsx` holds the Lifecycle (six phases with gates and outputs),
ADLC Foundation, and Use cases sections. Spectrum's homepage only has a hero and FAQ, so these
are new, built from the same visual vocabulary: orange corner marks, mono labels, Spectral
headings and the same card style.

## Before launch

All names, numbers, security claims and pilot terms are placeholders. Check them with product
and security before publishing.
