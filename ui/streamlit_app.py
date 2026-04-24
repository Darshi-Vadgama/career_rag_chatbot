# ui/streamlit_app.py
# REDUCED / CLEAN VERSION
# Same Features:
# Career Chat + Resume + Roadmap + Sessions + No Emojis

import streamlit as st
import requests, json, os, uuid, re
from datetime import datetime

BASE = "http://backend:8000"
CHAT_API = f"{BASE}/career-search"
RESUME_API = f"{BASE}/resume-scan"
ROADMAP_API = f"{BASE}/career-roadmap"
FILE = "chat_history.json"

st.set_page_config(page_title="Career AI", page_icon="💼", layout="wide")

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>
html,body,[class*="css"]{background:#0f0f0f;color:white;}
section[data-testid="stSidebar"]{background:#171717;}
.user{background:#1f1f1f;padding:12px;border-radius:12px;margin:8px 0;}
.bot{background:#111111;padding:12px;border-radius:12px;
border-left:4px solid #10a37f;margin:8px 0;font-size:14px;}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================
def clean(t):
    if not t:
        return ""
    return re.sub(
        "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U00002700-\U000027BF"
        "]+", "", t
    ).strip()

def load():
    if os.path.exists(FILE):
        return json.load(open(FILE))
    return []

def save():
    json.dump(st.session_state.sessions, open(FILE, "w"), indent=2)

def new_chat():
    cid = str(uuid.uuid4())
    st.session_state.sessions.append({
        "id": cid,
        "title": "New Chat",
        "messages": []
    })
    st.session_state.current = cid
    save()

def chat():
    for s in st.session_state.sessions:
        if s["id"] == st.session_state.current:
            return s

# =====================================================
# INIT
# =====================================================
if "sessions" not in st.session_state:
    st.session_state.sessions = load()

if not st.session_state.sessions:
    st.session_state.sessions = []

if "current" not in st.session_state:
    new_chat()

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.title("Career AI")

    mode = st.radio(
        "Choose Tool",
        ["Career Chat", "Resume Scan", "Roadmap"]
    )

    if st.button("New Chat"):
        new_chat()
        st.rerun()

    st.markdown("### Saved Chats")

    for s in reversed(st.session_state.sessions[-15:]):
        if st.button(s.get("title", "Chat")[:28], key=s["id"]):
            st.session_state.current = s["id"]
            st.rerun()

# =====================================================
# CAREER CHAT
# =====================================================
if mode == "Career Chat":

    st.title("Career Chat")

    c = chat()

    for m in c["messages"]:
        cls = "user" if m["role"] == "user" else "bot"
        txt = clean(m["content"]).replace("\n", "<br>")
        st.markdown(
            f"<div class='{cls}'>{txt}</div>",
            unsafe_allow_html=True
        )

    q = st.chat_input("Ask anything...")

    if q:

        c["messages"].append({
            "role": "user",
            "content": q
        })

        try:
            r = requests.post(
                CHAT_API,
                data={"question": q},
                timeout=180
            )
            ans = r.json().get("answer", "No Answer")
        except:
            ans = "Connection Error"

        ans = clean(ans)

        c["messages"].append({
            "role": "assistant",
            "content": ans
        })

        if c["title"] == "New Chat":
            c["title"] = q[:35]

        save()
        st.rerun()

# =====================================================
# RESUME
# =====================================================
elif mode == "Resume Scan":

    st.title("Resume Scanner")

    file = st.file_uploader("Upload PDF", type=["pdf"])
    txt = st.text_area("Or Paste Resume", height=220)

    if st.button("Scan Resume"):

        try:

            files = None
            data = {}

            if file:
                files = {
                    "file":(
                        file.name,
                        file.getvalue(),
                        "application/pdf"
                    )
                }

            if txt.strip():
                data["resume_text"] = txt

            r = requests.post(
                RESUME_API,
                files=files,
                data=data,
                timeout=180
            )

            res = r.json()

            st.success("Resume Analysis Complete")

            for k, title in {
                "career_matches":"Recommended Careers",
                "skills_found":"Skills Found",
                "missing_skills":"Missing Skills",
                "suggestions":"Suggestions"
            }.items():

                if k in res:
                    st.subheader(title)
                    for x in res[k]:
                        st.write("•", clean(x))

            if "summary" in res:
                st.subheader("Summary")
                st.info(clean(res["summary"]))

        except:
            st.error("Resume Scan Failed")

# =====================================================
# ROADMAP
# =====================================================
else:

    st.title("Career Roadmap")

    career = st.text_input(
        "Enter Career Name"
    )

    if st.button("Generate Roadmap"):

        try:

            r = requests.post(
                ROADMAP_API,
                data={"career": career},
                timeout=180
            )

            d = r.json()

            ans = (
                d.get("answer")
                or d.get("roadmap")
                or d.get("result")
                or "No roadmap"
            )

            ans = clean(ans).replace("\\n", "\n")

            st.text_area(
                "Roadmap",
                ans,
                height=500
            )

        except:
            st.error("Roadmap Failed")