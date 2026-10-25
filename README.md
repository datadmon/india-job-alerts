# India Job Alerts: new IIMJobs, Hirist, Foundit and Instahyre jobs every morning

Get the **new jobs** from India's recruiter job boards, **IIMJobs** (MBA, finance, consulting, management), **Hirist.tech** (tech), **Foundit** (formerly Monster India) and **Instahyre** (startups and product companies), every morning as a **GitHub issue, Slack, Discord or Telegram message** and a growing **CSV file**, without writing or maintaining a scraper. You pick the keywords, cities and experience range; a GitHub Actions workflow in your copy of this repository does the rest, and every job reaches you once.

It is built for job seekers who follow a few searches, recruiters and staffing agencies tracking new mandates, and anyone building an India job feed. Put `*` as the keyword to follow **every job on a board** (IIMJobs posts about 170 a day, Hirist about 140, Foundit about 2,800).

![Outputs](https://img.shields.io/badge/output-GitHub%20issue%20%7C%20Slack%20%7C%20Telegram%20%7C%20Discord%20%7C%20CSV-blue) ![License: MIT](https://img.shields.io/badge/license-MIT-green)

## What you get

Every run adds the new jobs to [`data/jobs.csv`](data/jobs.csv), rewrites [`data/latest.md`](data/latest.md) and sends the alerts you switched on. Real runs on 26 October 2026 with the default [`config.json`](config.json) searches (capped at 10 jobs each) returned 39 jobs; one row per board:

| Board | Posted | Job | Company | Location | Experience |
|---|---|---|---|---|---|
| iimjobs | 2026-10-24 | [Product Manager - Payments & Core Ledger Systems - FinTech](https://www.iimjobs.com/j/product-manager-payments-core-ledger-systems-fintech-1741760) | HiringBlaze | Bangalore | 4-8 yrs |
| hirist | 2026-10-24 | [Data Engineer - BigQuery/Python](https://www.hirist.tech/j/data-engineer-bigquerypython-1679994) | Trident Automobiles | Bangalore | 4-8 yrs |
| foundit | 2026-10-25 | [Senior Data Analyst](https://www.foundit.in/job/senior-data-analyst-tally-solutions-pvt-ltd-bengaluru-bangalore-india-69558782) | tally solutions pvt ltd | Bengaluru, India | 2-4 yrs |
| instahyre | 2026-10-19 | [Product Software Engineer II - 476](https://www.instahyre.com/job-447419-product-software-engineer-ii-476-at-amazon-bangalore/) | Amazon | Bangalore | 2-5 yrs |

Each CSV row has the board, posting date, title, company, locations, experience range, salary in LPA when the employer discloses it, applicant count (IIMJobs, Hirist, Foundit), up to eight skills, the job URL and a stable ID such as `iimjobs:1741760`.

## Set it up in five minutes

1. Click **Use this template → Create a new repository** (public or private, your choice).
2. Create a free [Apify](https://apify.com) account and copy your API token from **Console → Settings → Integrations**. In your new repository open **Settings → Secrets and variables → Actions → New repository secret**, name it `APIFY_TOKEN` and paste the token.
3. Add the workflow: in your repository click **Add file → Create new file**, name it `.github/workflows/job-alerts.yml`, paste the contents of [`setup/job-alerts.yml`](setup/job-alerts.yml) and commit.
4. Edit [`config.json`](config.json) with your searches, then open **Actions → India job alerts → Run workflow** once to test it. From then on it runs every day at 08:00 IST.

The first run delivers the jobs posted in the last three days (seven for the Instahyre example); every later run delivers only the jobs it has not delivered before.

## Choose your searches

```json
{
  "searches": [
    {"board": "iimjobs", "keywords": ["product manager"], "locations": ["Bangalore"]},
    {"board": "hirist", "keywords": ["data engineer"]},
    {"board": "foundit", "keywords": ["data analyst"]},
    {"board": "instahyre", "keywords": ["python"], "locations": ["Bangalore"], "postedWithinDays": 7, "maxJobs": 20}
  ],
  "defaults": {"postedWithinDays": 3, "maxJobs": 50, "descriptions": false},
  "maxCostPerSearchUsd": 0.5,
  "notify": {"githubIssue": true, "maxJobsPerMessage": 20}
}
```

| Field | What it does |
|---|---|
| `board` | `iimjobs`, `hirist`, `foundit` or `instahyre`. |
| `keywords` | Role or skill words, one board search each. `["*"]` means every job on the board in the window. |
| `locations` | Optional cities as the board lists them: `Bangalore`, `Mumbai`, `Delhi NCR`, `Gurgaon`, `Pune`, `Hyderabad`, `Chennai`, `Remote`. |
| `minExperience`, `maxExperience` | Optional experience range in years. |
| `postedWithinDays` | Only jobs posted in the last N days (default 3; IIMJobs and Hirist count calendar days in India time). Instahyre has no date filter on the site, so it is not sent there unless you set it; when you do, the Actor reads each job's page to check the date (slower, and skipped jobs are not charged). |
| `maxJobs` | Cap per search and run (default 50). |
| `descriptions` | `true` adds the full job description to the Actor output (more expensive on IIMJobs and Hirist until 2 November 2026). |
| `maxCostPerSearchUsd` | Hard spending cap per search and run; the Actor stops cleanly when it is reached. |

## Notifications

- **GitHub issue** (on by default): each run with new jobs opens an issue in your repository, and GitHub emails you about it if you watch the repository.
- **Slack**: add an [incoming webhook](https://api.slack.com/messaging/webhooks) URL as the secret `SLACK_WEBHOOK_URL`.
- **Discord**: add a channel webhook URL as `DISCORD_WEBHOOK_URL`.
- **Telegram**: create a bot with [@BotFather](https://t.me/BotFather), then add `TELEGRAM_BOT_TOKEN` and your chat ID as `TELEGRAM_CHAT_ID`.

A channel that fails is reported in the log; the jobs are still saved.

## What it costs

The searches run on [Apify](https://apify.com) Actors that charge per job saved; there is no subscription, and Apify's free plan includes $5 of usage every month. Prices on 26 October 2026 (free plan):

| Board | Price |
|---|---|
| [IIMJobs Jobs Scraper](https://apify.com/data_daemon/iimjobs-jobs-scraper) | $0.002 per job (+$0.002 with descriptions); from 2 Nov 2026 $0.002 per job with the description included + $0.001 per run |
| [Hirist.tech Jobs Scraper](https://apify.com/data_daemon/hirist-jobs-scraper) | same as IIMJobs |
| [Foundit Jobs Scraper](https://apify.com/data_daemon/foundit-jobs-scraper) | $0.0008 per job, description included, + $0.001 per run |
| [Instahyre Jobs Scraper](https://apify.com/data_daemon/instahyre-jobs-scraper) | $0.0008 per job, description included, + $0.001 per run |

The default four searches with about 25 new jobs each per day cost roughly **$0.13 a day, about $4 a month**, inside the free credit. Jobs skipped because you already received them are **never charged**. Check each Actor's pricing tab for current prices.

## How "only new jobs" works

Each search is sent with the Actor's **only new jobs since the last run** mode and a memory name unique to your repository and search. The Actor remembers the job IDs it delivered (in a key-value store in your own Apify account, for 120 days) and skips them before fetching anything, so repeats are neither returned nor charged. Changing a search's settings starts a new memory for it. The script also de-duplicates the CSV by job ID.

## Run it without GitHub Actions

```bash
export APIFY_TOKEN=...
python job_alerts.py --dry-run   # shows what would be sent to each board, runs nothing
python job_alerts.py             # runs the searches, writes data/, sends alerts (Slack/Discord/Telegram from env vars)
```

Python 3.9+ and the standard library only; schedule it with cron or Windows Task Scheduler if you prefer.

## Follow a whole job board

`"keywords": ["*"]` uses the Actors' **All jobs on the board** mode: every listing posted in the window instead of a keyword search. Measured on 26 October 2026: IIMJobs 1,199 jobs in the last 7 days, Hirist 959, Foundit 2,815 in the last day, Instahyre 12,724 open jobs. Raise `maxJobs` accordingly and keep an eye on the cost; the guide [Export every IIMJobs and Hirist job daily](https://datadmon.github.io/guides/iimjobs-hirist-full-board-job-feed/) covers it in detail.

## FAQ

**Is there an official IIMJobs, Hirist, Foundit or Instahyre API?**
No public one. The Actors read the same public JSON the job boards' own websites load, without logins or cookies, and return it as clean rows.

**Can I get the full job description?**
Yes, set `"descriptions": true`. The Actors return the description as HTML and plain text; this script keeps the CSV compact and links to the job page instead.

**Will GitHub stop my scheduled workflow?**
GitHub disables schedules in public repositories after 60 days without activity. The workflow commits new jobs to `data/`, which counts as activity on days with new jobs; if your searches are very narrow, run it manually once in a while.

**Does it collect personal data?**
No. It stores job postings and company names; recruiter names and contact details are not collected.

**Can I use the data from another tool?**
Yes. Read `data/jobs.csv` from Google Sheets (`=IMPORTDATA` on the raw file URL of a public repository), or call the Actors directly from Python, Node.js, n8n, Make or Zapier: see [apify-data-actors-examples](https://github.com/datadmon/apify-data-actors-examples).

## Related

- [apify-data-actors-examples](https://github.com/datadmon/apify-data-actors-examples): Python, Node.js, curl and n8n examples for the same Actors.
- [Daemon Data on Apify](https://apify.com/data_daemon): IIMJobs, Hirist, Foundit, Instahyre, Oracle HCM career sites, India IPO GMP and more as pay-per-result APIs.

## More templates by Daemon Data

- [india-job-alerts](https://github.com/datadmon/india-job-alerts): daily new-job alerts from IIMJobs, Hirist, Foundit and Instahyre.
- [uk-insolvency-monitor](https://github.com/datadmon/uk-insolvency-monitor): alerts when a watchlist company appears in The Gazette (winding-up petitions, administrations).
- [india-ipo-gmp-tracker](https://github.com/datadmon/india-ipo-gmp-tracker): daily IPO GMP table, GMP history and Telegram alerts.

Not affiliated with IIMJobs, Hirist, Foundit or Instahyre. Use the data in line with each site's terms.
