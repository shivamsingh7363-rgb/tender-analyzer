# Tender Analyzer — Deployment Guide

## What's in this folder

```
tender-analyzer/
├── main.py              # FastAPI backend (API proxy + file serving)
├── requirements.txt     # Python dependencies
├── render.yaml          # Render.com deployment config
├── static/
│   └── index.html       # Full frontend UI
└── README.md
```

---

## Step 1 — Get your Anthropic API key

1. Go to https://console.anthropic.com
2. Sign up / log in
3. Click **API Keys** in the left sidebar
4. Click **Create Key**, name it "Tender Analyzer", copy it
5. Keep it safe — you'll paste it in Step 4

---

## Step 2 — Upload code to GitHub

1. Go to https://github.com and sign in (create a free account if needed)
2. Click **New repository** (top right → + icon)
3. Name it `tender-analyzer`, set to **Private**, click **Create repository**
4. On the next page, click **uploading an existing file**
5. Drag and drop ALL files from this folder:
   - `main.py`
   - `requirements.txt`
   - `render.yaml`
   - The `static/` folder (with `index.html` inside)
6. Click **Commit changes**

---

## Step 3 — Deploy on Render.com

1. Go to https://render.com and sign up with your GitHub account
2. Click **New +** → **Web Service**
3. Click **Connect** next to your `tender-analyzer` repository
4. Render will auto-detect settings from `render.yaml`. Verify:
   - **Name**: tender-analyzer
   - **Runtime**: Python
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Click **Create Web Service**

---

## Step 4 — Add your API key (critical)

1. After the service is created, go to your service dashboard on Render
2. Click **Environment** in the left sidebar
3. Click **Add Environment Variable**
4. Key: `ANTHROPIC_API_KEY`
5. Value: paste your key from Step 1
6. Click **Save Changes** — Render will automatically redeploy

---

## Step 5 — Access your app

- Your app URL will be: `https://tender-analyzer.onrender.com`
  (or similar — check your Render dashboard)
- Share this URL with your operations team
- The first load may take 30–60 seconds (free tier spins down when idle)

---

## Upgrade tips (optional)

- **Custom domain**: In Render → Settings → Custom Domains, add your own domain
- **Paid tier ($7/mo)**: Eliminates the cold-start delay — app is always live
- **Password protect**: Add a simple API key check in main.py if you want login

---

## Troubleshooting

| Problem | Fix |
|---|---|
| "Analysis failed: Server error" | Check ANTHROPIC_API_KEY is set in Render → Environment |
| Slow first load | Normal on free tier — Render sleeps after 15min inactivity |
| PDF upload fails | Make sure PDF is under 20MB and is a real text-based PDF |
| "API error: 529" | Anthropic servers busy — wait a moment and retry |

---

## Cost estimate

- **Render free tier**: $0/month (with cold starts)
- **Anthropic API**: ~$0.01–0.05 per tender analysis (depending on PDF size)
- Total for 100 analyses/month: roughly ₹100–300
