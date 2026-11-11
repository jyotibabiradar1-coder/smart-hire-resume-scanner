"""
AI Resume Screening and Ranking System (CLI Engine)
Processes resumes against a target job description using TF-IDF,
cosine similarity, and calibrated machine learning ranking.
"""
import os
import sys

# Configure UTF-8 stdout encoding for Windows console compatibility
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import string
import pandas as pd
import numpy as np
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

# Determine base directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------
# OPTIONAL IMPORTS FOR PDF / DOCX
# ------------------------------------------
try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx2txt
except ImportError:
    docx2txt = None

try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

# ------------------------------------------
# NLP & SPACY SETUP
# ------------------------------------------
try:
    nltk.download('stopwords', quiet=True)
    from nltk.corpus import stopwords
    STOPWORDS = set(stopwords.words('english'))
except Exception:
    STOPWORDS = set()

import spacy
try:
    nlp = spacy.load("en_core_web_sm")
except Exception:
    print("⏳ Downloading SpaCy language model (en_core_web_sm)...")
    spacy.cli.download("en_core_web_sm")
    nlp = spacy.load("en_core_web_sm")

# ------------------------------------------
# TEXT EXTRACTION FUNCTIONS
# ------------------------------------------
def extract_text_from_pdf(file_path):
    text = ""
    if pdfplumber is not None:
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text += (page.extract_text() or "") + "\n"
            if text.strip():
                return text
        except Exception:
            pass
    if PdfReader is not None:
        try:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text += (page.extract_text() or "") + "\n"
        except Exception:
            pass
    return text

def extract_text_from_docx(file_path):
    if docx2txt is not None:
        try:
            return docx2txt.process(file_path)
        except Exception:
            pass
    return ""

def clean_text(text):
    if not text:
        return ""
    text = text.lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    doc = nlp(text)
    tokens = [
        token.lemma_ for token in doc
        if token.text not in STOPWORDS and token.is_alpha and len(token.text) > 1
    ]
    return " ".join(tokens)

# ------------------------------------------
# ENSURE JOB DESCRIPTION & RESUMES EXIST
# ------------------------------------------
jd_path = os.path.join(BASE_DIR, "job_description.txt")
resume_folder = os.path.join(BASE_DIR, "resumes")
os.makedirs(resume_folder, exist_ok=True)

if not os.path.exists(jd_path):
    with open(jd_path, "w", encoding="utf-8") as f:
        f.write(
            "Job Title: Senior Python & Machine Learning Engineer\n"
            "Requirements: Python, Machine Learning, Scikit-Learn, Pandas, NumPy, NLP, SpaCy, NLTK, SQL, FastAPI, Docker."
        )

with open(jd_path, "r", encoding="utf-8") as f:
    raw_jd = f.read()

cleaned_jd = clean_text(raw_jd)
if not cleaned_jd:
    cleaned_jd = "python machine learning scikit nlp data developer"

# ------------------------------------------
# READ ALL RESUMES
# ------------------------------------------
resumes = []
names = []

for file in sorted(os.listdir(resume_folder)):
    file_path = os.path.join(resume_folder, file)
    if os.path.isdir(file_path):
        continue

    text = ""
    lower = file.lower()
    if lower.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif lower.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    elif lower.endswith(".txt"):
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                text = f.read()
        except Exception:
            text = ""

    cleaned = clean_text(text)
    if cleaned.strip():
        resumes.append(cleaned)
        names.append(file)
    else:
        # Fallback raw word tokens if cleaning returned empty
        resumes.append(text.lower())
        names.append(file)

if not resumes:
    print("⚠️ No resumes found in 'resumes/' folder. Please add resumes (.pdf, .docx, .txt).")
    sys.exit(0)

# ------------------------------------------
# TF-IDF FEATURE EXTRACTION + SIMILARITY
# ------------------------------------------
vectorizer = TfidfVectorizer(stop_words="english", sublinear_tf=True)
all_docs = [cleaned_jd] + resumes
tfidf = vectorizer.fit_transform(all_docs)

similarity_scores = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()

# ------------------------------------------
# MACHINE LEARNING CALIBRATION & RANKING
# ------------------------------------------
# Sigmoid probability calibration based on similarity
alpha = 10.0
center = 0.40
pred_probs = 1.0 / (1.0 + np.exp(-alpha * (similarity_scores - center)))

# If multiple classes exist, train Logistic Regression
if len(resumes) >= 4:
    y_pseudo = (similarity_scores >= np.median(similarity_scores)).astype(int)
    if len(set(y_pseudo)) > 1:
        try:
            lr_model = LogisticRegression(max_iter=200)
            lr_model.fit(tfidf[1:], y_pseudo)
            pred_probs = lr_model.predict_proba(tfidf[1:])[:, 1]
        except Exception:
            pass

# Create results dataframe
results = pd.DataFrame({
    "Candidate": names,
    "Similarity_Score": np.round(similarity_scores, 4),
    "Shortlist_Probability": np.round(pred_probs, 4)
})

results["Status"] = results["Shortlist_Probability"].apply(
    lambda p: "Selected" if p >= 0.50 else "Rejected"
)

results = results.sort_values(by="Shortlist_Probability", ascending=False).reset_index(drop=True)
results.index = results.index + 1
results.index.name = "Rank"

# ------------------------------------------
# OUTPUT RESULTS
# ------------------------------------------
print("\n" + "="*70)
print("🏆 FINAL RESUME RANKING RESULTS")
print("="*70)
print(results.to_string())
print("="*70)

out_csv = os.path.join(BASE_DIR, "resume_ranking_results.csv")
results.to_csv(out_csv)
print(f"\n✅ Results successfully saved to: {out_csv}")
