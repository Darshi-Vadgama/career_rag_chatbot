# app/services/rag_pipeline.py
import re
from app.services.qdrant_service import search_docs
from app.services.llm_service import ask_llm_stream
from app.services.redis_service import (
    get_cache,
    set_cache,
    save_memory,
    get_last_n_messages,
)

# ── Rejection Message ──────────────────────────────────────────────────────────
REJECTION_MESSAGE = (
    "I'm a career counseling assistant and can only help with career-related questions. "
    "Please ask me about careers, jobs, skills, salaries, roadmaps, courses, or professional development!"
)

# ── Prompt Rules ───────────────────────────────────────────────────────────────
RULE = """
STRICT RULES:
- Conclusion must be maximum 3 lines only.
- Do NOT repeat the conclusion anywhere else.
- Do NOT repeat suggestions.
- Do NOT cut the answer short — complete every section fully.
- Stop ONLY after the Conclusion section.
"""

# ── Follow-up / Correction Prompt ─────────────────────────────────────────────
FOLLOWUP_PROMPT = """
You are an expert career counselor AI with 20+ years of experience.

Chat History:
{history}

User's Follow-up Question:
{question}

STRICT INSTRUCTIONS:
- You are a CAREER COUNSELOR ONLY. You only answer career-related follow-up questions.
- If this follow-up is NOT related to careers, jobs, education, or professional development,
  respond with ONLY: "I'm a career counseling assistant. I can only answer career-related questions!"
- Read the chat history carefully and directly address what the user is asking.
- If the user is correcting a fact (e.g. "isn't MBBS 5 years?"), acknowledge and give accurate info.
- Do NOT repeat the full career template (Overview, Skills, Salary, etc.) again.
- Give a focused, conversational, accurate answer in 3-6 paragraphs.
- Use Indian context where relevant (MBBS in India is 5.5 years including internship).
- Be factual and honest. Do not hallucinate durations, salaries, or certifications.
"""

