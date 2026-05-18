import os
import json
import zipfile
import time
from tqdm import tqdm

import torch
from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, VectorParams, Distance

UPLOADED_FILE = "data/final_career_dataset_updated.zip"

QDRANT_URL= "https://a68732de-e745-46ea-8323-82aa4d83cb95.us-east-1-1.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIiwic3ViamVjdCI6ImFwaS1rZXk6YTUwMTZlYTktMjE4ZC00OWQzLTg1MTctMWYwZGQwZTJiZDkzIn0.SNJ9ldEDJwQ5wAN9oKDWHOcHPqz3Stz6LAV6VM_ZwgU"

COLLECTION = "career_collection"

MODEL_NAME = "BAAI/bge-base-en-v1.5"
VECTOR_SIZE = 768

ROW_BATCH = 1000
EMBED_BATCH = 128
UPLOAD_BATCH = 512
TIMEOUT = 120

device = "cuda" if torch.cuda.is_available() else "cpu"

print("Using Device:", device)

if device == "cuda":
    print("GPU Name:", torch.cuda.get_device_name(0))

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=TIMEOUT
)

print("Connected to Qdrant")

collections = [c.name for c in client.get_collections().collections]

if COLLECTION in collections:
    client.delete_collection(COLLECTION)

client.create_collection(
    collection_name=COLLECTION,
    vectors_config=VectorParams(
        size=VECTOR_SIZE,
        distance=Distance.COSINE
    )
)

print("Collection Ready")

model = SentenceTransformer(
    MODEL_NAME,
    device=device
)

print("Model Loaded")

if UPLOADED_FILE.endswith(".zip"):
    with zipfile.ZipFile(UPLOADED_FILE, "r") as z:
        z.extractall("dataset")

    files = os.listdir("dataset")
    json_file = [f for f in files if f.endswith(".json")][0]
    JSON_FILE = os.path.join("dataset", json_file)
else:
    JSON_FILE = UPLOADED_FILE

with open(JSON_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

print("Loaded Rows:", len(data))

def clean(v):
    x = str(v).strip()
    return "" if x.lower() in ["", "nan", "none", "null"] else x

def make_chunks(row):
    career = clean(row.get("career"))
    domain = clean(row.get("domain"))
    desc = clean(row.get("description"))
    skills = clean(row.get("skills"))
    education = clean(row.get("education"))
    salary = clean(row.get("salary"))
    experience = clean(row.get("experience"))
    path = clean(row.get("career_path"))

    chunks = []

    if desc:
        chunks.append({
            "chunk_type": "overview",
            "text": f"Career: {career}\nDomain: {domain}\n\nOverview:\n{desc}"
        })

    if skills:
        chunks.append({
            "chunk_type": "skills",
            "text": f"Career: {career}\n\nSkills Required:\n{skills}"
        })

    if education:
        chunks.append({
            "chunk_type": "education",
            "text": f"Career: {career}\n\nEducation Needed:\n{education}"
        })

    if salary:
        chunks.append({
            "chunk_type": "salary",
            "text": f"Career: {career}\n\nSalary Range:\n{salary}"
        })

    if experience:
        chunks.append({
            "chunk_type": "experience",
            "text": f"Career: {career}\n\nExperience Required:\n{experience}"
        })

    if path:
        chunks.append({
            "chunk_type": "roadmap",
            "text": f"Career: {career}\n\nCareer Growth Path:\n{path}"
        })

    return chunks

def safe_upsert(points):
    for i in range(5):
        try:
            client.upsert(
                collection_name=COLLECTION,
                points=points
            )
            return True
        except Exception as e:
            print("Retry", i + 1, e)
            time.sleep(5)
    return False

pid = 1
uploaded = 0

for start in tqdm(range(0, len(data), ROW_BATCH), desc="Processing"):
    rows = data[start:start + ROW_BATCH]

    all_texts = []
    all_payloads = []

    for row in rows:
        chunks = make_chunks(row)

        for c in chunks:
            all_texts.append(c["text"])

            all_payloads.append({
                "career": clean(row.get("career")),
                "domain": clean(row.get("domain")),
                "chunk_type": c["chunk_type"],
                "text": c["text"]
            })

    if not all_texts:
        continue

    vectors = model.encode(
        all_texts,
        batch_size=EMBED_BATCH,
        normalize_embeddings=True,
        show_progress_bar=False
    )

    points = []

    for payload, vec in zip(all_payloads, vectors):
        points.append(
            PointStruct(
                id=pid,
                vector=vec.tolist(),
                payload=payload
            )
        )

        pid += 1

        if len(points) >= UPLOAD_BATCH:
            ok = safe_upsert(points)

            if ok:
                uploaded += len(points)

            points = []

    if points:
        ok = safe_upsert(points)

        if ok:
            uploaded += len(points)

print("INGEST COMPLETE")
print("Total Uploaded:", uploaded)
print("Collection:", COLLECTION)