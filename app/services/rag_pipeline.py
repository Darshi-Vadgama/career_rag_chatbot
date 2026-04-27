# app/services/rag_pipeline.py
# Small + Clean + Better Real Scores

from app.services.qdrant_service import search_docs
from app.services.llm_service import ask_llm
from app.utils.logger import logger

REC = ["marks","score","percentage","career","after 10th","after 12th"]
SAL = ["salary","pay","income"]
SKL = ["skill","skills"]
EXP = ["experience","year","years"]

# =====================================================
async def run_rag(question:str):

    q = question.lower().strip()
    logger.info(f"Query: {question}")

    docs = search_docs(question, limit=3)
    best = docs[0].payload if docs else {}

    c = career(q, best)
    d = domain(c, best)

    if any(x in q for x in REC):
        return await llm(rec_prompt(question), src(stream(q)))

    if any(x in q for x in SAL):
        return await llm(base(question,c,d,"Salary"), c)

    if any(x in q for x in SKL):
        return await llm(base(question,c,d,"Skills Required"), c)

    if any(x in q for x in EXP):
        return await llm(base(question,c,d,"Experience Required"), c)

    return await llm(overview(question,c,d,docs), c)

# =====================================================
async def llm(prompt, source):
    return {
        "answer": await ask_llm(prompt),
        "sources": source if isinstance(source,list) else [source]
    }

# =====================================================
def rec_prompt(q):
    return f"""
User Query:{q}

Career Name: Best Career Suggestions
Specific Field: Recommendation
Domain: Education / Career Planning

Recommended Careers:
• Option 1
• Option 2
• Option 3
• Option 4
• Option 5

Reason:
(3 lines)

Next Steps:
• Step 1
• Step 2
• Step 3

No markdown.
"""

# =====================================================
def base(q,c,d,f):
    return f"""
User Query:{q}

Answer only for {c}

Career Name:{c}
Specific Field:{f}
Domain:{d}

Use bullet points.
No markdown.
"""

# =====================================================
def overview(q,c,d,docs):

    ctx = "\n".join(
        f"Career:{val(x.payload,'career')} "
        f"Description:{val(x.payload,'description')}"
        for x in docs
    )

    return f"""
User Query:{q}

Answer only about {c}

Career Name:{c}
Specific Field:Career Overview
Domain:{d}

Overview:
(3 lines)

Skills:
• Skill 1
• Skill 2
• Skill 3
• Skill 4

Education:
(short)

Experience:
(short)

Career Path:
• Entry
• Mid
• Senior

Context:
{ctx}

No markdown.
"""

# =====================================================
def stream(q):

    if any(x in q for x in ["science","biology","pcm","pcb"]):
        return "Science"

    if any(x in q for x in ["accounts","commerce","finance"]):
        return "Commerce"

    if any(x in q for x in ["arts","history","psychology"]):
        return "Arts"

    return "General"

# =====================================================
def src(s):
    data = {
        "Science":["Doctor","Engineer","Pharmacist","Data Scientist"],
        "Commerce":["CA","CMA","Accountant","MBA Finance"],
        "Arts":["Lawyer","Journalism","Designer","UPSC"],
        "General":["Software Engineer","Business","Gov Jobs"]
    }
    return data.get(s,data["General"])

# =====================================================
def career(q,b):

    mp = {
        "doctor":"Doctor",
        "medical":"Doctor",

        "teacher":"Teacher",
        "education":"Teacher",

        "lawyer":"Lawyer",
        "legal":"Lawyer",
        "advocate":"Lawyer",

        "engineer":"Engineer",
        "software":"Software Engineer",
        "developer":"Software Engineer",

        "data":"Data Scientist",
        "analytics":"Data Scientist",

        "account":"Accountant",
        "commerce":"Accountant",
        "finance":"Accountant"
    }

    for k,v in mp.items():
        if k in q:
            return v

    return val(b,"career") or "Professional"

# =====================================================
def domain(c,b):

    x = c.lower()

    if "doctor" in x:
        return "Healthcare"
    if "teacher" in x:
        return "Education"
    if "lawyer" in x:
        return "Legal"
    if "engineer" in x or "software" in x:
        return "Technology"
    if "data" in x:
        return "IT / Analytics"
    if "account" in x:
        return "Commerce / Finance"

    return val(b,"domain") or "Professional"

# =====================================================
def val(p,k):
    x = str(p.get(k,"")).strip()
    return "" if x.lower() in ["nan","none","null"] else x