from dotenv import load_dotenv

load_dotenv()

import streamlit as st
import os
import io
import json
import re
import time
import textwrap
import plotly.graph_objects as go
from google import genai
from google.genai import types

# ── PDF rendering & text extraction: PyMuPDF ──────────────────────────────────
try:
    import pymupdf as fitz
    _PYMUPDF_AVAILABLE = True
except ImportError:
    _PYMUPDF_AVAILABLE = False

if not _PYMUPDF_AVAILABLE:
    import pdf2image
    from PIL import Image
    def _find_poppler_path():
        for p in ["/opt/homebrew/bin", "/usr/local/bin", "/usr/bin"]:
            if os.path.isfile(os.path.join(p, "pdftoppm")):
                return p
        return None
    _POPPLER_PATH = _find_poppler_path()

# ── Gemini client ──────────────────────────────────────────────────────────────
client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
MODEL = "gemini-2.5-flash"

# ── Custom CSS (Supports both Light & Dark Streamlit Themes) ───────────────────
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

* { font-family: 'Plus Jakarta Sans', sans-serif; }

/* Page Header */
.main-header {
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    color: #F8FAFC;
    padding: 24px 32px;
    border-radius: 16px;
    margin-bottom: 24px;
    border: 1px solid #334155;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.4);
}
.main-header h1 { color: #FFFFFF !important; font-weight: 800; margin: 0 0 6px 0; font-size: 2.1rem; }
.main-header p { color: #94A3B8; margin: 0; font-size: 0.95rem; }

/* Metric Cards */
.metric-card {
    background: #1E293B;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 20px 14px;
    text-align: center;
    box-shadow: 0 4px 12px rgba(0,0,0,0.25);
    transition: transform 0.2s ease;
}
.metric-card:hover {
    transform: translateY(-2px);
    border-color: #6366F1;
}
.metric-val { font-size: 2.2rem; font-weight: 800; line-height: 1.1; }
.metric-title { font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.8px; font-weight: 700; color: #94A3B8; margin-top: 8px; }

/* Status Colors */
.text-green { color: #10B981 !important; }
.text-yellow { color: #F59E0B !important; }
.text-red { color: #EF4444 !important; }

/* Section Cards */
.section-card {
    border-radius: 14px;
    padding: 18px 22px;
    margin-bottom: 16px;
    border-left: 6px solid;
    background: #1E293B;
    border-top: 1px solid #334155;
    border-right: 1px solid #334155;
    border-bottom: 1px solid #334155;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}
.card-green  { border-left-color: #10B981; }
.card-yellow { border-left-color: #F59E0B; }
.card-red    { border-left-color: #EF4444; }

.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.card-title  { font-size: 1.05rem; font-weight: 700; margin: 0; color: #F8FAFC; }
.card-badge  {
    font-size: 0.75rem; font-weight: 700; padding: 4px 12px;
    border-radius: 999px; letter-spacing: 0.4px;
}
.badge-green  { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.4); }
.badge-yellow { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.4); }
.badge-red    { background: rgba(239, 68, 68, 0.2); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.4); }

.card-feedback { font-size: 0.92rem; color: #CBD5E1; margin-top: 6px; }

/* Bullet Advice Container */
.bullet-card {
    background: #0F172A;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 12px;
}
.bullet-header { display: flex; gap: 10px; align-items: flex-start; }
.bullet-dot { font-size: 1.1rem; flex-shrink: 0; margin-top: 2px; }
.bullet-text-content { font-size: 0.92rem; color: #F8FAFC; line-height: 1.5; font-weight: 500; }

.bullet-advice {
    font-size: 0.85rem; color: #E2E8F0; margin-top: 10px;
    padding: 10px 14px; background: rgba(99, 102, 241, 0.15);
    border-radius: 8px; border-left: 4px solid #6366F1;
    line-height: 1.45;
}
.bullet-advice b { color: #818CF8; }

/* Keyword Pills */
.pills-wrap { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.pill {
    font-size: 0.8rem; font-weight: 600;
    padding: 6px 14px; border-radius: 999px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.pill-green  { background: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
.pill-red    { background: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }

/* Priority Actions Box */
.action-box {
    background: linear-gradient(135deg, #1E1B4B 0%, #312E81 100%);
    border: 1px solid #4338CA; border-radius: 14px;
    padding: 22px; margin-bottom: 24px;
    box-shadow: 0 6px 16px rgba(0,0,0,0.25);
}
.action-box h4 { margin: 0 0 16px; color: #A5B4FC; font-size: 1.05rem; font-weight: 700; }
.action-item {
    display: flex; align-items: flex-start; gap: 12px;
    font-size: 0.92rem; color: #EEF2FF; margin-bottom: 12px; font-weight: 500;
    line-height: 1.5;
}
.action-item strong, .action-item b { color: #F43F5E; }
.action-num {
    background: #6366F1; color: white;
    font-size: 0.75rem; font-weight: 800;
    width: 24px; height: 24px; border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0; margin-top: 1px;
}
</style>
"""


# ── PDF helpers ────────────────────────────────────────────────────────────────
def _pdf_bytes_from_upload(uploaded_file) -> bytes:
    """Read and return raw bytes, then reset stream pointer."""
    data = uploaded_file.read()
    uploaded_file.seek(0)
    return data


def pdf_to_images_bytes(uploaded_file) -> list[bytes]:
    """Render ALL pages of PDF to compressed JPEG bytes for Gemini multimodal vision."""
    pdf_bytes = _pdf_bytes_from_upload(uploaded_file)

    if _PYMUPDF_AVAILABLE:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        result = []
        mat = fitz.Matrix(1.5, 1.5)
        for page in doc:
            pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
            result.append(pix.tobytes("jpeg", jpg_quality=85))
        doc.close()
        return result

    kwargs = {"poppler_path": _POPPLER_PATH} if _POPPLER_PATH else {}
    images = pdf2image.convert_from_bytes(pdf_bytes, **kwargs)
    result = []
    for img in images:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        result.append(buf.getvalue())
    return result


def extract_resume_text(uploaded_file) -> str:
    """Extract plain text from all PDF pages."""
    pdf_bytes = _pdf_bytes_from_upload(uploaded_file)
    if not _PYMUPDF_AVAILABLE:
        return ""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages_text = []
    for i, page in enumerate(doc):
        text = page.get_text("text").strip()
        if text:
            pages_text.append(f"--- Page {i+1} ---\n{text}")
    doc.close()
    return "\n\n".join(pages_text)


# ── Resilient Gemini API Call with Exponential Backoff Retry & Caching ──────────
def _call_gemini_with_retry(contents: list, max_retries: int = 3) -> str:
    """Call Gemini API with exponential backoff retry to handle 503/429 overloaded errors."""
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=MODEL,
                contents=contents,
            )
            if response and response.text:
                return response.text
            raise ValueError("Empty response received from Gemini API.")
        except Exception as e:
            err_msg = str(e)
            if attempt < max_retries - 1 and any(
                keyword in err_msg.lower() for keyword in ["overloaded", "503", "429", "resource_exhausted", "unavailable", "rate limit"]
            ):
                sleep_time = (2 ** attempt) + 1
                time.sleep(sleep_time)
            else:
                raise e


@st.cache_data(show_spinner=False)
def get_unified_resume_analysis(pdf_bytes: bytes, job_description: str) -> dict:
    """
    Perform a SINGLE comprehensive AI evaluation of the resume against the job description.
    Cached by (pdf_bytes, job_description) hash to eliminate redundant API calls completely.
    """
    class BytesFileWrapper:
        def __init__(self, raw_bytes):
            self._bytes = raw_bytes
        def read(self):
            return self._bytes
        def seek(self, pos):
            pass

    fake_file = BytesFileWrapper(pdf_bytes)
    images_bytes = pdf_to_images_bytes(fake_file)
    resume_text = extract_resume_text(fake_file)

    image_parts = [types.Part.from_bytes(data=b, mime_type="image/jpeg") for b in images_bytes]

    text_parts = []
    if job_description.strip():
        text_parts.append(types.Part.from_text(text=f"JOB DESCRIPTION:\n{job_description.strip()}"))
    if resume_text:
        text_parts.append(types.Part.from_text(text=f"RESUME TEXT (EXTRACTED):\n{resume_text}"))

    prompt_instructions = """
You are an uncompromising, highly objective ATS Resume Auditor and Senior Technical Recruiter.
Your mandate is to perform an unbiased, fact-based analysis of the provided resume against the job description.

CRITICAL GUARDRAILS & ANTI-HALLUCINATION RULES:
1. STRICT FACTUAL GROUNDING:
   - Evaluate ONLY information explicitly written in the provided resume text and images.
   - DO NOT hallucinate, assume, or invent skills, degrees, job titles, or metrics that are not explicitly stated.
   - For `matched_keywords`, list ONLY terms that actually appear in BOTH the resume and the job description.
   - For `missing_keywords`, list key requirements from the JD that are demonstrably missing from the resume.

2. NO OVER-PRAISING OR FALSE FLATTERY:
   - Do NOT inflate scores or give false praise. Be strictly honest and realistic about the candidate's fit.
   - If a resume is weak, poorly formatted, lacks quantitative impact, or misses core JD requirements, PENALIZE THE SCORES ACCORDINGLY.
   - An unqualified or poorly matched resume MUST receive a low score (e.g., 20–45%) and a "Weak Alignment" verdict.
   - Mark bullets without metrics, tool names, or measurable results as "yellow" or "red" with constructive criticism.

3. SCORE CALCULATION RIGOR:
   - `overall_score`: Weighted by Keyword Match (40%), Role Alignment & Experience (30%), Impact & Metrics (20%), and Structure (10%).
   - `keyword_coverage_score`: Percentage of essential JD technical & domain keywords found in the resume.
   - `impact_rating`: Reflects the density of quantified metrics (%, $, numbers, outcomes) in bullet points.
   - `formatting_score`: Reflects clarity, section organization, and readability.

Return ONLY valid JSON matching this exact schema (no markdown fences, no leading/trailing text):

{
  "overall_score": <integer 0-100>,
  "keyword_coverage_score": <integer 0-100>,
  "impact_rating": <integer 0-100>,
  "formatting_score": <integer 0-100>,
  "top_3_actions": [
    "<action item 1>",
    "<action item 2>",
    "<action item 3>"
  ],
  "sections": [
    {
      "name": "<section name, e.g. Summary, Experience, Technical Skills, Education, Projects>",
      "score": <integer 0-100>,
      "status": "<green|yellow|red>",
      "feedback": "<objective, factual summary of section quality>",
      "bullets": [
        {
          "text": "<exact bullet text from resume, max 120 chars>",
          "status": "<green|yellow|red>",
          "issue": "<null if green, otherwise concise objective criticism max 120 chars>",
          "improved_bullet": "<a high-impact, ATS-optimized, action-verb driven rewrite of this bullet with metrics, ready to copy>"
        }
      ]
    }
  ],
  "matched_keywords": ["<matched keyword 1>", "<matched keyword 2>", ...],
  "missing_keywords": ["<missing keyword 1>", "<missing keyword 2>", ...],
  "hr_evaluation": {
    "verdict": "<Strong Fit | Potential Match | Weak Alignment>",
    "summary": "<2-3 sentence candid executive evaluation>",
    "strengths": ["<fact-based strength 1>", "<fact-based strength 2>", ...],
    "weaknesses": ["<candid weakness 1>", "<candid weakness 2>", ...]
  },
  "skills_roadmap": {
    "high_priority_skills": ["<critical missing JD skill 1>", "<critical missing JD skill 2>"],
    "medium_priority_skills": ["<secondary skill 1>", "<secondary skill 2>"],
    "recommended_courses_certifications": ["<course/cert 1>", "<course/cert 2>"]
  }
}

Rules:
- `status` MUST be "green" if score >= 75, "yellow" if 50-74, "red" if < 50.
- Return ONLY pure JSON!
"""
    text_parts.append(types.Part.from_text(text=prompt_instructions))

    contents = image_parts + text_parts
    raw_response = _call_gemini_with_retry(contents, max_retries=3)

    cleaned = re.sub(r"^```(?:json)?\s*", "", raw_response.strip(), flags=re.MULTILINE)
    cleaned = re.sub(r"```\s*$", "", cleaned.strip(), flags=re.MULTILINE)
    return json.loads(cleaned.strip())


# ── Charting Helpers (Plotly with Dark/High-Contrast Styling) ─────────────────
def create_donut_chart(matched_count: int, missing_count: int) -> go.Figure:
    """Create a sleek donut chart showing keyword match proportion with high-contrast text."""
    if matched_count + missing_count == 0:
        labels = ['No Keywords Detected']
        values = [1]
        colors = ['#475569']
    else:
        labels = ['Matched Keywords', 'Missing Keywords']
        values = [matched_count, missing_count]
        colors = ['#10B981', '#EF4444']

    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.68,
        marker=dict(colors=colors),
        textinfo='percent' if (matched_count + missing_count > 0) else 'label',
        hoverinfo='label+value',
        textfont=dict(size=13, family="Plus Jakarta Sans", color="#FFFFFF")
    )])

    fig.update_layout(
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.25,
            xanchor="center",
            x=0.5,
            font=dict(color="#E2E8F0", size=12, family="Plus Jakarta Sans")
        ),
        margin=dict(t=20, b=30, l=20, r=20),
        height=260,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def create_section_bar_chart(sections: list) -> go.Figure:
    """Create horizontal bar chart of section scores with crisp high-contrast axis text."""
    sec_names = [s.get("name", "Section") for s in sections]
    sec_scores = [s.get("score", 0) for s in sections]

    bar_colors = []
    for sc in sec_scores:
        if sc >= 75: bar_colors.append('#10B981')
        elif sc >= 50: bar_colors.append('#F59E0B')
        else: bar_colors.append('#EF4444')

    fig = go.Figure(go.Bar(
        x=sec_scores,
        y=sec_names,
        orientation='h',
        marker=dict(color=bar_colors, cornerradius=6),
        text=[f"{s}%" for s in sec_scores],
        textposition='auto',
        textfont=dict(family="Plus Jakarta Sans", color="#FFFFFF", size=12, weight=700)
    ))

    fig.update_layout(
        xaxis=dict(
            range=[0, 100],
            title=dict(text="Score %", font=dict(color="#CBD5E1", size=12, family="Plus Jakarta Sans")),
            gridcolor="#334155",
            tickfont=dict(color="#CBD5E1", size=11, family="Plus Jakarta Sans")
        ),
        yaxis=dict(
            autorange="reversed",
            tickfont=dict(color="#F8FAFC", size=12, weight=600, family="Plus Jakarta Sans")
        ),
        margin=dict(t=15, b=25, l=20, r=20),
        height=max(240, len(sections) * 45),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


def create_radar_chart(data: dict) -> go.Figure:
    """Create a radar chart for overall metrics breakdown with crisp white labels."""
    categories = ['Overall Match', 'Keyword Coverage', 'Impact & Action', 'Formatting']
    scores = [
        data.get("overall_score", 0),
        data.get("keyword_coverage_score", 0),
        data.get("impact_rating", 0),
        data.get("formatting_score", 0)
    ]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=scores + [scores[0]],
        theta=categories + [categories[0]],
        fill='toself',
        fillcolor='rgba(99, 102, 241, 0.3)',
        line=dict(color='#818CF8', width=3),
        marker=dict(size=7, color='#6366F1')
    ))

    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100],
                gridcolor="#334155",
                linecolor="#475569",
                tickfont=dict(color="#94A3B8", size=10, family="Plus Jakarta Sans")
            ),
            angularaxis=dict(
                tickfont=dict(size=12, color="#F8FAFC", weight=600, family="Plus Jakarta Sans"),
                linecolor="#475569"
            ),
            bgcolor="rgba(15, 23, 42, 0.4)"
        ),
        showlegend=False,
        margin=dict(t=30, b=30, l=45, r=45),
        height=270,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig


# ── UI Components ──────────────────────────────────────────────────────────────
def render_metrics_summary(data: dict):
    """Render top key metric cards."""
    col1, col2, col3, col4 = st.columns(4)

    metrics = [
        ("ATS Overall Match", data.get("overall_score", 0), col1),
        ("Keyword Coverage", data.get("keyword_coverage_score", 0), col2),
        ("Impact & Action", data.get("impact_rating", 0), col3),
        ("Formatting & Layout", data.get("formatting_score", 0), col4)
    ]

    for title, score, col in metrics:
        with col:
            cls = "text-green" if score >= 75 else ("text-yellow" if score >= 50 else "text-red")
            card_html = textwrap.dedent(f"""
            <div class="metric-card">
                <div class="metric-val {cls}">{score}%</div>
                <div class="metric-title">{title}</div>
            </div>
            """).strip()
            st.markdown(card_html, unsafe_allow_html=True)


def render_top_actions(actions: list):
    if not actions:
        return

    items_html = ""
    for i, a in enumerate(actions[:3]):
        formatted_action = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', a)
        items_html += f'<div class="action-item"><span class="action-num">{i+1}</span><div>{formatted_action}</div></div>'

    box_html = textwrap.dedent(f"""
    <div class="action-box">
        <h4>⚡ Top 3 Priority Action Items</h4>
        {items_html}
    </div>
    """).strip()
    st.markdown(box_html, unsafe_allow_html=True)


def render_section_cards(sections: list):
    def status_emoji(status: str) -> str:
        return {"green": "🟢", "yellow": "🟡", "red": "🔴"}.get(status, "⚪")

    for sec in sections:
        status = sec.get("status", "green")
        name   = sec.get("name", "Section")
        score  = sec.get("score", 0)
        fb     = sec.get("feedback", "")
        bullets = sec.get("bullets", [])

        badge_label = {"green": "✓ Strong", "yellow": "⚠ Needs Work", "red": "✗ Critical Gap"}.get(status, "")
        with st.expander(f"{status_emoji(status)} **{name}** — {score}/100 Score", expanded=(status in ["red", "yellow"])):
            card_header_html = textwrap.dedent(f"""
            <div class="section-card card-{status}">
                <div class="card-header">
                    <p class="card-title">{name}</p>
                    <span class="card-badge badge-{status}">{badge_label}</span>
                </div>
                <div class="card-feedback">{fb}</div>
            </div>
            """).strip()
            st.markdown(card_header_html, unsafe_allow_html=True)

            if bullets:
                st.markdown("**Pinpointed Bullet Feedback & Copyable Rewrites:**")
                for i, b in enumerate(bullets):
                    b_status = b.get("status", "green")
                    b_text   = b.get("text", "")
                    b_issue  = b.get("issue")
                    improved = b.get("improved_bullet") or b_text

                    st.markdown(f"**Bullet {i+1}:** {status_emoji(b_status)} {b_text}")
                    if b_issue and b_status != "green":
                        st.info(f"💡 **Recommendation:** {b_issue}")
                    
                    st.caption("✍️ Suggested High-Impact Rewrite (Click 📋 on right to copy):")
                    st.code(improved, language=None)
                    st.markdown("<br>", unsafe_allow_html=True)


def render_keyword_badges(matched: list, missing: list):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"##### Matched Keywords ({len(matched)})")
        if matched:
            pills = "".join(f'<span class="pill pill-green">{k}</span>' for k in matched)
            st.markdown(f'<div class="pills-wrap">{pills}</div>', unsafe_allow_html=True)
        else:
            st.caption("No matching keywords detected.")
    with col2:
        st.markdown(f"##### Missing Keywords ({len(missing)})")
        if missing:
            pills = "".join(f'<span class="pill pill-red">{k}</span>' for k in missing)
            st.markdown(f'<div class="pills-wrap">{pills}</div>', unsafe_allow_html=True)
        else:
            st.caption("No critical missing keywords! Excellent alignment.")


# ── Page Layout ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="ATS Resume Scanner & AI Coach",
    page_icon="📄",
    layout="wide",
)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>📄 ATS Resume Scanner & AI Coach</h1>
    <p>Upload your resume and job description to unlock pinpointed section advice, keyword statistics, and ATS scoring.</p>
</div>
""", unsafe_allow_html=True)

# Input Section
col_jd, col_pdf = st.columns([1, 1], gap="large")

with col_jd:
    st.subheader("📋 1. Target Job Description")
    input_text = st.text_area(
        "Paste the job description here:",
        height=240,
        placeholder="Paste the target role description, required qualifications, and skills…",
        key="input",
    )

with col_pdf:
    st.subheader("📁 2. Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload resume PDF:",
        type=["pdf"],
        help="Analyzes all pages of your PDF resume.",
    )
    if uploaded_file is not None:
        st.success("Resume PDF loaded!")
        pages = pdf_to_images_bytes(uploaded_file)
        uploaded_file.seek(0)
        if pages:
            with st.expander("Preview Resume Page 1"):
                st.image(pages[0], use_container_width=True)
    else:
        st.info("⬆️ Upload your PDF resume to begin.")

st.divider()

# Action Button
analyze_button = st.button("🚀 Run Full AI Resume Audit", type="primary", use_container_width=True)

if analyze_button:
    if uploaded_file is None:
        st.warning("Please upload your PDF resume first.")
    elif not input_text.strip():
        st.warning("Please paste a job description first.")
    else:
        with st.spinner("Running intelligent multimodal resume audit with Gemini..."):
            try:
                pdf_bytes = _pdf_bytes_from_upload(uploaded_file)
                st.session_state["analysis_data"] = get_unified_resume_analysis(pdf_bytes, input_text.strip())
                st.success("Audit Complete!")
            except Exception as e:
                st.error(f"Error during analysis: {e}")

# Display Analysis if Available in Session State
if "analysis_data" in st.session_state:
    data = st.session_state["analysis_data"]

    st.markdown("### Executive Summary & Key Metrics")
    render_metrics_summary(data)
    st.markdown("<br>", unsafe_allow_html=True)

    # Tabs for detailed breakdown
    tab_overview, tab_coach, tab_keywords, tab_hr, tab_skills = st.tabs([
        "📈 Audit Overview",
        "🎯 Section & Bullet Coach",
        "🔑 Keyword Analytics",
        "🔍 Recruiter Review",
        "💡 Skills Roadmap"
    ])

    # ── Tab 1: Audit Overview ──────────────────────────────────────────────────
    with tab_overview:
        col_left, col_right = st.columns([1, 1], gap="large")

        with col_left:
            st.markdown("##### ATS Category Performance Radar")
            st.plotly_chart(create_radar_chart(data), use_container_width=True)

            render_top_actions(data.get("top_3_actions", []))

        with col_right:
            st.markdown("##### Section Score Breakdown")
            st.plotly_chart(create_section_bar_chart(data.get("sections", [])), use_container_width=True)

            matched_cnt = len(data.get("matched_keywords", []))
            missing_cnt = len(data.get("missing_keywords", []))
            st.markdown("##### Keyword Match Ratio")
            st.plotly_chart(create_donut_chart(matched_cnt, missing_cnt), use_container_width=True)

    # ── Tab 2: Section & Bullet Coach ──────────────────────────────────────────
    with tab_coach:
        st.markdown("#### Pinpointed Resume Section Breakdown")
        st.caption("Review color-coded feedback and specific bullet recommendations to maximize impact.")
        render_section_cards(data.get("sections", []))

    # ── Tab 3: Keyword Analytics ───────────────────────────────────────────────
    with tab_keywords:
        st.markdown("#### Keyword Alignment & Coverage")
        st.caption("ATS algorithms score your resume by scanning for exact match keywords from the Job Description.")
        render_keyword_badges(data.get("matched_keywords", []), data.get("missing_keywords", []))

    # ── Tab 4: Recruiter Review ────────────────────────────────────────────────
    with tab_hr:
        hr_eval = data.get("hr_evaluation", {})
        verdict = hr_eval.get("verdict", "N/A")

        st.markdown(f"#### Senior Recruiter Evaluation: **{verdict}**")
        st.info(hr_eval.get("summary", "No summary available."))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### Key Candidate Strengths")
            for s in hr_eval.get("strengths", []):
                st.markdown(f"- {s}")

        with c2:
            st.markdown("##### Key Gaps & Concerns")
            for w in hr_eval.get("weaknesses", []):
                st.markdown(f"- {w}")

    # ── Tab 5: Skills Roadmap ──────────────────────────────────────────────────
    with tab_skills:
        roadmap = data.get("skills_roadmap", {})
        st.markdown("#### Targeted Skills & Certification Roadmap")

        sc1, sc2 = st.columns(2)
        with sc1:
            st.markdown("##### High Priority Skills to Acquire/Feature")
            for sk in roadmap.get("high_priority_skills", []):
                st.markdown(f"- **{sk}**")

            st.markdown("##### Medium Priority Skills")
            for sk in roadmap.get("medium_priority_skills", []):
                st.markdown(f"- {sk}")

        with sc2:
            st.markdown("##### Recommended Certifications & Courses")
            for cert in roadmap.get("recommended_courses_certifications", []):
                st.markdown(f"- {cert}")