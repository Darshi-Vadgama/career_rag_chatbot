# app/services/rag_pipeline.py
# FINAL FULL UPDATED VERSION
# All intents + improved Commerce recommendation sources

from app.services.qdrant_service import search_docs
from app.services.llm_service import ask_llm
from app.utils.logger import logger


# =====================================================
# MAIN ENTRY
# =====================================================
async def run_rag(question: str):

    q = question.lower().strip()
    logger.info(f"Query: {question}")

    docs = search_docs(question, limit=5)
    best = docs[0].payload if docs else {}

    career = detect_career(q, best)
    domain = detect_domain(career, best)

    # -------------------------------------------------
    # Recommendation Intent
    # -------------------------------------------------
    if is_recommendation_query(q):
        return await recommendation_intent(question)

    # -------------------------------------------------
    # Salary Intent
    # -------------------------------------------------
    if any(x in q for x in ["salary", "pay", "income"]):
        return await salary_intent(question, career, domain)

    # -------------------------------------------------
    # Skills Intent
    # -------------------------------------------------
    if "skill" in q:
        return await skills_intent(question, career, domain)

    # -------------------------------------------------
    # Experience Intent
    # -------------------------------------------------
    if any(x in q for x in ["experience", "years", "year"]):
        return await experience_intent(question, career, domain)

    # -------------------------------------------------
    # Default Overview
    # -------------------------------------------------
    return await overview_intent(question, career, domain, docs)


# =====================================================
# RECOMMENDATION QUERY DETECTOR
# =====================================================
def is_recommendation_query(q):

    keys = [
        "marks", "score", "percentage",
        "which career", "what career",
        "career choose", "choose career",
        "after 10th", "after 12th",
        "best career", "which field",
        "what should i do"
    ]

    return any(k in q for k in keys)


# =====================================================
# RECOMMENDATION INTENT
# =====================================================
async def recommendation_intent(question):

    q = question.lower()
    stream = detect_stream(q)

    prompt = f"""
User Query:
{question}

Detected Stream:
{stream}

Give smart balanced career guidance.

Format:

Career Name: Best Career Suggestions
Specific Field: Recommendation
Domain: Education / Career Planning

Recommended Careers:
• option 1
• option 2
• option 3
• option 4
• option 5

Reason:
(3 lines personalized based on marks + stream)

Next Steps:
• point 1
• point 2
• point 3

Rules:
- Give diverse options
- Include traditional + modern careers
- If marks high include premium options
- No markdown
"""

    ans = await ask_llm(prompt)

    return {
        "answer": ans,
        "sources": recommendation_sources(stream)
    }


# =====================================================
# STREAM DETECTION
# =====================================================
def detect_stream(q):

    if any(x in q for x in [
        "science", "physics", "chemistry",
        "biology", "maths", "pcm", "pcb"
    ]):
        return "Science"

    if any(x in q for x in [
        "accounts", "commerce", "business",
        "economics", "finance"
    ]):
        return "Commerce"

    if any(x in q for x in [
        "arts", "history", "psychology",
        "literature", "political"
    ]):
        return "Arts"

    return "General"


# =====================================================
# SOURCES
# =====================================================
def recommendation_sources(stream):

    if stream == "Science":
        return [
            "Engineering",
            "Doctor",
            "Pharmacy",
            "Data Scientist",
            "Architecture"
        ]

    if stream == "Commerce":
        return [
            "CA",
            "CMA",
            "BCom",
            "MBA Finance",
            "Banking",
            "Stock Market"
        ]

    if stream == "Arts":
        return [
            "Lawyer",
            "Journalism",
            "Designer",
            "Psychologist",
            "UPSC"
        ]

    return [
        "Software Engineer",
        "Entrepreneur",
        "Digital Marketing",
        "Government Jobs",
        "Business Management"
    ]


# =====================================================
# OVERVIEW INTENT
# =====================================================
async def overview_intent(question, career, domain, docs):

    ctx = build_context(docs)

    prompt = f"""
User Query:
{question}

Career:
{career}

Domain:
{domain}

Use context first else own knowledge.

Format:

Career Name: {career}
Specific Field: Career Overview
Domain: {domain}

Overview:
(4 lines)

Skills:
• point
• point
• point
• point

Education:
(clean)

Experience:
(clean)

Career Path:
• Entry Level
• Mid Level
• Senior Level

No markdown.

Context:
{ctx}
"""

    ans = await ask_llm(prompt)

    return {
        "answer": ans,
        "sources": [career]
    }


# =====================================================
# SALARY INTENT
# =====================================================
async def salary_intent(question, career, domain):

    country = detect_country(question)

    prompt = f"""
User Query:
{question}

Career:
{career}

Country:
{country}

Format:

Career Name: {career}
Specific Field: Salary
Domain: {domain}

Location: {country}

Monthly Salary:
(realistic range)

Yearly Salary:
(realistic range)

Factors Affecting Salary:
• point
• point
• point

No markdown.
"""

    ans = await ask_llm(prompt)

    return {
        "answer": ans,
        "sources": [career]
    }


# =====================================================
# SKILLS INTENT
# =====================================================
async def skills_intent(question, career, domain):

    prompt = f"""
User Query:
{question}

Career:
{career}

Format:

Career Name: {career}
Specific Field: Skills Required
Domain: {domain}

Skills:
• point
• point
• point
• point
• point
• point

Extra Advice:
(one line)

No markdown.
"""

    ans = await ask_llm(prompt)

    return {
        "answer": ans,
        "sources": [career]
    }


# =====================================================
# EXPERIENCE INTENT
# =====================================================
async def experience_intent(question, career, domain):

    prompt = f"""
User Query:
{question}

Career:
{career}

Format:

Career Name: {career}
Specific Field: Experience Required
Domain: {domain}

Required Experience:
• Fresher:
• Mid Level:
• Senior:

Typical Journey:
• point
• point
• point

No markdown.
"""

    ans = await ask_llm(prompt)

    return {
        "answer": ans,
        "sources": [career]
    }


# =====================================================
# HELPERS
# =====================================================
def detect_career(q, best):

    if "doctor" in q:
        return "Doctor"

    if "teacher" in q:
        return "Teacher"

    if "data science" in q or "data scientist" in q:
        return "Data Scientist"

    if "software" in q or "developer" in q:
        return "Software Engineer"

    if "account" in q or "commerce" in q:
        return "Commerce Professional"

    x = val(best, "career")
    return x if x else "Professional"


def detect_domain(career, best):

    c = career.lower()

    if "doctor" in c:
        return "Healthcare"

    if "teacher" in c:
        return "Education"

    if "data" in c:
        return "IT / Analytics"

    if "software" in c:
        return "IT"

    if "commerce" in c or "account" in c:
        return "Commerce / Finance"

    x = val(best, "domain")
    return x if x else "Professional"


def detect_country(q):

    x = q.lower()

    if "india" in x:
        return "India"

    if "usa" in x or "us" in x:
        return "USA"

    if "uk" in x:
        return "UK"

    return "India"


def build_context(docs):

    arr = []

    for d in docs:

        p = d.payload

        arr.append(f"""
Career: {val(p,'career')}
Description: {val(p,'description')}
Skills: {val(p,'skills')}
Salary: {val(p,'salary')}
Education: {val(p,'education')}
Experience: {val(p,'experience')}
Domain: {val(p,'domain')}
Career Path: {val(p,'career_path')}
""")

    return "\n".join(arr)


def val(p, key):

    x = str(p.get(key, "")).strip()

    if x.lower() in ["nan", "none", "null"]:
        return ""

    return x