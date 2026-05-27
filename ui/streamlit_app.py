import streamlit as st
import streamlit.components.v1 as components
import requests
import time

BASE_URL    = "http://backend:8000"
CAREER_API  = f"{BASE_URL}/career-search"
ROADMAP_API = f"{BASE_URL}/roadmap"
RESUME_API  = f"{BASE_URL}/resume-scan"
AUTH_URL    = f"{BASE_URL}/auth"
CHATS_URL   = f"{BASE_URL}/chats"

st.set_page_config(page_title="Career AI", layout="wide")

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
    "last_voice_processed": "",
    "pending_question":     "",
    "voice_counter":        0, 
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

def apply_theme():
    dark = st.session_state.theme == "dark"
    bg   = "#1e1f22" if dark else "#ffffff"
    bg2  = "#2a2b2f" if dark else "#f7f7f8"
    bg3  = "#27282c" if dark else "#f7f7f8"
    txt  = "#dcdcdc" if dark else "#1a1a1a"
    bdr  = "#2e2f33" if dark else "#e5e5e5"
    bdr2 = "#3a3b40" if dark else "#d9d9d9"
    st.markdown(f"""<style>
    html,body,[data-testid="stAppViewContainer"],[data-testid="stAppViewContainer"]>div,
    [data-testid="stMain"],[data-testid="stMainBlockContainer"],.stApp,.main,.block-container{{
        background-color:{bg}!important;color:{txt}!important;}}
    [data-testid="stHeader"]{{background-color:{bg}!important;border-bottom:1px solid {bdr}!important;}}
    [data-testid="stBottom"],[data-testid="stBottom"]>div,footer,footer *{{
        background-color:{bg}!important;color:{txt}!important;border-top:1px solid {bdr}!important;}}
    section[data-testid="stSidebar"],section[data-testid="stSidebar"]>div{{
        background-color:{bg3}!important;border-right:1px solid {bdr}!important;}}
    section[data-testid="stSidebar"] *{{color:{txt}!important;}}
    [data-testid="stChatMessage"]{{background-color:{bg2}!important;border:1px solid {bdr}!important;border-radius:10px!important;color:{txt}!important;}}
    [data-testid="stChatInputContainer"],[data-testid="stChatInputContainer"]>div,
    [data-testid="stChatInputContainer"]>div>div{{background-color:{bg}!important;border-top:1px solid {bdr}!important;}}
    [data-testid="stChatInputContainer"] textarea{{background-color:{bg2}!important;color:{txt}!important;border:1px solid {bdr2}!important;border-radius:10px!important;}}
    [data-testid="stTextInput"] input{{background-color:{bg2}!important;color:{txt}!important;border:1px solid {bdr2}!important;}}
    [data-testid="stButton"]>button{{background-color:{bg2}!important;color:{txt}!important;border:1px solid {bdr2}!important;}}
    [data-testid="stButton"]>button:hover{{background-color:{bg3}!important;}}
    [data-testid="stRadio"] label,[data-testid="stRadio"] p,[data-testid="stRadio"] span{{color:{txt}!important;}}
    [data-testid="stMarkdownContainer"] *{{color:{txt}!important;}}
    [data-testid="stFileUploader"]{{background-color:{bg2}!important;border:1px dashed {bdr2}!important;color:{txt}!important;}}
    div.voice-hidden{{display:none!important;visibility:hidden!important;height:0!important;overflow:hidden!important;}}
    ::-webkit-scrollbar{{width:5px;}}::-webkit-scrollbar-track{{background:{bg};}}::-webkit-scrollbar-thumb{{background:{bdr2};border-radius:4px;}}
    </style>""", unsafe_allow_html=True)

apply_theme()

