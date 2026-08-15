# NSE pattern scanner — setup guide

Everything you asked for, combined into one app:
- Squeeze → breakout pattern scan (5m/15m/1h/1D), including the last 30 days of history
- Two lists: your tracking list, and an auto-built NSE universe (market cap ≥ ₹1500cr) — promote any universe setup to tracking with one click
- Company announcements for tracking-list stocks
- Fundamentals tab: ratios, quarterly results, custom screens, peer comparison, best-effort shareholding
- In-app + browser/desktop notifications
- Runs 24/7 in the background, free

You need two free accounts: GitHub (to host the code) and Streamlit
Community Cloud (to host the live app). Both sign up with your email,
no card needed.

## 1. Put the code on GitHub
1. Go to github.com, sign up / log in.
2. Click **New repository**. Name it e.g. `nse-pattern-scanner`. Keep it
   Public (Streamlit's free tier needs that). Create it.
3. Click **uploading an existing file** and drag in every file from
   this folder — `app.py`, `scanner.py`, `announcements.py`,
   `fundamentals.py`, `fundamentals_builder.py`, `universe_builder.py`,
   `watchlist.txt`, `requirements.txt`, and the whole `.github` folder
   (make sure the path `.github/workflows/*.yml` is preserved — check
   the file list on GitHub afterwards to confirm). Commit.

## 2. Deploy the dashboard
1. Go to share.streamlit.io, sign in with your GitHub account.
2. Click **New app**, pick the `nse-pattern-scanner` repo, branch
   `main`, main file `app.py`. Click **Deploy**.
3. You'll get a public URL like `https://your-app.streamlit.app` —
   that's your dashboard.

## 3. Turn on the background jobs
These run automatically once the code is on GitHub — check the
**Actions** tab of your repo to confirm they're listed and running:
- **NSE pattern scan** — every 15 minutes, 24/7
- **NSE announcements poll** — every 5 minutes, 24/7
- **Build stock universe** — weekly, fills `universe.json`
- **Build fundamentals** — weekly, fills `fundamentals.json`

**Important first-time step**: universe and fundamentals data is empty
until their weekly job runs once. Go to the **Actions** tab, click
"Build stock universe" → **Run workflow**, wait for it to finish, then
do the same for "Build fundamentals" — otherwise the Universe and
Fundamentals tabs will look empty for up to a week.

## 4. Using it
- Edit your tracking list in the sidebar, click **Save tracking list**.
- Browse the **NSE universe** tab for setups outside your list — click
  **Add to tracking** on anything you like.
- Check the **Fundamentals** tab for ratios, results, custom screens,
  and peer comparison.
- Keep the dashboard tab open (background tab is fine) for
  browser/desktop notifications — click **Allow** when prompted.

## Known limitations (being upfront)
- **Data delay**: yfinance is free but a few minutes behind true
  real-time. Fine for 5m+ scanning, not tick-by-tick.
- **BSE isn't included** — the universe is NSE's largest ~500 stocks
  (Nifty 500), which covers effectively all liquid, sizeable stocks,
  but not BSE-only listings.
- **Announcements and shareholding data use unofficial NSE endpoints**
  — not officially documented, so field names or availability could
  shift if NSE changes their site. If these sections look wrong or
  empty, that's the most likely reason.
- **Fundamentals coverage varies** — some ratios/quarterly figures may
  be missing for smaller stocks, since NSE data on Yahoo Finance is
  inconsistent in places. Missing values show as blank rather than
  guessed.
- **Concall summaries were dropped** — no reliable free source exists
  for these, so they're intentionally not part of this app.
- **Notifications need the tab open** somewhere (can be backgrounded)
  — fully closing the browser stops them.
