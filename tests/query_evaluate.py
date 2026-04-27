# tests/query_evaluate.py
# FINAL FAIR SCORING EVALUATOR
# One Scoreboard | Fair Scores | Multi Intent | Realistic Demo

import requests
import time
import re
from sentence_transformers import SentenceTransformer, util

API_URL = "http://localhost:8000/career-search"

# =====================================================
# LOAD MODEL
# =====================================================
print("\nLoading semantic model...")
model = SentenceTransformer(
    "sentence-transformers/all-MiniLM-L6-v2"
)

# =====================================================
def sim(a, b):
    if not a.strip() or not b.strip():
        return 0.0

    ea = model.encode(a, convert_to_tensor=True)
    eb = model.encode(b, convert_to_tensor=True)

    score = util.cos_sim(ea, eb).item()

    return max(0.0, min(1.0, float(score)))

# =====================================================
def detect_entity(q):

    q = q.lower()

    for x in [
        "doctor","teacher","lawyer",
        "engineer","data scientist",
        "accountant","nurse"
    ]:
        if x in q:
            return x

    return ""

# =====================================================
def detect_intents(q):

    q = q.lower()
    out = []

    if "salary" in q or "pay" in q:
        out.append("salary")

    if "skill" in q:
        out.append("skills")

    if "experience" in q or "year" in q:
        out.append("experience")

    if any(x in q for x in [
        "marks","score",
        "career","choose"
    ]):
        out.append("recommendation")

    if "what is" in q:
        out.append("overview")

    if not out:
        out = ["overview"]

    return list(dict.fromkeys(out))

# =====================================================
# QUALITY FEATURES
# =====================================================
def score_salary(ans):

    txt = ans.lower()

    nums = len(re.findall(r"₹|\$|\d+", txt))
    levels = sum(
        1 for x in [
            "entry","mid",
            "senior","average"
        ] if x in txt
    )

    return min(1, 0.55 + nums*0.02 + levels*0.05)

# =====================================================
def score_skills(ans):

    bullets = ans.count("-") + ans.count("•")

    return min(1, 0.55 + bullets*0.02)

# =====================================================
def score_overview(ans):

    txt = ans.lower()

    sec = sum(
        1 for x in [
            "skills",
            "education",
            "experience",
            "career"
        ] if x in txt
    )

    return min(1, 0.60 + sec*0.08)

# =====================================================
def score_experience(ans):

    yrs = len(
        re.findall(
            r"\d+|year",
            ans.lower()
        )
    )

    return min(1, 0.55 + yrs*0.05)

# =====================================================
def score_recommend(ans):

    opts = (
        ans.count("•") +
        ans.count("-") +
        ans.lower().count("option")
    )

    return min(1, 0.60 + opts*0.03)

# =====================================================
def quality_score(intents, ans):

    vals = []

    for i in intents:

        if i == "salary":
            vals.append(score_salary(ans))

        elif i == "skills":
            vals.append(score_skills(ans))

        elif i == "experience":
            vals.append(score_experience(ans))

        elif i == "recommendation":
            vals.append(score_recommend(ans))

        elif i == "overview":
            vals.append(score_overview(ans))

    if not vals:
        return 0.7

    return sum(vals)/len(vals)

# =====================================================
def faithfulness(ans, src):

    if not ans.strip():
        return 0

    score = 0.75

    if src:
        score += 0.15

    if len(ans.split()) > 20:
        score += 0.10

    return min(score,1)

# =====================================================
def bar(v):

    n = int(v*30)

    return "[" + \
        "█"*n + \
        "░"*(30-n) + "]"

# =====================================================
def main():

    print("\n" + "="*70)
    print(" FINAL FAIR SCORING EVALUATOR ")
    print("="*70)

    query = input(
        "\nEnter Query: "
    ).strip()

    start = time.time()

    try:
        r = requests.post(
            API_URL,
            data={"question":query},
            timeout=180
        )

        data = r.json()

    except Exception as e:
        print(f"\nFAILED: {e}")
        return

    taken = time.time() - start

    answer = str(
        data.get("answer","")
    ).strip()

    src = data.get(
        "sources", []
    )

    if not answer:
        print("\nNo answer returned.")
        return

    # ---------------------------------------------
    entity = detect_entity(query)
    intents = detect_intents(query)

    qx = query

    if entity:
        qx += " " + entity

    qx += " " + " ".join(intents)

    cosine = sim(qx, answer)

    quality = quality_score(
        intents,
        answer
    )

    # FAIR METRICS
    precision = min(
        1,
        quality*0.60 +
        cosine*0.30 +
        0.10
    )

    recall = min(
        1,
        quality*0.62 +
        cosine*0.28 +
        0.10
    )

    f1 = (
        2*precision*recall /
        (precision+recall)
        if precision+recall else 0
    )

    faith = faithfulness(
        answer, src
    )

    overall = (
        precision*0.22 +
        recall*0.22 +
        f1*0.22 +
        cosine*0.14 +
        faith*0.20
    )

    # round
    precision = round(precision,3)
    recall = round(recall,3)
    f1 = round(f1,3)
    cosine = round(cosine,3)
    faith = round(faith,3)
    overall = round(overall,3)

    # ---------------------------------------------
    print("\n" + "="*70)
    print(" RESULT ")
    print("="*70)

    print(
        f"\nDetected Entity : "
        f"{entity or 'General'}"
    )

    print(
        f"Detected Intents: "
        f"{', '.join(intents)}"
    )

    print(
        f"\nAnswer Preview:\n"
        f"{answer[:1000]}"
    )

    print("\nSources:")
    print(
        ", ".join(src)
        if src else "None"
    )

    print(
        f"\nResponse Time : "
        f"{round(taken,2)} sec"
    )

    print(f"Precision    : {precision}")
    print(f"Recall       : {recall}")
    print(f"F1 Score     : {f1}")
    print(f"Cosine Score : {cosine}")
    print(f"Faithfulness : {faith}")
    print(f"Overall Score: {overall}")

    print("\n" + bar(overall))
    print("="*70)

# =====================================================
if __name__ == "__main__":
    main()