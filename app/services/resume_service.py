# resume_service.py

from fastapi import UploadFile
from PyPDF2 import PdfReader
from io import BytesIO
from app.services.llm_service import ask_llm_stream


RESUME_PROMPT = """
You are an expert resume analyzer.

STRICT RULE: You MUST follow EXACTLY this structure every time.
Do NOT skip any section. Do NOT rename any section.
Do NOT add extra sections. Do NOT change the order.

Analyze the resume below and fill each section in detail.

---

# Profile Summary

Write 3-5 lines summarizing the candidate's background, experience level, and career focus.

---

# Skills

## Technical Skills
List all technical skills found in the resume as bullet points.

## Tools & Technologies
List all tools, software, and platforms as bullet points.

## Soft Skills
List soft skills as bullet points. If not mentioned, infer from context.

---

# Recommended Job Roles

List 4-6 specific job roles this candidate is suited for as bullet points.

---

# Why These Roles Fit

For each recommended role, write 1-2 lines explaining why the candidate fits.

---

# Strengths

List 4-6 strengths as bullet points with 1-2 lines explanation each.

---

# Weaknesses

List 3-4 weaknesses as bullet points with 1-2 lines explanation each.

---

# Improvements

List 4-6 specific improvements the candidate should make to their resume as bullet points.

---

# Career Suggestions

Write 3-5 lines of career path advice based on the candidate's current profile.

---

# Learning Recommendations

List 4-6 specific courses, skills, or certifications the candidate should pursue as bullet points.

---

Resume:
{resume_text}
"""


async def scan_resume(file: UploadFile):

    try:

        content = await file.read()

        try:

            pdf = BytesIO(content)

            reader = PdfReader(pdf)

            text = "\n".join(
                page.extract_text() or ""
                for page in reader.pages
            )

        except:

            text = content.decode(
                "utf-8",
                errors="ignore"
            )

        prompt = RESUME_PROMPT.format(resume_text=text)

        return ask_llm_stream(prompt)

    except Exception as e:

        async def err():
            yield f"Resume Error: {str(e)}"

        return err()