# ── Full Career Template Prompt ────────────────────────────────────────────────
MASTER_PROMPT = """
You are an expert career counselor AI with 20+ years of experience in career guidance, industry knowledge, and professional development across India and globally.

User Question:
{question}

{context_block}

CRITICAL INSTRUCTION — TOPIC FOCUS:
- Answer ONLY about the exact career or topic mentioned in the "User Question" above.
- Do NOT answer about any other career, specialty, or profession.
- If the user asks "what is doctor", answer about doctors in general — NOT neurosurgeons specifically.
- If the user asks "what is teacher", answer about teachers in general — NOT a specific type.
- The answer topic must come ONLY from the current question. Ignore any previous context.

IMPORTANT FACTS — ALWAYS USE THESE CORRECTLY:
- MBBS in India = 4.5 years of study + 1 year compulsory internship = 5.5 years total
- MS General Surgery = 3 years after MBBS
- MCh Neurosurgery = 3 years after MS (superspecialty)
- DNB Neurosurgery = alternative to MCh, also 3 years
- Total time to become a Neurosurgeon in India = ~14 years after 12th grade
- NEET UG = entrance exam for MBBS after 12th grade
- NEET PG = entrance exam for MD/MS after MBBS
- NEET SS = entrance exam for MCh/DM superspecialty after MS/MD
- BTech = 4 years, MBA = 2 years, LLB = 3 years after graduation, CA = ~5 years
- Always use accurate degree durations. Never fabricate timelines.

Your task: Write a THOROUGH, HIGHLY DETAILED, and PROFESSIONAL career counseling response
about the EXACT career asked in the question above.
Every section must be COMPLETE and INFORMATIVE — do not give short or vague answers.

ALWAYS use EXACTLY this structure in this exact order:

# Overview
Write 4-6 lines explaining:
- What this career/profession is in GENERAL (not a subspecialty unless specifically asked)
- What professionals in this field do day-to-day
- What industry they work in and why this role matters
- Work environment and typical workplace

# Skills Required
List 6-8 specific, realistic, and practical skills needed for this career.
For EACH skill, write 3-4 lines explaining:
- What the skill is
- Why it is important for this role
- How to develop or demonstrate it

# Salary in India
Use EXACTLY this format with realistic INR figures:
- Fresher (0-2 years):     ₹X LPA – ₹X LPA
- Mid-Level (2-5 years):   ₹X LPA – ₹X LPA
- Senior (5-10 years):     ₹X LPA – ₹X LPA
- Experienced (10+ years): ₹X LPA+

Also mention top cities where salaries are highest and sector differences (govt vs private).
Do NOT invent crore-level salaries. Keep figures realistic and grounded.

# Career Roadmap
Give a HIGHLY DETAILED step-by-step progression with 4 phases.
Each phase MUST include:
- Exact year ranges (e.g. "Years 1–6 after 12th")
- Specific exam names (NEET UG, NEET PG, NEET SS, JEE, UPSC, etc.) with brief explanation of what they are
- Exact degree names and durations
- Specific actions the person should take

Use this level of detail for medical careers:

**Phase 1 — Getting Started (Years 1–6 after 12th):**
- Clear NEET UG (National Eligibility cum Entrance Test for undergraduate medical admissions)
- Complete MBBS: 4.5 years of study + 1 year compulsory rotating internship = 5.5 years total
- During internship: start preparing for NEET PG
- Register with State Medical Council after MBBS completion

**Phase 2 — Building Expertise (Years 6–10):**
- Clear NEET PG (entrance exam for MD/MS postgraduate admissions)
- Join MS General Surgery (3 years) or MD in relevant specialty
- Build surgical/clinical skills, assist in OTs, attend conferences
- Publish case reports and research papers

**Phase 3 — Specialization (Years 10–14):**
- Clear NEET SS (entrance for superspecialty MCh/DM programs)
- Join MCh in chosen superspecialty (3 years) — e.g. MCh Neurosurgery, MCh Urology
- Develop subspecialty interest, complete senior residency at top institutes (AIIMS, NIMHANS, PGI)
- Obtain DNB if MCh seat not available — equivalent qualification

**Phase 4 — Senior & Leadership (Year 14+):**
- Join as consultant/attending at hospital or medical college
- Consider private practice, academic position, or research role
- Mentor junior doctors, lead research projects, attend global conferences
- Explore hospital administration, healthcare entrepreneurship, or policy roles

For non-medical careers (engineering, law, business, arts, sports, etc.),
use equivalent detail with the correct exams, degrees, and timelines for that field.

# Future Scope
Write 5-6 lines on:
- How this career is evolving over the next 5-10 years
- Impact of technology, AI, or market trends on this role
- New opportunities emerging in this field
- Job market demand forecast in India and globally

# Additional Suggestions
Give 5-6 specific, actionable suggestions covering:
- Top certifications or courses (name them specifically)
- Networking and professional communities to join
- Tools or software to learn
- Portfolio or projects to build
- Books, resources, or mentors to seek

# Conclusion
{rule}
Write exactly 3 lines summarizing:
- Why this is a good career choice
- The key to success in it
- One motivational closing line
"""


# ── Career Relevance Keywords ──────────────────────────────────────────────────
CAREER_KEYWORDS = [
    "career", "job", "profession", "work", "employment", "occupation",
    "field", "industry", "role", "position", "post",
    "degree", "course", "college", "university", "study", "education",
    "mbbs", "btech", "mba", "phd", "diploma", "certification", "exam",
    "neet", "jee", "upsc", "gate", "cat", "ielts", "gre",
    "12th", "after graduation", "after college", "after school",
    "become", "how to become", "want to be", "want to become",
    "skills", "salary", "roadmap", "scope", "future", "growth",
    "internship", "training", "resume", "interview", "promotion",
    "doctor", "engineer", "lawyer", "teacher", "nurse", "designer",
    "developer", "programmer", "scientist", "analyst", "manager",
    "architect", "accountant", "pilot", "chef", "artist", "writer",
    "neurosurgeon", "surgeon", "cricketer", "athlete", "sportsperson",
    "footballer", "actor", "musician", "photographer", "journalist",
    "ias", "ips", "ca", "cs", "data scientist", "ai engineer",
    "startup", "entrepreneur", "business", "freelance", "consulting",
    "finance", "marketing", "sales", "hr", "operations",
    "what is doctor", "what is engineer", "what is teacher",
]

# ── Non-career Rejection Patterns ─────────────────────────────────────────────
REJECT_PATTERNS = [
    r"^[\d\s\+\-\*\/\.\(\)]+$",   # pure math: 5+5, 100/2
    r"^\d+\s*[\+\-\*\/]\s*\d+",   # math expressions
]

REJECT_KEYWORDS = [
    "joke", "jokes", "funny", "laugh", "meme", "comedy",
    "recipe", "cook", "food", "restaurant",
    "movie", "film", "song", "lyrics", "music", "netflix",
    "weather", "temperature", "forecast",
    "news", "politics", "election", "religion",
    "translate", "translation",
    "good morning", "good night", "good evening",
    "how are you", "what's up", "whats up",
    "who are you", "your name", "are you ai",
]


