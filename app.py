import streamlit as st
from openai import OpenAI
import json
import os
import shutil
import glob
from datetime import datetime

# ==================== 页面配置 ====================
st.set_page_config(page_title="我的小手机", page_icon="📱", layout="wide")

# ==================== 默认参数 ====================
DEFAULT_SETTINGS = {
    "model": "deepseek-reasoner",
    "temperature": 0.7,
    "top_p": 0.9,
    "max_tokens": 2000,
    "system_prompt": "你是一个温柔的聊天助手，回答简洁友好。",
    "auto_save": True
}

SETTINGS_FILE = "my_settings.json"
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            return {**DEFAULT_SETTINGS, **json.load(f)}
    return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=2)

settings = load_settings()

# ==================== 聊天记录 ====================
HISTORY_FILE = "chat_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_history(messages):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

def export_history(format_type):
    messages = st.session_state.messages
    if format_type == "TXT":
        return "\n\n".join([f"{m['role']}: {m['content']}" for m in messages if m['role'] != 'system'])
    elif format_type == "JSON":
        return json.dumps([m for m in messages if m['role'] != 'system'], ensure_ascii=False, indent=2)
    return ""

# ==================== CSS ====================
def apply_css():
    st.markdown("""
    <style>
        [data-testid="stChatMessageAvatar"] { display: none !important; }
        
        .stChatMessage {
            background-color: transparent !important;
            padding: 0 !important;
            margin: 0 !important;
        }
        
        .message-row {
            display: flex;
            flex-direction: column;
            margin-bottom: 16px;
            width: 100%;
        }
        
        .message-row.user { align-items: flex-end; }
        .message-row.assistant { align-items: flex-start; }
        
        .bubble {
            max-width: 80%;
            padding: 8px 12px;
            border-radius: 18px;
            font-size: 14px;
            line-height: 1.4;
            background-color: #e9ecef;
            color: #111111;
        }
        
        .timestamp {
            font-size: 10px;
            color: #999;
            margin-top: 4px;
        }
        
        .message-row.user .timestamp { text-align: right; margin-right: 4px; }
        .message-row.assistant .timestamp { text-align: left; margin-left: 4px; }
        
        .stChatInput input { border-radius: 24px !important; }
        
        h1 { font-size: 22px !important; margin-bottom: 16px !important; }
        
        .stExpander {
            background-color: #f5f5f5;
            border-radius: 12px;
            margin-bottom: 8px;
        }
        
        .loading-dots::after {
            content: "...";
            animation: dots 1.5s steps(4, end) infinite;
            display: inline-block;
            width: 0px;
            overflow: visible;
        }
        @keyframes dots {
            0%, 20% { content: ""; }
            40% { content: "."; }
            60% { content: ".."; }
            80%, 100% { content: "..."; }
        }
    </style>
    """, unsafe_allow_html=True)

apply_css()

# ==================== 侧边栏 ====================
with st.sidebar:
    st.markdown("## ⚙️ 设置")
    
    with st.expander("🤖 模型参数", expanded=True):
        settings["model"] = st.selectbox("模型", ["deepseek-reasoner", "deepseek-chat"])
        settings["temperature"] = st.slider("创造力", 0.0, 2.0, settings["temperature"], 0.05)
        settings["top_p"] = st.slider("多样性", 0.0, 1.0, settings["top_p"], 0.05)
        settings["max_tokens"] = st.slider("回复长度", 500, 4000, settings["max_tokens"], 100)
    
    with st.expander("💬 系统提示词", expanded=False):
        settings["system_prompt"] = st.text_area("AI角色设定", settings["system_prompt"], height=100)
    
    with st.expander("💾 数据管理", expanded=False):
        settings["auto_save"] = st.toggle("自动保存", settings["auto_save"])
        
        backup_name_input = st.text_input("📝 备份名称", placeholder="留空则自动生成", key="backup_name_input")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📁 备份当前", use_container_width=True):
                if os.path.exists(HISTORY_FILE):
                    name = backup_name_input.strip()[:30] if backup_name_input.strip() else datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_name = f"chat_history_{name}.json"
                    counter = 1
                    while os.path.exists(backup_name):
                        backup_name = f"chat_history_{name}_{counter}.json"
                        counter += 1
                    shutil.copy(HISTORY_FILE, backup_name)
                    st.toast(f"已备份到 {backup_name}", icon="✅")
                    st.session_state.backup_name_input = ""
                    st.rerun()
                else:
                    st.toast("没有聊天记录可备份", icon="⚠️")
        with col2:
            if st.button("✨ 新建对话", use_container_width=True):
                if os.path.exists(HISTORY_FILE) and len(st.session_state.messages) > 0:
                    name = backup_name_input.strip()[:30] if backup_name_input.strip() else datetime.now().strftime('%Y%m%d_%H%M%S')
                    backup_name = f"chat_history_{name}.json"
                    counter = 1
                    while os.path.exists(backup_name):
                        backup_name = f"chat_history_{name}_{counter}.json"
                        counter += 1
                    shutil.copy(HISTORY_FILE, backup_name)
                    st.toast(f"已备份到 {backup_name}", icon="📦")
                st.session_state.messages = []
                if settings["auto_save"]:
                    save_history([])
                st.toast("已创建新对话", icon="✨")
                st.session_state.backup_name_input = ""
                st.rerun()
        
        st.markdown("---")
        st.markdown("### 📜 对话历史")
        backup_files = glob.glob("chat_history_*.json")
        backup_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        
        if backup_files:
            for f in backup_files:
                display_name = f.replace("chat_history_", "").replace(".json", "")
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    if st.button(f"📄 {display_name}", key=f"load_{f}", use_container_width=True):
                        shutil.copy(f, HISTORY_FILE)
                        with open(HISTORY_FILE, 'r', encoding='utf-8') as f_load:
                            st.session_state.messages = json.load(f_load)
                        st.toast(f"已加载 {display_name}", icon="📂")
                        st.rerun()
                with col_b:
                    if st.button("🗑️", key=f"del_{f}", help="删除此备份"):
                        os.remove(f)
                        st.toast(f"已删除 {display_name}", icon="🗑️")
                        st.rerun()
        else:
            st.caption("暂无历史记录，新建对话时输入名称即可备份")
        
        st.markdown("---")
        
        if st.button("导出当前对话"):
            fmt = st.radio("格式", ["TXT", "JSON"], horizontal=True, key="export_fmt")
            content = export_history(fmt)
            st.download_button(
                label="下载",
                data=content,
                file_name=f"chat_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{fmt.lower()}",
                mime="text/plain"
            )
    
    if st.button("💾 保存设置", use_container_width=True):
        save_settings(settings)
        st.toast("设置已保存", icon="✅")
    
    st.markdown("---")
    if st.button("🗑️ 清空对话", use_container_width=True):
        st.session_state.messages = []
        if settings["auto_save"]:
            save_history([])
        st.rerun()

