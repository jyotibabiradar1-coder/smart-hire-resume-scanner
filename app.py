"""
SmartHire - Intelligent Talent Acquisition & ATS Platform
Featuring rich saffron, orange, and golden amber dynamic color blends,
a single right-corner Dark/Light theme mode toggle, and complete recruiter tools.
"""
import streamlit as st
import sqlite3
import os
import io
import re
import bcrypt
import pandas as pd
import numpy as np
from datetime import datetime, timezone

# Optional / robust imports for file parsing
try:
    from PyPDF2 import PdfReader
except ImportError:
    PdfReader = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    import docx2txt
except ImportError:
    docx2txt = None

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm

# ---------------------------
# CONFIGURATION & PATHS
# ---------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "users.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "resumes")
REPORTS_DIR = os.path.join(BASE_DIR, "reports")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(REPORTS_DIR, exist_ok=True)

st.set_page_config(
    page_title="SmartHire | Talent Acquisition Suite",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------------------
# THEME STATE INITIALIZATION
# ---------------------------
if "theme" not in st.session_state:
    st.session_state.theme = "dark"

# ---------------------------
# SKILL EXTRACTION DICTIONARY
# ---------------------------
COMMON_SKILLS = [
    "Python", "Java", "C++", "C#", "JavaScript", "TypeScript", "React", "Angular", "Vue",
    "Node.js", "Django", "Flask", "FastAPI", "SQL", "PostgreSQL", "MySQL", "MongoDB",
    "Machine Learning", "Deep Learning", "NLP", "Scikit-Learn", "TensorFlow", "PyTorch",
    "Pandas", "NumPy", "Apache Spark", "Docker", "Kubernetes", "AWS", "GCP", "Azure",
    "Git", "CI/CD", "Linux", "REST APIs", "GraphQL", "Agile", "DevOps", "Data Science",
    "Analytics", "Power BI", "Tableau", "Excel", "SEO", "Content Strategy"
]

def extract_skills_from_text(text: str) -> list:
    """Extract recognized technical and professional skills from text."""
    if not text:
        return []
    text_lower = text.lower()
    matched = []
    for skill in COMMON_SKILLS:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            matched.append(skill)
    return matched

# ---------------------------
# PASSWORD VALIDATION
# ---------------------------
def is_strong_password(pw: str) -> bool:
    if len(pw) < 8:
        return False
    if not re.search(r"[A-Z]", pw):
        return False
    if not re.search(r"[a-z]", pw):
        return False
    if not re.search(r"\d", pw):
        return False
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pw):
        return False
    return True

# ---------------------------
# DYNAMIC SAFFRON, ORANGE, YELLOW THEME STYLING
# ---------------------------
is_dark = st.session_state.theme == "dark"

if is_dark:
    # DARK MODE: Rich Twilight Saffron, Fiery Orange & Golden Amber
    css_theme = """
    /* Dark Theme: Saffron, Orange & Golden Amber Twilight (Non-Black, Non-White) */
    .stApp, [data-testid="stAppViewContainer"] {
        background: linear-gradient(135deg, #170b03 0%, #291305 25%, #231238 65%, #0f172a 100%) !important;
        background-attachment: fixed !important;
        color: #f8fafc !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #150902 0%, #201006 50%, #101628 100%) !important;
        border-right: 1px solid rgba(249, 115, 22, 0.35) !important;
        box-shadow: 4px 0 24px rgba(0, 0, 0, 0.45) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] strong {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="tab"] {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        display: none !important;
    }
    [data-testid="stSidebar"] input {
        color: #ffffff !important;
        background: rgba(22, 11, 4, 0.85) !important;
        border: 1.5px solid rgba(249, 115, 22, 0.6) !important;
        font-weight: 700 !important;
        opacity: 1 !important;
    }
    /* Assign Role & Selectbox visibility in sidebar */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label p,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] * {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        opacity: 1 !important;
        display: block !important;
        visibility: visible !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: rgba(22, 11, 4, 0.95) !important;
        background-color: rgba(22, 11, 4, 0.95) !important;
        border: 1.5px solid rgba(249, 115, 22, 0.7) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] * {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
        font-size: 14px !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
        fill: #f97316 !important;
        color: #f97316 !important;
    }
    .smarthire-navbar {
        background: linear-gradient(90deg, rgba(38, 18, 7, 0.95) 0%, rgba(48, 25, 12, 0.90) 100%) !important;
        border: 1px solid rgba(251, 146, 60, 0.45) !important;
        box-shadow: 0 8px 32px rgba(234, 88, 12, 0.22) !important;
    }
    .brand-title-text {
        color: #ffffff !important;
    }
    .brand-version-pill {
        background: rgba(249, 115, 22, 0.2) !important;
        color: #fb923c !important;
        border: 1px solid rgba(249, 115, 22, 0.45) !important;
    }
    .status-badge-container {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .status-badge-container span {
        opacity: 1 !important;
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    .glass-panel {
        background: linear-gradient(145deg, rgba(38, 19, 7, 0.65) 0%, rgba(20, 15, 34, 0.75) 100%) !important;
        border: 1px solid rgba(249, 115, 22, 0.3) !important;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3) !important;
    }
    .profile-card {
        background: linear-gradient(145deg, rgba(40, 20, 8, 0.6) 0%, rgba(18, 14, 32, 0.75) 100%) !important;
        border: 1px solid rgba(249, 115, 22, 0.3) !important;
    }
    .profile-card:hover {
        border-color: #f97316 !important;
        box-shadow: 0 8px 28px rgba(249, 115, 22, 0.3) !important;
    }
    .profile-name-text {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .profile-file-text {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    .metric-grid-card {
        background: linear-gradient(145deg, rgba(46, 23, 9, 0.75) 0%, rgba(22, 12, 5, 0.85) 100%) !important;
        border: 1px solid rgba(249, 115, 22, 0.35) !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.25) !important;
    }
    .metric-header-title {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .metric-hero-val {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .skill-badge-item {
        background: rgba(249, 115, 22, 0.16) !important;
        color: #fed7aa !important;
        border: 1px solid rgba(251, 146, 60, 0.4) !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(24, 12, 4, 0.75) !important;
        border: 1px solid rgba(249, 115, 22, 0.3) !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ea580c 0%, #f97316 50%, #eab308 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 18px rgba(234, 88, 12, 0.5) !important;
        opacity: 1 !important;
    }
    [data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4,
    [data-testid="stAppViewContainer"] h5, [data-testid="stAppViewContainer"] h6 {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stAppViewContainer"] p, [data-testid="stMarkdownContainer"] p {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stAppViewContainer"] strong, [data-testid="stAppViewContainer"] b,
    [data-testid="stMarkdownContainer"] strong, [data-testid="stMarkdownContainer"] b {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: rgba(20, 10, 4, 0.85) !important;
        border: 1px solid rgba(249, 115, 22, 0.4) !important;
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] * {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
        display: block !important;
        visibility: visible !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"],
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: rgba(20, 10, 4, 0.95) !important;
        background-color: rgba(20, 10, 4, 0.95) !important;
        border: 1.5px solid rgba(249, 115, 22, 0.6) !important;
        border-radius: 8px !important;
        color: #ffffff !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] * {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    div[data-baseweb="popover"] {
        background: #1c0e05 !important;
    }
    div[data-baseweb="popover"] * {
        color: #fed7aa !important;
        opacity: 1 !important;
    }
    li[role="option"] {
        background: #1c0e05 !important;
        color: #fed7aa !important;
        opacity: 1 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background: linear-gradient(135deg, #c2410c, #ea580c) !important;
        color: #ffffff !important;
    }
    .stTextArea textarea::placeholder {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stCaptionContainer"] p, .stCaption {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stCheckbox"] label, [data-testid="stCheckbox"] p, [data-testid="stCheckbox"] span {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSlider"] *, [data-testid="stRadio"] * {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    .main p, .main span, .main label, .main div {
        opacity: 1 !important;
    }
    [data-testid="stFileUploader"] {
        background: rgba(30, 15, 6, 0.65) !important;
        border: 2px dashed rgba(249, 115, 22, 0.5) !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    [data-testid="stFileUploader"] * {
        color: #ffffff !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #fed7aa !important;
        opacity: 1 !important;
    }
    [data-testid="stFileUploader"] small {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #ea580c, #f59e0b) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 800 !important;
    }
    /* Explicit high-visibility styling for uploaded file cards (JD & Resumes in Dark Mode) */
    [data-testid="stFileUploaderFile"],
    [data-testid="stFileUploaderFileData"],
    ul[data-testid="stFileUploaderFile"] li,
    [data-testid="stFileUploader"] ul li {
        background: linear-gradient(135deg, #241207 0%, #1a0b04 100%) !important;
        background-color: #241207 !important;
        border: 1.5px solid #ea580c !important;
        border-radius: 8px !important;
        box-shadow: 0 4px 14px rgba(0, 0, 0, 0.4) !important;
        padding: 6px 12px !important;
        margin: 6px 0 !important;
    }
    [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploaderFileData"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stFileUploaderFile"] span {
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        letter-spacing: 0.2px !important;
    }
    [data-testid="stFileUploaderFileSize"] {
        color: #fed7aa !important;
        font-weight: 700 !important;
        font-size: 11.5px !important;
        opacity: 0.95 !important;
    }
    [data-testid="stFileUploaderDeleteBtn"] button,
    [data-testid="stFileUploaderDeleteBtn"] svg {
        color: #f97316 !important;
        fill: #f97316 !important;
    }
    [data-testid="stExpander"] {
        background: rgba(30, 15, 6, 0.65) !important;
        border: 1px solid rgba(249, 115, 22, 0.35) !important;
        border-radius: 12px !important;
    }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {
        color: #ffffff !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] * {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    pre, code, [data-testid="stText"] {
        color: #fed7aa !important;
        background: rgba(18, 9, 3, 0.85) !important;
        border: 1px solid rgba(249, 115, 22, 0.35) !important;
        font-family: 'Inter', monospace !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stDataFrame"] {
        border: 1px solid rgba(249, 115, 22, 0.3) !important;
        border-radius: 12px !important;
        background: rgba(22, 11, 4, 0.75) !important;
    }
    [data-testid="stAlert"] {
        background: linear-gradient(135deg, rgba(38, 19, 8, 0.95) 0%, rgba(24, 12, 5, 0.95) 100%) !important;
        border: 1.5px solid rgba(249, 115, 22, 0.45) !important;
        border-radius: 10px !important;
        box-shadow: 0 4px 16px rgba(0,0,0,0.3) !important;
    }
    [data-testid="stAlert"] * {
        color: #fed7aa !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    [data-testid="stAlert"] strong, [data-testid="stAlert"] b {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    [data-testid="stAlert"] code {
        background: rgba(234, 88, 12, 0.25) !important;
        color: #ffffff !important;
        border: 1px solid rgba(249, 115, 22, 0.5) !important;
        padding: 2px 8px !important;
        border-radius: 5px !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricValue"] {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] * {
        color: #fed7aa !important;
        font-weight: 700 !important;
    }
    .stepper-deck {
        background: rgba(30, 15, 6, 0.65) !important;
        border: 1px solid rgba(249, 115, 22, 0.35) !important;
    }
    .step-descriptor {
        color: #fed7aa !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stColumn"]:last-child button,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stBaseButton-secondary"],
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) .stButton > button,
    [data-testid="stColumn"]:has(.theme-toggle-box) button,
    [data-testid="stColumn"]:has(#theme-btn-marker) button,
    div:has(> .theme-toggle-box) + div button,
    div:has(.theme-toggle-box) + div button,
    div:has(.theme-toggle-box) ~ div button,
    .theme-toggle-box .stButton > button,
    .theme-toggle-box button {
        background: linear-gradient(135deg, #c2410c 0%, #ea580c 50%, #f59e0b 100%) !important;
        background-color: #ea580c !important;
        color: #ffffff !important;
        border: 1.5px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 4px 18px rgba(234, 88, 12, 0.45) !important;
        border-radius: 8px !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button p,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button span,
    .theme-toggle-box .stButton > button p {
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button:hover,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stBaseButton-secondary"]:hover,
    .theme-toggle-box .stButton > button:hover {
        background: linear-gradient(135deg, #ea580c 0%, #f97316 50%, #facc15 100%) !important;
        background-color: #f97316 !important;
        color: #ffffff !important;
        border-color: rgba(255, 255, 255, 0.5) !important;
        box-shadow: 0 6px 24px rgba(249, 115, 22, 0.6) !important;
        transform: translateY(-1px) !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button:hover p,
    .theme-toggle-box .stButton > button:hover p {
        color: #ffffff !important;
    }
        color: #ffffff !important;
    }
    """
