# tests/evaluate.py
# FINAL UPGRADED EVALUATION FILE
# Career AI Project (Current API)
# Includes:
# Relevance Score
# Answer Quality
# Response Time
# Similarity
# Correct / Incorrect
# Overall Score

import requests
import time
import json
import os
import re
import numpy as np

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# =====================================================
# CONFIG
# =====================================================
API_URL = "http://localhost:8000/career-search"
REPORT_FILE = "docs/evaluation_report.json"

# =====================================================
# TEST CASES
# query, expected_keywords, expected_intent
# =====================================================
TEST_CASES = [

    ("what is doctor?",
     ["doctor", "healthcare", "skills", "career"],
     "overview"),

    ("what is teacher?",
     ["teacher", "education", "students"],
     "overview"),

    ("what is salary of doctor in india?",
     ["salary", "doctor", "india", "monthly"],
     "salary"),

    ("salary of software engineer in usa?",
     ["salary", "software", "engineer", "usa"],
     "salary"),

    ("which skills need to become data science?",
     ["python", "sql", "machine", "skills"],
     "skills"),

    ("skills required for teacher?",
     ["teaching", "communication", "skills"],
     "skills"),

    ("how many years experience need for doctor?",
     ["experience", "doctor", "years"],
     "experience"),

    ("experience required for software engineer?",
     ["experience", "developer", "software"],
     "experience"),

    ("what is data scientist?",
     ["data", "scientist", "analytics"],
     "overview"),

    ("what is salary of data scientist in india?",
     ["salary", "data", "scientist", "india"],
     "salary"),
]

# =====================================================
# HELPERS
# =====================================================
def normalize(txt):
    return re.sub(r"\s+", " ", txt.lower()).strip()


def keyword_metrics(answer, keywords):

    ans = normalize(answer)

    tp = sum(1 for k in keywords if k.lower() in ans)
    fp = max(0, len(keywords) - tp)
    fn = max(0, len(keywords) - tp)

    precision = tp / (tp + fp) if (tp + fp) else 0
    recall = tp / (tp + fn) if (tp + fn) else 0
    f1 = (
        2 * precision * recall / (precision + recall)
        if (precision + recall)
        else 0
    )

    return round(precision, 3), round(recall, 3), round(f1, 3)


def semantic_similarity(query, answer):

    try:
        vec = TfidfVectorizer()
        tfidf = vec.fit_transform([query, answer])
        sim = cosine_similarity(tfidf[0:1], tfidf[1:2])[0][0]
        return round(float(sim), 3)
    except:
        return 0.0


def relevance_score(answer, keywords):

    ans = normalize(answer)
    found = sum(1 for k in keywords if k.lower() in ans)

    return round(found / len(keywords), 3)


def correctness(answer, intent):

    ans = normalize(answer)

    if intent == "salary":
        return (
            "salary" in ans
            or "monthly" in ans
            or "yearly" in ans
            or "₹" in ans
            or "$" in ans
        )

    if intent == "skills":
        return "skills" in ans or "•" in answer

    if intent == "experience":
        return "experience" in ans or "years" in ans

    return len(answer.strip()) > 50


def bar(score, width=24):

    fill = int(score * width)
    return "█" * fill + "░" * (width - fill)


# =====================================================
# MAIN
# =====================================================
def run():

    print("\n" + "=" * 70)
    print(" Career AI - Final Evaluation Report ")
    print("=" * 70)

    all_rows = []

    total_time = []
    total_precision = []
    total_recall = []
    total_f1 = []
    total_similarity = []
    total_relevance = []
    total_correct = 0

    for i, (query, keywords, intent) in enumerate(TEST_CASES, 1):

        print(f"\n[{i}/{len(TEST_CASES)}] {query}")

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
                raise Exception(f"HTTP {r.status_code}")

            data = r.json()
            answer = data.get("answer", "")

            precision, recall, f1 = keyword_metrics(
                answer,
                keywords
            )

            similarity = semantic_similarity(
                query,
                answer
            )

            relevance = relevance_score(
                answer,
                keywords
            )

            is_correct = correctness(
                answer,
                intent
            )

            overall = round(
                (
                    precision +
                    recall +
                    f1 +
                    similarity +
                    relevance +
                    (1 if is_correct else 0)
                ) / 6,
                3
            )

            # accumulate
            total_time.append(latency)
            total_precision.append(precision)
            total_recall.append(recall)
            total_f1.append(f1)
            total_similarity.append(similarity)
            total_relevance.append(relevance)

            if is_correct:
                total_correct += 1

            print(f"Time       : {latency} sec")
            print(f"Precision  : {precision:.2f}")
            print(f"Recall     : {recall:.2f}")
            print(f"F1 Score   : {f1:.2f}")
            print(f"Similarity : {similarity:.2f}")
            print(f"Relevance  : {relevance:.2f}")
            print(f"Correct    : {'PASS' if is_correct else 'FAIL'}")
            print(f"Overall    : {overall*100:.1f}%")
            print(f"[{bar(overall)}]")

            all_rows.append({
                "query": query,
                "latency_sec": latency,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "similarity": similarity,
                "relevance": relevance,
                "correct": is_correct,
                "overall": overall
            })

        except Exception as e:

            print("FAILED :", str(e))

            all_rows.append({
                "query": query,
                "error": str(e)
            })

    # =================================================
    # SUMMARY
    # =================================================
    n = len(TEST_CASES)

    avg_time = round(np.mean(total_time), 2) if total_time else 0
    avg_precision = round(np.mean(total_precision), 3)
    avg_recall = round(np.mean(total_recall), 3)
    avg_f1 = round(np.mean(total_f1), 3)
    avg_similarity = round(np.mean(total_similarity), 3)
    avg_relevance = round(np.mean(total_relevance), 3)
    accuracy = round(total_correct / n, 3)

    final_score = round(
        (
            avg_precision +
            avg_recall +
            avg_f1 +
            avg_similarity +
            avg_relevance +
            accuracy
        ) / 6,
        3
    )

    print("\n" + "=" * 70)
    print(" FINAL SUMMARY ")
    print("=" * 70)

    print(f"Average Response Time : {avg_time} sec")
    print(f"Average Precision    : {avg_precision*100:.1f}%")
    print(f"Average Recall       : {avg_recall*100:.1f}%")
    print(f"Average F1 Score     : {avg_f1*100:.1f}%")
    print(f"Average Similarity   : {avg_similarity*100:.1f}%")
    print(f"Average Relevance    : {avg_relevance*100:.1f}%")
    print(f"Correctness Accuracy : {accuracy*100:.1f}%")
    print(f"Overall System Score : {final_score*100:.1f}%")
    print(f"[{bar(final_score)}]")

    # save report
    os.makedirs("docs", exist_ok=True)

    report = {
        "summary": {
            "avg_response_time_sec": avg_time,
            "avg_precision": avg_precision,
            "avg_recall": avg_recall,
            "avg_f1_score": avg_f1,
            "avg_similarity": avg_similarity,
            "avg_relevance": avg_relevance,
            "correctness_accuracy": accuracy,
            "overall_system_score": final_score
        },
        "results": all_rows
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report, f, indent=2)

    print("\nSaved Report:", REPORT_FILE)
    print("=" * 70 + "\n")


# =====================================================
if __name__ == "__main__":
    run()