# ==================== API客户端 ====================
client = OpenAI(
    api_key="sk-f4fef2aca66a441d86e9da16959b8cbb",
    base_url="https://api.deepseek.com"
)

# ==================== 初始化 ====================
if "messages" not in st.session_state:
    loaded = load_history()
    st.session_state.messages = loaded if loaded else []

if settings["system_prompt"] and not any(m.get("role") == "system" for m in st.session_state.messages):
    st.session_state.messages.insert(0, {"role": "system", "content": settings["system_prompt"]})

# ==================== 标题 ====================
st.title("📱 我的小手机")

# ==================== 显示聊天记录 ====================
for idx, msg in enumerate(st.session_state.messages):
    if msg["role"] == "system":
        continue
    
    role_class = "user" if msg["role"] == "user" else "assistant"
    time_str = msg["timestamp"] if "timestamp" in msg else datetime.now().strftime("%H:%M")
    
    if msg["role"] == "user":
        col1, col2 = st.columns([1, 10])
        with col1:
            if st.button("🗑️", key=f"del_user_{idx}", help="删除本条"):
                st.session_state.messages.pop(idx)
                if settings["auto_save"]:
                    save_history(st.session_state.messages)
                st.rerun()
        with col2:
            st.markdown(f"""
            <div class="message-row user">
                <div class="bubble">{msg["content"]}</div>
                <div class="timestamp">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        col1, col2 = st.columns([10, 1])
        with col1:
            if msg.get("reasoning"):
                with st.expander("💭 思考过程"):
                    st.markdown(msg["reasoning"])
            st.markdown(f"""
            <div class="message-row assistant">
                <div class="bubble">{msg["content"]}</div>
                <div class="timestamp">{time_str}</div>
            </div>
            """, unsafe_allow_html=True)
        with col2:
            if st.button("🗑️", key=f"del_ai_{idx}", help="删除本条"):
                st.session_state.messages.pop(idx)
                if settings["auto_save"]:
                    save_history(st.session_state.messages)
                st.rerun()

# ==================== 聊天输入 ====================
if prompt := st.chat_input("说点什么..."):
    current_time = datetime.now().strftime("%H:%M")
    
    st.markdown(f"""
    <div class="message-row user">
        <div class="bubble">{prompt}</div>
        <div class="timestamp">{current_time}</div>
    </div>
    """, unsafe_allow_html=True)
    
    st.session_state.messages.append({
        "role": "user", 
        "content": prompt,
        "timestamp": current_time
    })
    
    loading_placeholder = st.empty()
    loading_placeholder.markdown("""
    <div class="message-row assistant">
        <div class="bubble" style="opacity: 0.7;"><span class="loading-dots">正在思考</span></div>
    </div>
    """, unsafe_allow_html=True)
    
    try:
        response = client.chat.completions.create(
            model=settings["model"],
            messages=st.session_state.messages,
            temperature=settings["temperature"],
            top_p=settings["top_p"],
            max_tokens=settings["max_tokens"]
        )
        
        reply = response.choices[0].message.content
        
        reasoning = ""
        if hasattr(response.choices[0].message, 'reasoning_content'):
            reasoning = response.choices[0].message.reasoning_content
        elif hasattr(response.choices[0].message, 'reasoning'):
            reasoning = response.choices[0].message.reasoning
        
        loading_placeholder.empty()
        
        if reasoning:
            with st.expander("💭 思考过程"):
                st.markdown(reasoning)
        
        st.markdown(f"""
        <div class="message-row assistant">
            <div class="bubble">{reply}</div>
            <div class="timestamp">{datetime.now().strftime("%H:%M")}</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.session_state.messages.append({
            "role": "assistant", 
            "content": reply,
            "reasoning": reasoning if reasoning else "",
            "timestamp": datetime.now().strftime("%H:%M")
        })
        
        if settings["auto_save"]:
            save_history(st.session_state.messages)
        
        st.rerun()
    except Exception as e:
        loading_placeholder.empty()
        st.error(f"出错了：{e}")

if settings["auto_save"] and st.session_state.messages:
    save_history(st.session_state.messages)