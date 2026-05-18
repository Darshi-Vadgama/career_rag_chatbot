# ui/streamlit_app.py

import streamlit as st
import streamlit.components.v1 as components
import requests

BASE_URL   = "http://backend:8000"
CAREER_API = f"{BASE_URL}/career-search"
AUTH_URL   = f"{BASE_URL}/auth"
CHATS_URL  = f"{BASE_URL}/chats"

st.set_page_config(page_title="Career AI", layout="wide")

# ── Session defaults ──────────────────────────────────────────────────────────

for key, val in {
    "messages":             [],
    "theme":                "light",
    "processing":           False,
    "access_token":         None,
    "refresh_token":        None,
    "user_id":              None,
    "username":             None,
    "current_chat_id":      None,
    "chat_list":            [],
    "voice_input":          "",
    "last_voice_processed": "",   # prevents re-processing same voice input on rerun
    "voice_pending":        "",   # holds voice text waiting to be processed next rerun
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ── Theme ─────────────────────────────────────────────────────────────────────

def apply_theme():
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        html, body, [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > div,
        [data-testid="stMain"], [data-testid="stMainBlockContainer"],
        .stApp, .main, .block-container {
            background-color: #1e1f22 !important; color: #dcdcdc !important;
        }
        [data-testid="stHeader"] {
            background-color: #1e1f22 !important;
            border-bottom: 1px solid #2e2f33 !important;
        }
        [data-testid="stBottom"], [data-testid="stBottom"] > div,
        footer, footer * {
            background-color: #1e1f22 !important; color: #dcdcdc !important;
            border-top: 1px solid #2e2f33 !important;
        }
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background-color: #27282c !important;
            border-right: 1px solid #2e2f33 !important;
        }
        section[data-testid="stSidebar"] * { color: #dcdcdc !important; }
        [data-testid="stChatMessage"] {
            background-color: #2a2b2f !important;
            border: 1px solid #35363b !important;
            border-radius: 10px !important; color: #dcdcdc !important;
        }
        [data-testid="stChatInputContainer"],
        [data-testid="stChatInputContainer"] > div,
        [data-testid="stChatInputContainer"] > div > div,
        div[class*="stChatInput"],
        div[class*="chatInputContainer"] {
            background-color: #27282c !important;
            border-top: 1px solid #2e2f33 !important;
        }
        [data-testid="stChatInputContainer"] textarea,
        div[class*="stChatInput"] textarea {
            background-color: #2a2b2f !important; color: #dcdcdc !important;
            border: 1px solid #3a3b40 !important; border-radius: 10px !important;
            caret-color: #dcdcdc !important;
        }
        [data-testid="stChatInputContainer"] textarea::placeholder { color: #7a7b80 !important; }
        [data-testid="stChatInputContainer"] button,
        [data-testid="stChatInputContainer"] button svg {
            background-color: #2a2b2f !important; color: #dcdcdc !important;
            fill: #dcdcdc !important;
        }
        [data-testid="stTextInput"] input {
            background-color: #2a2b2f !important; color: #dcdcdc !important;
            border: 1px solid #3a3b40 !important;
        }
        [data-testid="stButton"] > button {
            background-color: #2a2b2f !important; color: #dcdcdc !important;
            border: 1px solid #3a3b40 !important;
        }
        [data-testid="stButton"] > button:hover {
            background-color: #35363b !important; border-color: #5c5d63 !important;
        }
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] p,
        [data-testid="stRadio"] span { color: #dcdcdc !important; }
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] code { color: #dcdcdc !important; }
        [data-testid="stFileUploader"] {
            background-color: #2a2b2f !important;
            border: 1px dashed #3a3b40 !important; color: #dcdcdc !important;
        }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #1e1f22; }
        ::-webkit-scrollbar-thumb { background: #3a3b40; border-radius: 4px; }
        </style>
        """, unsafe_allow_html=True)
    else:
        st.markdown("""
        <style>
        html, body, [data-testid="stAppViewContainer"],
        [data-testid="stAppViewContainer"] > div,
        [data-testid="stMain"], [data-testid="stMainBlockContainer"],
        .stApp, .main, .block-container {
            background-color: #ffffff !important; color: #1a1a1a !important;
        }
        [data-testid="stHeader"] {
            background-color: #ffffff !important;
            border-bottom: 1px solid #e5e5e5 !important;
        }
        [data-testid="stBottom"], [data-testid="stBottom"] > div,
        footer, footer * {
            background-color: #ffffff !important; color: #1a1a1a !important;
            border-top: 1px solid #e5e5e5 !important;
        }
        section[data-testid="stSidebar"],
        section[data-testid="stSidebar"] > div {
            background-color: #f7f7f8 !important;
            border-right: 1px solid #e5e5e5 !important;
        }
        section[data-testid="stSidebar"] * { color: #1a1a1a !important; }
        [data-testid="stChatMessage"] {
            background-color: #f7f7f8 !important;
            border: 1px solid #e5e5e5 !important;
            border-radius: 10px !important; color: #1a1a1a !important;
        }
        [data-testid="stChatInputContainer"],
        [data-testid="stChatInputContainer"] > div,
        [data-testid="stChatInputContainer"] > div > div {
            background-color: #ffffff !important;
            border-top: 1px solid #e5e5e5 !important;
        }
        [data-testid="stChatInputContainer"] textarea {
            background-color: #f7f7f8 !important; color: #1a1a1a !important;
            border: 1px solid #d9d9d9 !important; border-radius: 10px !important;
        }
        [data-testid="stChatInputContainer"] textarea::placeholder { color: #9a9a9a !important; }
        [data-testid="stTextInput"] input {
            background-color: #ffffff !important; color: #1a1a1a !important;
            border: 1px solid #d9d9d9 !important;
        }
        [data-testid="stButton"] > button {
            background-color: #f0f0f0 !important; color: #1a1a1a !important;
            border: 1px solid #d9d9d9 !important;
        }
        [data-testid="stButton"] > button:hover { background-color: #e5e5e5 !important; }
        [data-testid="stRadio"] label,
        [data-testid="stRadio"] p,
        [data-testid="stRadio"] span { color: #1a1a1a !important; }
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] h1,
        [data-testid="stMarkdownContainer"] h2,
        [data-testid="stMarkdownContainer"] h3,
        [data-testid="stMarkdownContainer"] h4,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] code { color: #1a1a1a !important; }
        [data-testid="stFileUploader"] {
            background-color: #ffffff !important;
            border: 1px dashed #d9d9d9 !important; color: #1a1a1a !important;
        }
        ::-webkit-scrollbar { width: 5px; }
        ::-webkit-scrollbar-track { background: #f7f7f8; }
        ::-webkit-scrollbar-thumb { background: #d0d0d0; border-radius: 4px; }
        </style>
        """, unsafe_allow_html=True)

apply_theme()

# ── Patch Streamlit iframe to allow microphone ────────────────────────────────
st.markdown("""
<script>
(function patchIframes() {
    function allow(iframe) {
        if (!iframe.allow || !iframe.allow.includes('microphone')) {
            iframe.allow = (iframe.allow ? iframe.allow + '; ' : '') + 'microphone';
        }
    }
    document.querySelectorAll('iframe').forEach(allow);
    new MutationObserver(function(mutations) {
        mutations.forEach(function(m) {
            m.addedNodes.forEach(function(n) {
                if (n.tagName === 'IFRAME') allow(n);
                if (n.querySelectorAll) n.querySelectorAll('iframe').forEach(allow);
            });
        });
    }).observe(document.body, { childList: true, subtree: true });
})();
</script>
""", unsafe_allow_html=True)


# ── STT Component ─────────────────────────────────────────────────────────────

def stt_component():
    """
    Renders mic button using components.html.
    Returns transcript string when user clicks Send, else None.
    """
    result = components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; font-family: sans-serif; }
  body { padding: 8px; background: transparent; }

  .row { display: flex; align-items: center; gap: 12px; margin-bottom: 8px; }

  #micBtn {
    width: 44px; height: 44px; border-radius: 50%;
    background: #4CAF50; color: white; border: none;
    font-size: 20px; cursor: pointer;
    box-shadow: 0 2px 6px rgba(0,0,0,0.2);
    flex-shrink: 0;
  }
  #micBtn.on { background: #f44336; }

  #status { font-size: 13px; color: #666; }

  #transcript {
    display: none;
    padding: 8px 12px;
    border: 1px solid #4CAF50;
    border-radius: 8px;
    background: #f0fff0;
    font-size: 14px;
    color: #222;
    margin-bottom: 6px;
    min-height: 32px;
  }

  .btnrow { display: none; gap: 8px; }

  .sendbtn {
    padding: 7px 18px; background: #1976D2; color: #fff;
    border: none; border-radius: 8px; cursor: pointer; font-size: 13px;
  }
  .clrbtn {
    padding: 7px 14px; background: #aaa; color: #fff;
    border: none; border-radius: 8px; cursor: pointer; font-size: 13px;
  }
</style>
</head>
<body>

<div class="row">
  <button id="micBtn" onclick="toggle()">🎤</button>
  <span id="status">Click 🎤 to speak &nbsp;(Chrome / Edge only)</span>
</div>

<div id="transcript"></div>

<div class="btnrow" id="btnrow">
  <button class="sendbtn" onclick="send()">➤ Send</button>
  <button class="clrbtn"  onclick="clr()">✖ Clear</button>
</div>

<script>
var rec   = null;
var on    = false;
var final = '';

function toggle() { on ? stop() : start(); }

function start() {
  var SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    document.getElementById('status').innerText = '❌ Use Chrome or Edge';
    document.getElementById('status').style.color = 'red';
    return;
  }
  rec = new SR();
  rec.lang           = 'en-IN';
  rec.continuous     = true;
  rec.interimResults = true;
  on    = true;
  final = '';

  document.getElementById('micBtn').className = 'on';
  document.getElementById('micBtn').innerText = '⏹';
  document.getElementById('status').innerText = '🔴 Listening... click ⏹ to stop';
  document.getElementById('status').style.color = '#f44336';
  document.getElementById('transcript').style.display = 'block';
  document.getElementById('transcript').innerText = '';
  document.getElementById('btnrow').style.display = 'none';

  rec.onresult = function(e) {
    var interim = '';
    for (var i = e.resultIndex; i < e.results.length; i++) {
      if (e.results[i].isFinal) final += e.results[i][0].transcript + ' ';
      else interim += e.results[i][0].transcript;
    }
    document.getElementById('transcript').innerText = final + interim;
  };

  rec.onerror = function(e) {
    document.getElementById('status').innerText = '❌ ' + e.error;
    document.getElementById('status').style.color = 'red';
    reset();
  };

  rec.onend = function() { if (on) reset(); };
  rec.start();
}

function stop() { if (rec) rec.stop(); reset(); }

function reset() {
  on = false;
  document.getElementById('micBtn').className = '';
  document.getElementById('micBtn').innerText = '🎤';
  if (final.trim()) {
    document.getElementById('status').innerText = '✅ Done! Click Send.';
    document.getElementById('status').style.color = 'green';
    document.getElementById('btnrow').style.display = 'flex';
  } else {
    document.getElementById('status').innerText = 'Click 🎤 to speak (Chrome / Edge only)';
    document.getElementById('status').style.color = '#666';
  }
}

function send() {
  var t = final.trim();
  if (!t) return;
  // send transcript to Streamlit parent
  window.parent.postMessage({ type: 'streamlit:setComponentValue', value: t }, '*');
  document.getElementById('transcript').innerText = '✅ Sent: ' + t;
  document.getElementById('btnrow').style.display = 'none';
  document.getElementById('status').innerText = 'Click 🎤 to speak (Chrome / Edge only)';
  document.getElementById('status').style.color = '#666';
  final = '';
}

function clr() {
  final = '';
  document.getElementById('transcript').style.display = 'none';
  document.getElementById('transcript').innerText = '';
  document.getElementById('btnrow').style.display = 'none';
  document.getElementById('status').innerText = 'Click 🎤 to speak (Chrome / Edge only)';
  document.getElementById('status').style.color = '#666';
}
</script>
</body>
</html>
""", height=160)
    return result


# ── Token helpers ─────────────────────────────────────────────────────────────

def do_refresh() -> bool:
    try:
        res = requests.post(
            f"{AUTH_URL}/refresh",
            json={
                "user_id":       st.session_state.user_id,
                "refresh_token": st.session_state.refresh_token,
            },
            timeout=10,
        )
        if res.status_code == 200:
            data = res.json()
            st.session_state.access_token  = data["access_token"]
            st.session_state.refresh_token = data["refresh_token"]
            return True
        return False
    except Exception:
        return False


def auth_headers() -> dict:
    return {"Authorization": f"Bearer {st.session_state.access_token}"}


def clear_session():
    st.session_state.access_token        = None
    st.session_state.refresh_token       = None
    st.session_state.user_id             = None
    st.session_state.username            = None
    st.session_state.messages            = []
    st.session_state.current_chat_id     = None
    st.session_state.chat_list           = []
    st.session_state.voice_input         = ""
    st.session_state.last_voice_processed = ""
    st.session_state.voice_pending        = ""


def post_stream(endpoint: str, **kwargs):
    res = requests.post(
        endpoint, headers=auth_headers(),
        stream=True, timeout=120, **kwargs
    )
    if res.status_code == 401:
        if do_refresh():
            res = requests.post(
                endpoint, headers=auth_headers(),
                stream=True, timeout=120, **kwargs
            )
        else:
            clear_session()
            st.error("Session expired. Please login again.")
            st.rerun()
    return res


def api_get(endpoint: str):
    res = requests.get(endpoint, headers=auth_headers(), timeout=10)
    if res.status_code == 401:
        if do_refresh():
            res = requests.get(endpoint, headers=auth_headers(), timeout=10)
        else:
            clear_session()
            st.rerun()
    return res


def api_post(endpoint: str, json_data: dict):
    res = requests.post(endpoint, headers=auth_headers(), json=json_data, timeout=10)
    if res.status_code == 401:
        if do_refresh():
            res = requests.post(endpoint, headers=auth_headers(), json=json_data, timeout=10)
        else:
            clear_session()
            st.rerun()
    return res


def api_delete(endpoint: str):
    res = requests.delete(endpoint, headers=auth_headers(), timeout=10)
    if res.status_code == 401:
        if do_refresh():
            res = requests.delete(endpoint, headers=auth_headers(), timeout=10)
    return res


# ── Chat helpers ──────────────────────────────────────────────────────────────

def load_chat_list():
    try:
        res = api_get(f"{CHATS_URL}/{st.session_state.user_id}")
        if res.status_code == 200:
            st.session_state.chat_list = res.json()
    except Exception:
        st.session_state.chat_list = []


def start_new_chat():
    try:
        res = api_post(f"{CHATS_URL}/new", {"user_id": st.session_state.user_id})
        if res.status_code == 200:
            chat = res.json()
            st.session_state.current_chat_id = chat["id"]
            st.session_state.messages        = []
            load_chat_list()
    except Exception as e:
        st.error(f"Could not create new chat: {str(e)}")


def load_chat(chat_id: str):
    try:
        res = api_get(f"{CHATS_URL}/{chat_id}/messages")
        if res.status_code == 200:
            st.session_state.messages        = res.json()
            st.session_state.current_chat_id = chat_id
    except Exception as e:
        st.error(f"Could not load chat: {str(e)}")


def persist_message(role: str, content: str):
    if st.session_state.current_chat_id:
        try:
            api_post(f"{CHATS_URL}/message", {
                "chat_id": st.session_state.current_chat_id,
                "role":    role,
                "content": content,
            })
        except Exception:
            pass


def auto_title(question: str):
    if st.session_state.current_chat_id:
        try:
            api_post(f"{CHATS_URL}/title", {
                "chat_id": st.session_state.current_chat_id,
                "title":   question[:50],
            })
            load_chat_list()
        except Exception:
            pass


# ── Auth page ─────────────────────────────────────────────────────────────────

def show_auth_page():
    st.title("💼 Career AI")
    st.markdown("---")

    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])

        with tab1:
            st.subheader("Welcome back!")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")

            if st.button("Login", use_container_width=True, key="login_btn"):
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    try:
                        res = requests.post(
                            f"{AUTH_URL}/login",
                            json={"username": username, "password": password},
                            timeout=10,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.access_token  = data["access_token"]
                            st.session_state.refresh_token = data["refresh_token"]
                            st.session_state.user_id       = data["user_id"]
                            st.session_state.username      = data["username"]
                            load_chat_list()
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Login failed"))
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")

        with tab2:
            st.subheader("Create account")
            new_user = st.text_input("Username", key="signup_user")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            confirm  = st.text_input("Confirm Password", type="password", key="signup_confirm")

            if st.button("Sign Up", use_container_width=True, key="signup_btn"):
                if not new_user or not new_pass or not confirm:
                    st.error("Please fill in all fields")
                elif new_pass != confirm:
                    st.error("Passwords do not match")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    try:
                        res = requests.post(
                            f"{AUTH_URL}/register",
                            json={"username": new_user, "password": new_pass},
                            timeout=10,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state.access_token  = data["access_token"]
                            st.session_state.refresh_token = data["refresh_token"]
                            st.session_state.user_id       = data["user_id"]
                            st.session_state.username      = data["username"]
                            load_chat_list()
                            st.rerun()
                        else:
                            st.error(res.json().get("detail", "Signup failed"))
                    except Exception as e:
                        st.error(f"Connection error: {str(e)}")


# ── Main app ──────────────────────────────────────────────────────────────────

def show_main_app():

    st.sidebar.title("🚀 Career AI")
    st.sidebar.markdown(f"👤 **{st.session_state.username}**")
    st.sidebar.markdown("---")

    if st.sidebar.button("🌙 Toggle Dark/Light"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

    tool = st.sidebar.radio(
        "Select Tool",
        ["Career Chat", "Resume Scan", "Roadmap"]
    )

    if tool == "Career Chat":
        st.sidebar.markdown("---")

        if st.sidebar.button("➕ New Chat", use_container_width=True):
            start_new_chat()
            st.rerun()

        if st.session_state.chat_list:
            st.sidebar.markdown("**💬 Past Chats**")
            for chat in st.session_state.chat_list:
                chat_id    = chat["id"]
                title      = chat["title"] or "New Chat"
                created_at = chat["created_at"][:10]
                col1, col2 = st.sidebar.columns([4, 1])
                with col1:
                    is_active = chat_id == st.session_state.current_chat_id
                    btn_label = f"**{title}**" if is_active else title
                    if st.button(f"{btn_label}\n{created_at}", key=f"chat_{chat_id}", use_container_width=True):
                        load_chat(chat_id)
                        st.rerun()
                with col2:
                    if st.button("🗑", key=f"del_{chat_id}"):
                        api_delete(f"{CHATS_URL}/{chat_id}")
                        if st.session_state.current_chat_id == chat_id:
                            st.session_state.current_chat_id = None
                            st.session_state.messages        = []
                        load_chat_list()
                        st.rerun()

    st.sidebar.markdown("---")

    if st.sidebar.button("🚪 Logout"):
        try:
            requests.post(
                f"{AUTH_URL}/logout",
                json={"user_id": st.session_state.user_id, "refresh_token": st.session_state.refresh_token},
                timeout=5,
            )
        except Exception:
            pass
        clear_session()
        st.rerun()

    st.title(f"💼 {tool}")

    # ── Career Chat ───────────────────────────────────────────────────────────
    if tool == "Career Chat":

        if not st.session_state.current_chat_id:
            start_new_chat()

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # ── Voice input (Web Speech API → query param bridge → Streamlit) ──────
        # JS sets ?voice=<transcript> on the parent URL, which triggers a
        # Streamlit rerun and lets us read st.query_params["voice"].
        components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:sans-serif; }
  body { padding:6px 0; background:transparent; }
  .row { display:flex; align-items:center; gap:10px; margin-bottom:4px; }
  #micBtn {
    width:42px; height:42px; border-radius:50%;
    background:#4CAF50; color:#fff; border:none;
    font-size:20px; cursor:pointer;
    box-shadow:0 2px 5px rgba(0,0,0,.25); flex-shrink:0;
  }
  #micBtn.on { background:#f44336; }
  #status { font-size:13px; color:#666; }
  #preview {
    font-size:13px; color:#333; min-height:18px;
    padding:4px 8px; border-radius:6px;
    background:#f0fff0; border:1px solid #c8e6c9;
    display:none; margin-top:2px; word-break:break-word;
  }
</style>
</head>
<body>
<div class="row">
  <button id="micBtn" onclick="toggle()">🎤</button>
  <span id="status">Click 🎤 to speak (Chrome / Edge only)</span>
</div>
<div id="preview"></div>
<script>
var rec=null, on=false, final_t='';

function toggle(){ on ? stop() : start(); }

function start(){
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){ setStatus('❌ Use Chrome or Edge','red'); return; }
  rec=new SR(); rec.lang='en-IN'; rec.continuous=true; rec.interimResults=true;
  on=true; final_t='';
  document.getElementById('micBtn').className='on';
  document.getElementById('micBtn').innerText='⏹';
  setStatus('🔴 Listening… click ⏹ to stop','#f44336');
  document.getElementById('preview').style.display='block';
  document.getElementById('preview').innerText='';

  rec.onresult=function(e){
    var interim='';
    for(var i=e.resultIndex;i<e.results.length;i++){
      if(e.results[i].isFinal) final_t+=e.results[i][0].transcript+' ';
      else interim+=e.results[i][0].transcript;
    }
    document.getElementById('preview').innerText = final_t+interim;
  };
  rec.onerror=function(e){ setStatus('❌ '+e.error,'red'); reset(); };
  rec.onend=function(){ if(on) reset(); };
  rec.start();
}

function stop(){ if(rec) rec.stop(); reset(); }

function reset(){
  on=false;
  document.getElementById('micBtn').className='';
  document.getElementById('micBtn').innerText='🎤';
  var t=final_t.trim();
  if(t){
    setStatus('✅ Sending…','green');
    // Write transcript into parent URL as query param → triggers Streamlit rerun
    var url=new URL(window.parent.location.href);
    url.searchParams.set('voice', t);
    window.parent.history.pushState({}, '', url.toString());
    // Also fire Streamlit's internal rerun via postMessage (belt + suspenders)
    window.parent.postMessage({type:'streamlit:forceRerun'}, '*');
    document.getElementById('preview').innerText='✅ Sent: '+t;
    final_t='';
  } else {
    setStatus('Click 🎤 to speak (Chrome / Edge only)','#666');
    document.getElementById('preview').style.display='none';
  }
}

function setStatus(msg,color){
  var s=document.getElementById('status');
  s.innerText=msg; s.style.color=color||'#666';
}
</script>
</body>
</html>
""", height=90)

        # Read voice transcript from query params (set by JS above)
        qp_voice = st.query_params.get("voice", "")
        if qp_voice and qp_voice.strip() and qp_voice != st.session_state.last_voice_processed:
            # Clear the query param immediately so it won't re-trigger
            st.query_params.clear()
            voice_text = qp_voice.strip()
            st.session_state.last_voice_processed = voice_text
            st.session_state.processing = True
            st.session_state.messages.append({"role": "user", "content": voice_text})
            persist_message("user", voice_text)
            if len(st.session_state.messages) == 1:
                auto_title(voice_text)
            st.rerun()

        # ── Normal text input ─────────────────────────────────────────────────
        user_input = st.chat_input(
            "Please wait..." if st.session_state.processing else "Ask your career question...",
            disabled=st.session_state.processing
        )

        if user_input and not st.session_state.processing:
            st.session_state.processing = True
            st.session_state.messages.append({"role": "user", "content": user_input})
            persist_message("user", user_input)
            if len(st.session_state.messages) == 1:
                auto_title(user_input)
            st.rerun()

        # ── Stream response (handles both text input and voice input) ──────────
        if st.session_state.processing:
            last_user_message = next(
                (m["content"] for m in reversed(st.session_state.messages) if m["role"] == "user"),
                None
            )
            if last_user_message:
                with st.chat_message("assistant"):
                    placeholder = st.empty()
                    full_text   = ""
                    try:
                        res = post_stream(
                            CAREER_API,
                            data={"question": last_user_message, "session_id": st.session_state.current_chat_id}
                        )
                        for chunk in res.iter_content(chunk_size=1024):
                            if chunk:
                                full_text += chunk.decode("utf-8")
                                placeholder.markdown(full_text)
                    except Exception as e:
                        full_text = f"❌ Error: {str(e)}"
                        placeholder.markdown(full_text)

                    st.session_state.messages.append({"role": "assistant", "content": full_text})
                    persist_message("assistant", full_text)
                    st.session_state.processing = False
                    st.rerun()

    # ── Resume Scan ───────────────────────────────────────────────────────────
    elif tool == "Resume Scan":
        st.subheader("📄 Upload Resume")
        uploaded_file = st.file_uploader("Upload PDF or Text Resume")
        if uploaded_file:
            if st.button("Analyze Resume"):
                try:
                    files  = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    res    = post_stream(CAREER_API, files=files)
                    output, placeholder = "", st.empty()
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            output += chunk.decode("utf-8")
                            placeholder.markdown(output)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # ── Roadmap ───────────────────────────────────────────────────────────────
    elif tool == "Roadmap":
        st.subheader("🧭 Career Roadmap")
        career = st.text_input("Enter Career")
        if st.button("Generate Roadmap"):
            if not career:
                st.warning("Please enter a career")
            else:
                try:
                    res    = post_stream(CAREER_API, data={"question": f"roadmap for {career}"})
                    output, placeholder = "", st.empty()
                    for chunk in res.iter_content(chunk_size=1024):
                        if chunk:
                            output += chunk.decode("utf-8")
                            placeholder.markdown(output)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")


# ── Entry point ───────────────────────────────────────────────────────────────

if st.session_state.access_token:
    show_main_app()
else:
    show_auth_page()