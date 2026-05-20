# app/services/rag_pipeline.py

import re
from app.services.qdrant_service import search_docs
from app.services.llm_service import ask_llm_stream
from app.services.redis_service import (
    get_cache, set_cache, save_memory, get_last_n_messages,
)

# ── Static responses ──────────────────────────────────────────────────────────

REJECTION_MESSAGE = (
    "I'm a career counseling assistant and can only help with career-related questions. "
    "Please ask me about careers, jobs, skills, salaries, roadmaps, courses, or professional development!"
)

GREETING_MESSAGE = (
    "Hello! 👋 I'm your **Career AI** assistant. I can help you with:\n\n"
    "- 🎯 **Career guidance** — explore any profession in depth\n"
    "- 📄 **Resume scanning** — upload your resume for expert feedback\n"
    "- 🧭 **Career roadmaps** — step-by-step paths to your dream career\n"
    "- 💰 **Salary insights** — realistic INR salary ranges by experience\n"
    "- 📚 **Skill advice** — what to learn and how to grow\n\n"
    "Try asking: *'How do I become a Data Scientist?'* or *'What is the scope of Civil Engineering?'*"
)

RULE = """
STRICT RULES:
- Conclusion must be maximum 3 lines only.
- Do NOT repeat the conclusion anywhere else.
- Do NOT repeat suggestions.
- Do NOT cut the answer short — complete every section fully.
- Stop ONLY after the Conclusion section.
"""

FOLLOWUP_PROMPT = """
You are an expert career counselor AI with 20+ years of experience.

Chat History:
{history}

User's Follow-up Question:
{question}

STRICT INSTRUCTIONS:
- Only answer career-related follow-up questions.
- If NOT career-related, respond ONLY: "I'm a career counseling assistant. I can only answer career-related questions!"
- Directly address what the user is asking based on the chat history.
- If correcting a fact (e.g. "isn't MBBS 5 years?"), acknowledge it and give accurate info.
- Do NOT repeat the full career template again.
- Give a focused, conversational, accurate answer in 3-6 paragraphs.
- Use Indian context where relevant (MBBS in India = 5.5 years including internship).
"""

MASTER_PROMPT = """
You are an expert career counselor AI with 20+ years of experience in career guidance,
industry knowledge, and professional development across India and globally.

User Question:
{question}

{context_block}

CRITICAL — TOPIC FOCUS:
- Answer ONLY about the exact career in the question above.
- Do NOT mix in other careers or specialties.

IMPORTANT FACTS:
- MBBS India = 4.5 years study + 1 year internship = 5.5 years total
- MS General Surgery = 3 years after MBBS
- MCh Neurosurgery = 3 years after MS
- Total to become Neurosurgeon ≈ 14 years after 12th
- NEET UG = MBBS entrance after 12th
- NEET PG = MD/MS entrance after MBBS
- NEET SS = MCh/DM entrance after MS/MD
- BTech=4yr, MBA=2yr, LLB=3yr after graduation, CA≈5yr

Write a THOROUGH, DETAILED, PROFESSIONAL response using EXACTLY this structure:

# Overview
4-6 lines: what the career is, day-to-day work, industry, work environment.

# Skills Required
6-8 skills. Each skill: 3-4 lines on what it is, why important, how to develop.

# Salary in India
- Fresher (0-2 yrs):     ₹X LPA – ₹X LPA
- Mid-Level (2-5 yrs):   ₹X LPA – ₹X LPA
- Senior (5-10 yrs):     ₹X LPA – ₹X LPA
- Experienced (10+ yrs): ₹X LPA+
Mention top cities and govt vs private salary differences.

# Career Roadmap
4 detailed phases with exact year ranges, exam names, degree names, durations.

# Future Scope
5-6 lines: evolution, AI/tech impact, new opportunities, demand forecast.

# Additional Suggestions
5-6 actionable items: certifications, tools, networking, portfolio, books.

# Conclusion
{rule}
Exactly 3 lines: why good career, key to success, one motivational line.
"""

# ── Classifiers ───────────────────────────────────────────────────────────────

GREETING_EXACT = {
    "hello","hi","hey","hii","helo","howdy","greetings","sup",
    "what's up","whats up","how are you","how r you","how do you do",
    "who are you","what are you","are you ai","are you a bot",
    "help","start","begin","assist me",
    "good morning","good afternoon","good evening","good night",
}

def is_greeting(q: str) -> bool:
    ql = q.lower().strip().rstrip("!?,.")
    if ql in GREETING_EXACT:
        return True
    for g in GREETING_EXACT:
        if ql.startswith(g) and len(ql) <= len(g) + 5:
            return True
    return False

