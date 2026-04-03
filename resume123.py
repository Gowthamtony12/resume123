import streamlit as st
import pdfplumber
from groq import Groq
import re
import json
import plotly.graph_objects as go
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, ListFlowable, ListItem
from reportlab.lib.enums import TA_CENTER
import io
import requests
from bs4 import BeautifulSoup

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="ATS Co-Pilot",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
# GLOBAL CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700;900&family=Instrument+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] { font-family: 'Instrument Sans', sans-serif; }

section[data-testid="stSidebar"] {
    background: #0a0a0a; border-right: 1px solid #1e1e1e;
}
section[data-testid="stSidebar"] * { color: #d4d4d4 !important; }
section[data-testid="stSidebar"] .stTextInput input {
    background: #161616 !important; border: 1px solid #2e2e2e !important;
    color: #fff !important; border-radius: 8px;
    font-family: 'Instrument Sans', sans-serif !important;
}

.main, [data-testid="stAppViewContainer"] { background: #f7f7f5; }

.hero-wrap { padding: 2rem 0 1.6rem; border-bottom: 1px solid #e4e4e0; margin-bottom: 2rem; }
.hero-eyebrow { font-size: 0.72rem; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase; color: #999; margin-bottom: 0.4rem; }
.hero-title { font-family: 'Playfair Display', serif; font-size: 3rem; font-weight: 900; color: #0a0a0a; line-height: 1.05; letter-spacing: -1px; margin-bottom: 0.5rem; }
.hero-title span { color: #1a6b3c; }
.hero-desc { font-size: 0.95rem; color: #777; font-weight: 300; max-width: 540px; line-height: 1.65; }

.step-bar { display: flex; gap: 6px; margin-bottom: 2.2rem; flex-wrap: wrap; }
.step-pill { display: flex; align-items: center; gap: 7px; padding: 0.5rem 1rem; border-radius: 50px; font-size: 0.78rem; font-weight: 500; border: 1.5px solid #e0e0dc; background: #fff; color: #aaa; white-space: nowrap; }
.step-pill .num { width: 20px; height: 20px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 0.68rem; font-weight: 700; background: #eee; color: #aaa; }
.step-pill.done  { border-color:#c8e6c9; background:#f1faf2; color:#2e7d32; }
.step-pill.done .num { background:#2e7d32; color:#fff; }
.step-pill.active { border-color:#0a0a0a; background:#0a0a0a; color:#fff; }
.step-pill.active .num { background:#fff; color:#0a0a0a; }
.step-pill.locked { opacity:0.4; }

.sec-label { font-size: 0.68rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #999; margin-bottom: 0.5rem; }
.sec-title { font-family: 'Playfair Display', serif; font-size: 1.5rem; font-weight: 700; color: #0a0a0a; margin-bottom: 0.2rem; border-bottom: 2px solid #0a0a0a; padding-bottom: 0.35rem; }

[data-testid="stFileUploader"] { border: 2px dashed #d8d8d4 !important; border-radius: 12px !important; background: #fff !important; padding: 0.5rem !important; }
[data-testid="stFileUploader"]:hover { border-color: #0a0a0a !important; }

.stTextArea textarea { font-family: 'Instrument Sans', sans-serif !important; font-size: 0.88rem !important; border: 1.5px solid #e0e0dc !important; border-radius: 10px !important; background: #fff !important; color: #0a0a0a !important; line-height: 1.65 !important; padding: 0.9rem 1rem !important; }
.stTextArea textarea:focus { border-color: #0a0a0a !important; box-shadow: 0 0 0 3px rgba(10,10,10,0.06) !important; }

.score-card { background: #fff; border: 1.5px solid #e8e8e4; border-radius: 16px; padding: 1.8rem; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.score-num { font-family: 'Playfair Display', serif; font-size: 4.5rem; font-weight: 900; line-height: 1; letter-spacing: -2px; }
.score-unit { font-size: 2rem; font-weight: 400; }
.score-lbl { font-size: 0.65rem; font-weight: 700; letter-spacing: 2.5px; text-transform: uppercase; color: #888; margin-top: 4px; }

.pbar-wrap { background: #eeede9; border-radius: 50px; height: 8px; width: 100%; overflow: hidden; margin: 1rem 0 0.3rem; }
.pbar-fill { height: 100%; border-radius: 50px; }
.pbar-meta { display: flex; justify-content: space-between; font-size: 0.72rem; color: #aaa; margin-top: 3px; }

.alert { padding: 0.75rem 1rem; border-radius: 8px; font-size: 0.85rem; line-height: 1.5; margin: 0.8rem 0; display: flex; gap: 0.5rem; align-items: flex-start; }
.alert-green  { background:#f0faf1; border-left:3px solid #2e7d32; color:#1b5e20; }
.alert-yellow { background:#fffbf0; border-left:3px solid #e6a817; color:#6d4c00; }
.alert-grey   { background:#f5f5f3; border-left:3px solid #ccc;    color:#888; }
.alert-blue   { background:#f0f6ff; border-left:3px solid #1565c0; color:#0d3c6e; }
.alert-purple { background:#f5f0ff; border-left:3px solid #6a1b9a; color:#4a148c; }

.skill-confirmed-wrap { display:flex; flex-wrap:wrap; gap:8px; margin:1rem 0; }
.skill-confirmed-pill { background:#f0faf1; border:1.5px solid #c8e6c9; color:#1b5e20; padding:4px 12px; border-radius:50px; font-size:0.78rem; font-weight:500; }

.pdf-success-banner { background: linear-gradient(135deg,#f0faf1 0%,#e8f5e9 100%); border: 1.5px solid #a5d6a7; border-radius: 14px; padding: 1.5rem 1.8rem; text-align: center; margin-bottom: 1.2rem; }
.pdf-success-banner .big-check { font-size:2.5rem; margin-bottom:0.3rem; }
.pdf-success-banner h3 { font-family:'Playfair Display',serif; font-size:1.4rem; color:#1b5e20; margin:0 0 0.3rem; }
.pdf-success-banner p { font-size:0.85rem; color:#388e3c; margin:0; }

/* ── JD Compare Cards ── */
.jd-card {
    background: #fff;
    border: 1.5px solid #e8e8e4;
    border-radius: 16px;
    padding: 1.5rem 1.6rem;
    box-shadow: 0 2px 10px rgba(0,0,0,0.04);
    height: 100%;
    position: relative;
    transition: border-color 0.2s;
}
.jd-card.winner {
    border-color: #1a6b3c;
    box-shadow: 0 4px 20px rgba(26,107,60,0.12);
}
.jd-card .best-badge {
    position: absolute;
    top: -12px; right: 16px;
    background: #1a6b3c; color: #fff;
    font-size: 0.72rem; font-weight: 700;
    letter-spacing: 1.5px; text-transform: uppercase;
    padding: 4px 12px; border-radius: 50px;
}
.jd-card .job-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.1rem; font-weight: 700;
    color: #0a0a0a; margin-bottom: 0.15rem;
}
.jd-card .company-name {
    font-size: 0.82rem; color: #888; margin-bottom: 1rem;
}
.jd-card .jd-score {
    font-family: 'Playfair Display', serif;
    font-size: 2.8rem; font-weight: 900; line-height: 1;
}
.jd-card .jd-score-lbl {
    font-size: 0.65rem; font-weight: 700; letter-spacing: 2px;
    text-transform: uppercase; color: #aaa; margin-bottom: 1rem;
}
.missing-tag {
    display: inline-block;
    background: #fff8e1; border: 1px solid #ffe082;
    color: #6d4c00; font-size: 0.75rem; font-weight: 500;
    padding: 3px 10px; border-radius: 50px; margin: 3px 3px 3px 0;
}
.confirmed-tag {
    display: inline-block;
    background: #f0faf1; border: 1px solid #c8e6c9;
    color: #1b5e20; font-size: 0.75rem; font-weight: 500;
    padding: 3px 10px; border-radius: 50px; margin: 3px 3px 3px 0;
}

/* ── AI Recommendation banner ── */
.ai-rec-banner {
    background: linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%);
    border-radius: 16px; padding: 1.8rem 2rem;
    color: #fff; margin: 1.5rem 0;
}
.ai-rec-banner .rec-eyebrow {
    font-size: 0.68rem; font-weight: 700; letter-spacing: 2.5px;
    text-transform: uppercase; color: #888; margin-bottom: 0.5rem;
}
.ai-rec-banner .rec-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.6rem; font-weight: 900; color: #fff;
    margin-bottom: 0.6rem; line-height: 1.2;
}
.ai-rec-banner .rec-title span { color: #4caf50; }
.ai-rec-banner .rec-reason {
    font-size: 0.9rem; color: #bbb; line-height: 1.65;
}

/* Interview */
.interview-card { background: #fff; border: 1.5px solid #e8e8e4; border-radius: 14px; padding: 1.4rem 1.6rem; margin-bottom: 1rem; box-shadow: 0 1px 6px rgba(0,0,0,0.04); }
.interview-card .q-num { font-size: 0.68rem; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: #1565c0; margin-bottom: 0.3rem; }
.interview-card .q-text { font-family: 'Playfair Display', serif; font-size: 1.05rem; font-weight: 700; color: #0a0a0a; margin-bottom: 0.6rem; line-height: 1.4; }
.interview-card .q-framework { font-size: 0.84rem; color: #555; line-height: 1.65; }
.interview-section-header { font-family: 'Playfair Display', serif; font-size: 1.8rem; font-weight: 900; color: #0a0a0a; margin-bottom: 0.3rem; letter-spacing: -0.5px; }
.interview-sub { font-size: 0.88rem; color: #777; margin-bottom: 1.5rem; line-height: 1.6; }

.divider { border:none; border-top:1px solid #e4e4e0; margin:2rem 0; }

@keyframes fadeUp { from { opacity:0; transform:translateY(20px); } to { opacity:1; transform:translateY(0); } }
.fade-up { animation: fadeUp 0.5s ease forwards; }

div.stButton > button { background: #0a0a0a; color: #fff; border: none; border-radius: 10px; padding: 0.65rem 1.5rem; font-family: 'Instrument Sans', sans-serif; font-size: 0.88rem; font-weight: 600; letter-spacing: 0.3px; transition: all 0.2s; width: 100%; }
div.stButton > button:hover { background: #222; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,0.15); }
div.stDownloadButton > button { background: #fff; color: #0a0a0a; border: 2px solid #0a0a0a; border-radius: 10px; padding: 0.65rem 1.5rem; font-family: 'Instrument Sans', sans-serif; font-weight: 600; font-size: 0.9rem; transition: all 0.2s; width: 100%; }
div.stDownloadButton > button:hover { background: #0a0a0a; color: #fff; transform: translateY(-1px); box-shadow: 0 4px 14px rgba(0,0,0,0.15); }
#MainMenu, footer { visibility: hidden; }

/* ── Mode radio ── */
div[data-testid="stRadio"] > div {
    display: flex; gap: 10px; flex-direction: row !important;
}
div[data-testid="stRadio"] label {
    background: #fff;
    border: 1.5px solid #e0e0dc;
    border-radius: 50px;
    padding: 0.45rem 1.2rem;
    font-size: 0.85rem;
    font-weight: 500;
    color: #555;
    cursor: pointer;
    transition: all 0.2s;
}
div[data-testid="stRadio"] label:hover {
    border-color: #0a0a0a;
    color: #0a0a0a;
}
div[data-testid="stRadio"] input:checked + div {
    font-weight: 600;
    color: #0a0a0a;
}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🎯 ATS Co-Pilot")
    st.markdown("---")
    # API key from Streamlit secrets (no input needed for deployed app)
    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        api_key = st.text_input("Groq API Key", type="password", placeholder="gsk_... (local use only)")
    else:
        st.markdown("<div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:8px;padding:0.5rem 0.8rem;font-size:0.78rem;color:#4caf50'>🔐 API key loaded securely</div>", unsafe_allow_html=True)
    st.caption("Powered by llama-3.3-70b-versatile")
    st.markdown("---")
    st.markdown("**Workflow**")
    st.markdown("1. 📄 Upload resume PDF")
    st.markdown("2. 📋 Paste JD or compare 3 JDs")
    st.markdown("3. 📊 Review radar score")
    st.markdown("4. ✅ Confirm hidden skills")
    st.markdown("5. 🚀 Generate & download PDF")
    st.markdown("6. 🎤 Interview prep questions")
    st.markdown("---")
    st.caption("Score must reach **80%** to unlock resume generation.")
    st.markdown("---")
    st.markdown("""
<div style='background:#111;border:1px solid #1e3a1e;border-radius:10px;padding:0.9rem 1rem'>
<div style='font-size:0.68rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#4caf50;margin-bottom:0.5rem'>🛡 Privacy & Data</div>
<div style='font-size:0.78rem;color:#aaa;line-height:1.6'>
Your resume and job descriptions are <b style='color:#e0e0e0'>never stored</b>.<br><br>
Everything lives in your browser session only — when you close this tab, all data is permanently gone.<br><br>
Content is sent to <b style='color:#e0e0e0'>Groq's API</b> for AI processing only, and is not used for training.
</div>
</div>
""", unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🔁 Start Over", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

MODEL = "llama-3.3-70b-versatile"

# ─────────────────────────────────────────────
# SESSION STATE
# ─────────────────────────────────────────────
defaults = {
    "step": 1,
    "resume_text": "",
    "jd_text": "",
    "analysis": None,
    "score": 0,
    "radar_scores": {},
    "missing_skills": [],
    "confirmed_skills": [],
    "updated_score": 0,
    "tailored_data": None,
    "interview_questions": None,
    # Compare mode
    "compare_mode": False,
    "compare_results": [],       # list of dicts per JD
    "compare_confirmed": {},     # {jd_index: [confirmed skills]}
    "compare_updated_scores": {},# {jd_index: score}
    "ai_recommendation": None,  # {winner_index, job_title, reason}
    "proceeded_from_compare": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def extract_pdf(file):
    try:
        with pdfplumber.open(file) as pdf:
            text = "\n\n".join(p.extract_text(layout=True) or "" for p in pdf.pages)
        return text.strip() or None
    except Exception:
        return None

def scrape_jd_from_url(url: str) -> dict:
    """Scrape job description text from a URL. Returns {title, company, text}."""
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=12)
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove scripts/styles
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()

        # Try to get title
        title = ""
        for sel in ["h1", ".job-title", ".posting-headline", "[data-testid='job-title']"]:
            el = soup.select_one(sel)
            if el:
                title = el.get_text(strip=True)
                break
        if not title:
            title = soup.title.string.strip() if soup.title else "Job"

        # Try to get company
        company = ""
        for sel in [".company-name", ".employer-name", "[data-testid='company-name']", ".topcard__org-name-link"]:
            el = soup.select_one(sel)
            if el:
                company = el.get_text(strip=True)
                break

        # Get all text
        text = soup.get_text(separator="\n", strip=True)
        # Keep only meaningful lines
        lines = [l.strip() for l in text.splitlines() if len(l.strip()) > 30]
        jd_text = "\n".join(lines[:200])  # cap at 200 lines

        return {"title": title[:80], "company": company[:60], "text": jd_text, "error": None}
    except Exception as e:
        return {"title": "", "company": "", "text": "", "error": str(e)}

def call_groq(prompt):
    try:
        client = Groq(api_key=api_key)
        res = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.15,
        )
        return res.choices[0].message.content
    except Exception as e:
        return f"API_ERROR: {e}"

def clean_markdown_bold(text: str) -> str:
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

def clean_for_pdf(text: str) -> str:
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = clean_markdown_bold(text)
    text = re.sub(r'&(?!lt;|gt;|amp;|nbsp;)', '&amp;', text)
    return text

def dedup_list(lst: list) -> list:
    seen = set()
    result = []
    for item in lst:
        key = item.strip().lower()
        if key not in seen:
            seen.add(key)
            result.append(item.strip())
    return result

def radar_chart(scores: dict, updated_scores: dict = None):
    categories = list(scores.keys())
    vals       = list(scores.values())
    v_close    = vals + [vals[0]]
    c_close    = categories + [categories[0]]
    fig = go.Figure()
    if updated_scores:
        uv = [updated_scores.get(c, scores[c]) for c in categories]
        fig.add_trace(go.Scatterpolar(
            r=uv + [uv[0]], theta=c_close,
            fill='toself', name='After Skills',
            line=dict(color='#2e7d32', width=2),
            fillcolor='rgba(46,125,50,0.12)'
        ))
    fig.add_trace(go.Scatterpolar(
        r=v_close, theta=c_close, fill='toself', name='Current',
        line=dict(color='#0a0a0a', width=2.5),
        fillcolor='rgba(10,10,10,0.07)'
    ))
    fig.update_layout(
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0,100], tickfont=dict(size=9, color='#aaa'), gridcolor='#e8e8e4', linecolor='#e8e8e4'),
            angularaxis=dict(tickfont=dict(size=11, color='#333', family='Instrument Sans'), gridcolor='#e8e8e4', linecolor='#ddd')
        ),
        showlegend=bool(updated_scores),
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=20, b=20, l=55, r=55), height=360,
        font=dict(family='Instrument Sans'),
        legend=dict(x=0.75, y=1.15, font=dict(size=10, color='#555'))
    )
    return fig

def score_color(s):
    if s >= 80: return "#1a6b3c"
    if s >= 60: return "#c97b00"
    return "#b71c1c"

def render_progress(score):
    color = score_color(score)
    st.markdown(f"""
    <div class="pbar-wrap">
        <div class="pbar-fill" style="width:{min(score,100)}%;background:{color};"></div>
    </div>
    <div class="pbar-meta">
        <span>0%</span>
        <span style="color:{color};font-weight:600">{score}% match</span>
        <span>80% target</span><span>100%</span>
    </div>
    """, unsafe_allow_html=True)

def step_bar(current):
    labels = ["Resume", "Job Description", "Score & Skills", "Generate PDF", "Interview Prep"]
    html   = '<div class="step-bar">'
    for i, lbl in enumerate(labels, 1):
        if i < current:    cls = "done";   num = "✓"
        elif i == current: cls = "active"; num = str(i)
        else:              cls = "locked"; num = str(i)
        html += f'<div class="step-pill {cls}"><span class="num">{num}</span>{lbl}</div>'
    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# PDF GENERATION
# ─────────────────────────────────────────────
def generate_pdf(data: dict) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=18*mm, bottomMargin=18*mm)
    BLACK = colors.HexColor("#0a0a0a")
    GREY  = colors.HexColor("#555555")

    name_s    = ParagraphStyle("N",  fontName="Helvetica-Bold",    fontSize=22, leading=28, textColor=BLACK, alignment=TA_CENTER)
    contact_s = ParagraphStyle("C",  fontName="Helvetica",         fontSize=9,  leading=13, textColor=GREY,  alignment=TA_CENTER)
    sec_s     = ParagraphStyle("S",  fontName="Helvetica-Bold",    fontSize=10, leading=14, textColor=BLACK, spaceBefore=12, spaceAfter=3)
    body_s    = ParagraphStyle("B",  fontName="Helvetica",         fontSize=9.5, leading=15, textColor=BLACK, spaceAfter=2)
    bold_s    = ParagraphStyle("Bo", fontName="Helvetica-Bold",    fontSize=9.5, leading=15, textColor=BLACK)
    sub_s     = ParagraphStyle("Su", fontName="Helvetica-Oblique", fontSize=9,  leading=13, textColor=GREY, spaceAfter=3)

    def hr():
        return HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#cccccc"), spaceAfter=5, spaceBefore=2)

    def section(title):
        return [Paragraph(title.upper(), sec_s), hr()]

    story = []
    story.append(Paragraph(clean_for_pdf(data.get("name", "Candidate")), name_s))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(clean_for_pdf(data.get("contact", "")), contact_s))
    story.append(Spacer(1, 5*mm))
    story.append(hr())

    story += section("Professional Summary")
    story.append(Paragraph(clean_for_pdf(data.get("summary", "")), body_s))
    story.append(Spacer(1, 4*mm))

    story += section("Core Skills")
    raw_skills  = data.get("skills", []) + data.get("extra_skills", [])
    deduped     = dedup_list(raw_skills)
    skills_line = "  ·  ".join(f"<b>{clean_for_pdf(s)}</b>" for s in deduped)
    story.append(Paragraph(skills_line, body_s))
    story.append(Spacer(1, 4*mm))

    story += section("Professional Experience")
    for exp in data.get("experience", []):
        story.append(Paragraph(clean_for_pdf(exp.get("title", "")), bold_s))
        story.append(Paragraph(f"{clean_for_pdf(exp.get('company',''))}  |  {clean_for_pdf(exp.get('duration',''))}", sub_s))
        story.append(Spacer(1, 2*mm))
        bullets = [ListItem(Paragraph(clean_for_pdf(b), body_s), leftIndent=14, bulletColor=BLACK, spaceAfter=3)
                   for b in exp.get("bullets", [])]
        if bullets:
            story.append(ListFlowable(bullets, bulletType='bullet', leftIndent=18, bulletFontSize=7, spaceBefore=2, spaceAfter=2))
        story.append(Spacer(1, 6*mm))

    story += section("Education")
    for edu in data.get("education", []):
        story.append(Paragraph(clean_for_pdf(edu.get("degree", "")), bold_s))
        story.append(Paragraph(f"{clean_for_pdf(edu.get('institution',''))}  |  {clean_for_pdf(edu.get('year',''))}", sub_s))
        story.append(Spacer(1, 4*mm))

    doc.build(story)
    buf.seek(0)
    return buf.read()

# ─────────────────────────────────────────────
# PROMPTS
# ─────────────────────────────────────────────
ANALYSIS_PROMPT = """
You are a senior ATS expert and technical recruiter.
Analyse the resume against the job description. Return ONLY valid JSON — no markdown, no explanation.

{{
  "overall_score": <integer 0-100>,
  "radar": {{
    "Technical Skills":   <integer 0-100>,
    "Tools & Frameworks": <integer 0-100>,
    "Domain Knowledge":   <integer 0-100>,
    "Experience Level":   <integer 0-100>
  }},
  "missing_skills": ["skill1","skill2","skill3","skill4","skill5","skill6"],
  "candidate_name": "<full name or Candidate>",
  "contact_info":   "<email | phone | linkedin>",
  "existing_skills":["skill1","skill2"],
  "experience": [
    {{"title":"","company":"","duration":"Month YYYY – Month YYYY","bullets":["","",""]}}
  ],
  "education": [{{"degree":"","institution":"","year":"YYYY"}}],
  "summary": "2-3 sentence professional summary tailored to the JD."
}}

IMPORTANT: Do NOT use **markdown bold** anywhere. Plain text only.

RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""

COMPARE_ANALYSIS_PROMPT = """
You are a senior ATS expert. Analyse this resume against the job description.
Return ONLY valid JSON — no markdown, no explanation.

{{
  "overall_score": <integer 0-100>,
  "job_title": "<job title from the JD>",
  "company": "<company name from JD or Unknown>",
  "missing_skills": ["skill1","skill2","skill3","skill4","skill5"],
  "existing_skills": ["skill1","skill2","skill3"]
}}

RESUME:
{resume}

JOB DESCRIPTION:
{jd}
"""

RECOMMEND_PROMPT = """
You are a senior career advisor. A candidate has compared their resume against 3 job descriptions.
Based on the scores, skills overlap, and role fit, recommend which job they should apply to first.

Return ONLY valid JSON — no markdown, no explanation.

{{
  "winner_index": <0, 1, or 2>,
  "job_title": "<winning job title>",
  "company": "<winning company>",
  "reason": "<2-3 sentences explaining why this is the best match — mention score, skill overlap, and role fit>"
}}

JOB COMPARISONS:
{comparisons}

CANDIDATE RESUME SUMMARY:
{resume_summary}
"""

TAILORING_PROMPT = """
You are an expert resume writer. Rewrite the resume to maximally match the JD.
Return ONLY valid JSON — no markdown fences, no explanation.

RULES:
- Do NOT use **markdown bold** (asterisks). Plain text only in all fields.
- Do NOT duplicate skills — each skill appears only once.
- Summary must be 3 strong sentences mentioning the most important confirmed extra skills.
- CRITICAL: The confirmed extra skills MUST be naturally woven into the experience bullets.
  For each role, rewrite at least 1-2 bullets to reference the confirmed extra skills where relevant.
  Do not just list them in skills — show them being used in real work context.
- Keep bullets achievement-focused, starting with a strong action verb, ATS-friendly.
- Each role should have 3-4 strong bullets.

{{
  "name":        "<candidate name>",
  "contact":     "<contact info>",
  "summary":     "<3 sentences mentioning confirmed extra skills naturally>",
  "skills":      ["skill1","skill2"],
  "extra_skills": {extra_skills},
  "experience": [{{
    "title":    "",
    "company":  "",
    "duration": "",
    "bullets":  [
      "<bullet naturally referencing a confirmed extra skill if relevant>",
      "<achievement bullet>",
      "<achievement bullet>"
    ]
  }}],
  "education": [{{"degree":"","institution":"","year":""}}]
}}

ANALYSIS: {analysis}
CONFIRMED EXTRA SKILLS TO WEAVE INTO EXPERIENCE: {extra_skills}
JOB DESCRIPTION: {jd}
"""

INTERVIEW_PROMPT = """
You are an expert interview coach. Generate exactly 8 targeted interview questions.
Return ONLY valid JSON — no markdown, no explanation.

{{
  "questions": [
    {{
      "number": 1,
      "category": "Technical / Behavioural / Situational / Role-Specific",
      "question": "Full interview question?",
      "framework": "2-3 sentence answer guidance referencing the candidate's background."
    }}
  ]
}}

RESUME SUMMARY: {summary}
JOB DESCRIPTION: {jd}
CANDIDATE SKILLS: {skills}
"""

# ─────────────────────────────────────────────
# HERO
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero-wrap fade-up">
    <div class="hero-eyebrow">AI-Powered Career Tool</div>
    <div class="hero-title">Land the Job.<br><span>Beat the ATS.</span></div>
    <div class="hero-desc">
        Upload your resume, analyse against a job description or compare 3 at once.
        Confirm hidden skills, hit 80%, get a tailored PDF, and prep for your interview — all in one place.
    </div>
</div>
""", unsafe_allow_html=True)

step_bar(st.session_state.step)

# Privacy notice bar
st.markdown("""
<div style='background:#f0faf1;border:1px solid #c8e6c9;border-radius:10px;
padding:0.7rem 1.2rem;display:flex;align-items:center;gap:0.8rem;margin-bottom:1.5rem'>
  <span style='font-size:1.2rem'>🛡️</span>
  <div>
    <span style='font-size:0.82rem;font-weight:600;color:#1b5e20'>Your data never leaves your session.</span>
    <span style='font-size:0.82rem;color:#388e3c'> &nbsp;No accounts. No storage. No tracking. Resume and JD content is processed in real-time and permanently discarded when you close this tab.</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════
# STEP 1 — Resume Upload
# ══════════════════════════════════════════════
st.markdown('<div class="sec-label">Step 01</div><div class="sec-title">Your Resume</div>', unsafe_allow_html=True)
st.markdown("<p style='color:#777;font-size:0.85rem;margin:0.4rem 0 0.8rem'>Upload a text-based PDF — not a scanned image.</p>", unsafe_allow_html=True)

resume_file = st.file_uploader("Upload resume PDF", type="pdf", label_visibility="collapsed", key="resume_upload")
if resume_file:
    text = extract_pdf(resume_file)
    if text:
        st.session_state.resume_text = text
        st.markdown('<div class="alert alert-green">✓ Resume extracted successfully.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="alert alert-yellow">⚠ Could not read text. Make sure your PDF is not a scanned image.</div>', unsafe_allow_html=True)

st.markdown('<hr class="divider">', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# STEP 2 — JD Input Mode Toggle
# ══════════════════════════════════════════════
st.markdown('<div class="sec-label">Step 02</div><div class="sec-title">Job Description</div>', unsafe_allow_html=True)
st.markdown("<p style='color:#777;font-size:0.85rem;margin:0.4rem 0 1rem'>Paste a single JD or compare 3 jobs by URL to find your best match.</p>", unsafe_allow_html=True)

jd_mode = st.radio(
    "JD Input Mode",
    options=["📋 Paste Single JD", "📊 Compare 3 JDs"],
    horizontal=True,
    label_visibility="collapsed",
    key="jd_mode_radio"
)

# Sync radio to session state — but don't interfere after user proceeds from compare
if not st.session_state.proceeded_from_compare:
    if jd_mode == "📊 Compare 3 JDs":
        if not st.session_state.compare_mode:
            st.session_state.compare_mode     = True
            st.session_state.analysis         = None
            st.session_state.jd_text          = ""
    else:
        if st.session_state.compare_mode:
            st.session_state.compare_mode     = False
            st.session_state.compare_results  = []
            st.session_state.ai_recommendation = None

st.markdown("<br>", unsafe_allow_html=True)

# ── Single JD Mode ──
if not st.session_state.compare_mode:
    jd_input = st.text_area(
        "Paste JD", height=240,
        placeholder="Paste the full job description here…\n\nTip: include everything — responsibilities, requirements, preferred skills.",
        label_visibility="collapsed", key="jd_textarea"
    )
    if jd_input and jd_input.strip():
        st.session_state.jd_text = jd_input.strip()
        wc = len(jd_input.split())
        st.markdown(f'<div class="alert alert-green">✓ Job description ready — {wc} words.</div>', unsafe_allow_html=True)
    else:
        st.session_state.jd_text = ""

    st.markdown("<br>", unsafe_allow_html=True)
    both_ready = bool(st.session_state.resume_text and st.session_state.jd_text)
    if both_ready:
        if st.button("🔍 Analyse My Match", use_container_width=True):
            if not api_key:
                st.error("Enter your Groq API Key in the sidebar.")
            else:
                with st.spinner("Analysing — takes 10–15 seconds…"):
                    raw = call_groq(ANALYSIS_PROMPT.format(
                        resume=st.session_state.resume_text,
                        jd=st.session_state.jd_text
                    ))
                    if raw.startswith("API_ERROR"):
                        st.error(raw)
                    else:
                        try:
                            clean = re.sub(r"```json|```", "", raw).strip()
                            data  = json.loads(clean)
                            st.session_state.analysis         = data
                            st.session_state.score            = data.get("overall_score", 0)
                            st.session_state.radar_scores     = data.get("radar", {})
                            st.session_state.missing_skills   = data.get("missing_skills", [])
                            st.session_state.updated_score    = st.session_state.score
                            st.session_state.confirmed_skills = []
                            st.session_state.tailored_data    = None
                            st.session_state.interview_questions = None
                            st.session_state.step             = 3
                            st.rerun()
                        except Exception:
                            st.error("Could not parse AI response. Please try again.")
    else:
        st.markdown('<div class="alert alert-grey">🔒 Upload your resume and paste a job description to continue.</div>', unsafe_allow_html=True)

# ── Compare Mode ──
else:
    st.markdown("""
    <p style='color:#555;font-size:0.87rem;margin-bottom:1.2rem;line-height:1.65'>
    Copy-paste 3 job descriptions from LinkedIn, Naukri, Indeed, or any platform.
    Give each a label so you can tell them apart. AI will analyse all 3 and pick your best match.
    </p>
    """, unsafe_allow_html=True)

    jd_entries = []
    for i in range(3):
        st.markdown(f"<div style='font-size:0.68rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#999;margin-bottom:0.4rem'>Job {i+1}</div>", unsafe_allow_html=True)
        lcol, rcol = st.columns([1, 2], gap="small")
        with lcol:
            title   = st.text_input("Job title",    key=f"cmp_title_{i}",   placeholder="e.g. Product Designer", label_visibility="collapsed")
            company = st.text_input("Company name", key=f"cmp_company_{i}", placeholder="e.g. Google",           label_visibility="collapsed")
        with rcol:
            jd_val = st.text_area(f"Paste JD {i+1}", key=f"cmp_jd_{i}", height=130,
                                   placeholder=f"Paste the full job description for Job {i+1} here…",
                                   label_visibility="collapsed")
        jd_entries.append({
            "title":   title.strip()   if title   else f"Job {i+1}",
            "company": company.strip() if company else "Unknown",
            "text":    jd_val.strip()  if jd_val  else ""
        })
        if jd_val and jd_val.strip():
            wc = len(jd_val.split())
            st.markdown(f'<div class="alert alert-green" style="margin-bottom:0.5rem">✓ Job {i+1} ready — {wc} words.</div>', unsafe_allow_html=True)
        if i < 2:
            st.markdown('<hr style="border:none;border-top:1px dashed #e0e0dc;margin:1rem 0">', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    filled     = sum(1 for e in jd_entries if e["text"])
    all_filled = filled == 3

    if not all_filled:
        st.markdown(f'<div class="alert alert-grey">🔒 Paste all 3 job descriptions to compare. ({filled}/3 filled)</div>', unsafe_allow_html=True)

    if st.session_state.resume_text and all_filled:
        if st.button("🔍 Analyse & Compare All 3 Jobs", use_container_width=True):
            if not api_key:
                st.error("Enter your Groq API Key in the sidebar.")
            else:
                results  = []
                progress = st.progress(0, text="Starting analysis…")
                for i, entry in enumerate(jd_entries):
                    progress.progress(i / 3, text=f"Analysing Job {i+1} — {entry['title']}…")
                    raw = call_groq(COMPARE_ANALYSIS_PROMPT.format(
                        resume=st.session_state.resume_text,
                        jd=entry["text"]
                    ))
                    try:
                        clean    = re.sub(r"```json|```", "", raw).strip()
                        analysis = json.loads(clean)
                        results.append({
                            "error":           False,
                            "title":           entry["title"],
                            "company":         entry["company"],
                            "text":            entry["text"],
                            "score":           analysis.get("overall_score", 0),
                            "missing_skills":  analysis.get("missing_skills", []),
                            "existing_skills": analysis.get("existing_skills", []),
                        })
                    except Exception:
                        results.append({
                            "error":           True,
                            "title":           entry["title"],
                            "company":         entry["company"],
                            "text":            entry["text"],
                            "score":           0,
                            "missing_skills":  [],
                            "existing_skills": [],
                        })
                progress.progress(1.0, text="All 3 jobs analysed!")
                st.session_state.compare_results        = results
                st.session_state.compare_confirmed      = {i: [] for i in range(3)}
                st.session_state.compare_updated_scores = {i: r["score"] for i, r in enumerate(results)}
                st.session_state.ai_recommendation      = None
                st.rerun()

# ── Compare Results ──
if st.session_state.compare_mode and st.session_state.compare_results:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="sec-label">Comparison Results</div>', unsafe_allow_html=True)
    st.markdown('<div class="sec-title">Your Match Across 3 Jobs</div>', unsafe_allow_html=True)
    st.markdown("<p style='color:#666;font-size:0.87rem;margin:0.5rem 0 1.5rem;line-height:1.65'>Tick any skills you genuinely have but didn't mention in your resume. Then click <b>Find My Best Match</b> — AI will pick the best one.</p>", unsafe_allow_html=True)

    results  = st.session_state.compare_results
    winner_i = st.session_state.ai_recommendation.get("winner_index") if st.session_state.ai_recommendation else None
    card_cols = st.columns(3, gap="medium")

    for i, (col, res) in enumerate(zip(card_cols, results)):
        with col:
            u_score   = st.session_state.compare_updated_scores.get(i, res["score"])
            is_winner = (winner_i == i)
            color     = score_color(u_score)

            if res.get("error"):
                st.error(f"Job {i+1}: Could not analyse. Check your JD text.")
                continue

            # Winner badge
            if is_winner:
                st.markdown("<div style='background:#1a6b3c;color:#fff;text-align:center;font-size:0.72rem;font-weight:700;letter-spacing:1.5px;padding:6px 0;border-radius:8px 8px 0 0;margin-bottom:-4px'>🏆 BEST MATCH</div>", unsafe_allow_html=True)

            # Card border color
            border = "2px solid #1a6b3c" if is_winner else "1.5px solid #e8e8e4"
            shadow = "0 4px 20px rgba(26,107,60,0.12)" if is_winner else "0 2px 8px rgba(0,0,0,0.04)"

            # Render full self-contained card in one markdown call
            st.markdown(f"""
<div style='background:#fff;border:{border};border-radius:12px;padding:1.2rem 1.3rem;box-shadow:{shadow}'>
  <div style='font-family:Playfair Display,serif;font-size:1.05rem;font-weight:700;color:#0a0a0a;margin-bottom:2px'>{res['title']}</div>
  <div style='font-size:0.8rem;color:#888;margin-bottom:0.8rem'>{res['company']}</div>
  <div style='font-family:Playfair Display,serif;font-size:2.8rem;font-weight:900;color:{color};line-height:1'>{u_score}<span style='font-size:1.3rem'>%</span></div>
  <div style='font-size:0.62rem;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:#aaa;margin-bottom:0.4rem'>ATS Match</div>
</div>
""", unsafe_allow_html=True)

            # Progress bar outside card
            st.markdown(f"<div style='background:#eeede9;border-radius:50px;height:7px;overflow:hidden;margin:6px 0 4px'><div style='height:100%;width:{min(u_score,100)}%;background:{color};border-radius:50px'></div></div>", unsafe_allow_html=True)

            # Missing skills checkboxes
            missing = res.get("missing_skills", [])
            if missing:
                st.markdown("<div style='font-size:0.72rem;font-weight:700;color:#888;margin:0.8rem 0 0.3rem;text-transform:uppercase;letter-spacing:1px'>Missing Skills</div>", unsafe_allow_html=True)
                confirmed_now = []
                for j, skill in enumerate(missing):
                    already = skill in st.session_state.compare_confirmed.get(i, [])
                    if st.checkbox(skill, value=already, key=f"cmp_{i}_{j}"):
                        confirmed_now.append(skill)
                st.session_state.compare_confirmed[i] = confirmed_now

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Find Best Match ──
    if st.button("🤖 Find My Best Match", use_container_width=True):
        if not api_key:
            st.error("Enter your Groq API Key in the sidebar.")
        else:
            # Recalculate scores with confirmed skills
            for i, res in enumerate(results):
                if not res.get("error"):
                    base   = res["score"]
                    bonus  = len(st.session_state.compare_confirmed.get(i, [])) * 6
                    st.session_state.compare_updated_scores[i] = min(base + bonus, 100)

            # Build comparison summary for AI
            comparisons = []
            for i, res in enumerate(results):
                if not res.get("error"):
                    comparisons.append({
                        "index": i,
                        "job_title": res["title"],
                        "company": res["company"],
                        "score": st.session_state.compare_updated_scores[i],
                        "existing_skills": res.get("existing_skills", []),
                        "confirmed_extra": st.session_state.compare_confirmed.get(i, []),
                        "still_missing": [s for s in res.get("missing_skills",[]) if s not in st.session_state.compare_confirmed.get(i,[])]
                    })

            with st.spinner("AI is picking your best match…"):
                raw = call_groq(RECOMMEND_PROMPT.format(
                    comparisons=json.dumps(comparisons, indent=2),
                    resume_summary=st.session_state.resume_text[:800]
                ))
                try:
                    clean = re.sub(r"```json|```", "", raw).strip()
                    st.session_state.ai_recommendation = json.loads(clean)
                    st.rerun()
                except Exception:
                    st.error("Could not get AI recommendation. Please try again.")

    # ── AI Recommendation Banner ──
    if st.session_state.ai_recommendation:
        rec = st.session_state.ai_recommendation
        wi  = rec.get("winner_index", 0)
        st.markdown(f"""
        <div class="ai-rec-banner fade-up">
            <div class="rec-eyebrow">AI Recommendation</div>
            <div class="rec-title">Apply to <span>{rec.get('job_title','')}</span> at {rec.get('company','')}</div>
            <div class="rec-reason">{rec.get('reason','')}</div>
        </div>
        """, unsafe_allow_html=True)

        # Proceed button — load the winning JD into main flow
        if not results[wi].get("error"):
            if st.button(f"🚀 Proceed with Job {wi+1} — {results[wi]['title']}", use_container_width=True):
                winning = results[wi]
                # Run full analysis on the winner
                with st.spinner("Running full analysis on the winning JD…"):
                    raw = call_groq(ANALYSIS_PROMPT.format(
                        resume=st.session_state.resume_text,
                        jd=winning["text"]
                    ))
                    try:
                        clean = re.sub(r"```json|```", "", raw).strip()
                        data  = json.loads(clean)
                        # Add confirmed skills from compare
                        confirmed_extra = st.session_state.compare_confirmed.get(wi, [])
                        bonus  = len(confirmed_extra) * 6
                        st.session_state.analysis         = data
                        st.session_state.score            = data.get("overall_score", 0)
                        st.session_state.radar_scores     = data.get("radar", {})
                        st.session_state.missing_skills   = data.get("missing_skills", [])
                        st.session_state.confirmed_skills = confirmed_extra
                        st.session_state.updated_score    = min(st.session_state.score + bonus, 100)
                        st.session_state.jd_text          = winning["text"]
                        st.session_state.tailored_data    = None
                        st.session_state.interview_questions = None
                        st.session_state.compare_mode          = False
                        st.session_state.proceeded_from_compare = True
                        st.session_state.step                  = 3
                        st.rerun()
                    except Exception:
                        st.error("Could not run full analysis. Please try again.")

# ══════════════════════════════════════════════
# STEP 3 — Score + Radar + Skill Gap (Single JD)
# ══════════════════════════════════════════════
if st.session_state.analysis and not st.session_state.compare_mode:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    score   = st.session_state.score
    u_score = st.session_state.updated_score

    c1, c2 = st.columns([1, 2], gap="large")
    with c1:
        color = score_color(u_score)
        st.markdown(f"""
        <div class="score-card fade-up">
            <div class="sec-label">ATS Match Score</div>
            <div class="score-num" style="color:{color}">{u_score}<span class="score-unit">%</span></div>
            <div class="score-lbl">Overall Match</div>
        </div>
        """, unsafe_allow_html=True)
        render_progress(u_score)
        st.markdown("<br>", unsafe_allow_html=True)
        if u_score >= 80:
            st.markdown('<div class="alert alert-green">🎉 <b>Above 80%!</b> Resume generation is unlocked below.</div>', unsafe_allow_html=True)
        else:
            needed = 80 - u_score
            st.markdown(f'<div class="alert alert-yellow">⚡ <b>{needed}% more needed.</b> Select hidden skills below, then click Recalculate.</div>', unsafe_allow_html=True)

    with c2:
        updated_radar = None
        if st.session_state.confirmed_skills:
            n = max(len(st.session_state.radar_scores), 1)
            updated_radar = {
                k: min(100, v + len(st.session_state.confirmed_skills) * 8 // n)
                for k, v in st.session_state.radar_scores.items()
            }
        st.plotly_chart(radar_chart(st.session_state.radar_scores, updated_radar),
                        use_container_width=True, config={"displayModeBar": False})

    # Skill gap
    if st.session_state.missing_skills and not st.session_state.tailored_data:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="sec-label">Step 03</div><div class="sec-title">Close the Skill Gap</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#666;font-size:0.87rem;margin:0.5rem 0 1.2rem;line-height:1.65'>Select all skills you genuinely have, then click <b>Recalculate Score</b>.</p>", unsafe_allow_html=True)

        skills   = st.session_state.missing_skills
        num_cols = min(4, len(skills))
        cols     = st.columns(num_cols)
        confirmed_now = []
        for i, skill in enumerate(skills):
            with cols[i % num_cols]:
                already = skill in st.session_state.confirmed_skills
                if st.checkbox(skill, value=already, key=f"sk_{i}"):
                    confirmed_now.append(skill)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄 Recalculate Score", use_container_width=True):
            bonus = len(confirmed_now) * 6
            new_s = min(score + bonus, 100)
            st.session_state.confirmed_skills = confirmed_now
            st.session_state.updated_score    = new_s
            st.rerun()

    elif st.session_state.tailored_data and st.session_state.confirmed_skills:
        st.markdown('<hr class="divider">', unsafe_allow_html=True)
        st.markdown('<div class="sec-label">Skills Added to Resume</div>', unsafe_allow_html=True)
        pills = "".join(f'<span class="skill-confirmed-pill">✓ {s}</span>' for s in st.session_state.confirmed_skills)
        st.markdown(f'<div class="skill-confirmed-wrap">{pills}</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# STEP 4 — Generate PDF
# ══════════════════════════════════════════════
if st.session_state.updated_score >= 80 and st.session_state.analysis and not st.session_state.compare_mode:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)

    if not st.session_state.tailored_data:
        st.markdown('<div class="sec-label">Step 04</div><div class="sec-title">Generate Your Resume</div>', unsafe_allow_html=True)
        st.markdown("<p style='color:#666;font-size:0.87rem;margin:0.5rem 0 1.2rem;line-height:1.65'>Your score qualifies for resume generation. We'll rewrite with the right keywords, structure, and impact bullets.</p>", unsafe_allow_html=True)

        if st.button("🚀 Generate Tailored Resume PDF", use_container_width=True):
            if not api_key:
                st.error("Enter your Groq API Key in the sidebar.")
            else:
                with st.spinner("Crafting your tailored resume — takes about 15 seconds…"):
                    extra = json.dumps(st.session_state.confirmed_skills)
                    raw   = call_groq(TAILORING_PROMPT.format(
                        analysis=json.dumps(st.session_state.analysis),
                        extra_skills=extra,
                        jd=st.session_state.jd_text
                    ))
                    if raw.startswith("API_ERROR"):
                        st.error(raw)
                    else:
                        try:
                            clean = re.sub(r"```json|```", "", raw).strip()
                            st.session_state.tailored_data = json.loads(clean)
                            st.session_state.step          = 4
                            st.rerun()
                        except Exception:
                            st.error("Could not parse tailored resume. Please try again.")

    if st.session_state.tailored_data:
        td = st.session_state.tailored_data
        st.markdown("""
        <div class="pdf-success-banner fade-up">
            <div class="big-check">✅</div>
            <h3>Your Resume is Ready</h3>
            <p>Tailored to this job &nbsp;·&nbsp; ATS-optimised &nbsp;·&nbsp; Professional B&W format &nbsp;·&nbsp; Ready to send</p>
        </div>
        """, unsafe_allow_html=True)

        with st.expander("👁 Preview Resume Before Downloading", expanded=False):
            st.markdown(f"## {td.get('name','')}")
            st.caption(td.get('contact',''))
            st.markdown("---")
            st.markdown("#### Professional Summary")
            st.write(td.get('summary',''))
            st.markdown("#### Core Skills")
            all_s = dedup_list(td.get('skills',[]) + td.get('extra_skills',[]))
            st.write("  ·  ".join(all_s))
            st.markdown("#### Experience")
            for exp in td.get('experience',[]):
                st.markdown(f"**{exp.get('title','')}** — {exp.get('company','')} _{exp.get('duration','')}_")
                for b in exp.get('bullets',[]): st.markdown(f"- {b}")
                st.markdown("")
            st.markdown("#### Education")
            for edu in td.get('education',[]):
                st.markdown(f"**{edu.get('degree','')}** — {edu.get('institution','')} ({edu.get('year','')})")

        pdf_bytes = generate_pdf(td)
        candidate = td.get('name','Resume').replace(' ','_')
        st.download_button(
            label="📥 Download PDF Resume",
            data=pdf_bytes,
            file_name=f"{candidate}_ATS_Resume.pdf",
            mime="application/pdf",
            use_container_width=True
        )
        st.markdown('<div class="alert alert-blue" style="margin-top:0.8rem">💡 <b>Pro tip:</b> Review the PDF before sending — verify contact details and personalise the summary if needed.</div>', unsafe_allow_html=True)

elif st.session_state.analysis and st.session_state.updated_score < 80 and not st.session_state.compare_mode:
    st.markdown('<div class="alert alert-grey" style="margin-top:1.5rem">🔒 <b>Resume generation locked.</b> Select hidden skills and click "Recalculate Score" to reach 80%.</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════
# STEP 5 — Interview Prep
# ══════════════════════════════════════════════
if st.session_state.tailored_data and not st.session_state.compare_mode:
    st.markdown('<hr class="divider">', unsafe_allow_html=True)
    st.markdown('<div class="sec-label">Step 05</div>', unsafe_allow_html=True)
    st.markdown('<div class="interview-section-header">Interview Prep Mode 🎤</div>', unsafe_allow_html=True)
    st.markdown('<div class="interview-sub">Targeted questions based on your resume and this specific JD — with frameworks on how to answer each one.</div>', unsafe_allow_html=True)

    if not st.session_state.interview_questions:
        if st.button("🎤 Generate My Interview Questions", use_container_width=True):
            if not api_key:
                st.error("Enter your Groq API Key in the sidebar.")
            else:
                with st.spinner("Generating targeted questions — takes about 10 seconds…"):
                    td     = st.session_state.tailored_data
                    skills = ", ".join(dedup_list(td.get('skills',[]) + td.get('extra_skills',[])))
                    raw    = call_groq(INTERVIEW_PROMPT.format(
                        summary=td.get('summary',''),
                        jd=st.session_state.jd_text,
                        skills=skills
                    ))
                    if raw.startswith("API_ERROR"):
                        st.error(raw)
                    else:
                        try:
                            clean = re.sub(r"```json|```", "", raw).strip()
                            st.session_state.interview_questions = json.loads(clean)
                            st.session_state.step = 5
                            st.rerun()
                        except Exception:
                            st.error("Could not parse interview questions. Please try again.")

    if st.session_state.interview_questions:
        questions = st.session_state.interview_questions.get("questions", [])
        cat_colors = {
            "Technical": "#1565c0", "Behavioural": "#6a1b9a",
            "Situational": "#c97b00", "Role-Specific": "#1a6b3c",
        }
        for q in questions:
            category  = q.get("category", "General")
            cat_color = next((c for k, c in cat_colors.items() if k.lower() in category.lower()), "#555")
            st.markdown(f"""
            <div class="interview-card fade-up">
                <div class="q-num" style="color:{cat_color}">Q{q.get('number','')} &nbsp;·&nbsp; {category}</div>
                <div class="q-text">{q.get('question','')}</div>
                <div class="q-framework">💬 <b>How to answer:</b> {q.get('framework','')}</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('<div class="alert alert-purple" style="margin-top:1rem">🎯 <b>Prep tip:</b> Use the STAR method (Situation, Task, Action, Result) for behavioural questions. Think out loud for technical ones — interviewers value your process as much as the answer.</div>', unsafe_allow_html=True)
