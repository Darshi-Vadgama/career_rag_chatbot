# ui/streamlit_app.py
# Final Premium Reduced UI
# Clean Answers (No ### ** etc.)
# Career Chat + Resume + Roadmap
# 3 Dots Delete Chat
# Roadmap Saved

import streamlit as st
import requests, json, os, uuid, re

BASE = "http://backend:8000"
CHAT = f"{BASE}/career-search"
RESUME = f"{BASE}/resume-scan"
ROADMAP = f"{BASE}/career-roadmap"
FILE = "chat_history.json"

st.set_page_config(
    page_title="Career AI",
    layout="wide"
)

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>
html,body,[class*="css"]{
background:#0f0f0f;color:white;
}
section[data-testid="stSidebar"]{
background:#171717;
}
.user,.bot{
padding:12px;
border-radius:12px;
margin:8px 0;
font-size:14px;
}
.user{background:#1f1f1f;}
.bot{
background:#111111;
border-left:4px solid #10a37f;
}
.stButton button{
border-radius:10px;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================
def clean(t):
    if not t:
        return ""
    return re.sub(
        "[\U00010000-\U0010ffff]",
        "",
        str(t)
    ).strip()

def format_answer(t):

    t = clean(t)

    for x in [
        "###","##","#",
        "**","__","`"
    ]:
        t = t.replace(x, "")

    t = t.replace("- ", "• ")
    t = t.replace("* ", "• ")

    while "\n\n\n" in t:
        t = t.replace("\n\n\n", "\n\n")

    return t.strip()

def load():
    if os.path.exists(FILE):
        return json.load(open(FILE))
    return []

def save():
    json.dump(
        st.session_state.sessions,
        open(FILE, "w"),
        indent=2
    )

def new_chat():

    cid = str(uuid.uuid4())

    st.session_state.sessions.append({
        "id": cid,
        "title": "New Chat",
        "messages": []
    })

    st.session_state.current = cid
    save()

def cur():
    for s in st.session_state.sessions:
        if s["id"] == st.session_state.current:
            return s

def api(url, data=None, files=None):

    try:
        r = requests.post(
            url,
            data=data,
            files=files,
            timeout=180
        )
        return r.json()

    except:
        return {}

# =====================================================
# INIT
# =====================================================
if "sessions" not in st.session_state:
    st.session_state.sessions = load()

if not st.session_state.sessions:
    st.session_state.sessions = []

if "current" not in st.session_state:
    new_chat()

if "delete_id" not in st.session_state:
    st.session_state.delete_id = ""

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

    for s in reversed(
        st.session_state.sessions[-20:]
    ):

        c1,c2 = st.columns([5,1])

        with c1:
            if st.button(
                s.get("title","Chat")[:26],
                key=f"open_{s['id']}",
                use_container_width=True
            ):
                st.session_state.current = s["id"]
                st.rerun()

        with c2:
            if st.button(
                "⋮",
                key=f"menu_{s['id']}",
                use_container_width=True
            ):
                st.session_state.delete_id = s["id"]

        if st.session_state.delete_id == s["id"]:

            if st.button(
                "Delete",
                key=f"del_{s['id']}",
                use_container_width=True
            ):

                st.session_state.sessions = [
                    x for x in
                    st.session_state.sessions
                    if x["id"] != s["id"]
                ]

                if st.session_state.sessions:
                    st.session_state.current = \
                    st.session_state.sessions[-1]["id"]
                else:
                    new_chat()

                st.session_state.delete_id = ""
                save()
                st.rerun()

# =====================================================
# CAREER CHAT
# =====================================================
if mode == "Career Chat":

    st.title("Career Chat")

    c = cur()

    for m in c["messages"]:

        box = "user" if \
        m["role"]=="user" else "bot"

        txt = format_answer(
            m["content"]
        ).replace("\n","<br>")

        st.markdown(
            f"<div class='{box}'>{txt}</div>",
            unsafe_allow_html=True
        )

    q = st.chat_input("Ask anything...")

    if q:

        c["messages"].append({
            "role":"user",
            "content":q
        })

        res = api(
            CHAT,
            {"question":q}
        )

        ans = format_answer(
            res.get(
                "answer",
                "No Answer"
            )
        )

        c["messages"].append({
            "role":"assistant",
            "content":ans
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

    f = st.file_uploader(
        "Upload Resume PDF",
        type=["pdf"]
    )

    txt = st.text_area(
        "Or Paste Resume",
        height=220
    )

    if st.button("Scan Resume"):

        files = None
        data = {}

        if f:
            files = {
                "file":(
                    f.name,
                    f.getvalue(),
                    "application/pdf"
                )
            }

        if txt.strip():
            data["resume_text"] = txt

        res = api(
            RESUME,
            data=data,
            files=files
        )

        if res:

            st.success(
                "Resume Analysis Complete"
            )

            for k,t in {

                "career_matches":
                "Recommended Careers",

                "skills_found":
                "Skills Found",

                "missing_skills":
                "Missing Skills",

                "suggestions":
                "Suggestions"

            }.items():

                if k in res:

                    st.subheader(t)

                    for i in res[k]:
                        st.write(
                            "•",
                            format_answer(i)
                        )

            if "summary" in res:

                st.subheader("Summary")

                st.info(
                    format_answer(
                        res["summary"]
                    )
                )

        else:
            st.error("Scan Failed")

# =====================================================
# ROADMAP
# =====================================================
else:

    st.title("Career Roadmap")

    name = st.text_input(
        "Enter Career Name"
    )

    if st.button("Generate Roadmap"):

        res = api(
            ROADMAP,
            {"career":name}
        )

        ans = format_answer(
            res.get("answer") or
            res.get("roadmap") or
            "No roadmap"
        ).replace("\\n","\n")

        st.text_area(
            "Roadmap",
            ans,
            height=520
        )

        c = cur()

        c["messages"].append({
            "role":"user",
            "content":
            f"Roadmap for {name}"
        })

        c["messages"].append({
            "role":"assistant",
            "content":ans
        })

        if c["title"] == "New Chat":
            c["title"] = f"Roadmap {name}"

        save()