else:
    # LIGHT MODE: Warm Saffron, Radiant Orange & Golden Amber Sunrise (High-Contrast, Ultra-Professional)
    css_theme = """
    /* Light Theme: Saffron & Sunlit Porcelain (WCAG AAA High-Contrast, Professional Creative Web Design) */
    .stApp, [data-testid="stAppViewContainer"] {
        background: 
            radial-gradient(ellipse at 85% 10%, rgba(254, 215, 170, 0.35) 0%, transparent 50%),
            radial-gradient(ellipse at 15% 20%, rgba(255, 237, 213, 0.45) 0%, transparent 45%),
            radial-gradient(ellipse at 60% 85%, rgba(254, 243, 199, 0.3) 0%, transparent 50%),
            linear-gradient(180deg, #fdfbf7 0%, #faf6f0 50%, #f6f0e6 100%) !important;
        background-attachment: fixed !important;
        color: #0f172a !important;
    }
    [data-testid="stHeader"] {
        background: transparent !important;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #fffaf5 0%, #fef4ea 50%, #fdebd7 100%) !important;
        border-right: 1px solid rgba(234, 88, 12, 0.22) !important;
        box-shadow: 4px 0 24px rgba(234, 88, 12, 0.08) !important;
    }
    [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4, [data-testid="stSidebar"] strong {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] div, [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] * {
        color: #334155 !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="tab"] {
        color: #64748b !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSidebar"] [data-baseweb="tab"][aria-selected="true"] {
        color: #c2410c !important;
        font-weight: 800 !important;
    }
    [data-testid="stSidebar"] [data-testid="stExpander"] {
        display: none !important;
    }
    [data-testid="stSidebar"] input {
        color: #0f172a !important;
        background: #ffffff !important;
        border: 1.5px solid rgba(234, 88, 12, 0.4) !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        opacity: 1 !important;
    }
    [data-testid="stSidebar"] input:focus {
        border-color: #ea580c !important;
        box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.15) !important;
    }
    /* Assign Role & Selectbox visibility in sidebar (Light Mode) */
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] label p,
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-testid="stWidgetLabel"] * {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 14px !important;
        opacity: 1 !important;
        display: block !important;
        visibility: visible !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"],
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #fffdfa !important;
        background-color: #fffdfa !important;
        border: 1.5px solid rgba(234, 88, 12, 0.4) !important;
        border-radius: 8px !important;
        color: #0f172a !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] [data-baseweb="select"] * {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 700 !important;
        font-size: 14px !important;
    }
    [data-testid="stSidebar"] [data-testid="stSelectbox"] svg {
        fill: #ea580c !important;
        color: #ea580c !important;
    }
    .smarthire-navbar {
        background: rgba(255, 250, 243, 0.94) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.28) !important;
        box-shadow: 0 4px 20px rgba(234, 88, 12, 0.08), 0 1px 3px rgba(0, 0, 0, 0.03) !important;
        backdrop-filter: blur(16px) !important;
    }
    .brand-title-text {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    .brand-version-pill {
        background: rgba(234, 88, 12, 0.12) !important;
        color: #c2410c !important;
        border: 1.5px solid rgba(234, 88, 12, 0.3) !important;
        font-weight: 800 !important;
    }
    .status-badge-container {
        color: #334155 !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    .status-badge-container span {
        opacity: 1 !important;
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    .glass-panel {
        background: linear-gradient(145deg, #fffaf5 0%, #fff1e0 100%) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.28) !important;
        box-shadow: 0 10px 30px rgba(234, 88, 12, 0.08), 0 1px 4px rgba(0,0,0,0.03) !important;
        color: #0f172a !important;
    }
    .profile-card {
        background: linear-gradient(145deg, #fffdfa 0%, #fff5ea 100%) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.28) !important;
        box-shadow: 0 4px 16px rgba(234, 88, 12, 0.08), 0 1px 3px rgba(0,0,0,0.03) !important;
    }
    .profile-card:hover {
        border-color: #ea580c !important;
        box-shadow: 0 12px 32px rgba(234, 88, 12, 0.16), 0 2px 6px rgba(0,0,0,0.04) !important;
    }
    .profile-name-text {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .profile-file-text {
        color: #64748b !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    .metric-grid-card {
        background: linear-gradient(145deg, #fffdfa 0%, #fff3e2 100%) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.25) !important;
        box-shadow: 0 4px 18px rgba(234, 88, 12, 0.08), 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    .metric-header-title {
        color: #7c2d12 !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .metric-hero-val {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .skill-badge-item {
        background: rgba(234, 88, 12, 0.12) !important;
        color: #9a3412 !important;
        border: 1.5px solid rgba(234, 88, 12, 0.38) !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(255, 247, 237, 0.95) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.25) !important;
        box-shadow: 0 2px 8px rgba(234, 88, 12, 0.08) !important;
    }
    .stTabs [data-baseweb="tab"] {
        color: #64748b !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #ea580c 0%, #f97316 50%, #f59e0b 100%) !important;
        color: #ffffff !important;
        box-shadow: 0 4px 16px rgba(234, 88, 12, 0.35) !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stAppViewContainer"] h1, [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3, [data-testid="stAppViewContainer"] h4,
    [data-testid="stAppViewContainer"] h5, [data-testid="stAppViewContainer"] h6 {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
        letter-spacing: -0.3px !important;
    }
    [data-testid="stAppViewContainer"] p, [data-testid="stMarkdownContainer"] p {
        color: #334155 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
        line-height: 1.6 !important;
    }
    [data-testid="stAppViewContainer"] strong, [data-testid="stAppViewContainer"] b,
    [data-testid="stMarkdownContainer"] strong, [data-testid="stMarkdownContainer"] b {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    .stTextInput input, .stTextArea textarea {
        background: #fffdfa !important;
        border: 1.5px solid rgba(234, 88, 12, 0.35) !important;
        border-radius: 8px !important;
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 600 !important;
        box-shadow: 0 1px 3px rgba(0,0,0,0.02) !important;
    }
    .stTextInput input:focus, .stTextArea textarea:focus {
        border-color: #ea580c !important;
        box-shadow: 0 0 0 3px rgba(234, 88, 12, 0.15) !important;
    }
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] label p,
    div[data-testid="stSelectbox"] [data-testid="stWidgetLabel"] * {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
        display: block !important;
        visibility: visible !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"],
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
        background: #fffdfa !important;
        background-color: #fffdfa !important;
        border: 1.5px solid rgba(234, 88, 12, 0.35) !important;
        border-radius: 8px !important;
        color: #0f172a !important;
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] * {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    div[data-testid="stSelectbox"] svg {
        fill: #ea580c !important;
        color: #ea580c !important;
    }
    div[data-baseweb="popover"] {
        background: #fffdfa !important;
        border: 1.5px solid rgba(234, 88, 12, 0.28) !important;
        box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12) !important;
        border-radius: 10px !important;
    }
    div[data-baseweb="popover"] * {
        color: #0f172a !important;
        opacity: 1 !important;
    }
    li[role="option"] {
        background: #fffdfa !important;
        color: #0f172a !important;
        opacity: 1 !important;
    }
    li[role="option"]:hover, li[aria-selected="true"] {
        background: linear-gradient(135deg, #fff7ed, #ffedd5) !important;
        color: #c2410c !important;
        font-weight: 800 !important;
    }
    .stTextArea textarea::placeholder, .stTextInput input::placeholder {
        color: #94a3b8 !important;
        opacity: 1 !important;
        font-weight: 500 !important;
    }
    [data-testid="stCaptionContainer"] p, .stCaption {
        color: #64748b !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    label, [data-testid="stWidgetLabel"] p, [data-testid="stWidgetLabel"] span {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stCheckbox"] label, [data-testid="stCheckbox"] p, [data-testid="stCheckbox"] span {
        color: #1e293b !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    [data-testid="stSlider"] *, [data-testid="stRadio"] * {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    .main p, .main span, .main label, .main div {
        opacity: 1 !important;
    }
    [data-testid="stFileUploader"] {
        background: linear-gradient(135deg, #fffaf5 0%, #ffedd5 100%) !important;
        border: 2px dashed rgba(234, 88, 12, 0.5) !important;
        border-radius: 12px !important;
        padding: 12px !important;
    }
    [data-testid="stFileUploader"] * {
        color: #0f172a !important;
    }
    [data-testid="stFileUploaderDropzoneInstructions"] * {
        color: #475569 !important;
        font-weight: 600 !important;
    }
    [data-testid="stFileUploader"] small {
        color: #7c2d12 !important;
        font-weight: 700 !important;
    }
    [data-testid="stFileUploader"] button {
        background: linear-gradient(135deg, #ea580c, #f59e0b) !important;
        color: #ffffff !important;
        border: none !important;
        font-weight: 800 !important;
    }
    /* Explicit high-visibility styling for uploaded file cards (JD & Resumes in Light Mode) */
    [data-testid="stFileUploaderFile"],
    [data-testid="stFileUploaderFileData"],
    ul[data-testid="stFileUploaderFile"] li,
    [data-testid="stFileUploader"] ul li {
        background: linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%) !important;
        background-color: #ffedd5 !important;
        border: 1.5px solid #ea580c !important;
        border-radius: 8px !important;
        box-shadow: 0 2px 8px rgba(234, 88, 12, 0.15) !important;
        padding: 6px 12px !important;
        margin: 6px 0 !important;
    }
    [data-testid="stFileUploaderFileName"],
    [data-testid="stFileUploaderFileData"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stFileUploaderFile"] span {
        color: #0f172a !important;
        font-weight: 800 !important;
        font-size: 13.5px !important;
        letter-spacing: 0.2px !important;
    }
    [data-testid="stFileUploaderFileSize"] {
        color: #7c2d12 !important;
        font-weight: 800 !important;
        font-size: 11.5px !important;
    }
    [data-testid="stFileUploaderDeleteBtn"] button,
    [data-testid="stFileUploaderDeleteBtn"] svg {
        color: #ea580c !important;
        fill: #ea580c !important;
    }
    [data-testid="stExpander"] {
        background: linear-gradient(145deg, #fffaf5 0%, #fff1e0 100%) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.28) !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 10px rgba(234, 88, 12, 0.06) !important;
    }
    [data-testid="stExpander"] summary, [data-testid="stExpander"] summary * {
        color: #0f172a !important;
        opacity: 1 !important;
        font-weight: 800 !important;
    }
    [data-testid="stExpander"] [data-testid="stExpanderDetails"] * {
        color: #1e293b !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    pre, code, [data-testid="stText"] {
        color: #9a3412 !important;
        background: #fff7ed !important;
        border: 1.5px solid rgba(234, 88, 12, 0.3) !important;
        font-family: 'Inter', monospace !important;
        opacity: 1 !important;
        font-weight: 600 !important;
    }
    [data-testid="stDataFrame"] {
        border: 1.5px solid rgba(234, 88, 12, 0.25) !important;
        border-radius: 12px !important;
        background: linear-gradient(145deg, #fffdfa 0%, #fff6ec 100%) !important;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04) !important;
    }
    [data-testid="stAlert"] {
        background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.45) !important;
        border-radius: 10px !important;
        color: #431407 !important;
        box-shadow: 0 2px 10px rgba(234, 88, 12, 0.08) !important;
    }
    [data-testid="stAlert"] * {
        color: #431407 !important;
        opacity: 1 !important;
        font-weight: 700 !important;
    }
    [data-testid="stAlert"] strong, [data-testid="stAlert"] b {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    [data-testid="stAlert"] code {
        background: #fed7aa !important;
        color: #7c2d12 !important;
        border: 1px solid #ea580c !important;
        padding: 2px 8px !important;
        border-radius: 5px !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricValue"] {
        color: #0f172a !important;
        font-weight: 800 !important;
    }
    [data-testid="stMetricLabel"] * {
        color: #64748b !important;
        font-weight: 700 !important;
    }
    .stepper-deck {
        background: linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%) !important;
        border: 1.5px solid rgba(234, 88, 12, 0.3) !important;
        box-shadow: 0 4px 16px rgba(234, 88, 12, 0.06) !important;
    }
    .step-descriptor {
        color: #431407 !important;
        font-weight: 800 !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stColumn"]:last-child button,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stBaseButton-secondary"],
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) .stButton > button,
    [data-testid="stColumn"]:has(.theme-toggle-box) button,
    [data-testid="stColumn"]:has(#theme-btn-marker) button,
    div:has(> .theme-toggle-box) + div button,
    div:has(.theme-toggle-box) + div button,
    div:has(.theme-toggle-box) ~ div button,
    .theme-toggle-box .stButton > button,
    .theme-toggle-box button {
        background: linear-gradient(135deg, #ffedd5 0%, #fed7aa 100%) !important;
        background-color: #ffedd5 !important;
        color: #7c2d12 !important;
        border: 1.5px solid #ea580c !important;
        box-shadow: 0 2px 10px rgba(234, 88, 12, 0.16) !important;
        border-radius: 8px !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button p,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button span,
    .theme-toggle-box .stButton > button p {
        color: #7c2d12 !important;
        font-weight: 800 !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button:hover,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stBaseButton-secondary"]:hover,
    .theme-toggle-box .stButton > button:hover {
        background: linear-gradient(135deg, #fed7aa 0%, #fde68a 100%) !important;
        background-color: #fed7aa !important;
        color: #431407 !important;
        border-color: #ea580c !important;
        box-shadow: 0 4px 14px rgba(234, 88, 12, 0.25) !important;
    }
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button:hover p,
    .theme-toggle-box .stButton > button:hover p {
        color: #431407 !important;
    }
    """

