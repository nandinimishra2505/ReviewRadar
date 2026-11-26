import os
from flask import Flask, render_template, request, redirect, url_for, flash
import pandas as pd
from werkzeug.utils import secure_filename
from database import init_db, save_reviews, get_reviews, get_stats
from analyzer import analyze_reviews, build_insights, summarize_feedback

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "reviewradar-development-key")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024
ALLOWED_EXTENSIONS = {"csv"}

init_db()

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def refresh_analysis():
    reviews = get_reviews()
    if not reviews:
        return [], {}, "Upload reviews or load the sample dataset to begin."
    df = pd.DataFrame(reviews)
    analyzed = analyze_reviews(df)
    insights = build_insights(analyzed)
    summary = summarize_feedback(analyzed)
    return analyzed.to_dict(orient="records"), insights, summary

@app.route("/")
def index():
    rows, insights, summary = refresh_analysis()
    stats = get_stats()
    return render_template("index.html", reviews=rows[:12], stats=stats,
                           insights=insights, summary=summary)

@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("file")
    if not file or not file.filename:
        flash("Please choose a CSV file.", "error")
        return redirect(url_for("index"))
    if not allowed_file(file.filename):
        flash("Only CSV files are supported.", "error")
        return redirect(url_for("index"))
    try:
        df = pd.read_csv(file)
        required = {"review"}
        if not required.issubset(set(df.columns.str.lower())):
            flash("CSV must contain a 'review' column. Optional columns: date, product, rating.", "error")
            return redirect(url_for("index"))
        df.columns = [c.strip().lower() for c in df.columns]
        if "date" not in df: df["date"] = pd.Timestamp.today().strftime("%Y-%m-%d")
        if "product" not in df: df["product"] = "General"
        if "rating" not in df: df["rating"] = None
        df = df[["review", "date", "product", "rating"]].dropna(subset=["review"])
        if df.empty:
            flash("No valid reviews found in the CSV.", "error")
        else:
            save_reviews(df.to_dict(orient="records"))
            flash(f"Successfully imported {len(df)} reviews.", "success")
    except Exception as exc:
        flash(f"Could not read CSV: {exc}", "error")
    return redirect(url_for("index"))

@app.route("/sample")
def sample():
    path = os.path.join(os.path.dirname(__file__), "data", "sample_reviews.csv")
    df = pd.read_csv(path)
    save_reviews(df.to_dict(orient="records"))
    flash(f"Loaded {len(df)} sample reviews.", "success")
    return redirect(url_for("index"))

@app.route("/clear", methods=["POST"])
def clear():
    from database import clear_reviews
    clear_reviews()
    flash("All reviews have been cleared.", "success")
    return redirect(url_for("index"))

@app.route("/api/insights")
def api_insights():
    rows, insights, summary = refresh_analysis()
    return {"insights": insights, "summary": summary, "reviews": rows}

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=False)
