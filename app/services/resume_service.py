# app/services/resume_service.py
# FINAL RESUME SCANNER WITH LLM (Mistral Cloud)

from app.services.llm_service import ask_llm
import io
from PyPDF2 import PdfReader

# =====================================================
# MAIN
# =====================================================
async def scan_resume(text="", file=None):

    content = await extract_content(text, file)

    if not content.strip():
        return {
            "career_matches":["No resume content found"],
            "skills_found":[],
            "missing_skills":[],
            "suggestions":["Upload valid resume file"],
            "summary":"No content detected."
        }

    prompt = f"""
You are an expert ATS Resume Analyzer and Career Coach.

Analyze this resume content:

{content}

Return ONLY clean plain text in this exact format:

Best Career Matches:
• career 1
• career 2
• career 3

Skills Found:
• skill 1
• skill 2

Missing Skills:
• skill 1
• skill 2

Suggestions:
• suggestion 1
• suggestion 2
• suggestion 3

Summary:
2-3 lines summary

Rules:
- No markdown
- No ** symbols
- No ###
- Clear professional answer
"""

    ans = await ask_llm(prompt)

    return parse_output(ans)

# =====================================================
# EXTRACT TEXT
# =====================================================
async def extract_content(text,file):

    content = text + " " if text else ""

    if not file:
        return content

    name = file.filename.lower()

    # PDF
    if name.endswith(".pdf"):
        try:
            pdf = PdfReader(io.BytesIO(await file.read()))
            for p in pdf.pages:
                tx = p.extract_text()
                if tx:
                    content += tx + " "
        except:
            pass

    # TXT
    elif name.endswith(".txt"):
        try:
            content += (await file.read()).decode("utf-8")
        except:
            pass

    # DOCX fallback
    elif name.endswith(".docx"):
        content += "resume uploaded"

    return content

# =====================================================
# PARSE OUTPUT
# =====================================================
def parse_output(ans):

    lines = [x.strip() for x in ans.splitlines() if x.strip()]

    sec = {
        "career_matches":[],
        "skills_found":[],
        "missing_skills":[],
        "suggestions":[],
        "summary":""
    }

    mode = ""

    for line in lines:

        low = line.lower()

        if "best career matches" in low:
            mode="career"; continue

        if "skills found" in low:
            mode="skills"; continue

        if "missing skills" in low:
            mode="missing"; continue

        if "suggestions" in low:
            mode="suggest"; continue

        if "summary" in low:
            mode="summary"; continue

        item = line.replace("•","").strip()

        if mode=="career":
            sec["career_matches"].append(item)

        elif mode=="skills":
            sec["skills_found"].append(item)

        elif mode=="missing":
            sec["missing_skills"].append(item)

        elif mode=="suggest":
            sec["suggestions"].append(item)

        elif mode=="summary":
            sec["summary"] += item + " "

    # fallback
    if not sec["career_matches"]:
        sec["career_matches"]=["Software Engineer"]

    if not sec["suggestions"]:
        sec["suggestions"]=[
            "Add projects",
            "Add certifications",
            "Improve ATS keywords"
        ]

    return sec