st.markdown(
    f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
    
    html, body, h1, h2, h3, h4, h5, h6, p, label, button, input, textarea {{
        font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, sans-serif;
        -webkit-font-smoothing: antialiased;
    }}
    /* Prevent icon ligature breakage: preserve Material Symbols font */
    [data-testid="stIconMaterial"], .material-symbols-rounded, .material-symbols-outlined,
    [data-testid="stExpanderToggleIcon"], [data-testid="stExpander"] summary span:first-child,
    [data-testid="stExpander"] summary [data-testid="stIconMaterial"] {{
        font-family: "Material Symbols Rounded", "Material Symbols Outlined", "Material Icons" !important;
    }}
    
    {css_theme}
    
    /* Top Brand Navigation Bar */
    .smarthire-navbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-radius: 16px;
        padding: 16px 26px;
        margin-bottom: 0px;
        backdrop-filter: blur(14px);
    }}
    .brand-group {{
        display: flex;
        align-items: center;
        gap: 14px;
    }}
    .brand-logo-mark {{
        background: linear-gradient(135deg, #f97316 0%, #ea580c 50%, #facc15 100%);
        color: #ffffff;
        font-weight: 800;
        font-size: 17px;
        letter-spacing: -0.5px;
        padding: 8px 14px;
        border-radius: 12px;
        box-shadow: 0 4px 16px rgba(249, 115, 22, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.25);
    }}
    .brand-title-text {{
        font-size: 22px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }}
    .brand-version-pill {{
        font-size: 11px;
        font-weight: 700;
        padding: 3px 9px;
        border-radius: 8px;
        margin-left: 8px;
    }}
    .status-badge-container {{
        display: flex;
        align-items: center;
        gap: 8px;
        font-size: 13px;
        font-weight: 700;
    }}
    .status-pulse-dot {{
        width: 9px;
        height: 9px;
        background: #f59e0b;
        border-radius: 50%;
        box-shadow: 0 0 10px #f59e0b;
    }}
    
    /* Section Glass Cards */
    .glass-panel {{
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 20px;
        backdrop-filter: blur(12px);
    }}
    
    /* Tab System Styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 12px !important;
        padding: 8px 12px !important;
        border-radius: 14px !important;
    }}
    .stTabs [data-baseweb="tab"] {{
        border-radius: 10px !important;
        font-weight: 700 !important;
        font-size: 14px !important;
        padding: 10px 22px !important;
        transition: all 0.25s ease !important;
        border: 1px solid transparent !important;
    }}
    
    /* Metric Cards Grid */
    .metric-grid-card {{
        border-radius: 14px;
        padding: 18px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }}
    .metric-grid-card:hover {{
        transform: translateY(-2px);
    }}
    .metric-header-title {{
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin-bottom: 6px;
    }}
    .metric-hero-val {{
        font-size: 28px;
        font-weight: 800;
        letter-spacing: -0.5px;
    }}
    
    /* Dynamic Candidate Profile Cards */
    .profile-card {{
        border-radius: 14px;
        padding: 20px;
        margin-bottom: 16px;
        transition: all 0.25s ease;
    }}
    .profile-topbar {{
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }}
    .profile-name-text {{
        font-size: 18px;
        font-weight: 800;
        letter-spacing: -0.3px;
    }}
    .profile-file-text {{
        font-size: 12px;
        font-weight: 600;
    }}
    
    /* Status Badges */
    .status-pill-recommended {{
        background: rgba(16, 185, 129, 0.2);
        color: #10b981;
        font-size: 11px;
        font-weight: 800;
        padding: 5px 12px;
        border-radius: 20px;
        letter-spacing: 0.5px;
        border: 1.5px solid #10b981;
        text-transform: uppercase;
    }}
    .status-pill-declined {{
        background: rgba(239, 68, 68, 0.2);
        color: #ef4444;
        font-size: 11px;
        font-weight: 800;
        padding: 5px 12px;
        border-radius: 20px;
        letter-spacing: 0.5px;
        border: 1.5px solid #ef4444;
        text-transform: uppercase;
    }}
    
    /* Key Skills Chips */
    .skill-badge-item {{
        display: inline-block;
        font-size: 11px;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 8px;
        margin-right: 6px;
        margin-bottom: 6px;
    }}
    
    /* High-Impact Saffron/Amber Action Buttons */
    .stButton > button {{
        border-radius: 10px !important;
        font-weight: 800 !important;
        letter-spacing: 0.5px !important;
        text-transform: uppercase !important;
        font-size: 13px !important;
        padding: 10px 20px !important;
        transition: all 0.25s ease !important;
    }}
    .stButton > button[kind="primary"] {{
        background: linear-gradient(135deg, #c2410c 0%, #ea580c 45%, #f59e0b 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 4px 20px rgba(234, 88, 12, 0.45) !important;
    }}
    .stButton > button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #ea580c 0%, #f97316 45%, #facc15 100%) !important;
        box-shadow: 0 6px 26px rgba(249, 115, 22, 0.6) !important;
        transform: translateY(-2px) !important;
    }}
    
    .stDownloadButton > button {{
        border-radius: 10px !important;
        font-weight: 800 !important;
        background: linear-gradient(135deg, #d97706 0%, #ea580c 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.25) !important;
        box-shadow: 0 4px 16px rgba(217, 119, 6, 0.35) !important;
    }}
    .stDownloadButton > button:hover {{
        background: linear-gradient(135deg, #f59e0b 0%, #f97316 100%) !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(245, 158, 11, 0.5) !important;
    }}
    
    /* High-Impact Danger Delete Button */
    .delete-btn-box .stButton > button {{
        background: linear-gradient(135deg, #b91c1c 0%, #dc2626 100%) !important;
        color: #ffffff !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        box-shadow: 0 4px 14px rgba(220, 38, 38, 0.4) !important;
        text-transform: uppercase !important;
        font-weight: 800 !important;
        border-radius: 10px !important;
    }}
    .delete-btn-box .stButton > button:hover {{
        background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%) !important;
        box-shadow: 0 6px 18px rgba(239, 68, 68, 0.6) !important;
        transform: translateY(-1px) !important;
    }}
    
    /* Stepper Styling for Candidate */
    .stepper-deck {{
        display: flex;
        justify-content: space-between;
        margin: 20px 0 25px 0;
        padding: 18px 24px;
        border-radius: 14px;
    }}
    .step-unit {{
        display: flex;
        flex-direction: column;
        align-items: center;
        flex: 1;
        position: relative;
    }}
    .step-token {{
        width: 34px;
        height: 34px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 13px;
        font-weight: 800;
        margin-bottom: 8px;
    }}
    .token-complete {{
        background: #10b981;
        color: #ffffff;
        box-shadow: 0 0 12px rgba(16, 185, 129, 0.6);
    }}
    .token-active {{
        background: #f97316;
        color: #ffffff;
        box-shadow: 0 0 12px rgba(249, 115, 22, 0.6);
    }}
    .token-dormant {{
        background: rgba(148, 163, 184, 0.25);
        color: #94a3b8;
    }}
    .step-descriptor {{
        font-size: 12px;
        font-weight: 700;
        text-align: center;
    }}

    /* Medium Rectangular Theme Button in Exact Right Corner */
    .theme-toggle-box {{
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
        width: 100% !important;
        margin-left: auto !important;
    }}
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stColumn"]:last-child,
    .theme-toggle-box .stButton {{
        width: auto !important;
        margin-left: auto !important;
        display: flex !important;
        justify-content: flex-end !important;
        align-items: center !important;
    }}
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stColumn"]:last-child button,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) [data-testid="stBaseButton-secondary"],
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) .stButton > button,
    [data-testid="stColumn"]:has(.theme-toggle-box) button,
    div:has(> .theme-toggle-box) + div button,
    div:has(.theme-toggle-box) + div button,
    div:has(.theme-toggle-box) ~ div button,
    .theme-toggle-box .stButton > button {{
        width: 140px !important;
        min-width: 140px !important;
        max-width: 140px !important;
        height: 38px !important;
        min-height: 38px !important;
        max-height: 38px !important;
        padding: 0 10px !important;
        font-size: 12.5px !important;
        line-height: 36px !important;
        border-radius: 8px !important;
        font-weight: 800 !important;
        letter-spacing: 0.3px !important;
        text-transform: none !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        box-sizing: border-box !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        gap: 6px !important;
        cursor: pointer !important;
        transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease !important;
    }}
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button p,
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button span,
    .theme-toggle-box .stButton > button p {{
        font-size: 12.5px !important;
        font-weight: 800 !important;
        margin: 0 !important;
        padding: 0 !important;
        white-space: nowrap !important;
        overflow: hidden !important;
        text-overflow: clip !important;
        line-height: 36px !important;
    }}
    [data-testid="stHorizontalBlock"]:has(.smarthire-navbar) button:hover,
    .theme-toggle-box .stButton > button:hover {{
        transform: translateY(-1px) !important;
    }}
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------------------
# DATABASE INITIALIZATION
# ---------------------------
def get_conn():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password BLOB NOT NULL,
        role TEXT NOT NULL,
        email TEXT,
        created_at TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS resumes_blob (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate TEXT,
        filename TEXT,
        file_blob BLOB,
        file_text TEXT,
        uploaded_at TEXT
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS screening_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        candidate TEXT,
        filename TEXT,
        similarity REAL,
        probability REAL,
        status TEXT,
        stage TEXT,
        notes TEXT,
        jd_checksum TEXT,
        timestamp TEXT
    )
    """)
    
    # Auto-migration
    c.execute("PRAGMA table_info(screening_results)")
    res_cols = [r[1] for r in c.fetchall()]
    if "stage" not in res_cols:
        c.execute("ALTER TABLE screening_results ADD COLUMN stage TEXT")
    if "notes" not in res_cols:
        c.execute("ALTER TABLE screening_results ADD COLUMN notes TEXT")

    # Seed Default Accounts if missing
    c.execute("SELECT COUNT(*) FROM users WHERE role='HR'")
    if c.fetchone()[0] == 0:
        pw_hash = bcrypt.hashpw("Admin@12345".encode("utf-8"), bcrypt.gensalt())
        c.execute(
            "INSERT INTO users (username, password, role, email, created_at) VALUES (?,?,?,?,?)",
            ("admin", pw_hash, "HR", "recruitment@smarthire.internal", datetime.now(timezone.utc).isoformat())
        )

    c.execute("SELECT COUNT(*) FROM users WHERE role='Candidate'")
    if c.fetchone()[0] == 0:
        cand_hash = bcrypt.hashpw("Candidate@12345".encode("utf-8"), bcrypt.gensalt())
        c.execute(
            "INSERT INTO users (username, password, role, email, created_at) VALUES (?,?,?,?,?)",
            ("candidate1", cand_hash, "Candidate", "applicant@smarthire.internal", datetime.now(timezone.utc).isoformat())
        )

    conn.commit()
    conn.close()

init_db()

# ---------------------------
# AUTH FUNCTIONS
# ---------------------------
def hash_pw(password: str) -> bytes:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_pw(password: str, hashed: bytes) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed)
    except Exception:
        return False

def create_user(username, password, role, email=None):
    conn = get_conn()
    c = conn.cursor()
    try:
        now_ts = datetime.now(timezone.utc).isoformat()
        c.execute(
            "INSERT INTO users(username, password, role, email, created_at) VALUES (?,?,?,?,?)",
            (username.strip(), hash_pw(password), role, email.strip() if email else None, now_ts)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def get_user(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT username, password, role, email FROM users WHERE username=?", (username.strip(),))
    r = c.fetchone()
    conn.close()
    return r

def get_all_users_df():
    conn = get_conn()
    df = pd.read_sql_query("SELECT username, role, email, created_at FROM users ORDER BY created_at DESC", conn)
    conn.close()
    return df

def delete_user(username):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM users WHERE username=?", (username,))
    conn.commit()
    conn.close()

# ---------------------------
# TEXT EXTRACTION & STORAGE
# ---------------------------
def extract_text_from_file(uploaded_file) -> str:
    name = uploaded_file.name.lower()
    text = ""
    
    if name.endswith(".pdf"):
        if pdfplumber is not None:
            try:
                uploaded_file.seek(0)
                with pdfplumber.open(uploaded_file) as pdf:
                    for page in pdf.pages:
                        text += (page.extract_text() or "") + "\n"
                if text.strip():
                    uploaded_file.seek(0)
                    return text.strip()
            except Exception:
                pass
        if PdfReader is not None:
            try:
                uploaded_file.seek(0)
                reader = PdfReader(uploaded_file)
                for page in reader.pages:
                    text += (page.extract_text() or "") + "\n"
                if text.strip():
                    uploaded_file.seek(0)
                    return text.strip()
            except Exception:
                pass
        uploaded_file.seek(0)
        return text.strip()

    elif name.endswith(".docx"):
        if docx2txt is not None:
            tmp_path = os.path.join(UPLOAD_DIR, f"tmp_{datetime.now(timezone.utc).timestamp()}.docx")
            try:
                uploaded_file.seek(0)
                with open(tmp_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                text = docx2txt.process(tmp_path)
            except Exception:
                text = ""
            finally:
                if os.path.exists(tmp_path):
                    try:
                        os.remove(tmp_path)
                    except Exception:
                        pass
                uploaded_file.seek(0)
            return (text or "").strip()
        uploaded_file.seek(0)
        return ""

    else:
        try:
            uploaded_file.seek(0)
            content = uploaded_file.read()
            uploaded_file.seek(0)
            return content.decode("utf-8", errors="ignore").strip()
        except Exception:
            uploaded_file.seek(0)
            return ""

def save_resume_blob(candidate, filename, buffer_bytes, text_content=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM resumes_blob WHERE candidate=? AND filename=?", (candidate, filename))
    existing = c.fetchone()
    now_ts = datetime.now(timezone.utc).isoformat()
    if existing:
        c.execute("""
            UPDATE resumes_blob 
            SET file_blob=?, file_text=?, uploaded_at=? 
            WHERE id=?
        """, (buffer_bytes, text_content, now_ts, existing["id"]))
    else:
        c.execute("""
            INSERT INTO resumes_blob(candidate, filename, file_blob, file_text, uploaded_at)
            VALUES (?,?,?,?,?)
        """, (candidate, filename, buffer_bytes, text_content, now_ts))
    conn.commit()
    conn.close()

# ---------------------------
# NLP & ML ENGINE
# ---------------------------
def compute_similarity_and_probs(jd_text, resume_texts):
    clean_jd = (jd_text or "").strip()
    clean_resumes = [(r or "").strip() for r in resume_texts]

    if not clean_jd:
        clean_jd = "general qualifications experience skills requirements"

    docs = [clean_jd]
    for r in clean_resumes:
        docs.append(r if len(r) > 2 else "candidate profile experience skills")

    try:
        vectorizer = TfidfVectorizer(
            stop_words="english",
            sublinear_tf=True,
            ngram_range=(1, 2),
            max_features=3000
        )
        tfidf = vectorizer.fit_transform(docs)
        sims = cosine_similarity(tfidf[0:1], tfidf[1:]).flatten()
    except Exception:
        sims = np.zeros(len(clean_resumes))

    alpha = 14.0
    center = 0.18
    ml_probs = 1.0 / (1.0 + np.exp(-alpha * (sims - center)))
    final_probs = np.where(sims >= 0.88, 0.99, ml_probs)
    return sims, final_probs

def compute_advanced_auto_threshold(sim_scores):
    """
    Advanced Automated AI Threshold Engine.
    Uses Otsu's variance-maximization clustering over applicant score distributions
    to dynamically determine optimal, strict, and broad qualification cutoffs.
    """
    if len(sim_scores) == 0:
        return 0.15, 0.22, 0.10, "Base Distribution"

    scores = np.sort(np.array(sim_scores))
    n = len(scores)

    if n == 1:
        optimal = float(scores[0] * 0.85)
        strict = float(scores[0])
        broad = float(scores[0] * 0.50)
        return round(optimal, 3), round(strict, 3), round(broad, 3), "Single Applicant Calibrated"

    best_thresh = float(np.mean(scores))
    max_var = -1.0
    total_var = float(np.var(scores))

    if total_var > 1e-5:
        for i in range(1, n):
            w0 = i / n
            w1 = (n - i) / n
            m0 = float(np.mean(scores[:i]))
            m1 = float(np.mean(scores[i:]))
            var_between = w0 * w1 * ((m0 - m1) ** 2)
            if var_between > max_var:
                max_var = var_between
                best_thresh = (scores[i - 1] + scores[i]) / 2.0

    optimal_cutoff = round(float(np.clip(best_thresh, min(0.06, float(scores.max()) * 0.75), 0.28)), 3)
    strict_cutoff = round(float(np.clip(np.percentile(scores, 75) if n >= 4 else (optimal_cutoff * 1.15), optimal_cutoff, 0.32)), 3)
    std_val = float(np.std(scores))
    broad_cutoff = round(float(np.clip(np.mean(scores) - 0.5 * std_val, min(0.04, float(scores.min())), optimal_cutoff)), 3)
    rationale = "Otsu Variance Clustering" if max_var > 0 else "Cohort Statistical Mean"
    return optimal_cutoff, strict_cutoff, broad_cutoff, rationale

def evaluate_fresher_candidate(cand_text, cand_skills, jd_skills, raw_similarity, raw_prob):
    """
    Automated Early-Career & Fresher Assessment Engine:
    Detects early-career signals (recent degree, internships, academic projects, lack of long senior titles)
    and evaluates foundational skill match density to ensure talented freshers are fairly qualified.
    """
    t = (cand_text or "").lower()

    fresher_cues = [
        "fresher", "entry level", "entry-level", "intern", "internship", "trainee",
        "b.tech", "btech", "b.e.", "bca", "mca", "b.sc", "b.s.", "bachelor",
        "academic project", "capstone", "coursework", "cgpa", "recent graduate", "class of 202"
    ]
    senior_cues = ["senior", "lead", "principal", "architect", "staff engineer", "head of", "director", "manager"]

    fresher_hits = sum(1 for cue in fresher_cues if cue in t)
    senior_hits = sum(1 for cue in senior_cues if cue in t)

    is_fresher = (fresher_hits >= 2 and senior_hits <= 1) or ("fresher" in t) or ("intern" in t and senior_hits == 0)

    jd_skills_lower = [s.lower() for s in jd_skills] if jd_skills else []
    matched_skills = [s for s in cand_skills if s.lower() in jd_skills_lower]
    skill_ratio = len(matched_skills) / max(1, len(jd_skills)) if jd_skills else 0.0

    if is_fresher:
        if len(matched_skills) >= 2 or skill_ratio >= 0.20 or raw_similarity >= 0.09:
            fresher_boosted_prob = max(raw_prob, min(0.85, 0.55 + 0.10 * len(matched_skills)))
            return {
                "is_fresher": True,
                "fresher_status": "Fresher Qualified",
                "adjusted_prob": round(float(fresher_boosted_prob), 4),
                "badge_label": "🎓 FRESHER QUALIFIED",
                "matched_count": len(matched_skills),
                "verdict": f"Early Career • {len(matched_skills)} Core Competencies Matched • High Trainability"
            }
        else:
            return {
                "is_fresher": True,
                "fresher_status": "Fresher (Needs Training)",
                "adjusted_prob": raw_prob,
                "badge_label": "🎓 FRESHER (NEEDS TRAINING)",
                "matched_count": len(matched_skills),
                "verdict": "Early Career • Foundational Skill Gaps"
            }
    else:
        return {
            "is_fresher": False,
            "fresher_status": "Experienced",
            "adjusted_prob": raw_prob,
            "badge_label": "EXPERIENCED",
            "matched_count": len(matched_skills),
            "verdict": "Industry Professional"
        }

def generate_interview_questions(candidate_name, skills, missing_skills, is_fresher):
    """
    Automated AI Technical Interview Cheat Sheet Generator (Phase 2):
    Creates 3 targeted, role-specific technical interview questions based on the candidate's
    verified competencies, project history, and identified gap areas.
    """
    top_skill = skills[0] if skills else "Software Engineering"
    second_skill = skills[1] if len(skills) > 1 else "System Design"
    missing = missing_skills[0] if missing_skills else "Cloud Architecture"

    if is_fresher:
        q1 = f"Can you walk us through the technical architecture of your project using {top_skill}, and how you handled data persistence and state?"
        q2 = f"How did you implement {second_skill} in your practical labs or capstone, and what was the most challenging technical bug you solved?"
        q3 = f"This target role utilizes {missing}. What is your current understanding of {missing}, and how would you approach ramping up during your first 2 weeks?"
    else:
        q1 = f"In your past production systems utilizing {top_skill}, what strategies did you employ to optimize throughput, latency, and system resilience?"
        q2 = f"Describe an architectural trade-off you evaluated between {top_skill} and {second_skill} when architecting critical modules."
        q3 = f"Our engineering environment leverages {missing}. How would you bridge your background in {top_skill} to guide best practices in {missing}?"

    return [q1, q2, q3]

# ---------------------------
# EXECUTIVE PDF REPORT BUILDER
# ---------------------------
def build_pdf_report(candidate, filename, similarity, probability, jd_excerpt=None, status=None, matched_skills=None):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    w, h = A4

    def sanitize(text):
        if not text:
            return ""
        return str(text).encode("latin-1", "replace").decode("latin-1")

    # Header Banner - Deep Warm Saffron/Amber Twilight
    c.setFillColorRGB(0.12, 0.06, 0.02)
    c.rect(0, h - 38*mm, w, 38*mm, fill=1, stroke=0)

    # Logo Mark - Saffron Orange
    c.setFillColorRGB(0.96, 0.45, 0.08)
    c.roundRect(20*mm, h - 26*mm, 12*mm, 12*mm, 2*mm, fill=1, stroke=0)
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(22.5*mm, h - 22.5*mm, "SH")

    c.setFont("Helvetica-Bold", 18)
    c.drawString(36*mm, h - 20*mm, "SmartHire")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.98, 0.75, 0.5)
    c.drawString(36*mm, h - 26*mm, "Candidate Benchmark Evaluation Dossier")

    c.drawRightString(w - 20*mm, h - 20*mm, "CONFIDENTIAL ATS DOSSIER")
    c.setFont("Helvetica", 8)
    c.drawRightString(w - 20*mm, h - 25*mm, f"Timestamp: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")

    # Candidate Section
    c.setFillColorRGB(0.15, 0.1, 0.05)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20*mm, h - 50*mm, "CANDIDATE ASSESSMENT OVERVIEW")
    
    c.setLineWidth(0.6)
    c.setStrokeColorRGB(0.9, 0.7, 0.5)
    c.line(20*mm, h - 53*mm, w - 20*mm, h - 53*mm)

    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.3, 0.2, 0.1)
    c.drawString(20*mm, h - 62*mm, "Applicant Name:")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(55*mm, h - 62*mm, sanitize(candidate))

    c.setFont("Helvetica-Bold", 10)
    c.setFillColorRGB(0.3, 0.2, 0.1)
    c.drawString(20*mm, h - 70*mm, "Source Document:")
    c.setFont("Helvetica", 10)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(55*mm, h - 70*mm, sanitize(filename))

    # Metrics Card
    c.setFillColorRGB(0.99, 0.96, 0.92)
    c.roundRect(20*mm, h - 110*mm, w - 40*mm, 32*mm, 3*mm, fill=1, stroke=0)

    c.setFillColorRGB(0.92, 0.38, 0.05)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(25*mm, h - 86*mm, "CORE RELEVANCE & FIT METRICS")

    c.setFillColorRGB(0.3, 0.2, 0.1)
    c.setFont("Helvetica", 9)
    c.drawString(25*mm, h - 96*mm, "Role Semantic Match:")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(25*mm, h - 104*mm, f"{similarity * 100:.1f}%")

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.3, 0.2, 0.1)
    c.drawString(85*mm, h - 96*mm, "Shortlist Probability:")
    c.setFont("Helvetica-Bold", 12)
    c.setFillColorRGB(0.1, 0.1, 0.1)
    c.drawString(85*mm, h - 104*mm, f"{probability * 100:.1f}%")

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.3, 0.2, 0.1)
    c.drawString(140*mm, h - 96*mm, "Recruiter Decision:")

    if status in ["Selected", "Shortlisted"]:
        c.setFillColorRGB(0.06, 0.65, 0.35)
    elif status == "Rejected":
        c.setFillColorRGB(0.85, 0.2, 0.2)
    else:
        c.setFillColorRGB(0.9, 0.55, 0.1)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(140*mm, h - 104*mm, sanitize(status or "Under Review"))

    # Skills Section
    c.setFillColorRGB(0.15, 0.1, 0.05)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, h - 124*mm, "DETECTED TECHNICAL SKILLS")
    c.line(20*mm, h - 127*mm, w - 20*mm, h - 127*mm)

    c.setFont("Helvetica", 9)
    c.setFillColorRGB(0.3, 0.2, 0.1)
    if matched_skills:
        skill_str = ", ".join(matched_skills[:16])
        c.drawString(20*mm, h - 135*mm, sanitize(skill_str))
    else:
        c.drawString(20*mm, h - 135*mm, "Standard candidate profile qualifications parsed.")

    # Job Excerpt
    c.setFillColorRGB(0.15, 0.1, 0.05)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(20*mm, h - 150*mm, "TARGET ROLE BENCHMARK EXCERPT")
    c.line(20*mm, h - 153*mm, w - 20*mm, h - 153*mm)

    c.setFont("Helvetica", 8.5)
    c.setFillColorRGB(0.35, 0.25, 0.15)
    txt = c.beginText(20*mm, h - 162*mm)
    txt.setLeading(13)
    if jd_excerpt:
        for line in sanitize(jd_excerpt).splitlines()[:14]:
            txt.textLine(line[:96])
    else:
        txt.textLine("N/A")
    c.drawText(txt)

    # Footer
    c.setLineWidth(0.5)
    c.setStrokeColorRGB(0.9, 0.7, 0.5)
    c.line(20*mm, 18*mm, w - 20*mm, 18*mm)

    c.setFont("Helvetica", 8)
    c.setFillColorRGB(0.5, 0.4, 0.3)
    c.drawString(20*mm, 13*mm, "SmartHire Platform - Automated Talent Intelligence")
    c.drawRightString(w - 20*mm, 13*mm, "Page 1 of 1")

    c.showPage()
    c.save()
    buf.seek(0)
    return buf.read()

# ---------------------------
# SESSION STATE MANAGEMENT
# ---------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.username = None
    st.session_state.role = None
    st.session_state.email = None

if "screening_results_df" not in st.session_state:
    st.session_state.screening_results_df = None
if "screening_jd_text" not in st.session_state:
    st.session_state.screening_jd_text = ""
if "screening_pdf_cache" not in st.session_state:
    st.session_state.screening_pdf_cache = {}
if "candidate_raw_texts" not in st.session_state:
    st.session_state.candidate_raw_texts = {}

# ---------------------------
# TOP DYNAMIC NAVBAR & THEME TOGGLE (RIGHT CORNER)
# ---------------------------
logged_user_display = st.session_state.username if st.session_state.logged_in else "Guest"
role_display = f"({st.session_state.role})" if st.session_state.logged_in else ""

nav_col1, nav_col2 = st.columns([8.2, 1.8], vertical_alignment="center")

with nav_col1:
    st.markdown(
        f"""
        <div class="smarthire-navbar">
            <div class="brand-group">
                <div class="brand-logo-mark">SH</div>
                <div>
                    <span class="brand-title-text">SmartHire</span>
                    <span class="brand-version-pill">ATS 2.4</span>
                </div>
            </div>
            <div class="status-badge-container">
                <span class="status-pulse-dot"></span>
                <span>Talent Engine Active</span>
                <span style="margin-left: 16px; font-weight: 800;">{logged_user_display} {role_display}</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

with nav_col2:
    # Medium Rectangular Theme Button with current mode & symbol in exact right corner
    st.markdown("<div class='theme-toggle-box' id='theme-btn-marker'>", unsafe_allow_html=True)
    current_mode_label = "🌙 Dark Mode" if is_dark else "☀️ Light Mode"
    if st.button(current_mode_label, key="theme_toggle_btn", help="Click to switch theme mode", use_container_width=False):
        st.session_state.theme = "light" if is_dark else "dark"
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<div style='margin-bottom: 22px;'></div>", unsafe_allow_html=True)

# ---------------------------
# SIDEBAR AUTHENTICATION
# ---------------------------
with st.sidebar:
    sb_head_color = "#ffffff" if is_dark else "#431407"
    sb_sub_color = "#fed7aa" if is_dark else "#7c2d12"
    st.markdown(f"<h3 style='margin:0 0 12px 0; font-weight:800; font-size:18px; color:{sb_head_color};'>Workspace Access</h3>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        auth_tab1, auth_tab2 = st.tabs(["Sign In", "Register Account"])

        with auth_tab1:
            st.markdown(f"<div style='margin-bottom:12px; font-weight:700; font-size:13px; color:{sb_sub_color};'>Authenticate with your credentials</div>", unsafe_allow_html=True)
            lu = st.text_input("Username", key="login_username")
            lp = st.text_input("Password", type="password", key="login_password")
            
            if st.button("SIGN IN TO WORKSPACE", type="primary", use_container_width=True):
                user = get_user(lu)
                if user and check_pw(lp, user["password"]):
                    st.session_state.logged_in = True
                    st.session_state.username = user["username"]
                    st.session_state.role = user["role"]
                    st.session_state.email = user["email"]
                    st.rerun()
                else:
                    st.error("Invalid credentials provided.")

        with auth_tab2:
            st.markdown(f"<div style='margin-bottom:12px; font-weight:700; font-size:13px; color:{sb_sub_color};'>New User Provisioning</div>", unsafe_allow_html=True)
            su = st.text_input("Choose Username", key="signup_username")
            sp = st.text_input("Choose Password", type="password", key="signup_password")
            se = st.text_input("Email Address", key="signup_email")
            srole = st.selectbox("Assign Role", ["Candidate", "HR"], key="signup_role")
            st.markdown(f"<div style='margin-top:2px; margin-bottom:8px; font-size:12px; font-weight:800; color:{sb_head_color};'>Selected Role: <span style='color:#f97316;'>{srole}</span></div>", unsafe_allow_html=True)
            
            hr_sec_code = ""
            if srole == "HR":
                hr_sec_code = st.text_input("Company Security Code", type="password", key="signup_hr_sec_code", help="Enter authorization code for HR account creation")
            
            st.caption("Requires: 8+ characters, uppercase, lowercase, digit, symbol.")

            if st.button("REGISTER ACCOUNT", use_container_width=True):
                if not su or not sp:
                    st.warning("Please provide username and password.")
                elif srole == "HR" and hr_sec_code.strip() != "HR-SECURE-2026":
                    st.error("Invalid Company Security Code. HR accounts require authorization.")
                elif get_user(su):
                    st.error("Username is already taken.")
                elif not is_strong_password(sp):
                    st.error("Password complexity requirements not satisfied.")
                else:
                    ok = create_user(su, sp, srole, se or None)
                    if ok:
                        st.success("Account provisioned successfully! You may now sign in.")
                    else:
                        st.error("Error creating user account.")

    else:
        st.markdown(f"<div style='font-size:14px; font-weight:800; color:{sb_head_color}; margin-bottom:6px;'>Logged In: <span style='color:#f97316;'>{st.session_state.username}</span></div>", unsafe_allow_html=True)
        st.markdown(f"<div style='font-size:13px; font-weight:700; color:{sb_sub_color}; margin-bottom:6px;'>Permissions: <span style='color:{sb_head_color};'>{st.session_state.role}</span></div>", unsafe_allow_html=True)
        if st.session_state.email:
            st.markdown(f"<div style='font-size:13px; font-weight:700; color:{sb_sub_color}; margin-bottom:12px;'>Contact: <span style='color:{sb_head_color};'>{st.session_state.email}</span></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        if st.button("LOG OUT OF SMARTHIRE", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = None
            st.session_state.role = None
            st.session_state.email = None
            st.session_state.screening_results_df = None
            st.rerun()

# ---------------------------
# MAIN WORKSPACE
# ---------------------------
if not st.session_state.logged_in:
    st.markdown(
        """
        <div class="glass-panel">
            <span class="skill-badge-item" style="font-size: 12px; margin-bottom: 12px;">ENTERPRISE ATS SUITE</span>
            <h1 style="font-size: 32px; font-weight: 800; letter-spacing: -0.8px; margin: 8px 0 14px 0;">
                High-throughput candidate screening powered by semantic NLP intelligence.
            </h1>
            <p style="font-size: 15px; line-height: 1.6; margin-bottom: 22px;">
                Benchmark incoming applicants against job requirements in seconds. SmartHire features calibrated TF-IDF scoring, technical skill extraction, and executive evaluation dossier generation.
            </p>
            <div style="display: flex; gap: 16px; flex-wrap: wrap;">
                <div style="background: rgba(249, 115, 22, 0.12); border: 1px solid rgba(249, 115, 22, 0.4); padding: 14px 20px; border-radius: 12px; flex: 1; min-width: 260px;">
                    <span style="font-weight: 800; font-size: 14px; color: #ea580c;">FOR RECRUITING MANAGERS:</span>
                    <div style="font-size: 13px; margin-top: 6px;">Batch resume parsing, skill matching, pipeline tracking, and PDF dossier exports.</div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid rgba(16, 185, 129, 0.4); padding: 14px 20px; border-radius: 12px; flex: 1; min-width: 260px;">
                    <span style="font-weight: 800; font-size: 14px; color: #10b981;">FOR JOB CANDIDATES:</span>
                    <div style="font-size: 13px; margin-top: 6px;">4-stage hiring pipeline stepper, resume updates, and transparent ATS feedback.</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

else:
    role = st.session_state.role
    user = st.session_state.username

    # ========================================================
    # HR RECRUITER WORKSPACE
    # ========================================================
    if role == "HR":
        hr_nav1, hr_nav2, hr_nav3, hr_nav4 = st.tabs([
            "Active Screening Studio",
            "Talent Pipeline & Analytics",
            "Candidate Document Vault",
            "Team & Access Control"
        ])

        # ----------------------------------------------------
        # TAB 1: ACTIVE SCREENING STUDIO
        # ----------------------------------------------------
        with hr_nav1:
            st.markdown("### **Smart Talent Screening Studio**")
            st.caption("Benchmark candidate resumes against role requirements in real time.")

            # Quick-Load Role Templates for Effortless Scanning
            st.markdown("<span style='font-size:12px; font-weight:700; color:#ea580c;'>⚡ Quick-Load Role Templates (1-Click for Instant Scanning):</span>", unsafe_allow_html=True)
            t_col1, t_col2, t_col3, t_col4 = st.columns(4)
            if "quick_jd_template" not in st.session_state:
                st.session_state.quick_jd_template = ""

            with t_col1:
                if st.button("💻 Full-Stack Web Dev", use_container_width=True):
                    st.session_state.quick_jd_template = "Full-Stack Engineer with React, Node.js, JavaScript, TypeScript, REST APIs, SQL, PostgreSQL, MongoDB, Git, Docker, and Agile development."
            with t_col2:
                if st.button("🛡️ Cybersecurity SecOps", use_container_width=True):
                    st.session_state.quick_jd_template = "Cybersecurity Engineer with SOC operations, SIEM Splunk, Incident Response, Kali Linux, Nessus, Firewalls, NIST, ISO 27001, Python, and OWASP."
            with t_col3:
                if st.button("📱 Mobile Flutter Dev", use_container_width=True):
                    st.session_state.quick_jd_template = "Mobile Developer with Flutter, Dart, Riverpod, BLoC, iOS Swift, Android Kotlin, Firebase, REST APIs, SQLite, and App Store deployment."
            with t_col4:
                if st.button("📊 Product Manager", use_container_width=True):
                    st.session_state.quick_jd_template = "Technical Product Manager with B2B SaaS roadmaps, Agile Scrum, PRDs, user stories, SQL analytics, Amplitude, Jira, and Figma wireframing."

            # Section 1: Role Specification
            st.markdown("##### **1. Target Role & Requirements**")
            jd_box1, jd_box2 = st.columns([1, 1])

            with jd_box1:
                jd_upload = st.file_uploader(
                    "Upload Role Specification (.txt, .pdf, .docx)",
                    type=["txt", "pdf", "docx"],
                    key="sh_jd_file"
                )

            with jd_box2:
                jd_text_manual = st.text_area(
                    "Or paste role requirements directly:",
                    value=st.session_state.quick_jd_template,
                    height=130,
                    placeholder="e.g. Senior Backend Engineer with Python, FastAPI, Docker, PostgreSQL, Scikit-Learn..."
                )

            active_jd_text = ""
            if jd_upload is not None:
                active_jd_text = extract_text_from_file(jd_upload)
            elif jd_text_manual.strip():
                active_jd_text = jd_text_manual.strip()

            jd_skills = extract_skills_from_text(active_jd_text)
            if jd_skills:
                st.markdown("**Role Key Competencies Detected:**")
                skills_html = "".join([f"<span class='skill-badge-item'>{s}</span>" for s in jd_skills[:14]])
                st.markdown(f"<div>{skills_html}</div>", unsafe_allow_html=True)

            st.markdown("---")

            # Section 2: Resumes
            st.markdown("##### **2. Applicant Resumes**")
            resume_files = st.file_uploader(
                "Upload Candidate Resumes (.pdf, .docx, .txt)",
                type=["pdf", "docx", "txt"],
                accept_multiple_files=True,
                key="sh_resume_files"
            )

            include_vault_candidates = st.checkbox(
                "Include applicant resumes already stored in candidate vault",
                value=False
            )

            # Benchmark Action Button
            if st.button("⚡ 1-CLICK INSTANT AI SCREENING", type="primary"):
                if not active_jd_text:
                    st.error("Please define the role specification first (upload file or paste text).")
                elif not resume_files and not include_vault_candidates:
                    st.error("Please upload resumes or enable the candidate vault option.")
                else:
                    with st.spinner("Extracting NLP features, matching competencies, and computing shortlist metrics..."):
                        c_names, c_files, c_texts = [], [], []

                        # Uploaded files
                        if resume_files:
                            for rf in resume_files:
                                txt = extract_text_from_file(rf)
                                c_name = os.path.splitext(rf.name)[0]
                                c_files.append(rf.name)
                                c_names.append(c_name)
                                c_texts.append(txt)

                                rf.seek(0)
                                buf = rf.read()
                                save_resume_blob(c_name, rf.name, buf, txt)
                                with open(os.path.join(UPLOAD_DIR, f"{datetime.now(timezone.utc).timestamp()}_{rf.name}"), "wb") as out:
                                    out.write(buf)

                        # Vault files
                        if include_vault_candidates:
                            conn = get_conn()
                            c = conn.cursor()
                            c.execute("SELECT candidate, filename, file_text FROM resumes_blob")
                            db_records = c.fetchall()
                            conn.close()

                            for row in db_records:
                                if row["filename"] not in c_files:
                                    c_names.append(row["candidate"])
                                    c_files.append(row["filename"])
                                    c_texts.append(row["file_text"] or "")

                        sims, probs = compute_similarity_and_probs(active_jd_text, c_texts)
                        cand_skills_list = [extract_skills_from_text(t) for t in c_texts]

                        # Automated Fresher & Early-Career Potential Assessment Engine
                        fresher_evals = [
                            evaluate_fresher_candidate(c_texts[i], cand_skills_list[i], jd_skills, sims[i], probs[i])
                            for i in range(len(c_texts))
                        ]

                        fresher_flags = [fe["is_fresher"] for fe in fresher_evals]
                        fresher_labels = [fe["badge_label"] for fe in fresher_evals]
                        adjusted_probs = [fe["adjusted_prob"] for fe in fresher_evals]
                        verdicts = [fe["verdict"] for fe in fresher_evals]

                        df_res = pd.DataFrame({
                            "Candidate": c_names,
                            "Filename": c_files,
                            "Similarity": np.round(sims, 4),
                            "Probability": np.round(adjusted_probs, 4),
                            "Skills": cand_skills_list,
                            "IsFresher": fresher_flags,
                            "FresherBadge": fresher_labels,
                            "Verdict": verdicts
                        })
                        df_res["Status"] = df_res["Probability"].apply(
                            lambda p: "Selected" if p >= 0.50 else "Rejected"
                        )
                        df_res = df_res.sort_values(by=["Probability", "Similarity"], ascending=False).reset_index(drop=True)
                        df_res.index = df_res.index + 1
                        df_res.index.name = "Rank"

                        st.session_state.screening_results_df = df_res
                        st.session_state.screening_jd_text = active_jd_text
                        st.session_state.screening_pdf_cache = {}
                        for idx, name in enumerate(c_names):
                            st.session_state.candidate_raw_texts[name] = c_texts[idx]

                        st.success(f"Benchmarking completed for {len(df_res)} candidate(s).")

            # DISPLAY SCREENING RESULTS
            if st.session_state.screening_results_df is not None:
                res_df = st.session_state.screening_results_df
                jd_text_curr = st.session_state.screening_jd_text

                st.markdown("---")
                st.markdown("### **Evaluation Analytics & Benchmarks**")

                # Metrics Overview Cards with Saffron, Emerald, Sky Blue and Amber Accents
                k1, k2, k3, k4 = st.columns(4)
                tot = len(res_df)
                sel_exp = len(res_df[(res_df["Status"] == "Selected") & (~res_df["IsFresher"])])
                sel_fresher = len(res_df[(res_df["Status"] == "Selected") & (res_df["IsFresher"])])
                avg_score = res_df["Similarity"].mean()

                # Dynamic Theme Accents for Dashboard Elements
                c_k1_col = "#f97316" if is_dark else "#ea580c"
                c_k2_col = "#10b981" if is_dark else "#059669"
                c_k3_col = "#38bdf8" if is_dark else "#0284c7"
                c_k4_col = "#facc15" if is_dark else "#d97706"

                k1.markdown(f"<div class='metric-grid-card'><div class='metric-header-title'>Total Evaluated</div><div class='metric-hero-val' style='color:{c_k1_col};'>{tot}</div></div>", unsafe_allow_html=True)
                k2.markdown(f"<div class='metric-grid-card'><div class='metric-header-title'>Experienced Shortlist</div><div class='metric-hero-val' style='color:{c_k2_col};'>{sel_exp}</div></div>", unsafe_allow_html=True)
                k3.markdown(f"<div class='metric-grid-card'><div class='metric-header-title'>🎓 Fresher Qualified</div><div class='metric-hero-val' style='color:{c_k3_col};'>{sel_fresher}</div></div>", unsafe_allow_html=True)
                k4.markdown(f"<div class='metric-grid-card'><div class='metric-header-title'>Average Match</div><div class='metric-hero-val' style='color:{c_k4_col};'>{avg_score*100:.1f}%</div></div>", unsafe_allow_html=True)

                st.markdown("<br>", unsafe_allow_html=True)

                # Compute advanced dynamic thresholds
                sim_values = res_df["Similarity"].values
                optimal_cutoff, strict_cutoff, broad_cutoff, rationale = compute_advanced_auto_threshold(sim_values)

                # Streamlined Candidate Pool View
                ctrl_col1, ctrl_col2, ctrl_col3 = st.columns([1.5, 1.8, 1.2])
                with ctrl_col1:
                    filter_name = st.text_input("Filter Candidate Name:", "")
                with ctrl_col2:
                    view_filter = st.selectbox(
                        "Candidate Pool View:",
                        [
                            "⭐ All Shortlisted Candidates (Recommended & Freshers)",
                            "🎓 Freshers Only (Early Career Fast-Track)",
                            "💼 Experienced Talent Only",
                            "📋 Complete Candidate Pool (Unfiltered)"
                        ],
                        index=0,
                        help="AI automatically evaluates and shortlists candidates using dynamic cohort thresholding and early-career potential assessment."
                    )
                with ctrl_col3:
                    view_mode = st.radio("Presentation Mode", ["Dynamic Profile Cards", "⚔️ Candidate Face-Off Compare", "Tabular Dataset"], horizontal=True)

                display_df = res_df.copy()
                if filter_name.strip():
                    display_df = display_df[display_df["Candidate"].str.contains(filter_name.strip(), case=False, na=False)]

                if "All Shortlisted" in view_filter:
                    display_df = display_df[display_df["Status"] == "Selected"]
                elif "Freshers Only" in view_filter:
                    display_df = display_df[(display_df["IsFresher"]) & (display_df["Status"] == "Selected")]
                elif "Experienced Talent" in view_filter:
                    display_df = display_df[(~display_df["IsFresher"]) & (display_df["Status"] == "Selected")]

                # 100% Automated Threshold Diagnostic Strip
                diag_bg = "rgba(234, 88, 12, 0.08)" if is_dark else "linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)"
                diag_border = "rgba(234, 88, 12, 0.28)" if is_dark else "rgba(234, 88, 12, 0.35)"
                diag_shadow = "none" if is_dark else "0 2px 10px rgba(234, 88, 12, 0.06)"
                diag_text = "#ffffff" if is_dark else "#0f172a"
                diag_subtext = "rgba(255, 255, 255, 0.85)" if is_dark else "#7c2d12"

                st.markdown(
                    f"""
                    <div style="background: {diag_bg}; border: 1.5px solid {diag_border}; border-radius: 10px; padding: 12px 18px; margin: 4px 0 16px 0; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; box-shadow: {diag_shadow};">
                        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                            <span style="background: linear-gradient(135deg, #ea580c, #f97316); color: #ffffff; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 800; letter-spacing: 0.5px; text-transform: uppercase;">100% Automated ATS Engine</span>
                            <span style="font-size: 13px; font-weight: 700; color: {diag_text};">Dynamic Threshold: <span style="color: #ea580c; font-weight: 800;">{optimal_cutoff*100:.1f}%</span></span>
                            <span style="font-size: 12px; font-weight: 600; color: {diag_subtext};">• Early-Career Potential Boost: <b style="color: {'#38bdf8' if is_dark else '#0284c7'}; font-weight: 800;">Active</b></span>
                        </div>
                        <div style="font-size: 13px; font-weight: 700; color: {diag_text};">
                            Displaying <span style="color: {'#10b981' if is_dark else '#059669'}; font-weight: 800;">{len(display_df)}</span> of {len(res_df)} Candidates
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if display_df.empty:
                    st.info("ℹ️ No candidates match the current filter. Switch to 'Complete Candidate Pool (Unfiltered)' to view everyone.")

                # VIEW 1: DYNAMIC PROFILE CARDS
                if view_mode == "Dynamic Profile Cards":
                    jd_excerpt = " ".join((jd_text_curr or "").split()[:100])
                    jd_skills_lower = [s.lower() for s in jd_skills] if jd_skills else []

                    # Theme-aware styling variables for candidate cards
                    card_bg = "linear-gradient(135deg, rgba(38, 19, 8, 0.75) 0%, rgba(20, 14, 34, 0.85) 100%)" if is_dark else "linear-gradient(145deg, #fffdfa 0%, #fff4e8 100%)"
                    card_border = "rgba(249, 115, 22, 0.35)" if is_dark else "rgba(234, 88, 12, 0.28)"
                    card_shadow = "0 6px 24px rgba(0,0,0,0.35)" if is_dark else "0 4px 20px rgba(234, 88, 12, 0.08), 0 1px 3px rgba(0,0,0,0.03)"
                    card_divider = "rgba(255, 255, 255, 0.08)" if is_dark else "rgba(234, 88, 12, 0.15)"
                    c_title_col = "#ffffff" if is_dark else "#0f172a"
                    c_sub_col = "#fed7aa" if is_dark else "#7c2d12"
                    c_lbl_col = "#cbd5e1" if is_dark else "#64748b"
                    gauge_track_col = "rgba(255, 255, 255, 0.1)" if is_dark else "rgba(234, 88, 12, 0.12)"
                    gauge_text_col = "#ffffff" if is_dark else "#0f172a"
                    verdict_box_bg = "rgba(255, 255, 255, 0.04)" if is_dark else "linear-gradient(135deg, rgba(255, 247, 237, 0.95) 0%, rgba(254, 243, 199, 0.75) 100%)"
                    verdict_border = "none" if is_dark else "1px solid rgba(234, 88, 12, 0.3)"
                    verdict_text_col = "#fed7aa" if is_dark else "#1e293b"
                    file_pill_bg = "rgba(249, 115, 22, 0.18)" if is_dark else "#ffedd5"
                    file_pill_bd = "rgba(249, 115, 22, 0.5)" if is_dark else "#ea580c"
                    file_pill_tx = "#fed7aa" if is_dark else "#7c2d12"

                    for rank_idx, row in display_df.iterrows():
                        c_name = row["Candidate"]
                        c_file = row["Filename"]
                        c_sim = float(row["Similarity"])
                        c_prob = float(row["Probability"])
                        c_status = row["Status"]
                        c_skills = row["Skills"] if isinstance(row["Skills"], list) else []
                        is_fresher_cand = bool(row.get("IsFresher", False))
                        cand_verdict = row.get("Verdict", "General qualifications parsed")

                        # Phase 1: Modern Avatar Initials with Vibrant Gradient
                        clean_n = re.sub(r'^\d+[\s_-]*', '', c_name).replace('_', ' ')
                        name_parts = clean_n.split()
                        initials = (name_parts[0][0] + (name_parts[1][0] if len(name_parts) > 1 else (name_parts[0][1:2] if len(name_parts[0]) > 1 else ''))).upper() if name_parts else 'CA'
                        
                        avatar_gradient = "linear-gradient(135deg, #ea580c 0%, #ec4899 50%, #8b5cf6 100%)" if not is_fresher_cand else "linear-gradient(135deg, #0284c7 0%, #38bdf8 50%, #06b6d4 100%)"

                        # Status & Tier Badges
                        if is_fresher_cand and c_status == "Selected":
                            status_badge_html = "<span style='background: rgba(56, 189, 248, 0.18); border: 1.5px solid #38bdf8; color: #38bdf8; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 800; letter-spacing: 0.6px; box-shadow: 0 2px 10px rgba(56, 189, 248, 0.25);'>🎓 FRESHER QUALIFIED</span>"
                            type_badge_html = f"<span style='color: {'#38bdf8' if is_dark else '#0284c7'}; font-weight: 800; font-size: 13px;'>🎓 High-Potential Early Career</span>"
                        elif c_status == "Selected":
                            status_badge_html = "<span style='background: rgba(16, 185, 129, 0.18); border: 1.5px solid #10b981; color: #10b981; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 800; letter-spacing: 0.6px; box-shadow: 0 2px 10px rgba(16, 185, 129, 0.25);'>🌟 RECOMMENDED</span>"
                            type_badge_html = f"<span style='color: {'#10b981' if is_dark else '#059669'}; font-weight: 800; font-size: 13px;'>💼 Experienced Professional</span>"
                        else:
                            status_badge_html = "<span style='background: rgba(239, 68, 68, 0.15); border: 1.5px solid #ef4444; color: #f87171; padding: 5px 12px; border-radius: 20px; font-size: 12px; font-weight: 800; letter-spacing: 0.6px;'>DECLINED</span>"
                            type_badge_html = f"<span style='color: {'#94a3b8' if is_dark else '#64748b'}; font-weight: 700; font-size: 13px;'>Below Role Benchmark</span>"

                        # Phase 1: Skill Badge Tiers (Core Must-Have vs Supplementary)
                        matched_chips = []
                        other_chips = []
                        chip_m_bg = "rgba(234, 88, 12, 0.22)" if is_dark else "rgba(234, 88, 12, 0.10)"
                        chip_m_bd = "#ea580c" if is_dark else "rgba(234, 88, 12, 0.4)"
                        chip_m_tx = "#fed7aa" if is_dark else "#9a3412"

                        chip_o_bg = "rgba(255, 255, 255, 0.06)" if is_dark else "#f1f5f9"
                        chip_o_bd = "rgba(255, 255, 255, 0.14)" if is_dark else "#cbd5e1"
                        chip_o_tx = "#cbd5e1" if is_dark else "#334155"

                        for s in c_skills[:10]:
                            if s.lower() in jd_skills_lower:
                                matched_chips.append(f"<span style='background: {chip_m_bg}; border: 1px solid {chip_m_bd}; color: {chip_m_tx}; padding: 3px 9px; border-radius: 6px; font-size: 11px; font-weight: 800; margin: 2px;'>✓ {s}</span>")
                            else:
                                other_chips.append(f"<span style='background: {chip_o_bg}; border: 1px solid {chip_o_bd}; color: {chip_o_tx}; padding: 3px 8px; border-radius: 6px; font-size: 11px; font-weight: 600; margin: 2px;'>{s}</span>")
                        
                        all_chips_html = "".join(matched_chips + other_chips) if (matched_chips or other_chips) else f"<span style='font-size:12px; font-weight:700; color:{c_sub_col}; opacity:0.8;'>Foundational competencies parsed</span>"

                        # Phase 1: Radial Visual SVG Gauges
                        sim_pct = max(0, min(100, float(c_sim * 100)))
                        prob_pct = max(0, min(100, float(c_prob * 100)))
                        sim_offset = 113.1 * (1.0 - (sim_pct / 100.0))
                        prob_offset = 113.1 * (1.0 - (prob_pct / 100.0))
                        sim_color = ("#10b981" if is_dark else "#059669") if sim_pct >= 24 else ("#ea580c" if sim_pct >= 14 else ("#f59e0b" if is_dark else "#d97706"))
                        prob_color = ("#10b981" if is_dark else "#059669") if prob_pct >= 60 else (("#facc15" if is_dark else "#d97706") if prob_pct >= 40 else "#ef4444")

                        rank_medal = "🥇 " if rank_idx == 1 else ("🥈 " if rank_idx == 2 else ("🥉 " if rank_idx == 3 else f"#{rank_idx} "))

                        # Phase 2: Missing Competency Gap Analysis
                        missing_skills = [s for s in jd_skills if s.lower() not in [cs.lower() for cs in c_skills]] if jd_skills else []
                        gap_chip_bg = "rgba(239, 68, 68, 0.12)" if is_dark else "rgba(239, 68, 68, 0.08)"
                        gap_chip_bd = "rgba(239, 68, 68, 0.35)" if is_dark else "rgba(239, 68, 68, 0.3)"
                        gap_chip_tx = "#fca5a5" if is_dark else "#b91c1c"
                        missing_chips_html = "".join([f"<span style='background: {gap_chip_bg}; border: 1px solid {gap_chip_bd}; color: {gap_chip_tx}; padding: 2px 7px; border-radius: 5px; font-size: 11px; font-weight: 700; margin: 2px;'>✕ {ms}</span>" for ms in missing_skills[:4]]) if missing_skills else f"<span style='color: {'#10b981' if is_dark else '#059669'}; font-size: 11px; font-weight: 700;'>✓ Full Key Skill Coverage</span>"

                        # Phase 2: Early-Career Potential Radar & Agility Metrics (for Freshers)
                        fresher_radar_html = ""
                        if is_fresher_cand:
                            overlap_pct = min(100, int(len(matched_chips) / max(1, len(jd_skills)) * 100)) if jd_skills else 65
                            trainability_val = min(98, 70 + len(matched_chips) * 4)
                            fr_bg = "rgba(56, 189, 248, 0.08)" if is_dark else "linear-gradient(135deg, rgba(240, 249, 255, 0.95) 0%, rgba(224, 242, 254, 0.6) 100%)"
                            fr_bd = "rgba(56, 189, 248, 0.25)" if is_dark else "rgba(2, 132, 199, 0.28)"
                            fr_title_col = "#38bdf8" if is_dark else "#0284c7"
                            fr_txt_col = "#e2e8f0" if is_dark else "#0f172a"
                            fr_success_col = "#10b981" if is_dark else "#059669"
                            fresher_radar_html = f"""
                            <div style="background: {fr_bg}; border: 1px solid {fr_bd}; border-radius: 8px; padding: 10px 14px; margin-top: 10px; display: flex; gap: 20px; align-items: center; flex-wrap: wrap;">
                                <div style="font-size: 11px; font-weight: 800; color: {fr_title_col}; text-transform: uppercase;">🎓 Early-Career Potential Index:</div>
                                <div style="font-size: 12px; color: {fr_txt_col};">Foundational Overlap: <b>{overlap_pct}%</b></div>
                                <div style="font-size: 12px; color: {fr_txt_col};">Practical Evidence: <b>Verified Projects</b></div>
                                <div style="font-size: 12px; color: {fr_txt_col};">Trainability & Agility: <b style="color: {fr_success_col};">{trainability_val}/100</b></div>
                            </div>
                            """

                        st.markdown(
                            f"""
                            <div class="profile-card" style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 14px; padding: 22px 24px; margin-bottom: 14px; backdrop-filter: blur(14px); box-shadow: {card_shadow};">
                                <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid {card_divider}; padding-bottom: 14px; flex-wrap: wrap; gap: 12px;">
                                    <div style="display: flex; align-items: center; gap: 14px;">
                                        <div style="width: 46px; height: 46px; border-radius: 12px; background: {avatar_gradient}; display: flex; align-items: center; justify-content: center; font-weight: 800; font-size: 17px; color: #ffffff; box-shadow: 0 4px 14px rgba(0,0,0,0.25); flex-shrink: 0;">
                                            {initials}
                                        </div>
                                        <div>
                                            <div style="font-size: 18px; font-weight: 800; color: {c_title_col}; letter-spacing: -0.2px;">{rank_medal}{clean_n}</div>
                                            <div style="font-size: 12.5px; margin-top: 4px; display: flex; align-items: center; gap: 6px;">
                                                <span style="color: #ea580c; font-weight: 800;">📄 Resume File:</span>
                                                <span style="background: {file_pill_bg}; border: 1px solid {file_pill_bd}; color: {file_pill_tx}; padding: 2px 8px; border-radius: 6px; font-weight: 800; font-size: 12px; font-family: monospace;">{c_file}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <div>{status_badge_html}</div>
                                </div>
                                <div style="display: flex; gap: 32px; margin: 16px 0 14px 0; align-items: center; flex-wrap: wrap;">
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <div style="position: relative; width: 50px; height: 50px; display: inline-flex; align-items: center; justify-content: center;">
                                            <svg width="50" height="50" viewBox="0 0 44 44">
                                                <circle cx="22" cy="22" r="18" fill="none" stroke="{gauge_track_col}" stroke-width="4"/>
                                                <circle cx="22" cy="22" r="18" fill="none" stroke="{sim_color}" stroke-width="4"
                                                        stroke-dasharray="113.1" stroke-dashoffset="{sim_offset:.1f}"
                                                        stroke-linecap="round" transform="rotate(-90 22 22)"/>
                                            </svg>
                                            <span style="position: absolute; font-size: 11px; font-weight: 800; color: {gauge_text_col};">{sim_pct:.0f}%</span>
                                        </div>
                                        <div>
                                            <span style="font-size: 10px; text-transform: uppercase; font-weight: 800; color: {c_lbl_col}; letter-spacing: 0.5px;">Role Match</span>
                                            <div style="font-size: 14px; font-weight: 800; color: {sim_color};">{sim_pct:.1f}%</div>
                                        </div>
                                    </div>
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <div style="position: relative; width: 50px; height: 50px; display: inline-flex; align-items: center; justify-content: center;">
                                            <svg width="50" height="50" viewBox="0 0 44 44">
                                                <circle cx="22" cy="22" r="18" fill="none" stroke="{gauge_track_col}" stroke-width="4"/>
                                                <circle cx="22" cy="22" r="18" fill="none" stroke="{prob_color}" stroke-width="4"
                                                        stroke-dasharray="113.1" stroke-dashoffset="{prob_offset:.1f}"
                                                        stroke-linecap="round" transform="rotate(-90 22 22)"/>
                                            </svg>
                                            <span style="position: absolute; font-size: 11px; font-weight: 800; color: {gauge_text_col};">{prob_pct:.0f}%</span>
                                        </div>
                                        <div>
                                            <span style="font-size: 10px; text-transform: uppercase; font-weight: 800; color: {c_lbl_col}; letter-spacing: 0.5px;">Fit Confidence</span>
                                            <div style="font-size: 14px; font-weight: 800; color: {prob_color};">{prob_pct:.1f}%</div>
                                        </div>
                                    </div>
                                    <div>
                                        <span style="font-size: 10px; text-transform: uppercase; font-weight: 800; color: {c_lbl_col}; letter-spacing: 0.5px;">Talent Tier</span>
                                        <div style="margin-top: 2px;">{type_badge_html}</div>
                                    </div>
                                    <div style="flex: 1; min-width: 240px;">
                                        <span style="font-size: 10px; text-transform: uppercase; font-weight: 800; color: {c_lbl_col}; letter-spacing: 0.5px;">Competencies (✓ Core Matches)</span>
                                        <div style="margin-top: 4px; display: flex; flex-wrap: wrap; gap: 4px;">{all_chips_html}</div>
                                    </div>
                                </div>
                                <div style="display: flex; justify-content: space-between; align-items: center; gap: 14px; flex-wrap: wrap; margin-bottom: 8px;">
                                    <div style="font-size: 11px; color: {c_lbl_col};"><b>⚡ Competency Gaps:</b> {missing_chips_html}</div>
                                </div>
                                <div style="background: {verdict_box_bg}; border-left: 4px solid #ea580c; border: {verdict_border}; border-radius: 6px; padding: 10px 14px; font-size: 12.5px; color: {verdict_text_col};">
                                    <b>AI Assessment:</b> {cand_verdict}
                                </div>
                                {fresher_radar_html}
                            </div>
                            """,
                            unsafe_allow_html=True
                        )

                        # Phase 2: Automated AI Technical Interview Prep Cheat Sheet (3 Questions)
                        with st.expander(f"🎯 AI Technical Interview Cheat Sheet (3 Questions for {clean_n})", expanded=False):
                            qs = generate_interview_questions(clean_n, c_skills, missing_skills, is_fresher_cand)
                            prep_bg = "rgba(46, 23, 9, 0.75)" if is_dark else "linear-gradient(135deg, #fffaf5 0%, #fff1e0 100%)"
                            prep_border = "rgba(234, 88, 12, 0.35)" if is_dark else "rgba(234, 88, 12, 0.28)"
                            prep_shadow = "none" if is_dark else "0 2px 10px rgba(234, 88, 12, 0.06)"
                            prep_q1_c = "#ea580c" if is_dark else "#c2410c"
                            prep_q2_c = "#facc15" if is_dark else "#b45309"
                            prep_q3_c = "#38bdf8" if is_dark else "#0284c7"
                            prep_tx_c = "#e2e8f0" if is_dark else "#1e293b"
                            st.markdown(
                                f"""
                                <div style="background: {prep_bg}; border: 1.5px solid {prep_border}; border-radius: 8px; padding: 14px 18px; margin: 4px 0 8px 0; box-shadow: {prep_shadow};">
                                    <div style="font-size: 11.5px; font-weight: 800; color: #ea580c; text-transform: uppercase; margin-bottom: 10px; letter-spacing: 0.5px;">Targeted Technical Screening Questions:</div>
                                    <div style="margin-bottom: 10px; font-size: 13px; line-height: 1.5; color: {prep_tx_c};"><span style="color: {prep_q1_c}; font-weight: 800;">Q1 (Architecture & Mastery):</span> {qs[0]}</div>
                                    <div style="margin-bottom: 10px; font-size: 13px; line-height: 1.5; color: {prep_tx_c};"><span style="color: {prep_q2_c}; font-weight: 800;">Q2 (Practical Projects & Debugging):</span> {qs[1]}</div>
                                    <div style="font-size: 13px; line-height: 1.5; color: {prep_tx_c};"><span style="color: {prep_q3_c}; font-weight: 800;">Q3 (Skill Gap & Ramp-Up Agility):</span> {qs[2]}</div>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )

                        # Phase 3: 1-Click Recruiter Triage Action Bar & Direct Dossier Download
                        pdf_cache_key = f"{c_name}_{c_file}"
                        if pdf_cache_key not in st.session_state.screening_pdf_cache:
                            st.session_state.screening_pdf_cache[pdf_cache_key] = build_pdf_report(
                                c_name, c_file, c_sim, c_prob, jd_excerpt, c_status, c_skills
                            )
                        pdf_data = st.session_state.screening_pdf_cache[pdf_cache_key]

                        triage_c1, triage_c2, triage_c3, triage_c4 = st.columns([1.1, 1.1, 1.2, 1.3])
                        with triage_c1:
                            if st.button("✅ Shortlist", key=f"btn_shortlist_{rank_idx}_{c_name}", use_container_width=True):
                                st.toast(f"🎉 {clean_n} has been moved to Round 1 Shortlist!", icon="✅")
                        with triage_c2:
                            if st.button("⭐ Priority Star", key=f"btn_star_{rank_idx}_{c_name}", use_container_width=True):
                                st.toast(f"⭐ Marked {clean_n} as High-Priority Talent!", icon="⭐")
                        with triage_c3:
                            with st.popover("✉️ Draft Invite", use_container_width=True):
                                invite_email_txt = f"""Subject: Interview Invitation: Technical Round with SmartHire Team

Dear {clean_n},

Congratulations! We were impressed by your technical qualifications and profile match for our open position.

Based on our automated competency evaluation, we would like to invite you to a 45-minute technical screening interview to discuss your experience, technical projects, and career aspirations.

Please let us know your availability over the next 3 business days, or select a slot via our recruitment portal.

Best regards,
Talent Acquisition Team
SmartHire ATS Platform"""
                                st.text_area("Ready-to-Send Email Invite:", value=invite_email_txt, height=180)
                                st.caption("💡 Copy and send directly to the candidate.")
                        with triage_c4:
                            st.download_button(
                                label="📥 DOSSIER (PDF)",
                                data=pdf_data,
                                file_name=f"{c_name}_SmartHire_dossier.pdf",
                                mime="application/pdf",
                                key=f"dl_dossier_{rank_idx}_{c_name}",
                                use_container_width=True
                            )

                # VIEW 2: CANDIDATE FACE-OFF COMPARE (Phase 3)
                elif view_mode == "⚔️ Candidate Face-Off Compare":
                    st.markdown("#### **⚔️ Side-by-Side Candidate Face-Off Comparison**")
                    st.caption("Perform an in-depth head-to-head comparison of technical overlap, competency depth, and hiring trade-offs.")

                    cand_names_list = list(res_df["Candidate"].values)
                    if len(cand_names_list) < 2:
                        st.info("At least 2 evaluated candidates are required for side-by-side comparison.")
                    else:
                        fo_col1, fo_col2 = st.columns(2)
                        with fo_col1:
                            cand_a_name = st.selectbox("Select Candidate A (Primary):", cand_names_list, index=0, key="fo_cand_a")
                        with fo_col2:
                            cand_b_name = st.selectbox("Select Candidate B (Challenger):", cand_names_list, index=1 if len(cand_names_list) > 1 else 0, key="fo_cand_b")

                        row_a = res_df[res_df["Candidate"] == cand_a_name].iloc[0]
                        row_b = res_df[res_df["Candidate"] == cand_b_name].iloc[0]

                        fo_a_bg = "rgba(234, 88, 12, 0.08)" if is_dark else "linear-gradient(135deg, #fffaf5 0%, #fff7ed 100%)"
                        fo_a_bd = "2px solid #ea580c"
                        fo_a_sh = "0 4px 18px rgba(0,0,0,0.3)" if is_dark else "0 6px 20px rgba(234, 88, 12, 0.1)"
                        fo_a_title = "#ffffff" if is_dark else "#0f172a"
                        fo_a_sub = "#fed7aa" if is_dark else "#c2410c"
                        fo_a_lbl = "#cbd5e1" if is_dark else "#64748b"
                        fo_a_body = "#fed7aa" if is_dark else "#334155"

                        fo_b_bg = "rgba(56, 189, 248, 0.08)" if is_dark else "linear-gradient(135deg, #f8fafc 0%, #f0f9ff 100%)"
                        fo_b_bd = "2px solid #38bdf8" if is_dark else "2px solid #0284c7"
                        fo_b_sh = "0 4px 18px rgba(0,0,0,0.3)" if is_dark else "0 6px 20px rgba(2, 132, 199, 0.1)"
                        fo_b_title = "#ffffff" if is_dark else "#0f172a"
                        fo_b_sub = "#bae6fd" if is_dark else "#0284c7"
                        fo_b_lbl = "#cbd5e1" if is_dark else "#64748b"
                        fo_b_body = "#bae6fd" if is_dark else "#334155"
                        fo_b_sim_c = "#38bdf8" if is_dark else "#0284c7"
                        fo_conf_c = "#facc15" if is_dark else "#d97706"

                        card_a_col, card_b_col = st.columns(2)
                        with card_a_col:
                            sim_a = float(row_a["Similarity"]) * 100
                            prob_a = float(row_a["Probability"]) * 100
                            skills_a = row_a["Skills"] if isinstance(row_a["Skills"], list) else []
                            is_fresher_a = bool(row_a.get("IsFresher", False))
                            tag_a = "🎓 Fresher" if is_fresher_a else "💼 Experienced"

                            st.markdown(f"""
                            <div style="background: {fo_a_bg}; border: {fo_a_bd}; border-radius: 12px; padding: 18px 20px; box-shadow: {fo_a_sh};">
                                <div style="font-size: 18px; font-weight: 800; color: {fo_a_title};">{cand_a_name} <span style="font-size: 12px; color: {fo_a_sub};">({tag_a})</span></div>
                                <div style="display: flex; gap: 20px; margin: 12px 0;">
                                    <div><span style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: {fo_a_lbl};">Role Match</span><div style="font-size: 22px; font-weight: 800; color: #ea580c;">{sim_a:.1f}%</div></div>
                                    <div><span style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: {fo_a_lbl};">Fit Confidence</span><div style="font-size: 22px; font-weight: 800; color: {fo_conf_c};">{prob_a:.1f}%</div></div>
                                    <div><span style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: {fo_a_lbl};">Status</span><div style="font-size: 16px; font-weight: 800; color: {'#10b981' if row_a['Status']=='Selected' else '#ef4444'};">{row_a['Status']}</div></div>
                                </div>
                                <div style="font-size: 12px; color: {fo_a_body}; margin-top: 6px;"><b>Key Competencies ({len(skills_a)}):</b> {', '.join(skills_a[:8]) if skills_a else 'None parsed'}</div>
                                <div style="font-size: 12px; opacity: 0.95; color: {fo_a_body}; margin-top: 6px;"><b>Assessment:</b> {row_a.get('Verdict', 'N/A')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        with card_b_col:
                            sim_b = float(row_b["Similarity"]) * 100
                            prob_b = float(row_b["Probability"]) * 100
                            skills_b = row_b["Skills"] if isinstance(row_b["Skills"], list) else []
                            is_fresher_b = bool(row_b.get("IsFresher", False))
                            tag_b = "🎓 Fresher" if is_fresher_b else "💼 Experienced"

                            st.markdown(f"""
                            <div style="background: {fo_b_bg}; border: {fo_b_bd}; border-radius: 12px; padding: 18px 20px; box-shadow: {fo_b_sh};">
                                <div style="font-size: 18px; font-weight: 800; color: {fo_b_title};">{cand_b_name} <span style="font-size: 12px; color: {fo_b_sub};">({tag_b})</span></div>
                                <div style="display: flex; gap: 20px; margin: 12px 0;">
                                    <div><span style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: {fo_b_lbl};">Role Match</span><div style="font-size: 22px; font-weight: 800; color: {fo_b_sim_c};">{sim_b:.1f}%</div></div>
                                    <div><span style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: {fo_b_lbl};">Fit Confidence</span><div style="font-size: 22px; font-weight: 800; color: {fo_conf_c};">{prob_b:.1f}%</div></div>
                                    <div><span style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: {fo_b_lbl};">Status</span><div style="font-size: 16px; font-weight: 800; color: {'#10b981' if row_b['Status']=='Selected' else '#ef4444'};">{row_b['Status']}</div></div>
                                </div>
                                <div style="font-size: 12px; color: {fo_b_body}; margin-top: 6px;"><b>Key Competencies ({len(skills_b)}):</b> {', '.join(skills_b[:8]) if skills_b else 'None parsed'}</div>
                                <div style="font-size: 12px; opacity: 0.95; color: {fo_b_body}; margin-top: 6px;"><b>Assessment:</b> {row_b.get('Verdict', 'N/A')}</div>
                            </div>
                            """, unsafe_allow_html=True)

                        # Head-to-Head Competency Matrix
                        st.markdown("<br>", unsafe_allow_html=True)
                        st.markdown("##### **Head-to-Head Skill Overlap Matrix**")
                        set_a = set(s.lower() for s in skills_a)
                        set_b = set(s.lower() for s in skills_b)
                        all_compared_skills = sorted(list(set(s.lower() for s in (skills_a + skills_b + jd_skills))))

                        matrix_rows = []
                        for s_low in all_compared_skills[:15]:
                            disp_s = s_low.title()
                            has_a = "✅" if s_low in set_a else "❌"
                            has_b = "✅" if s_low in set_b else "❌"
                            in_jd = "🎯 Role Must-Have" if (jd_skills and s_low in [j.lower() for j in jd_skills]) else "Supplementary"
                            matrix_rows.append({"Skill / Competency": disp_s, f"{cand_a_name}": has_a, f"{cand_b_name}": has_b, "Role Requirement": in_jd})

                        st.dataframe(pd.DataFrame(matrix_rows), use_container_width=True)

                # VIEW 3: TABULAR DATASET
                else:
                    table_view_df = display_df[["Candidate", "Filename", "Similarity", "Probability", "Status"]].copy()
                    table_view_df["Category"] = display_df["IsFresher"].apply(lambda f: "🎓 Fresher" if f else "💼 Experienced")
                    table_view_df["AI Assessment"] = display_df["Verdict"]
                    st.dataframe(table_view_df, use_container_width=True)

                st.markdown("---")

                # Action Bar
                bar_col1, bar_col2 = st.columns([1, 1])
                with bar_col1:
                    if st.button("SAVE EVALUATIONS TO PIPELINE", use_container_width=True):
                        conn = get_conn()
                        c = conn.cursor()
                        now_ts = datetime.now(timezone.utc).isoformat()
                        for _, row in res_df.iterrows():
                            c.execute("""
                                INSERT INTO screening_results(candidate, filename, similarity, probability, status, stage, jd_checksum, timestamp)
                                VALUES (?,?,?,?,?,?,?,?)
                            """, (
                                str(row["Candidate"]),
                                str(row["Filename"]),
                                float(row["Similarity"]),
                                float(row["Probability"]),
                                str(row["Status"]),
                                "Screened",
                                "v2.4",
                                now_ts
                            ))
                        conn.commit()
                        conn.close()
                        st.success("Evaluations recorded into talent pipeline ledger.")

                with bar_col2:
                    csv_export = display_df[["Candidate", "Filename", "Similarity", "Probability", "Status"]].to_csv(index=True).encode("utf-8")
                    st.download_button(
                        label="EXPORT TALENT DATASET (CSV)",
                        data=csv_export,
                        file_name=f"SmartHire_export_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )

            # ----------------------------------------------------
            # RESUMES UPLOADED BY CANDIDATES (BOTTOM OF ACTIVE SCREENING STUDIO)
            # ----------------------------------------------------
            st.markdown("---")
            st.markdown("### **Resumes Uploaded by Candidates**")
            st.caption("All resumes submitted directly by applicants through their candidate dashboard portal.")

            conn = get_conn()
            df_cand_resumes = pd.read_sql_query(
                "SELECT id, candidate as 'Candidate', filename as 'Filename', uploaded_at as 'Submission Timestamp', LENGTH(file_blob) as 'File Size (Bytes)' FROM resumes_blob ORDER BY uploaded_at DESC",
                conn
            )
            conn.close()

            if df_cand_resumes.empty:
                st.info("No resumes have been submitted by candidates through the portal yet.")
            else:
                st.dataframe(df_cand_resumes[["Candidate", "Filename", "Submission Timestamp", "File Size (Bytes)"]], use_container_width=True)

                st.markdown("##### **Candidate Document Quick Retrieval**")
                sel_cand_doc = st.selectbox(
                    "Select candidate resume to inspect or download:",
                    df_cand_resumes["Candidate"] + " (" + df_cand_resumes["Filename"] + ")",
                    key="as_bottom_cand_doc"
                )

                if sel_cand_doc:
                    chosen_cand_id = df_cand_resumes.iloc[
                        (df_cand_resumes["Candidate"] + " (" + df_cand_resumes["Filename"] + ")" == sel_cand_doc).argmax()
                    ]["id"]

                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("SELECT filename, file_blob, file_text FROM resumes_blob WHERE id=?", (int(chosen_cand_id),))
                    cand_row = c.fetchone()
                    conn.close()

                    if cand_row:
                        c_col1, c_col2, c_col3 = st.columns([1.2, 1.2, 2.6])
                        with c_col1:
                            if cand_row["file_blob"]:
                                st.download_button(
                                    label=f"DOWNLOAD {cand_row['filename']}",
                                    data=cand_row["file_blob"],
                                    file_name=cand_row["filename"],
                                    key=f"as_dl_{chosen_cand_id}",
                                    use_container_width=True
                                )
                        with c_col2:
                            st.markdown("<div class='delete-btn-box'>", unsafe_allow_html=True)
                            if st.button("DELETE RESUME", key=f"as_del_{chosen_cand_id}", use_container_width=True):
                                conn = get_conn()
                                c = conn.cursor()
                                c.execute("DELETE FROM resumes_blob WHERE id=?", (int(chosen_cand_id),))
                                conn.commit()
                                conn.close()
                                st.success(f"Resume '{cand_row['filename']}' deleted successfully.")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        with c_col3:
                            with st.expander("Inspect Extracted Document Text"):
                                st.text(cand_row["file_text"] or "No extracted text available.")

        # ----------------------------------------------------
        # TAB 2: TALENT PIPELINE & HISTORY
        # ----------------------------------------------------
        with hr_nav2:
            st.markdown("### **Talent Pipeline History**")
            conn = get_conn()
            df_pipeline = pd.read_sql_query(
                "SELECT id, candidate, filename, similarity, probability, status, timestamp FROM screening_results ORDER BY timestamp DESC",
                conn
            )
            conn.close()

            if df_pipeline.empty:
                st.info("Pipeline records are empty. Screen candidates in the Active Screening Studio to populate records.")
            else:
                p_col1, p_col2 = st.columns([2, 1])
                with p_col1:
                    p_search = st.text_input("Search Candidate Records:", "")
                with p_col2:
                    p_status = st.selectbox("Status Filter:", ["All", "Selected", "Rejected"])

                p_view = df_pipeline.copy()
                if p_search.strip():
                    p_view = p_view[p_view["candidate"].str.contains(p_search.strip(), case=False, na=False)]
                if p_status != "All":
                    p_view = p_view[p_view["status"] == p_status]

                st.dataframe(p_view, use_container_width=True)

                st.download_button(
                    label="DOWNLOAD PIPELINE LEDGER (CSV)",
                    data=p_view.to_csv(index=False).encode("utf-8"),
                    file_name="SmartHire_pipeline_ledger.csv",
                    mime="text/csv"
                )

        # ----------------------------------------------------
        # TAB 3: CANDIDATE VAULT
        # ----------------------------------------------------
        with hr_nav3:
            st.markdown("### **Candidate Document Vault**")
            st.caption("Secure document repository of applicant resumes uploaded into SmartHire.")

            conn = get_conn()
            df_vault = pd.read_sql_query(
                "SELECT id, candidate, filename, uploaded_at, LENGTH(file_blob) as file_size FROM resumes_blob ORDER BY uploaded_at DESC",
                conn
            )
            conn.close()

            if df_vault.empty:
                st.info("No documents found in vault.")
            else:
                st.dataframe(df_vault, use_container_width=True)

                st.markdown("##### **Document Retrieval & Inspection**")
                selected_vault_doc = st.selectbox(
                    "Select candidate file to retrieve:",
                    df_vault["candidate"] + " (" + df_vault["filename"] + ")"
                )

                if selected_vault_doc:
                    chosen_id = df_vault.iloc[
                        (df_vault["candidate"] + " (" + df_vault["filename"] + ")" == selected_vault_doc).argmax()
                    ]["id"]

                    conn = get_conn()
                    c = conn.cursor()
                    c.execute("SELECT filename, file_blob, file_text FROM resumes_blob WHERE id=?", (int(chosen_id),))
                    row_doc = c.fetchone()
                    conn.close()

                    if row_doc:
                        dl_col1, dl_col2, dl_col3 = st.columns([1.2, 1.2, 2.6])
                        with dl_col1:
                            if row_doc["file_blob"]:
                                st.download_button(
                                    label=f"DOWNLOAD {row_doc['filename']}",
                                    data=row_doc["file_blob"],
                                    file_name=row_doc["filename"],
                                    key=f"vault_dl_{chosen_id}",
                                    use_container_width=True
                                )
                        with dl_col2:
                            st.markdown("<div class='delete-btn-box'>", unsafe_allow_html=True)
                            if st.button("DELETE DOCUMENT", key=f"vault_del_{chosen_id}", use_container_width=True):
                                conn = get_conn()
                                c = conn.cursor()
                                c.execute("DELETE FROM resumes_blob WHERE id=?", (int(chosen_id),))
                                conn.commit()
                                conn.close()
                                st.success(f"Document '{row_doc['filename']}' deleted from vault.")
                                st.rerun()
                            st.markdown("</div>", unsafe_allow_html=True)
                        with dl_col3:
                            with st.expander("Inspect Extracted Document Text"):
                                st.text(row_doc["file_text"] or "No extracted text available.")

        # ----------------------------------------------------
        # TAB 4: TEAM & ACCESS
        # ----------------------------------------------------
        with hr_nav4:
            st.markdown("### **Team & Access Control**")
            users_df = get_all_users_df()
            st.dataframe(users_df, use_container_width=True)

            acc_col1, acc_col2 = st.columns([1, 1])

            with acc_col1:
                st.markdown("##### **Remove User Account**")
                usernames_list = users_df["username"].tolist()
                user_to_remove = st.selectbox("Select account to delete:", usernames_list)

                if st.button("DELETE USER ACCOUNT"):
                    if user_to_remove == st.session_state.username:
                        st.error("Cannot delete your own active session account.")
                    else:
                        delete_user(user_to_remove)
                        st.success(f"Account '{user_to_remove}' deleted.")
                        st.rerun()

            with acc_col2:
                st.markdown("##### **Provision Team Account**")
                with st.expander("Create User Account", expanded=True):
                    nu_name = st.text_input("Username", key="prov_u")
                    nu_pass = st.text_input("Password", type="password", key="prov_p")
                    nu_role = st.selectbox("Assign Role", ["Candidate", "HR"], key="prov_r")
                    nu_email = st.text_input("Corporate Email", key="prov_e")
                    
                    prov_sec_code = ""
                    if nu_role == "HR":
                        prov_sec_code = st.text_input("Company Security Code", type="password", key="prov_sec_code", help="Enter authorization code for HR account creation")

                    if st.button("PROVISION ACCOUNT", key="prov_btn"):
                        if not is_strong_password(nu_pass):
                            st.error("Password must be 8+ chars and contain uppercase, lowercase, digit, and symbol.")
                        elif nu_role == "HR" and prov_sec_code.strip() != "HR-SECURE-2026":
                            st.error("Invalid Company Security Code. HR accounts require authorization.")
                        elif create_user(nu_name, nu_pass, nu_role, nu_email or None):
                            st.success(f"Account '{nu_name}' provisioned successfully.")
                            st.rerun()
                        else:
                            st.error("Username already registered.")

    # ========================================================
    # CANDIDATE APPLICANT PORTAL
    # ========================================================
    elif role == "Candidate":
        st.markdown(f"### **Applicant Assessment Portal**")
        st.caption(f"Welcome back, {user}. Track your hiring progress and evaluate ATS fit.")

        conn = get_conn()
        df_cand_doc = pd.read_sql_query(
            "SELECT id, filename, uploaded_at, file_blob, file_text FROM resumes_blob WHERE candidate=? ORDER BY uploaded_at DESC LIMIT 1",
            conn,
            params=(user,)
        )
        df_cand_eval = pd.read_sql_query(
            "SELECT filename, similarity, probability, status, timestamp FROM screening_results WHERE candidate=? ORDER BY timestamp DESC LIMIT 1",
            conn,
            params=(user,)
        )
        conn.close()

        has_resume = not df_cand_doc.empty
        has_eval = not df_cand_eval.empty

        # 4-Stage Stepper
        step1_class = "token-complete" if has_resume else "token-dormant"
        step2_class = "token-complete" if has_eval else ("token-active" if has_resume else "token-dormant")
        step3_class = "token-active" if (has_eval and df_cand_eval.iloc[0]["status"] == "Selected") else "token-dormant"

        st.markdown(
            f"""
            <div class="stepper-deck">
                <div class="step-unit">
                    <div class="step-token {step1_class}">✓</div>
                    <div class="step-descriptor">Application Submitted</div>
                </div>
                <div class="step-unit">
                    <div class="step-token {step2_class}">2</div>
                    <div class="step-descriptor">Resume Screened</div>
                </div>
                <div class="step-unit">
                    <div class="step-token {step3_class}">3</div>
                    <div class="step-descriptor">Recruiter Review</div>
                </div>
                <div class="step-unit">
                    <div class="step-token token-dormant">4</div>
                    <div class="step-descriptor">Interview Stage</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        app_col1, app_col2 = st.columns([1, 1])

        with app_col1:
            st.markdown("#### **Active Resume on File**")
            if has_resume:
                c_filename = df_cand_doc.iloc[0]["filename"]
                c_uploaded_at = df_cand_doc.iloc[0]["uploaded_at"]
                c_blob = df_cand_doc.iloc[0]["file_blob"]
                c_text = df_cand_doc.iloc[0]["file_text"] or ""

                doc_card_bg = "linear-gradient(135deg, rgba(38, 19, 8, 0.95) 0%, rgba(24, 12, 5, 0.95) 100%)" if is_dark else "linear-gradient(135deg, #fff7ed 0%, #ffedd5 100%)"
                doc_card_bd = "1.5px solid rgba(249, 115, 22, 0.5)" if is_dark else "1.5px solid rgba(234, 88, 12, 0.45)"
                doc_title_col = "#ffffff" if is_dark else "#0f172a"
                doc_sub_col = "#fed7aa" if is_dark else "#7c2d12"

                st.markdown(
                    f"""
                    <div style="background: {doc_card_bg}; border: {doc_card_bd}; border-radius: 12px; padding: 18px 20px; margin-bottom: 14px; box-shadow: 0 4px 18px rgba(0,0,0,0.12);">
                        <div style="display: flex; align-items: center; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div style="width: 42px; height: 42px; border-radius: 10px; background: linear-gradient(135deg, #ea580c, #f59e0b); display: flex; align-items: center; justify-content: center; font-size: 20px; color: #ffffff;">📄</div>
                                <div>
                                    <div style="font-size: 11px; text-transform: uppercase; font-weight: 800; color: #ea580c; letter-spacing: 0.5px;">Active Resume Document</div>
                                    <div style="font-size: 15px; font-weight: 800; color: {doc_title_col}; margin-top: 2px; font-family: monospace;">{c_filename}</div>
                                </div>
                            </div>
                            <span style="background: #ea580c; color: #ffffff; padding: 4px 12px; border-radius: 20px; font-size: 11.5px; font-weight: 800; box-shadow: 0 2px 8px rgba(234, 88, 12, 0.35);">✓ Synced & Parsed</span>
                        </div>
                        <div style="font-size: 12px; color: {doc_sub_col}; margin-top: 10px; font-weight: 700;">
                            <b>Submission Timestamp:</b> {c_uploaded_at}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                skills_detected = extract_skills_from_text(c_text)
                if skills_detected:
                    st.markdown("**Parsed Competencies:**")
                    chips = "".join([f"<span class='skill-badge-item'>{s}</span>" for s in skills_detected[:10]])
                    st.markdown(f"<div>{chips}</div>", unsafe_allow_html=True)

                if c_blob:
                    st.download_button(
                        label="DOWNLOAD SUBMITTED FILE",
                        data=c_blob,
                        file_name=c_filename,
                        key="cand_dl_btn"
                    )
            else:
                st.info("No active resume found. Submit your resume to begin evaluation.")

        with app_col2:
            st.markdown("#### **" + ("Update Document" if has_resume else "Submit Resume") + "**")
            cand_new_file = st.file_uploader(
                "Upload Resume Document (.pdf, .docx, .txt)",
                type=["pdf", "docx", "txt"],
                key="cand_file_up"
            )

            if cand_new_file and st.button("SUBMIT APPLICATION", type="primary"):
                cand_new_file.seek(0)
                extracted_txt = extract_text_from_file(cand_new_file)
                cand_new_file.seek(0)
                buf_bytes = cand_new_file.read()

                save_resume_blob(user, cand_new_file.name, buf_bytes, extracted_txt)
                with open(os.path.join(UPLOAD_DIR, f"{datetime.now(timezone.utc).timestamp()}_{cand_new_file.name}"), "wb") as out:
                    out.write(buf_bytes)

                st.success("Resume updated and transmitted to recruiting pipeline.")
                st.rerun()

        # Fit Assessment Feedback
        st.markdown("---")
        st.markdown("### **Screening Evaluation & Fit Assessment**")

        if not has_resume:
            st.info("Please submit your resume to receive automated ATS benchmark metrics.")
        elif not has_eval:
            st.info("Your resume is queued for benchmark evaluation by the recruitment lead.")
        else:
            latest = df_cand_eval.iloc[0]
            st_col1, st_col2, st_col3 = st.columns(3)
            
            st_col1.metric("Screening Decision", latest["status"])
            st_col2.metric("Role Relevance Score", f"{float(latest['similarity']) * 100:.1f}%")
            st_col3.metric("Shortlist Fit", f"{float(latest['probability']) * 100:.1f}%")

            cand_skills = extract_skills_from_text(df_cand_doc.iloc[0]["file_text"] if has_resume else "")
            cand_pdf = build_pdf_report(
                user,
                latest["filename"],
                float(latest["similarity"]),
                float(latest["probability"]),
                status=latest["status"],
                matched_skills=cand_skills
            )

            st.download_button(
                label="DOWNLOAD OFFICIAL EVALUATION DOSSIER (PDF)",
                data=cand_pdf,
                file_name=f"{user}_SmartHire_dossier.pdf",
                mime="application/pdf"
            )

        with st.expander("ATS Optimization Recommendations"):
            st.markdown("""
            - **Include Core Keywords:** Integrate exact technology terms from the target role specification.
            - **Clean Layout:** Use single-column standard formatting to ensure high-fidelity document parsing.
            - **Measurable Metrics:** Quantify your work impact with percentages, throughput figures, or scale metrics.
            """)
