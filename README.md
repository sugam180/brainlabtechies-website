# Brainlab Techies — Website + Admin

A clean, white, highly interactive one-page site for **Brainlab Techies** (MSME / Udyam registered edu-tech),
domain-themed sub-pages, and a password-protected **admin dashboard** to see which students registered for which courses.

Built with **Flask + SQLite** — no external services needed.

## Features

**User side — white, professional, animated**
- Animated hero landing: rising headline, floating official logo with orbiting course nodes, mouse-move + scroll parallax.
- **Domain slider** — pick your background and get routed to a page themed for your field:
  - Geography → mountains, grass, topography / contour charts
  - Biology → DNA + cells · IT → code window + grid · AIML → neural network · Beginners → step-up path
  - The main page stays the same; each domain has its own accent theme, "why this fits you", recommended courses and a pre-filled free-demo form.
- Scroll progress bar, reveal-on-scroll, hover parallax on slides, animated counters, keyword marquee.
- All **11 courses** incl. the 3 Data-Analytics tiers (Starter / Pro / Placement-track with guaranteed paid internship, job assistance, interview grooming).
- **Register for free** — no payment. Every registrant is promised a free **demo + doubt-clearing session** with the subject trainer.
- MSME / Udyam badge (UDYAM-WB-16-0122821). No emojis. Sora + Inter fonts. Fully responsive.
- Uses your **official logo** (black background keyed out so it sits cleanly on white).

**Admin side** (`/admin`, login-protected)
- Every student's name, email, phone, address, academic background, course, message, time.
- Interest-by-course chart + stats, status tags (New / Contacted / Enrolled), CSV export.

## Run it

Double-click **`run.bat`**, or:

```bash
pip install -r requirements.txt
python app.py
```

Open:
- Website: <http://127.0.0.1:5000/>
- Domain pages: `/domain/geography` · `/domain/biology` · `/domain/it` · `/domain/aiml` · `/domain/beginners`
- Admin: <http://127.0.0.1:5000/admin>

### Default admin login
```
username: admin
password: brainlab@2026
```
Override before first run (recommended):
```
set BRAINLAB_ADMIN_USER=youruser
set BRAINLAB_ADMIN_PASS=yourstrongpassword
set BRAINLAB_SECRET=some-long-random-string
```
The admin account is created from these values on **first run** (when the DB is empty). To reset later, delete `brainlab.db` and restart.

## Data
Registrations are stored in **`brainlab.db`** (SQLite, auto-created). Back it up by copying that file.

## Cinematic landing
The site opens with a **scroll-driven cinematic hero** (GSAP ScrollTrigger): a mountain valley splits
apart to reveal **Human → Human Mind → Digital Brain → Neural Network → AI**, ending on the BrainLab
Techies brand hero with CTAs and glass badges. It's built with vanilla JS + GSAP (loaded from CDN) so it
works in this Flask site with no build step. Reduced-motion users get a clean static final composition.

A **React version** of the same section (`BrainLabLandingHero`) is included in the `react/` folder for
when the site is rebuilt in React/Next/Vite — see `react/README.md`.

## Files
```
app.py                          Flask backend, SQLite, routes, domain data, Groq chat
templates/index.html            Main one-page site
templates/_landing.html         Cinematic scroll landing markup (included at top of index)
templates/domain.html           Themed per-background pages
templates/admin_login.html      Admin login
templates/admin_dashboard.html  Admin dashboard
static/css/style.css            Light theme, animations, slider, responsive form
static/css/landing.css          Cinematic landing styles
static/js/main.js               Parallax / tilt / slider / form / chat / counters
static/js/landing.js            GSAP ScrollTrigger cinematic timeline
static/img/logo-*.png           Official logo (full / mark / original-on-black)
.env / .env.example             Config incl. GROQ_API_KEY for the AI counsellor
react/BrainLabLandingHero.jsx   Standalone React version of the landing
react/BrainLabLandingHero.css   Styles for the React version
react/README.md                 React install + usage
```

## Logo
Your official logo (`WhatsApp Image ... .jpeg`) was used directly — the solid black background was keyed out to
transparent so the exact brand mark and wordmark float on white. The original is preserved as `logo-original.png`.
To swap in a different file, drop it in `static/img/` and update the `src` paths in the templates.
