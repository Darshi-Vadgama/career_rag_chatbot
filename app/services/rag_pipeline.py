from app.services.qdrant_service import search_docs
from app.services.llm_service import ask_llm
from app.utils.logger import logger

REC = ["marks","score","percentage","career","after 10th","after 12th"]

SRC = {
    "Science":["Engineering","Doctor","Pharmacy","Data Scientist"],
    "Commerce":["CA","CMA","BCom","MBA Finance","Banking"],
    "Arts":["Lawyer","Journalism","Designer","UPSC"],
    "General":["Software Engineer","Business","Government Jobs"]
}

# =====================================================
async def run_rag(question:str):

    q = question.lower()
    logger.info(f"Query: {question}")

    docs = search_docs(question, limit=5)
    best = docs[0].payload if docs else {}

    c = career(q, best)
    d = domain(c, best)

    if any(x in q for x in REC):
        return await llm(rec_prompt(question), source(stream(q)))

    if "salary" in q or "pay" in q:
        return await llm(base(question,c,d,"Salary"))

    if "skill" in q:
        return await llm(base(question,c,d,"Skills Required"))

    if "experience" in q or "year" in q:
        return await llm(base(question,c,d,"Experience Required"))

    return await llm(overview(question,c,d,docs))


# =====================================================
async def llm(prompt, src="Professional"):
    return {
        "answer": await ask_llm(prompt),
        "sources": src if isinstance(src,list) else [src]
    }


# =====================================================
def rec_prompt(q):
    return f"""
User Query:{q}

Career Name: Best Career Suggestions
Specific Field: Recommendation
Domain: Education / Career Planning

Recommended Careers:
• option1
• option2
• option3
• option4
• option5

Reason:
(3 lines)

Next Steps:
• point1
• point2
• point3
"""


def base(q,c,d,f):
    return f"""
User Query:{q}

Career Name:{c}
Specific Field:{f}
Domain:{d}

Give clear bullet answer.
"""


def overview(q,c,d,docs):

    ctx = "\n".join(
        f"Career:{val(x.payload,'career')} "
        f"Description:{val(x.payload,'description')}"
        for x in docs
    )

    return f"""
User Query:{q}

Career Name:{c}
Specific Field:Career Overview
Domain:{d}

Overview:
(4 lines)

Skills:
• point
• point
• point

Education:
Experience:

Context:
{ctx}
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


def source(s):
    return SRC.get(s,SRC["General"])


def career(q,b):

    mp = {
        "doctor":"Doctor",
        "teacher":"Teacher",
        "data":"Data Scientist",
        "software":"Software Engineer",
        "developer":"Software Engineer",
        "account":"Commerce Professional",
        "commerce":"Commerce Professional"
    }

    for k,v in mp.items():
        if k in q:
            return v

    return val(b,"career") or "Professional"


def domain(c,b):

    c = c.lower()

    if "doctor" in c: return "Healthcare"
    if "teacher" in c: return "Education"
    if "data" in c: return "IT / Analytics"
    if "software" in c: return "IT"
    if "commerce" in c or "account" in c:
        return "Commerce / Finance"

    return val(b,"domain") or "Professional"


def val(p,k):
    x = str(p.get(k,"")).strip()
    return "" if x.lower() in ["nan","none","null"] else x