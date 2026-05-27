from app.services.llm_service import ask_llm_stream

ROADMAP_PROMPT = """
You are an expert career counselor AI with 20+ years of experience in career guidance,
industry knowledge, and professional development across India and globally.

Generate a THOROUGH, HIGHLY DETAILED, and PROFESSIONAL career roadmap for: {career}

CRITICAL INSTRUCTION — TOPIC FOCUS:
- Answer ONLY about the exact career mentioned above.
- Do NOT mix in other careers or specialties.

IMPORTANT FACTS — ALWAYS USE THESE CORRECTLY:
- MBBS in India = 4.5 years study + 1 year internship = 5.5 years total
- MS General Surgery = 3 years after MBBS
- MCh Neurosurgery = 3 years after MS (superspecialty)
- DNB = alternative to MCh, also 3 years
- Total to become Neurosurgeon = ~14 years after 12th
- NEET UG = entrance for MBBS after 12th
- NEET PG = entrance for MD/MS after MBBS
- NEET SS = entrance for MCh/DM superspecialty after MS/MD
- BTech = 4 years, MBA = 2 years, LLB = 3 years after graduation, CA = ~5 years
- Never fabricate timelines or salaries.

STRICT OUTPUT RULES:
- Use EXACTLY the structure below — no skipping, no reordering, no extra sections.
- Use bullet points inside every section. No long paragraphs.
- Use the emojis exactly as shown.
- Each bullet point must be 2-3 lines with meaningful detail — NOT one liners.
- Salary must use the exact format shown — realistic INR figures only.
- Final Tips must be exactly 3 bullet points.

---

# 🚀 {career_upper} ROADMAP

---

# 📌 Phase 1 — Getting Started
## 📅 Timeline
State the exact years/time needed for this phase with specific degree names and exam names.
For medical: mention NEET UG, MBBS duration.
For engineering: mention JEE, BTech duration.
For law: mention CLAT, LLB duration.
Always give REAL durations — never say "0-3 months" for a career that takes years.

## 🎯 Goals
List 4-5 concrete goals for this phase as bullet points.
Each goal should be specific and actionable.

## 📚 What to Learn / Study
List specific topics, subjects, and concepts to focus on during this phase.

## 🛠 Skills to Build
List the practical skills to develop during this phase.

## 📖 Resources
List 4-5 specific, named resources: books, websites, YouTube channels, coaching institutes.

---

# 📌 Phase 2 — Building Expertise
## 📅 Timeline
State exact years/time for this phase with specific degree/certification names.

## 🎯 Goals
List 4-5 goals for this phase.

## 📚 Advanced Concepts to Study
List specific advanced topics and subjects for this phase.

## 🛠 Tools & Skills to Learn
List specific tools, software, clinical skills, or frameworks relevant to this career.

## 💻 Projects / Experience to Build
List 4-5 specific projects, internships, or hands-on experiences to pursue.

## 🏆 Certifications
List 3-4 relevant certifications with their full names and issuing bodies.

---

# 📌 Phase 3 — Specialization & Growth
## 📅 Timeline
State exact years/time for this phase.

## 🎯 Goals
List 4-5 goals for this phase.

## ⚡ Advanced Skills to Master
List specific advanced skills for this phase.

## ☁ Industry Tools & Technologies
List industry-standard tools, platforms, and technologies used by professionals.

## 💻 Real-world Projects / Research
List 4-5 real-world projects, research opportunities, or leadership experiences.

## 🔥 How to Stand Out
List specific ways to differentiate yourself at this stage of career.

---

# 📌 Phase 4 — Senior & Leadership
## 📅 Timeline
State when this phase typically begins (year after starting).

## 💼 Senior Role Options
List 5-6 specific senior job titles and roles available at this stage.

## 📄 Resume Tips
List 4-5 specific resume tips tailored for this career.

## 🌐 Portfolio / Profile Tips
List 3-4 portfolio or professional profile tips.

## 🎤 Common Interview Questions
List 5 common interview questions for senior roles in this career.

---

# 💰 Salary in India
Use EXACTLY this format with REALISTIC INR figures:
- 🟢 Fresher (0-2 years):     ₹X LPA – ₹X LPA
- 🟡 Mid-Level (2-5 years):   ₹X LPA – ₹X LPA
- 🔴 Senior (5-10 years):     ₹X LPA – ₹X LPA
- 🔵 Experienced (10+ years): ₹X LPA+

Also mention: top cities for highest salaries, govt vs private sector difference.

---

# 📈 Future Scope
Write 5-6 bullet points covering:
- How this career will evolve in the next 5-10 years in India and globally
- Impact of AI, technology, or market trends on this role
- New emerging opportunities in this field
- Job market demand forecast

---

# 🧠 Final Tips
Write EXACTLY 3 bullet points of practical, motivating advice for someone starting this career.
Each tip should be 2-3 lines — meaningful, not generic.

---

Career: {career}
"""


async def generate_roadmap(career: str):
    try:
        prompt = ROADMAP_PROMPT.format(
            career=career,
            career_upper=career.upper()
        )
        return ask_llm_stream(prompt)
    except Exception as e:
        async def err():
            yield f"Roadmap Error: {str(e)}"
        return err()