def stt_component():
    """
    Renders mic button. On Send, JS fills the Streamlit chat input
    and presses Enter — no page reload, session_state preserved.
    """
    components.html("""
<!DOCTYPE html>
<html>
<head>
<style>
  *{margin:0;padding:0;box-sizing:border-box;font-family:sans-serif;}
  body{padding:4px 0;background:transparent;}
  .row{display:flex;align-items:center;gap:10px;}
  #micBtn{width:40px;height:40px;border-radius:50%;background:#4CAF50;color:#fff;
    border:none;font-size:18px;cursor:pointer;box-shadow:0 2px 4px rgba(0,0,0,.2);flex-shrink:0;}
  #micBtn.on{background:#f44336;}
  #status{font-size:12px;color:#666;}
  #preview{font-size:12px;color:#333;padding:4px 8px;border-radius:5px;
    background:#f0fff0;border:1px solid #c8e6c9;display:none;
    margin-top:4px;word-break:break-word;}
  .btnrow{display:none;gap:6px;margin-top:4px;}
  .sendbtn{padding:5px 14px;background:#1976D2;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px;}
  .clrbtn{padding:5px 10px;background:#aaa;color:#fff;border:none;border-radius:6px;cursor:pointer;font-size:12px;}
</style>
</head>
<body>
<div class="row">
  <button id="micBtn" onclick="toggle()">🎤</button>
  <span id="status">Click 🎤 to speak (Chrome/Edge only)</span>
</div>
<div id="preview"></div>
<div class="btnrow" id="btnrow">
  <button class="sendbtn" onclick="send()">➤ Send Voice</button>
  <button class="clrbtn" onclick="clr()">✖ Clear</button>
</div>
<script>
var rec=null,on=false,final_t='';
function toggle(){on?stop():start();}
function start(){
  var SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){setStatus('❌ Chrome/Edge only','red');return;}
  rec=new SR();rec.lang='en-IN';rec.continuous=true;rec.interimResults=true;
  on=true;final_t='';
  document.getElementById('micBtn').className='on';
  document.getElementById('micBtn').innerText='⏹';
  setStatus('🔴 Listening… click ⏹ to stop','#f44336');
  document.getElementById('preview').style.display='block';
  document.getElementById('preview').innerText='';
  document.getElementById('btnrow').style.display='none';
  rec.onresult=function(e){
    var interim='';
    for(var i=e.resultIndex;i<e.results.length;i++){
      if(e.results[i].isFinal)final_t+=e.results[i][0].transcript+' ';
      else interim+=e.results[i][0].transcript;
    }
    document.getElementById('preview').innerText=final_t+interim;
  };
  rec.onerror=function(e){setStatus('❌ '+e.error,'red');reset();};
  rec.onend=function(){if(on)reset();};
  rec.start();
}
function stop(){if(rec)rec.stop();reset();}
function reset(){
  on=false;
  document.getElementById('micBtn').className='';
  document.getElementById('micBtn').innerText='🎤';
  if(final_t.trim()){
    setStatus('✅ Done! Click Send.','green');
    document.getElementById('btnrow').style.display='flex';
  } else {
    setStatus('Click 🎤 to speak (Chrome/Edge only)','#666');
    document.getElementById('preview').style.display='none';
  }
}
function send(){
  var t=final_t.trim();if(!t)return;
  setStatus('✅ Sending…','green');
  document.getElementById('btnrow').style.display='none';
  document.getElementById('preview').innerText='✅ Sent: '+t;
  final_t='';

  var doc=window.parent.document;

  // Find Streamlit chat textarea
  var textarea=doc.querySelector('textarea[data-testid="stChatInputTextArea"]');
  if(!textarea){
    var all=doc.querySelectorAll('textarea');
    for(var i=0;i<all.length;i++){
      if(all[i].offsetParent!==null){textarea=all[i];break;}
    }
  }

  // Step 1: Fill the chat textarea
  var textarea=doc.querySelector('textarea[data-testid="stChatInputTextArea"]');
  if(!textarea){
    var all=doc.querySelectorAll('textarea');
    for(var i=0;i<all.length;i++){if(all[i].offsetParent!==null){textarea=all[i];break;}}
  }
  if(textarea){
    textarea.focus();
    var setter=Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype,'value').set;
    setter.call(textarea,t);
    textarea.dispatchEvent(new Event('input',{bubbles:true}));
    textarea.dispatchEvent(new Event('change',{bubbles:true}));

    // Step 2: Wait for React to process value and re-enable button, then click
    var attempts=0;
    var interval=setInterval(function(){
      attempts++;
      var btn=doc.querySelector('button[data-testid="stChatInputSubmitButton"]');
      if(btn && !btn.disabled){
        clearInterval(interval);
        btn.click();
        setStatus('✅ Sent!','green');
      } else if(attempts>20){
        clearInterval(interval);
        // Final fallback: Enter key
        textarea.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',keyCode:13,which:13,bubbles:true,cancelable:true}));
        setStatus('✅ Sent (fallback)','green');
      }
    },100);
  } else {
    setStatus('❌ Input not found','red');
  }
  if(false){  // keep structure intact
  } else {
    setStatus('❌ Chat input not found','red');
  }
}
function clr(){
  final_t='';
  document.getElementById('preview').style.display='none';
  document.getElementById('preview').innerText='';
  document.getElementById('btnrow').style.display='none';
  setStatus('Click 🎤 to speak (Chrome/Edge only)','#666');
}
function setStatus(msg,color){
  var s=document.getElementById('status');
  s.innerText=msg;s.style.color=color||'#666';
}
</script>
</body>
</html>
""", height=110)
def do_refresh() -> bool:
    try:
        res = requests.post(
            f"{AUTH_URL}/refresh",
            json={"user_id": st.session_state.user_id,
                  "refresh_token": st.session_state.refresh_token},
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
    for k in ["access_token","refresh_token","user_id","username","current_chat_id"]:
        st.session_state[k] = None
    for k in ["messages","chat_list"]:
        st.session_state[k] = []
    for k in ["last_voice_processed","pending_question"]:
        st.session_state[k] = ""
    st.session_state.processing    = False
    st.session_state.voice_counter = 0


def post_stream(endpoint: str, **kwargs):
    res = requests.post(endpoint, headers=auth_headers(),
                        stream=True, timeout=180, **kwargs)
    if res.status_code == 401:
        if do_refresh():
            res = requests.post(endpoint, headers=auth_headers(),
                                stream=True, timeout=180, **kwargs)
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
            clear_session(); st.rerun()
    return res


def api_post(endpoint: str, json_data: dict):
    res = requests.post(endpoint, headers=auth_headers(),
                        json=json_data, timeout=10)
    if res.status_code == 401:
        if do_refresh():
            res = requests.post(endpoint, headers=auth_headers(),
                                json=json_data, timeout=10)
        else:
            clear_session(); st.rerun()
    return res


def api_delete(endpoint: str):
    res = requests.delete(endpoint, headers=auth_headers(), timeout=10)
    if res.status_code == 401:
        if do_refresh():
            res = requests.delete(endpoint, headers=auth_headers(), timeout=10)
    return res

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
        st.error(f"Could not create new chat: {e}")


def load_chat(chat_id: str):
    try:
        res = api_get(f"{CHATS_URL}/{chat_id}/messages")
        if res.status_code == 200:
            st.session_state.messages        = res.json()
            st.session_state.current_chat_id = chat_id
    except Exception as e:
        st.error(f"Could not load chat: {e}")


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
def do_stream_and_save(question: str):
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text   = ""
        try:
            res = post_stream(
                CAREER_API,
                data={"question": question,
                      "session_id": st.session_state.current_chat_id or ""},
            )
            if res.status_code not in (200, 201):
                full_text = f"❌ Backend error {res.status_code}: {res.text[:200]}"
            else:
                for chunk in res.iter_content(chunk_size=512):
                    if chunk:
                        full_text += chunk.decode("utf-8")
                        placeholder.markdown(full_text)
        except Exception as e:
            full_text = f"❌ Error: {str(e)}"
        if full_text:
            placeholder.markdown(full_text)

    st.session_state.messages.append({"role": "assistant", "content": full_text})
    persist_message("assistant", full_text)
    st.session_state.pending_question = ""
    st.session_state.processing       = False
    st.rerun()
def show_auth_page():
    st.title("💼 Career AI")
    st.markdown("---")
    _, col, _ = st.columns([1, 2, 1])
    with col:
        tab1, tab2 = st.tabs(["🔑 Login", "📝 Sign Up"])
        with tab1:
            st.subheader("Welcome back!")
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_pass")
            if st.button("Login", use_container_width=True):
                if not username or not password:
                    st.error("Please fill in all fields")
                else:
                    try:
                        res = requests.post(f"{AUTH_URL}/login",
                                            json={"username": username, "password": password},
                                            timeout=10)
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
                        st.error(f"Connection error: {e}")
        with tab2:
            st.subheader("Create account")
            new_user = st.text_input("Username", key="signup_user")
            new_pass = st.text_input("Password", type="password", key="signup_pass")
            confirm  = st.text_input("Confirm Password", type="password", key="signup_confirm")
            if st.button("Sign Up", use_container_width=True):
                if not new_user or not new_pass or not confirm:
                    st.error("Please fill in all fields")
                elif new_pass != confirm:
                    st.error("Passwords do not match")
                elif len(new_pass) < 6:
                    st.error("Password must be at least 6 characters")
                else:
                    try:
                        res = requests.post(f"{AUTH_URL}/register",
                                            json={"username": new_user, "password": new_pass},
                                            timeout=10)
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
                        st.error(f"Connection error: {e}")
def show_main_app():
    st.sidebar.title("🚀 Career AI")
    st.sidebar.markdown(f"👤 **{st.session_state.username}**")
    st.sidebar.markdown("---")

    if st.sidebar.button("🌙 Toggle Dark/Light"):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()

    tool = st.sidebar.radio("Select Tool", ["Career Chat", "Resume Scan", "Roadmap"])

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
                c1, c2 = st.sidebar.columns([4, 1])
                with c1:
                    label = f"**{title}**" if chat_id == st.session_state.current_chat_id else title
                    if st.button(f"{label}\n{created_at}", key=f"chat_{chat_id}", use_container_width=True):
                        load_chat(chat_id)
                        st.rerun()
                with c2:
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
            requests.post(f"{AUTH_URL}/logout",
                          json={"user_id": st.session_state.user_id,
                                "refresh_token": st.session_state.refresh_token},
                          timeout=5)
        except Exception:
            pass
        clear_session()
        st.rerun()

    st.title(f"💼 {tool}")
    if tool == "Career Chat":

        if not st.session_state.current_chat_id:
            start_new_chat()
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        if st.session_state.pending_question and st.session_state.processing:
            do_stream_and_save(st.session_state.pending_question)
            return
        stt_component()
        user_input = st.chat_input(
            "Please wait..." if st.session_state.processing else "Ask your career question...",
            disabled=st.session_state.processing,
        )

        if user_input and not st.session_state.processing:
            st.session_state.processing       = True
            st.session_state.pending_question = user_input
            st.session_state.messages.append({"role": "user", "content": user_input})
            persist_message("user", user_input)
            if len(st.session_state.messages) == 1:
                auto_title(user_input)
            st.rerun()
    elif tool == "Resume Scan":
        st.subheader("📄 Upload Resume")
        uploaded_file = st.file_uploader("Upload PDF or Text Resume")
        if uploaded_file:
            if st.button("Analyze Resume"):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                    res   = post_stream(RESUME_API, files=files)
                    output, placeholder = "", st.empty()
                    for chunk in res.iter_content(chunk_size=512):
                        if chunk:
                            output += chunk.decode("utf-8")
                            placeholder.markdown(output)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    elif tool == "Roadmap":
        st.subheader("🧭 Career Roadmap Generator")
        career = st.text_input("Enter Career (e.g. Neurosurgeon, Data Scientist, IAS Officer)")
        if st.button("Generate Roadmap"):
            if not career.strip():
                st.warning("Please enter a career name")
            else:
                try:
                    res    = post_stream(ROADMAP_API, data={"career": career.strip()})
                    output, placeholder = "", st.empty()
                    for chunk in res.iter_content(chunk_size=512):
                        if chunk:
                            output += chunk.decode("utf-8")
                            placeholder.markdown(output)
                except Exception as e:
                    st.error(f"❌ Error: {e}")
if st.session_state.access_token:
    show_main_app()
else:
    show_auth_page()