CAREER_KEYWORDS = [
    "career","job","profession","work","employment","occupation",
    "field","industry","role","position","post",
    "degree","course","college","university","study","education",
    "mbbs","btech","mba","phd","diploma","certification","exam",
    "neet","jee","upsc","gate","cat","ielts","gre",
    "12th","after graduation","after college","after school",
    "become","how to become","want to be","want to become",
    "skills","salary","roadmap","scope","future","growth",
    "internship","training","resume","interview","promotion",
    "doctor","engineer","lawyer","teacher","nurse","designer",
    "developer","programmer","scientist","analyst","manager",
    "architect","accountant","pilot","chef","artist","writer",
    "neurosurgeon","surgeon","cricketer","athlete","sportsperson",
    "footballer","actor","musician","photographer","journalist",
    "ias","ips","ca","cs","data scientist","ai engineer",
    "startup","entrepreneur","business","freelance","consulting",
    "finance","marketing","sales","hr","operations",
]

REJECT_PATTERNS = [
    r"^[\d\s\+\-\*\/\.\(\)]+$",
    r"^\d+\s*[\+\-\*\/]\s*\d+",
]

REJECT_KEYWORDS = [
    "joke","jokes","funny","laugh","meme","comedy",
    "recipe","cook","food","restaurant",
    "movie","film","song","lyrics","music","netflix",
    "weather","temperature","forecast",
    "news","politics","election","religion",
    "translate","translation",
]

def is_career_related(q: str) -> bool:
    ql = q.lower().strip()
    for p in REJECT_PATTERNS:
        if re.match(p, ql):
            return False
    for kw in REJECT_KEYWORDS:
        if kw in ql:
            return False
    if any(kw in ql for kw in CAREER_KEYWORDS):
        return True
    if len(ql.split()) >= 6:
        return True
    return False

def is_followup(q: str, history: str) -> bool:
    if not history.strip():
        return False
    ql = q.lower().strip()
    fresh = [
        "how to become","what is","what are","career in","skills for",
        "future of","salary of","roadmap for","scope of","i want to become",
        "i want to be","tell me about","explain","describe",
        "what should i do","how do i become","guide me",
        "after 12th","after graduation",
    ]
    if any(kw in ql for kw in fresh):
        return False
    followup = [
        "isn't","isnt","is it not","but wait","are you sure","really",
        "correct me","wrong","actually","how long","how many years",
        "what about","can you explain more","clarify","you said",
        "earlier you","that's wrong","thats wrong","not right","mistake",
        "what did you mean","tell me more about that","elaborate on",
        "then what","next step","after that","how so","so then","and then",
    ]
    if any(kw in ql for kw in followup):
        return True
    if len(ql.split()) < 8:
        return True
    return False

def normalize_question(q: str) -> str:
    return re.sub(r'\s+', ' ', q.strip().lower())

async def _static_stream(text: str):
    size = 40
    for i in range(0, len(text), size):
        yield text[i:i + size]


# ── Main entry point ──────────────────────────────────────────────────────────

async def run_rag(question: str, session_id: str = "default"):
    # Guard
    if not question or not question.strip():
        return _static_stream(REJECTION_MESSAGE)

    question = question.strip()

    # Greeting
    if is_greeting(question):
        return _static_stream(GREETING_MESSAGE)

    # Non-career
    if not is_career_related(question):
        return _static_stream(REJECTION_MESSAGE)

    normalized_q = normalize_question(question)
    history      = get_last_n_messages(session_id, n=6)
    followup     = is_followup(question, history)

    # Cache (fresh only)
    if not followup:
        cached = get_cache(normalized_q)
        if cached:
            return _static_stream(cached)

    # Qdrant (non-fatal)
    context_block = ""
    try:
        docs = search_docs(question)
        if docs:
            texts = [d.payload.get("text","") for d in docs[:5]
                     if d.payload.get("text","")]
            if texts:
                context_block = "Relevant Context:\n" + "\n".join(texts)
    except Exception:
        pass

    # Build prompt
    if followup:
        prompt = FOLLOWUP_PROMPT.format(history=history, question=question)
    else:
        prompt = MASTER_PROMPT.format(
            question=question, context_block=context_block, rule=RULE)

    # Stream from LLM
    stream = ask_llm_stream(prompt)

    async def final_stream():
        full = ""
        async for chunk in stream:
            if chunk:
                full += chunk
                yield chunk
        if not followup and full:
            try:
                set_cache(normalized_q, full)
            except Exception:
                pass
        try:
            save_memory(session_id, f"User: {question}")
            save_memory(session_id, f"AI: {full}")
        except Exception:
            pass

    return final_stream()