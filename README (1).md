# NSE pattern scanner — setup guide

You need two free accounts: GitHub (to host the code) and Streamlit
Community Cloud (to host the live app). Both sign up with your email,
no card needed.

## 1. Put the code on GitHub
1. Go to github.com, sign up / log in.
2. Click **New repository**. Name it e.g. `nse-pattern-scanner`. Keep it
   Public (Streamlit's free tier needs that). Create it.
3. On the new repo page, click **uploading an existing file** and drag
   in every file from this folder (`app.py`, `scanner.py`,
   `watchlist.txt`, `requirements.txt`, and the `.github` folder — make
   sure the `.github/workflows/scan.yml` path is preserved). Commit.

## 2. Deploy the dashboard
1. Go to share.streamlit.io, sign in with your GitHub account.
2. Click **New app**, pick the `nse-pattern-scanner` repo, branch
   `main`, main file `app.py`. Click **Deploy**.
3. In a minute or two you'll get a public URL like
   `https://your-app.streamlit.app` — open it, that's your dashboard.

## 3. Turn on the background scanner
The GitHub Actions workflow already in `.github/workflows/scan.yml`
runs automatically every 5 minutes during NSE market hours once the
code is on GitHub — nothing else to set up. You can check it ran under
the **Actions** tab of your repo.

## 4. Using it
- Edit your watchlist in the sidebar of the app and click **Save
  watchlist**.
- Keep the dashboard tab open (background tab is fine) to get
  browser/desktop notifications the moment a pattern fires.
- The first time you open it, click **Allow** when the browser asks
  for notification permission.

## Notes
- Data comes from yfinance for free — it's delayed by a few minutes,
  fine for 5m/15m/1h/1D pattern scanning, not tick-by-tick.
- The squeeze-breakout logic lives in `scanner.py` — this is where
  we'll add more patterns later.
- Browser notifications only fire while the tab is open somewhere
  (can be minimized/background). For alerts while your browser is
  fully closed, we'd need to add a separate always-on notification
  channel later.
