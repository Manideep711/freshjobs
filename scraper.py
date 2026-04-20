"""
Job Leads Scraper — runs once daily at midnight IST
Scrapes: Nitter (Twitter/X), Internshala, Naukri
Output: public/jobs.json
"""

import json
import time
import random
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ── dependencies: pip install playwright beautifulsoup4 requests
# ── after install: playwright install chromium
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────

OUTPUT_FILE = Path("public/jobs.json")
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

IST = timezone(timedelta(hours=5, minutes=30))

# Nitter public instances — we rotate if one is down
NITTER_INSTANCES = [
    "https://nitter.privacydev.net",
    "https://nitter.poast.org",
    "https://nitter.cz",
]

TWITTER_QUERIES = [
    "hiring fresher remote India javascript",
    "hiring fresher India MERN stack",
    "hiring fresher India java fullstack",
    "hiring fresher India machine learning",
    "hiring fresher India data analyst",
    "internship fresher India remote 2024 2025",
    "fresher job opening India fullstack",
    "we are hiring fresher India javascript react",
]

INTERNSHALA_URLS = [
    "https://internshala.com/jobs/computer-science-engineering-jobs/",
    "https://internshala.com/internships/computer-science-engineering-internship/",
    "https://internshala.com/jobs/web-development-jobs/",
    "https://internshala.com/jobs/data-science-jobs/",
    "https://internshala.com/internships/machine-learning-internship/",
]

NAUKRI_URLS = [
    "https://www.naukri.com/fresher-jobs?k=fresher&experience=0",
    "https://www.naukri.com/mern-stack-jobs-for-freshers",
    "https://www.naukri.com/java-developer-fresher-jobs",
    "https://www.naukri.com/machine-learning-fresher-jobs",
    "https://www.naukri.com/data-analyst-fresher-jobs",
]

# Role classification keywords
ROLE_KEYWORDS = {
    "mern_fullstack": ["mern", "react", "node", "javascript", "js", "frontend", "full stack js", "fullstack js", "next.js", "nextjs", "vue", "angular"],
    "java_fullstack": ["java", "spring", "spring boot", "hibernate", "j2ee", "java fullstack", "java developer"],
    "machine_learning": ["machine learning", "ml", "deep learning", "nlp", "computer vision", "pytorch", "tensorflow", "ai engineer", "artificial intelligence"],
    "data_analyst": ["data analyst", "data analysis", "sql", "tableau", "power bi", "excel", "business analyst", "data science"],
    "internship": ["intern", "internship", "stipend"],
}

def random_delay(min_s=2, max_s=5):
    """Human-like random delay between requests."""
    time.sleep(random.uniform(min_s, max_s))

def classify_role(text: str) -> list[str]:
    text_lower = text.lower()
    roles = []
    for role, keywords in ROLE_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            roles.append(role)
    if not roles:
        roles.append("general_fresher")
    return roles

def is_remote_or_india(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in [
        "remote", "india", "bangalore", "bengaluru", "mumbai", "delhi",
        "hyderabad", "chennai", "pune", "wfh", "work from home", "pan india"
    ])

def clean_text(text: str) -> str:
    return " ".join(text.split()).strip()

# ─────────────────────────────────────────────
# SCRAPER 1 — NITTER (Twitter/X)
# ─────────────────────────────────────────────

