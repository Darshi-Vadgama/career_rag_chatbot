# app/services/roadmap_service.py
# FINAL CAREER ROADMAP WITH LLM (Mistral Cloud)

from app.services.llm_service import ask_llm

# =====================================================
# MAIN
# =====================================================
async def generate_roadmap(career:str):

    prompt = f"""
You are an expert career mentor.

Create a complete roadmap for becoming:
{career}

Return ONLY clean plain text in this exact format:

Career: {career}

Step 1: Foundation (0-3 Months)
• point
• point
• point

Step 2: Skill Building (3-6 Months)
• point
• point
• point

Step 3: Projects / Practice (6-9 Months)
• point
• point
• point

Step 4: Job Ready (9-12 Months)
• point
• point
• point

Step 5: Growth Path
• point
• point
• point

Step 6: Helpful Certifications
• point
• point
• point

Step 7: Final Advice
• point
• point
• point

Rules:
- No markdown
- No ** symbols
- No ###
- Each bullet in new line
- Practical modern roadmap
"""

    ans = await ask_llm(prompt)

    return {
        "roadmap": clean(ans)
    }

# =====================================================
# CLEAN RESPONSE
# =====================================================
def clean(text):

    bad = ["**", "###", "---"]

    for b in bad:
        text = text.replace(b, "")

    return text.strip()