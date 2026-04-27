# ui/streamlit_app.py
# FINAL POLISHED VERSION
# Career Chat + Resume Scan + Roadmap
# Fixed resume ugly JSON output
# Mode isolation + Delete toggle + Multi query

import streamlit as st
import requests, json, os, uuid, re

BASE = "http://backend:8000"
CHAT = f"{BASE}/career-search"
ROADMAP = f"{BASE}/career-roadmap"
RESUME = f"{BASE}/resume-scan"
FILE = "chat_history.json"

st.set_page_config(page_title="Career AI", layout="wide")

# =====================================================
# STYLE
# =====================================================
st.markdown("""
<style>
html,body,[class*="css"]{
background:#0b1020;
color:white;
}

section[data-testid="stSidebar"]{
background:#151515;
}

.user,.bot{
padding:14px;
border-radius:12px;
margin:10px 0;
font-size:17px;
line-height:1.7;
}

.user{
background:#1e1e1e;
}

.bot{
background:#0d0d0d;
border-left:4px solid #18e6c3;
}

.stButton button{
border-radius:10px;
font-size:16px !important;
}

.stChatInput input,
.stTextInput input,
textarea{
font-size:17px !important;
}
</style>
""", unsafe_allow_html=True)

# =====================================================
# HELPERS
# =====================================================
def clean(t):
    if not t:
        return ""
    t = str(t)
    t = re.sub(r"[\U00010000-\U0010ffff]", "", t)
    for x in ["###","##","#","**","__","`"]:
        t = t.replace(x, "")
    t = t.replace("- ", "• ").replace("* ", "• ")
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

def get_chat(cid):
    for s in st.session_state.sessions:
        if s["id"] == cid:
            return s

def new_chat(mode):
    cid = str(uuid.uuid4())

    st.session_state.sessions.append({
        "id": cid,
        "mode": mode,
        "title": "New Chat",
        "messages": []
    })

    st.session_state.current = cid
    save()

def split_query(q):
    parts = re.split(
        r"\band\b|\balso\b|\&",
        q,
        flags=re.I
    )
    parts = [x.strip() for x in parts if x.strip()]
    return parts if len(parts) > 1 else [q]

# =====================================================
# SESSION
# =====================================================
if "sessions" not in st.session_state:
    st.session_state.sessions = load()

if "current" not in st.session_state:
    st.session_state.current = ""

if "delete_id" not in st.session_state:
    st.session_state.delete_id = ""

# =====================================================
# SIDEBAR
# =====================================================
with st.sidebar:

    st.title("Career AI")

    mode = st.radio(
        "Choose Tool",
        ["Career Chat","Resume Scan","Roadmap"]
    )

    cur = get_chat(st.session_state.current)

    if not cur or cur["mode"] != mode:

        found = None

        for s in reversed(st.session_state.sessions):
            if s["mode"] == mode:
                found = s["id"]
                break

        if found:
            st.session_state.current = found
        else:
            new_chat(mode)

        st.rerun()

    if st.button("New Chat"):
        new_chat(mode)
        st.rerun()

    st.markdown("### Saved Chats")

    chats = [
        x for x in st.session_state.sessions
        if x["mode"] == mode
    ]

    for s in reversed(chats[-20:]):

        c1, c2 = st.columns([5,1])

        with c1:
            if st.button(
                s["title"][:28],
                key="open_"+s["id"],
                use_container_width=True
            ):
                st.session_state.current = s["id"]
                st.session_state.delete_id = ""
                st.rerun()

        with c2:
            if st.button(
                "⋮",
                key="menu_"+s["id"],
                use_container_width=True
            ):
                if st.session_state.delete_id == s["id"]:
                    st.session_state.delete_id = ""
                else:
                    st.session_state.delete_id = s["id"]
                st.rerun()

        if st.session_state.delete_id == s["id"]:
            if st.button(
                "Delete",
                key="del_"+s["id"],
                use_container_width=True
            ):
                st.session_state.sessions = [
                    x for x in st.session_state.sessions
                    if x["id"] != s["id"]
                ]

                remain = [
                    x for x in st.session_state.sessions
                    if x["mode"] == mode
                ]

                st.session_state.delete_id = ""

                if remain:
                    st.session_state.current = remain[-1]["id"]
                else:
                    new_chat(mode)

                save()
                st.rerun()

chat = get_chat(st.session_state.current)

# =====================================================
# CAREER CHAT
# =====================================================
if mode == "Career Chat":

    st.title("Career Chat")

    for m in chat["messages"]:
        cls = "user" if m["role"] == "user" else "bot"

        st.markdown(
            f"<div class='{cls}'>{clean(m['content']).replace(chr(10),'<br>')}</div>",
            unsafe_allow_html=True
        )

    q = st.chat_input("Ask anything...")

    if q:

        chat["messages"].append({
            "role":"user",
            "content":q
        })

        out = []

        for part in split_query(q):
            res = api(CHAT, {"question":part})
            out.append(clean(res.get("answer","No Answer")))

        ans = "\n\n".join(out)

        chat["messages"].append({
            "role":"assistant",
            "content":ans
        })

        if chat["title"] == "New Chat":
            chat["title"] = q[:35]

        save()
        st.rerun()

# =====================================================
# ROADMAP
# =====================================================
elif mode == "Roadmap":

    st.title("Career Roadmap")

    name = st.text_input("Enter Career Name")

    if st.button("Generate Roadmap"):

        chat["messages"].append({
            "role":"user",
            "content":f"Roadmap for {name}"
        })

        res = api(
            ROADMAP,
            {"career":name}
        )

        ans = clean(
            res.get("answer") or
            res.get("roadmap") or
            "No Roadmap"
        )

        chat["messages"].append({
            "role":"assistant",
            "content":ans
        })

        if chat["title"] == "New Chat":
            chat["title"] = f"Roadmap {name}"

        save()
        st.rerun()

    for m in chat["messages"]:
        cls = "user" if m["role"] == "user" else "bot"

        st.markdown(
            f"<div class='{cls}'>{clean(m['content']).replace(chr(10),'<br>')}</div>",
            unsafe_allow_html=True
        )

# =====================================================
# RESUME
# =====================================================
else:

    st.title("Resume Scan")

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

        msg = ""

        titles = {
            "career_matches":"Recommended Careers",
            "skills_found":"Skills Found",
            "missing_skills":"Missing Skills",
            "suggestions":"Suggestions"
        }

        for k,t in titles.items():

            if k in res and res[k]:

                msg += t + "\n"

                for i in res[k]:
                    msg += f"• {i}\n"

                msg += "\n"

        if "summary" in res:
            msg += "Summary\n"
            msg += clean(res["summary"])

        chat["messages"].append({
            "role":"assistant",
            "content":msg or "No Result"
        })

        if chat["title"] == "New Chat":
            chat["title"] = "Resume Scan"

        save()
        st.rerun()

    for m in chat["messages"]:

        st.markdown(
            f"<div class='bot'>{clean(m['content']).replace(chr(10),'<br>')}</div>",
            unsafe_allow_html=True
        )