# ── Classifier: Is Career Related? ────────────────────────────────────────────
def is_career_related(question: str) -> bool:
    q = question.lower().strip()

    # Reject pure math
    for pattern in REJECT_PATTERNS:
        if re.match(pattern, q):
            return False

    # Reject explicit non-career
    for kw in REJECT_KEYWORDS:
        if kw in q:
            return False

    # Allow if career keyword present
    if any(kw in q for kw in CAREER_KEYWORDS):
        return True

    # Allow longer questions (benefit of doubt)
    if len(q.split()) >= 6:
        return True

    return False


# ── Classifier: Is Follow-up? ─────────────────────────────────────────────────
def is_followup(question: str, history: str) -> bool:
    """
    True  → FOLLOWUP_PROMPT (short, contextual, uses history)
    False → MASTER_PROMPT (full template, NO history passed)
    """
    if not history.strip():
        return False  # no history = always fresh

    q = question.lower().strip()

    # These always mean FRESH career question
    fresh_signals = [
        "how to become", "what is", "what are", "career in",
        "skills for", "future of", "salary of", "roadmap for",
        "scope of", "i want to become", "i want to be",
        "tell me about", "explain", "describe",
        "what should i do", "how do i become", "guide me",
        "after 12th", "after graduation",
    ]
    if any(kw in q for kw in fresh_signals):
        return False

    # These always mean FOLLOW-UP
    followup_signals = [
        "isn't", "isnt", "is it not", "but wait",
        "are you sure", "really", "correct me",
        "wrong", "actually", "how long", "how many years",
        "what about", "can you explain more", "clarify",
        "you said", "earlier you", "that's wrong", "thats wrong",
        "not right", "mistake", "what did you mean",
        "tell me more about that", "elaborate on",
        "then what", "next step", "after that",
        "how so", "so then", "and then",
    ]
    if any(kw in q for kw in followup_signals):
        return True

    # Short question without fresh signal = likely follow-up
    if len(q.split()) < 8:
        return True

    return False


# ── Normalize for Cache Key ────────────────────────────────────────────────────
def normalize_question(question: str) -> str:
    question = question.strip().lower()
    question = re.sub(r'\s+', ' ', question)
    return question


# ── Main RAG Entry Point ───────────────────────────────────────────────────────
async def run_rag(question: str, session_id: str = "default"):

    # ── Step 1: Reject non-career questions immediately ───────────────────────
    if not is_career_related(question):
        async def rejection_stream():
            yield REJECTION_MESSAGE
        return rejection_stream()

    normalized_q = normalize_question(question)

    # ── Step 2: Get session history ───────────────────────────────────────────
    history = get_last_n_messages(session_id, n=6)

    # ── Step 3: Detect question type ─────────────────────────────────────────
    followup = is_followup(question, history)

    # ── Step 4: Cache check (only for fresh questions) ────────────────────────
    if not followup:
        cached = get_cache(normalized_q)
        if cached:
            async def cache_stream():
                chunk_size = 20
                for i in range(0, len(cached), chunk_size):
                    yield cached[i:i + chunk_size]
            return cache_stream()

    # ── Step 5: Qdrant Vector Search ──────────────────────────────────────────
    context_block = ""
    docs = search_docs(question)
    if docs:
        texts = [
            d.payload.get("text", "")
            for d in docs[:5]
            if d.payload.get("text", "")
        ]
        if texts:
            context_block = "Relevant Context:\n" + "\n".join(texts)

    # ── Step 6: Build prompt ──────────────────────────────────────────────────
    if followup:
        # Follow-up: WITH history so LLM can address correction/clarification
        prompt = FOLLOWUP_PROMPT.format(
            history=history,
            question=question,
        )
    else:
        # Fresh question: NO history — prevents career contamination from previous chats
        prompt = MASTER_PROMPT.format(
            question=question,
            context_block=context_block,
            rule=RULE,
        )

    # ── Step 7: Stream from LLM ───────────────────────────────────────────────
    stream = ask_llm_stream(prompt)

    async def final_stream():
        full = ""
        async for chunk in stream:
            if chunk:
                full += chunk
                yield chunk

        # Cache only fresh career answers
        if not followup:
            set_cache(normalized_q, full)

        # Always save to session memory
        save_memory(session_id, f"User: {question}")
        save_memory(session_id, f"AI: {full}")

    return final_stream()