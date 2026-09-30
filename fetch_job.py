"""Fetch job postings to plain-text files in jobs/, so subagents never scrape pages.

Usage:
  python3 fetch_job.py <url> [<url> ...]

Prints one line per input: "OK <url> -> jobs/<slug>.txt" or "FAIL <url>: <reason>".

Many job pages (Ashby, Lever, Workday, most company career sites) load the
description with JavaScript, so a plain HTTP fetch only sees the title. This
script tries each platform's public job API first, then falls back to rendering
the page in headless Chrome.
"""
import html
import json
import re
import sys
import urllib.request
from pathlib import Path
from urllib.parse import parse_qs, urlparse

MIN_WORDS = 150  # anything shorter isn't a real job description
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126 Safari/537.36"


def http(url, data=None):
    req = urllib.request.Request(url, data=data, headers={"User-Agent": UA, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def html_to_text(s):
    s = re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", "", s)
    s = re.sub(r"(?i)<li[^>]*>", "- ", s)
    s = re.sub(r"(?i)<(br|/p|/li|/h\d|/div|/ul|/ol)[^>]*>", "\n", s)
    s = html.unescape(re.sub(r"<[^>]+>", "", s))
    s = re.sub(r"[ \t\xa0]+", " ", s)
    return re.sub(r"\n\s*\n+", "\n\n", s).strip()


def ashby(u):
    m = re.match(r"/([^/]+)/([0-9a-f-]{36})", u.path)
    if u.netloc != "jobs.ashbyhq.com" or not m:
        return None
    org, job_id = m.groups()
    query = ("query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) "
             "{ jobPosting(organizationHostedJobsPageName: $organizationHostedJobsPageName, "
             "jobPostingId: $jobPostingId) { title descriptionHtml } }")
    body = json.dumps({"operationName": "ApiJobPosting", "query": query,
                       "variables": {"organizationHostedJobsPageName": org, "jobPostingId": job_id}})
    post = json.loads(http("https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobPosting", body.encode()))
    post = (post.get("data") or {}).get("jobPosting")
    if not post:
        return None
    return org, post["title"], html_to_text(post["descriptionHtml"])


def greenhouse(u):
    m = re.match(r"/([^/]+)/jobs/(\d+)", u.path)
    if "greenhouse.io" in u.netloc and m:
        org, job_id = m.groups()
    elif "gh_jid" in parse_qs(u.query):
        # Company-hosted page backed by Greenhouse (e.g. stripe.com/...?gh_jid=123).
        org, job_id = u.netloc.split(".")[-2], parse_qs(u.query)["gh_jid"][0]
    else:
        return None
    try:
        post = json.loads(http(f"https://boards-api.greenhouse.io/v1/boards/{org}/jobs/{job_id}"))
    except Exception:
        return None
    return org, post["title"], html_to_text(html.unescape(post["content"]))


def lever(u):
    m = re.match(r"/([^/]+)/([0-9a-f-]{36})", u.path)
    if u.netloc != "jobs.lever.co" or not m:
        return None
    org, job_id = m.groups()
    post = json.loads(http(f"https://api.lever.co/v0/postings/{org}/{job_id}"))
    lists = "\n\n".join(f"{l['text']}\n{html_to_text(l['content'])}" for l in post.get("lists", []))
    text = "\n\n".join(filter(None, [post.get("descriptionPlain"), lists, post.get("additionalPlain")]))
    return org, post["text"], text


def browser(url):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        page = b.new_page(user_agent=UA)
        page.goto(url, wait_until="networkidle", timeout=45000)
        page.wait_for_timeout(1500)
        title, text = page.title(), page.inner_text("body")
        b.close()
    host = urlparse(url).netloc.removeprefix("www.").split(".")[0]
    return host, title, text


def slugify(*parts):
    return re.sub(r"[^a-z0-9]+", "-", " ".join(parts).lower()).strip("-")[:60]


def fetch(url):
    u = urlparse(url)
    for source in (ashby, greenhouse, lever):
        try:
            got = source(u)
        except Exception:
            got = None
        if got and len(got[2].split()) >= MIN_WORDS:
            return got
    got = browser(url)
    if len(got[2].split()) < MIN_WORDS:
        raise ValueError(f"page only had {len(got[2].split())} words; likely blocked, login wall, or expired")
    return got


def main():
    Path("jobs").mkdir(exist_ok=True)
    for url in sys.argv[1:]:
        url = url.strip(",")
        try:
            company, title, text = fetch(url)
            path = Path("jobs") / f"{slugify(company, title)}.txt"
            path.write_text(f"Company: {company}\nRole: {title}\nSource: {url}\n\n{text}\n")
            print(f"OK   {url} -> {path}")
        except Exception as e:
            print(f"FAIL {url}: {e}")


if __name__ == "__main__":
    main()
