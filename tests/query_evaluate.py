# tests/query_evaluate.py
# FINAL SINGLE QUERY EVALUATOR
# Auto keyword detect (no manual input)

import requests
import time
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

API_URL = "http://localhost:8000/career-search"

# =====================================================
# AUTO KEYWORD DETECTION
# =====================================================
def detect_keywords(query):

    q = query.lower()

    # career names
    mapping = {
        "doctor": ["doctor", "medical", "healthcare"],
        "teacher": ["teacher", "education", "students"],
        "data scientist": ["data scientist", "python", "analytics"],
        "data science": ["data scientist", "python", "analytics"],
        "software engineer": ["software", "developer", "coding"],
        "engineer": ["software", "developer", "coding"],
        "accounts": ["accounts", "commerce", "finance", "bcom", "ca"],
        "accounts": ["accounts", "commerce", "finance", "bcom", "ca"],
        "commerce": ["commerce", "finance", "bcom", "ca"],
    }

    keywords = []

    for key, vals in mapping.items():
        if key in q:
            keywords.extend(vals)

    # intent keywords
    if "salary" in q:
        keywords.extend(["salary", "monthly", "yearly"])

    if "skill" in q:
        keywords.extend(["skills"])

    if "experience" in q or "year" in q:
        keywords.extend(["experience", "years"])

    if any(x in q for x in ["marks", "score", "which career", "career choose"]):
        keywords.extend(["career", "recommendation"])

    # unique
    keywords = list(dict.fromkeys(keywords))

    if not keywords:
        keywords = q.split()[:4]

    return keywords


# =====================================================
# HELPERS
# =====================================================
def normalize(txt):
    return re.sub(r"\s+", " ", txt.lower()).strip()


def keyword_metrics(answer, keywords):

    ans = normalize(answer)

    found = sum(1 for k in keywords if k in ans)

    precision = found / len(keywords) if keywords else 1
    recall = precision
    f1 = precision

    return precision, recall, f1


def semantic_similarity(query, answer):

    try:
        vec = TfidfVectorizer()
        tfidf = vec.fit_transform([query, answer])
        score = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return float(score)
    except:
        return 0.0


def faithfulness(answer, sources):

    if not sources:
        return 0.5

    ans = normalize(answer)

    hits = 0

    for s in sources:
        if normalize(str(s))[:20] in ans:
            hits += 1

    return hits / len(sources)


def bar(score, width=30):

    fill = int(score * width)

    return "█" * fill + "░" * (width - fill)


# =====================================================
# MAIN
# =====================================================
def run():

    print("\n" + "=" * 70)
    print(" AUTO QUERY EVALUATION ")
    print("=" * 70)

    query = input("\nEnter Query: ").strip()

    if not query:
        print("No query entered.")
        return

    keywords = detect_keywords(query)

    try:

        start = time.perf_counter()

        r = requests.post(
            API_URL,
            data={"question": query},
            timeout=180
        )

        end = time.perf_counter()

        latency = round(end - start, 2)

        if r.status_code != 200:
            print("API Error:", r.status_code)
            return

        data = r.json()

        answer = data.get("answer", "")
        sources = data.get("sources", [])

        precision, recall, f1 = keyword_metrics(
            answer,
            keywords
        )

        similarity = semantic_similarity(
            query,
            answer
        )

        relevance = precision

        faithful = faithfulness(
            answer,
            sources
        )

        overall = (
            precision +
            recall +
            f1 +
            similarity +
            relevance +
            faithful
        ) / 6

        # =================================================
        # OUTPUT
        # =================================================
        print("\nDetected Keywords:")
        print(", ".join(keywords))

        print("\n" + "=" * 70)
        print(" RESULT ")
        print("=" * 70)

        print("\nAnswer Preview:")
        print(answer[:600])

        print("\nSources:")
        print(", ".join(sources) if sources else "No sources")

        print("\nResponse Time :", latency, "sec")
        print("Precision    :", round(precision, 3))
        print("Recall       :", round(recall, 3))
        print("F1 Score     :", round(f1, 3))
        print("Similarity   :", round(similarity, 3))
        print("Relevance    :", round(relevance, 3))
        print("Faithfulness :", round(faithful, 3))
        print("Overall Score:", round(overall * 100, 2), "%")

        print("\n[" + bar(overall) + "]")
        print("=" * 70)

    except Exception as e:
        print("FAILED:", str(e))


# =====================================================
if __name__ == "__main__":
    run()