# FreshLeads.dev — Daily Job Scraper for Freshers

Scrapes Twitter/X (via Nitter), Internshala, and Naukri every midnight IST.
Filters for freshers, remote/India roles, and your tech stack.
Runs 100% free on GitHub Actions.

---

## 📁 Project Structure

```
freshjobs/
├── scraper.py                  ← main scraper
├── public/
│   ├── index.html              ← dashboard (open this in browser)
│   └── jobs.json               ← scraped data (auto-updated by Actions)
├── .github/
│   └── workflows/
│       └── scrape.yml          ← GitHub Actions cron job
├── requirements.txt
└── README.md
```

---

## ⚡ Quick Setup (15 minutes)

### Step 1 — Create a GitHub repo

1. Go to github.com → New repository
2. Name it `freshjobs` (or anything)
3. Make it **Public** (needed for free GitHub Actions minutes)
4. Clone it locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/freshjobs.git
   cd freshjobs
   ```

### Step 2 — Add the files

Copy these files into your cloned repo:
- `scraper.py`
- `public/index.html`
- `public/jobs.json` (sample data, gets overwritten by Actions)
- `.github/workflows/scrape.yml`
- `requirements.txt`

### Step 3 — Push to GitHub

```bash
git add .
git commit -m "init: freshjobs scraper"
git push
```

### Step 4 — Enable GitHub Actions

1. Go to your repo on GitHub
2. Click **Actions** tab
3. If prompted, click **"I understand my workflows, go ahead and enable them"**
4. You'll see **"Nightly Job Scraper"** workflow listed

### Step 5 — Enable GitHub Pages (for dashboard)

1. Repo Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: `main`, Folder: `/public`
4. Save → your dashboard will be live at:
   `https://YOUR_USERNAME.github.io/freshjobs/`

---

## 🚀 Running the Scraper Manually (first time)

```bash
# install dependencies
pip install -r requirements.txt
playwright install chromium

# run scraper
python scraper.py
```

This fills `public/jobs.json` with real data.
Then just open `public/index.html` in your browser!

---

## ⏰ Automatic Schedule

The scraper runs every day at **12:00 AM IST (18:30 UTC)**.
This is low-traffic time — minimal load on the servers we scrape.

To trigger manually from GitHub:
1. Go to Actions tab
2. Click "Nightly Job Scraper"
3. Click "Run workflow" → Run

---

## 🎛️ Dashboard Features

- **Search** by company, title, or tech stack
- **Filter by role**: MERN/JS, Java Fullstack, ML/AI, Data Analyst, General Fresher
- **Filter by location**: Remote / India / All
- **Filter by source**: Twitter, Internshala, Naukri
- **Filter by type**: Full-time / Internship
- **Bookmark** jobs (saved in browser localStorage)
- **Stats bar**: total leads, remote count, internships, sources

---

## 🔧 Customizing Queries

Edit the top of `scraper.py` to add your own search queries:

```python
TWITTER_QUERIES = [
    "hiring fresher remote India javascript",
    # add your own here!
]
```

---

## ⚠️ Ethical Scraping Notes

This scraper:
- Runs **once per day** at low-traffic midnight hours
- Uses **random human-like delays** between requests (3–8 seconds)
- Does **not** hit any server continuously
- Only reads **publicly visible** job posts
- Uses **Nitter** (open-source frontend) instead of Twitter's paid API

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Nitter returns empty | Try a different Nitter instance in `NITTER_INSTANCES` list |
| Playwright not found | Run `playwright install chromium` |
| GitHub Actions fails | Check Actions tab logs for the exact error |
| Dashboard shows no jobs | Run `python scraper.py` locally first |
