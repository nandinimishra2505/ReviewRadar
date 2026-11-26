import os
import re
from collections import Counter
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

POSITIVE = {"great", "excellent", "amazing", "love", "good", "fast", "helpful", "perfect", "easy", "happy", "smooth", "reliable", "best", "wonderful", "quick"}
NEGATIVE = {"bad", "poor", "terrible", "awful", "broken", "late", "slow", "worse", "worst", "refund", "defect", "damaged", "rude", "issue", "problem", "disappointed", "fail", "missing"}
CATEGORIES = {
    "Delivery": ["delivery", "shipping", "courier", "late", "arrived", "package", "shipment"],
    "Product Quality": ["quality", "broken", "defect", "damaged", "faulty", "durable", "material"],
    "Customer Support": ["support", "service", "staff", "agent", "response", "rude", "help"],
    "Pricing & Payments": ["price", "cost", "expensive", "cheap", "payment", "billing", "refund", "charge"],
    "App & Website": ["app", "website", "login", "crash", "interface", "bug", "screen", "checkout"],
    "Other": []
}

def clean_text(value):
    return re.sub(r"\s+", " ", re.sub(r"[^a-zA-Z0-9\s']", " ", str(value).lower())).strip()

def sentiment(text):
    words = clean_text(text).split()
    score = sum(w in POSITIVE for w in words) - sum(w in NEGATIVE for w in words)
    if score >= 1: return "Positive"
    if score <= -1: return "Negative"
    return "Neutral"

def categorize(text):
    words = set(clean_text(text).split())
    scores = {category: sum(term in words for term in terms) for category, terms in CATEGORIES.items() if category != "Other"}
    best = max(scores, key=scores.get) if scores else "Other"
    return best if scores.get(best, 0) else "Other"

def cluster_topics(texts):
    if len(texts) < 3:
        return ["General feedback"] * len(texts)
    try:
        vectorizer = TfidfVectorizer(stop_words="english", max_features=500, ngram_range=(1, 2))
        matrix = vectorizer.fit_transform(texts)
        distinct = len(set(texts))
        k = max(2, min(5, distinct, len(texts) // 2))
        model = KMeans(n_clusters=k, random_state=42, n_init=10)
        labels = model.fit_predict(matrix)
        terms = vectorizer.get_feature_names_out()
        names = {}
        for cluster in set(labels):
            top = model.cluster_centers_[cluster].argsort()[::-1][:3]
            keywords = [terms[i] for i in top if model.cluster_centers_[cluster][i] > 0]
            names[cluster] = " / ".join(keywords[:2]) or f"Topic {cluster + 1}"
        return [names[x] for x in labels]
    except Exception:
        return ["General feedback"] * len(texts)

def analyze_reviews(df):
    result = df.copy()
    result.columns = [str(c).strip().lower() for c in result.columns]
    result["review"] = result["review"].fillna("").astype(str)
    result["date"] = pd.to_datetime(result.get("date", pd.Timestamp.today()), errors="coerce").fillna(pd.Timestamp.today())
    result["product"] = result.get("product", "General").fillna("General").astype(str)
    result["sentiment"] = result["review"].apply(sentiment)
    result["category"] = result["review"].apply(categorize)
    result["topic"] = cluster_topics(result["review"].apply(clean_text).tolist())
    result["severity"] = result.apply(lambda r: 3 if r["sentiment"] == "Negative" and any(x in clean_text(r["review"]).split() for x in ["broken", "refund", "damaged", "fraud", "worst"]) else (2 if r["sentiment"] == "Negative" else 1), axis=1)
    result["date"] = result["date"].dt.strftime("%Y-%m-%d")
    return result

def build_insights(df):
    if df.empty: return {}
    total = len(df)
    negatives = df[df.sentiment == "Negative"]
    category_counts = negatives.groupby("category").size().sort_values(ascending=False)
    daily = df.copy()
    daily["date"] = pd.to_datetime(daily["date"])
    daily_negative = daily[daily.sentiment == "Negative"].groupby("date").size().sort_index()
    anomaly_dates = []
    if len(daily_negative) >= 4:
        baseline = daily_negative.rolling(3, min_periods=2).mean().shift(1)
        for date, value in daily_negative.items():
            base = baseline.get(date)
            if pd.notna(base) and base >= 1 and value >= max(3, base * 2):
                anomaly_dates.append({"date": date.strftime("%Y-%m-%d"), "negative_reviews": int(value), "baseline": round(float(base), 1)})
    priorities = []
    for category, count in category_counts.items():
        subset = negatives[negatives.category == category]
        severity = float(subset.severity.mean()) if len(subset) else 1
        # Recent growth compares the latest half with the earlier half.
        ordered = subset.sort_values("date")
        mid = max(1, len(ordered) // 2)
        earlier, recent = len(ordered.iloc[:mid]), len(ordered.iloc[mid:])
        growth = max(0, (recent - earlier) / max(earlier, 1))
        score = round(count * severity * (1 + min(growth, 2) * 0.25), 2)
        priorities.append({"category": category, "count": int(count), "severity": round(severity, 1), "growth": round(growth * 100), "score": score})
    priorities.sort(key=lambda x: x["score"], reverse=True)
    return {
        "total": total,
        "sentiment": {k: int(v) for k, v in df.sentiment.value_counts().to_dict().items()},
        "categories": [{"name": str(k), "count": int(v)} for k, v in category_counts.items()],
        "priorities": priorities,
        "anomalies": anomaly_dates,
        "topics": [{"name": str(k), "count": int(v)} for k, v in df.topic.value_counts().head(6).items()]
    }

def summarize_feedback(df):
    if df.empty: return "No feedback available yet. Load the sample dataset or upload a CSV."
    positives = df[df.sentiment == "Positive"]
    negatives = df[df.sentiment == "Negative"]
    top_issue = negatives.category.value_counts().index[0] if len(negatives) else "No dominant complaint"
    top_issue_count = int(negatives.category.value_counts().iloc[0]) if len(negatives) else 0
    base = (f"Analysis of {len(df)} customer reviews found {len(positives)} positive, "
            f"{len(negatives)} negative and {len(df) - len(positives) - len(negatives)} neutral reviews. "
            f"The most frequent negative-feedback category is {top_issue} ({top_issue_count} reviews).")
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key: return base + " Add GROQ_API_KEY to enable AI-generated recommendations."
    try:
        import requests
        prompt = "Act as a customer experience analyst. Based only on these review analytics, write 3 concise actionable recommendations:\n" + base
        response = requests.post("https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": "llama-3.3-70b-versatile", "messages": [{"role": "user", "content": prompt}], "temperature": 0.3},
            timeout=20)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception:
        return base + " AI summary is temporarily unavailable; showing the built-in summary instead."
