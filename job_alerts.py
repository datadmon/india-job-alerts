"""India job alerts: the new jobs on IIMJobs, Hirist, Foundit and Instahyre since the last run.

    export APIFY_TOKEN=...            # https://console.apify.com/settings/integrations
    python job_alerts.py              # reads config.json, writes data/, sends the alerts you configured
    python job_alerts.py --dry-run    # prints the actor inputs and exits, nothing is run or charged

Each search in config.json runs one Apify Actor (pay per job saved, no subscription needed) with
"only new jobs since the last run" switched on, so a job is delivered and charged once and never again.
Standard library only; Python 3.9+.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://api.apify.com/v2"
ACTORS = {
    "iimjobs": "data_daemon~iimjobs-jobs-scraper",      # https://apify.com/data_daemon/iimjobs-jobs-scraper
    "hirist": "data_daemon~hirist-jobs-scraper",        # https://apify.com/data_daemon/hirist-jobs-scraper
    "foundit": "data_daemon~foundit-jobs-scraper",      # https://apify.com/data_daemon/foundit-jobs-scraper
    "instahyre": "data_daemon~instahyre-jobs-scraper",  # https://apify.com/data_daemon/instahyre-jobs-scraper
}
COLUMNS = ["board", "postedAt", "title", "company", "locations", "experience", "salaryLpa", "applicants", "skills", "url", "id"]
ROOT = Path(__file__).resolve().parent


def request(method, url, token, body=None, timeout=120):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as res:
        return json.load(res)


def run_actor(actor, run_input, token, max_charge_usd, timeout_secs=900):
    """Start an Actor run, wait for it and return its dataset items."""
    query = urllib.parse.urlencode({"timeout": timeout_secs, "maxTotalChargeUsd": max_charge_usd})
    run = request("POST", f"{API}/acts/{actor}/runs?{query}", token, run_input)["data"]
    while run["status"] in ("READY", "RUNNING"):
        time.sleep(5)
        run = request("GET", f"{API}/actor-runs/{run['id']}", token)["data"]
    if run["status"] != "SUCCEEDED":
        raise RuntimeError(f"{actor} run {run['id']} ended {run['status']}: {run.get('statusMessage')}")
    items, offset = [], 0
    while True:
        page = request("GET", f"{API}/datasets/{run['defaultDatasetId']}/items?clean=1&format=json&limit=1000&offset={offset}", token)
        items += page
        offset += len(page)
        if len(page) < 1000:
            return items, run.get("statusMessage") or ""


def actor_input(search, defaults, feed_id):
    board = search["board"]
    keywords = search.get("keywords") or []
    inp = {
        "onlyNewSinceLastRun": True,
        # One memory per search and per copy of this repository, kept by the Actor in your Apify account.
        "stateName": f"alerts-{feed_id}-{board}-" + hashlib.sha1(json.dumps(search, sort_keys=True).encode()).hexdigest()[:8],
        "postedWithinDays": search.get("postedWithinDays", defaults.get("postedWithinDays", 3)),
        "maxJobs": search.get("maxJobs", defaults.get("maxJobs", 50)),
        "includeDescription": search.get("descriptions", defaults.get("descriptions", False)),
    }
    if board in ("foundit", "instahyre") and "descriptions" not in search:
        # Same price with or without the description there, and Instahyre's posting date and experience
        # come from the job page, so always ask for it.
        inp["includeDescription"] = True
    if keywords in (["*"], ["all"]) or search.get("allJobs"):
        inp["allJobs"] = True  # every job on the board in the posting window
    else:
        inp["queries"] = keywords
    for key in ("locations", "minExperience", "maxExperience"):
        if search.get(key) not in (None, [], ""):
            inp[key] = search[key]
    if board == "instahyre" and "postedWithinDays" not in search:
        # Instahyre has no date filter on the site; only-new mode alone keeps the feed new.
        inp.pop("postedWithinDays")
    return inp


def normalize(board, job):
    company = job.get("company") or {}
    lo, hi = job.get("experienceMinYears"), job.get("experienceMaxYears")
    smin, smax = job.get("salaryMinLpa"), job.get("salaryMaxLpa")
    return {
        "board": board,
        "postedAt": (job.get("postedAt") or "")[:10],
        "title": job.get("title") or "",
        "company": company.get("name") or ("(confidential)" if company.get("confidential") else ""),
        "locations": ", ".join(job.get("locations") or []),
        "experience": f"{lo}-{hi} yrs" if lo is not None and hi is not None else "",
        "salaryLpa": f"{smin}-{smax}" if smin is not None and smax is not None else "",
        "applicants": job.get("applicants") if job.get("applicants") is not None else "",
        "skills": ", ".join((job.get("skills") or [])[:8]),
        "url": job.get("url") or "",
        "id": job.get("dedupKey") or f"{board}:{job.get('id')}",
    }


def write_outputs(rows, data_dir):
    data_dir.mkdir(parents=True, exist_ok=True)
    all_csv = data_dir / "jobs.csv"
    known = set()
    if all_csv.exists():
        with all_csv.open(encoding="utf-8", newline="") as f:
            known = {r["id"] for r in csv.DictReader(f)}
    fresh = [r for r in rows if r["id"] not in known]
    new_file = not all_csv.exists()
    with all_csv.open("a", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        if new_file:
            writer.writeheader()
        writer.writerows(fresh)
    today = dt.date.today().isoformat()
    lines = [f"# New jobs on {today}", "", f"{len(fresh)} new job(s). The full history is in [jobs.csv](jobs.csv).", ""]
    if fresh:
        lines += ["| Board | Posted | Job | Company | Location | Experience |", "|---|---|---|---|---|---|"]
        for r in fresh[:200]:
            cell = lambda s: str(s).replace("|", "/")
            lines.append(f"| {r['board']} | {r['postedAt']} | [{cell(r['title'])}]({r['url']}) | {cell(r['company'])} | {cell(r['locations'])} | {r['experience']} |")
    (data_dir / "latest.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (data_dir / "latest.json").write_text(json.dumps(fresh, ensure_ascii=False, indent=1), encoding="utf-8")
    return fresh


def post_json(url, payload, headers=None):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **(headers or {})})
    urllib.request.urlopen(req, timeout=60).read()


def notify(rows, cfg):
    if not rows:
        return
    top = rows[: cfg.get("maxJobsPerMessage", 20)]
    text = f"{len(rows)} new job(s) on India job boards\n" + "\n".join(
        f"• {r['title']} — {r['company']} ({r['locations'] or r['board']}) {r['url']}" for r in top)
    if len(rows) > len(top):
        text += f"\n…and {len(rows) - len(top)} more in data/latest.md"
    channels = []
    if os.environ.get("SLACK_WEBHOOK_URL"):
        channels.append(("Slack", os.environ["SLACK_WEBHOOK_URL"], {"text": text}, None))
    if os.environ.get("DISCORD_WEBHOOK_URL"):
        channels.append(("Discord", os.environ["DISCORD_WEBHOOK_URL"], {"content": text[:1990]}, None))
    if os.environ.get("TELEGRAM_BOT_TOKEN") and os.environ.get("TELEGRAM_CHAT_ID"):
        channels.append(("Telegram", f"https://api.telegram.org/bot{os.environ['TELEGRAM_BOT_TOKEN']}/sendMessage",
                         {"chat_id": os.environ["TELEGRAM_CHAT_ID"], "text": text[:4000], "disable_web_page_preview": True}, None))
    repo, gh = os.environ.get("GITHUB_REPOSITORY"), os.environ.get("GITHUB_TOKEN")
    if cfg.get("githubIssue", True) and repo and gh:
        body = "\n".join(f"- [{r['title']}]({r['url']}) — {r['company']}, {r['locations']} ({r['board']}, {r['postedAt']})" for r in rows[:100])
        channels.append(("GitHub issue", f"https://api.github.com/repos/{repo}/issues",
                         {"title": f"{len(rows)} new jobs on {dt.date.today().isoformat()}", "body": body},
                         {"Authorization": f"Bearer {gh}", "Accept": "application/vnd.github+json"}))
    for name, url, payload, headers in channels:
        try:  # one broken channel must not lose the run's data
            post_json(url, payload, headers)
            print("notified:", name)
        except urllib.error.URLError as err:
            print(f"could not notify {name}: {err}", file=sys.stderr)
    if not channels:
        print("no notification channel configured; see data/latest.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", default=str(ROOT / "config.json"))
    parser.add_argument("--dry-run", action="store_true", help="print the Actor inputs and exit")
    args = parser.parse_args()
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    feed_id = hashlib.sha1((os.environ.get("GITHUB_REPOSITORY") or "local").encode()).hexdigest()[:8]
    defaults = cfg.get("defaults", {})
    plans = [(s["board"], actor_input(s, defaults, feed_id)) for s in cfg["searches"]]
    for board, inp in plans:
        if board not in ACTORS:
            sys.exit(f"Unknown board {board!r}; use one of {', '.join(ACTORS)}")
    if args.dry_run:
        for board, inp in plans:
            print(board, json.dumps(inp))
        return
    token = os.environ.get("APIFY_TOKEN")
    if not token:
        sys.exit("Set APIFY_TOKEN (Apify Console > Settings > Integrations). In GitHub: Settings > Secrets > Actions.")
    rows, failures = [], []
    for board, inp in plans:
        try:
            items, status = run_actor(ACTORS[board], inp, token, cfg.get("maxCostPerSearchUsd", 0.5))
            rows += [normalize(board, j) for j in items]
            print(f"{board} {inp.get('queries') or 'all jobs'}: {len(items)} new | {status}")
        except (urllib.error.URLError, RuntimeError) as err:
            failures.append(f"{board}: {err}")
            print("FAILED", board, err, file=sys.stderr)
    fresh = write_outputs(rows, ROOT / cfg.get("dataDir", "data"))
    notify(fresh, cfg.get("notify", {}))
    if failures and not rows:
        sys.exit("All searches failed: " + "; ".join(failures))


if __name__ == "__main__":
    main()