def scrape_nitter(page, query: str, instance: str) -> list[dict]:
    jobs = []
    try:
        url = f"{instance}/search?q={query.replace(' ', '+')}&f=tweets&since=1d"
        page.goto(url, timeout=20000)
        random_delay(2, 4)
        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        tweets = soup.select(".timeline-item")
        for tweet in tweets[:15]:  # cap per query
            try:
                content_el = tweet.select_one(".tweet-content")
                if not content_el:
                    continue
                text = clean_text(content_el.get_text())
                if len(text) < 40:
                    continue

                # filter: must look like a job post
                job_signals = ["hiring", "opening", "opportunity", "apply", "intern", "fresher", "job", "role", "position"]
                if not any(sig in text.lower() for sig in job_signals):
                    continue

                if not is_remote_or_india(text):
                    continue

                # get tweet link
                link_el = tweet.select_one(".tweet-link")
                tweet_link = ""
                if link_el:
                    href = link_el.get("href", "")
                    tweet_link = f"https://twitter.com{href}" if href.startswith("/") else href

                # get username
                user_el = tweet.select_one(".username")
                username = user_el.get_text(strip=True) if user_el else "unknown"

                # get timestamp
                time_el = tweet.select_one(".tweet-date a")
                posted_at = time_el.get("title", "") if time_el else ""

                roles = classify_role(text)

                jobs.append({
                    "id": f"tw_{hash(text) & 0xFFFFFF}",
                    "source": "Twitter/X",
                    "title": text[:80] + ("..." if len(text) > 80 else ""),
                    "description": text,
                    "company": username,
                    "location": "Remote/India" if "remote" in text.lower() else "India",
                    "roles": roles,
                    "type": "internship" if "intern" in text.lower() else "full_time",
                    "link": tweet_link,
                    "posted_at": posted_at,
                    "scraped_at": datetime.now(IST).isoformat(),
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [nitter] error on {instance}: {e}")
    return jobs


# ─────────────────────────────────────────────
# SCRAPER 2 — INTERNSHALA
# ─────────────────────────────────────────────

def scrape_internshala(page, url: str) -> list[dict]:
    jobs = []
    try:
        page.goto(url, timeout=25000)
        random_delay(3, 6)
        # scroll to load more
        page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        random_delay(1, 2)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        listings = soup.select(".individual_internship, .job-internship-card, [id^='internship_']")

        for item in listings[:20]:
            try:
                title_el = item.select_one(".profile, .job-title, h3")
                company_el = item.select_one(".company_name, .company-name")
                location_el = item.select_one(".location_link, .location")
                stipend_el = item.select_one(".stipend, .salary")
                link_el = item.select_one("a[href]")

                title = clean_text(title_el.get_text()) if title_el else "N/A"
                company = clean_text(company_el.get_text()) if company_el else "N/A"
                location = clean_text(location_el.get_text()) if location_el else "India"
                stipend = clean_text(stipend_el.get_text()) if stipend_el else ""
                href = link_el.get("href", "") if link_el else ""
                link = f"https://internshala.com{href}" if href.startswith("/") else href

                if title == "N/A":
                    continue

                roles = classify_role(f"{title} {url}")
                is_intern = "internship" in url or "intern" in title.lower()

                jobs.append({
                    "id": f"is_{hash(title+company) & 0xFFFFFF}",
                    "source": "Internshala",
                    "title": title,
                    "description": f"{title} at {company}. {stipend}",
                    "company": company,
                    "location": location if location else "India",
                    "roles": roles,
                    "type": "internship" if is_intern else "full_time",
                    "stipend": stipend,
                    "link": link,
                    "posted_at": "",
                    "scraped_at": datetime.now(IST).isoformat(),
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [internshala] error: {e}")
    return jobs


# ─────────────────────────────────────────────
# SCRAPER 3 — NAUKRI
# ─────────────────────────────────────────────

def scrape_naukri(page, url: str) -> list[dict]:
    jobs = []
    try:
        page.goto(url, timeout=25000)
        random_delay(3, 6)
        page.evaluate("window.scrollTo(0, 600)")
        random_delay(2, 3)

        html = page.content()
        soup = BeautifulSoup(html, "html.parser")

        listings = soup.select(".jobTuple, article.jobTupleHeader, .srp-jobtuple-wrapper")

        for item in listings[:20]:
            try:
                title_el = item.select_one(".title, a.title, .jobTitle")
                company_el = item.select_one(".companyInfo span, .comp-name")
                location_el = item.select_one(".location span, .loc-wrap")
                exp_el = item.select_one(".experience span")
                link_el = item.select_one("a.title, a[href*='naukri.com/job']")

                title = clean_text(title_el.get_text()) if title_el else "N/A"
                company = clean_text(company_el.get_text()) if company_el else "N/A"
                location = clean_text(location_el.get_text()) if location_el else "India"
                experience = clean_text(exp_el.get_text()) if exp_el else "0-1 years"
                href = link_el.get("href", "") if link_el else ""

                if title == "N/A":
                    continue

                roles = classify_role(f"{title} {url}")

                jobs.append({
                    "id": f"nk_{hash(title+company) & 0xFFFFFF}",
                    "source": "Naukri",
                    "title": title,
                    "description": f"{title} at {company}. Experience: {experience}",
                    "company": company,
                    "location": location,
                    "roles": roles,
                    "type": "internship" if "intern" in title.lower() else "full_time",
                    "experience": experience,
                    "link": href,
                    "posted_at": "",
                    "scraped_at": datetime.now(IST).isoformat(),
                })
            except Exception:
                continue
    except Exception as e:
        print(f"  [naukri] error: {e}")
    return jobs


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def deduplicate(jobs: list[dict]) -> list[dict]:
    seen = set()
    unique = []
    for job in jobs:
        key = job["id"]
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique

def main():
    print(f"[{datetime.now(IST).strftime('%Y-%m-%d %H:%M IST')}] Starting job scrape...")
    all_jobs = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
            ]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            locale="en-IN",
            timezone_id="Asia/Kolkata",
        )
        # hide webdriver flag
        context.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        page = context.new_page()

        # ── Nitter
        print("\n[1/3] Scraping Twitter/X via Nitter...")
        nitter_instance = NITTER_INSTANCES[0]
        for i, query in enumerate(TWITTER_QUERIES):
            print(f"  Query {i+1}/{len(TWITTER_QUERIES)}: {query[:40]}...")
            # rotate instance if needed
            instance = NITTER_INSTANCES[i % len(NITTER_INSTANCES)]
            results = scrape_nitter(page, query, instance)
            all_jobs.extend(results)
            print(f"  → {len(results)} leads found")
            random_delay(3, 7)  # be polite

        # ── Internshala
        print("\n[2/3] Scraping Internshala...")
        for i, url in enumerate(INTERNSHALA_URLS):
            print(f"  Page {i+1}/{len(INTERNSHALA_URLS)}: {url.split('/')[-2]}")
            results = scrape_internshala(page, url)
            all_jobs.extend(results)
            print(f"  → {len(results)} leads found")
            random_delay(4, 8)

        # ── Naukri
        print("\n[3/3] Scraping Naukri...")
        for i, url in enumerate(NAUKRI_URLS):
            print(f"  Page {i+1}/{len(NAUKRI_URLS)}: {url.split('/')[-1][:40]}")
            results = scrape_naukri(page, url)
            all_jobs.extend(results)
            print(f"  → {len(results)} leads found")
            random_delay(4, 8)

        browser.close()

    # deduplicate and save
    unique_jobs = deduplicate(all_jobs)
    unique_jobs.sort(key=lambda x: x["scraped_at"], reverse=True)

    output = {
        "last_updated": datetime.now(IST).isoformat(),
        "total": len(unique_jobs),
        "jobs": unique_jobs,
    }

    OUTPUT_FILE.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n✅ Done! {len(unique_jobs)} unique jobs saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
