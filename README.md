# ReviewRadar – AI-Powered Customer Feedback Intelligence System

ReviewRadar is a Flask-based customer feedback analytics application. It processes customer reviews, classifies sentiment, identifies recurring complaint categories, clusters similar topics, flags unusual increases in negative feedback and ranks complaint areas for investigation.

## Features

- Sentiment classification: Positive, Negative and Neutral
- Rule-assisted complaint categorization
- TF-IDF vectorization and K-Means topic clustering
- Time-based negative-feedback anomaly detection
- Complaint prioritization using volume, severity and recent growth
- Optional LLM-generated recommendations through the Groq API
- CSV upload, SQLite persistence and an interactive dashboard

## Tech stack

Python, Flask, Pandas, Scikit-learn, SQLite, HTML, CSS, JavaScript, Chart.js.

## Run locally

```bash
git clone https://github.com/YOUR-USERNAME/ReviewRadar.git
cd ReviewRadar
python -m venv venv
```

Activate the environment:

**Windows PowerShell**
```powershell
.\venv\Scripts\Activate.ps1
```

**macOS / Linux**
```bash
source venv/bin/activate
```

Install dependencies and start:

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`.

## Input CSV format

The `review` column is required. `date`, `product` and `rating` are optional.

```csv
review,date,product,rating
"Delivery was late and the package was damaged",2026-10-01,Headphones,1
"Excellent quality and fast delivery",2026-10-02,Headphones,5
```

Use **Load sample dataset** on the dashboard to explore the application without preparing a CSV.

## Optional LLM integration

The application works without an API key. To enable LLM-generated recommendations, create a `.env` file or set the environment variable:

```bash
GROQ_API_KEY=your_api_key
```

The current implementation uses Groq's OpenAI-compatible chat completions endpoint and the `llama-3.3-70b-versatile` model. Never commit API keys to GitHub.

## Deployment

This repository includes a `Procfile` for platforms that support Gunicorn.

Build/install command:
```bash
pip install -r requirements.txt
```

Start command:
```bash
gunicorn app:app
```

Set `SECRET_KEY` in the deployment environment. Set `GROQ_API_KEY` only if you want LLM summaries.

**Persistence note:** SQLite is suitable for local use and demos. On hosting platforms with ephemeral filesystems, uploaded data may reset after redeployment/restart. Use a persistent disk or managed database for production deployments.

## Project structure

```text
ReviewRadar/
├── app.py
├── analyzer.py
├── database.py
├── data/
│   └── sample_reviews.csv
├── templates/
│   ├── base.html
│   └── index.html
├── static/
│   └── css/
│       └── style.css
├── requirements.txt
├── Procfile
├── runtime.txt
├── .env.example
├── .gitignore
└── README.md
```

## Current limitations and next steps

- Sentiment classification is a lightweight lexicon-based baseline, not a fine-tuned language model.
- Complaint categories use transparent keyword rules; domain-specific taxonomies can be added.
- Anomaly detection requires enough dated observations to establish a baseline.
- For production, add authentication, stronger validation, background processing, tests and a persistent managed database.

## Resume description

**ReviewRadar – AI-Powered Customer Feedback Intelligence System** | Python, NLP, Flask, Pandas, Scikit-learn, SQLite, LLM

- Built a Flask-based feedback analytics platform to classify customer sentiment and automatically categorize recurring complaints.
- Applied TF-IDF and K-Means clustering to group similar feedback and uncover recurring customer issues.
- Developed time-series anomaly detection and a complaint prioritization engine using issue volume, severity and growth patterns.
- Integrated an optional LLM-powered insight generator to summarize feedback and recommend actionable customer-experience improvements.
