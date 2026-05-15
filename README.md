# Mark — Trading Dashboard

Live portfolio tracker + AI agent for your 17 US stock positions.

## What it does

| Feature | Details |
|---------|---------|
| Live prices | Yahoo Finance via `yfinance`, refreshes every 5 min |
| Both currencies | USD + THB (live exchange rate) |
| Alerts | Auto-flags positions at ≤ −7% and ≤ −30% |
| Mark's News | Portfolio brief every 2 days + per-ticker news feed |
| Chat with Mark | AI analyst powered by Claude — ask anything about your portfolio |

---

## Deploy to Streamlit Cloud (free hosting)

### Step 1 — Push to GitHub
1. Create a **private** GitHub repo (e.g. `mark-dashboard`)
2. Push this `trading-dashboard/` folder as the repo root:
```bash
cd trading-dashboard
git init
git add .
git commit -m "initial"
git remote add origin https://github.com/YOUR_USER/mark-dashboard.git
git push -u origin main
```

### Step 2 — Deploy on Streamlit Cloud
1. Go to **share.streamlit.io**
2. Sign in with GitHub
3. Click **New app** → select your `mark-dashboard` repo → branch `main` → file `app.py`
4. Click **Deploy**

### Step 3 — Add your Anthropic API key (for Mark's AI chat)
1. In Streamlit Cloud → three-dot menu → **Settings → Secrets**
2. Add:
```toml
ANTHROPIC_API_KEY = "sk-ant-api03-..."
```
3. Click **Save** — Mark's chat and AI brief activate instantly

Get an API key at **console.anthropic.com**.
Cost: roughly $0.01–0.05 per conversation (Sonnet model).

---

## Run locally (optional)

```bash
cd trading-dashboard
pip install -r requirements.txt

# For Mark's AI features locally:
echo 'ANTHROPIC_API_KEY = "sk-ant-..."' > .streamlit/secrets.toml

streamlit run app.py
```

Open http://localhost:8501

---

## Portfolio positions

Seeded from your May 15, 2026 snapshot (17 positions, ~$8,237 USD total).
Prices update live from Yahoo Finance. Share counts are estimated from your snapshot values.

To update cost basis or add/remove positions, edit the `PORTFOLIO` dict at the top of `app.py`.
