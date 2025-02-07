import os
import yaml
import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import json
import logging
import sys

# Create a custom handler that writes to stderr
class StderrHandler(logging.StreamHandler):
    def __init__(self):
        super().__init__(sys.stderr)

    def format(self, record):
        # Customize the log format if needed
        return f"{record.levelname}: {record.getMessage()}"

# Configure logging
logger = logging.getLogger(__name__)
logger.handlers.clear()
logger.setLevel(logging.INFO)

# Add the custom handler
handler = StderrHandler()
logger.addHandler(handler)
logger.propagate = False

# 定义API的URL和认证信息
# Load configuration
def load_config(env=None):
    with open('config.yaml', 'r') as file:
        config = yaml.safe_load(file)
    
    # Use environment variable or default
    env = env or os.getenv('NEEDLE_ENV', config['default_environment'])
    return config['environments'][env]

# Get configuration
config = load_config()
API_URL = config['api_url']
SCORE_API_URL = config['score_api_url']
AUTH = HTTPBasicAuth('needle_assistant', 'needle_assistant')

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'role' not in st.session_state:
    st.session_state.role = "medium"
if 'scored' not in st.session_state:
    st.session_state.scored = False
if 'start_button_disabled' not in st.session_state:
    st.session_state.start_button_disabled = False
# 标题
st.title("Trainer")

# 选择role
role = st.selectbox("选择角色", ["easy", "medium", "hard"], index=["easy", "medium", "hard"].index(st.session_state.role))

col1, col2, col3 = st.columns(3)
# 开始按钮
with col1: 
    if st.button("开始", disabled=st.session_state.start_button_disabled):
        st.session_state.messages.append({"role": "assistant", "content": "你好！"})
        st.session_state.start_button_disabled = True
        st.rerun()

# 评分按钮
with col2:
    if st.button("评分") and not st.session_state.scored:
        st.session_state.start_button_disabled = False
        # 这里假设评分接口是另一个API，你可以根据实际情况修改
        data = {
            "messages": st.session_state.messages
        }
        score_response = requests.post(SCORE_API_URL, auth=AUTH, json=data)
        assistant_response = ""

        for line in score_response.iter_lines():
            if line:
                decoded_line = line.decode('utf-8')
                if decoded_line.startswith("data:"):
                    json_data = json.loads(decoded_line[5:])
                    if json_data["code"] == 200 and json_data["status"] == "success":
                        assistant_response += json_data["data"]["content"]

        st.success(f"评分结果: {assistant_response}")
        st.session_state.scored = True

# 清除聊天历史按钮
with col3:
    if st.button("清除聊天历史"):
        st.session_state.start_button_disabled = False
        st.session_state.messages = []
        st.session_state.scored = False
        st.rerun()

# 如果role发生变化，清除聊天历史
if role != st.session_state.role:
    st.session_state.messages = []
    st.session_state.role = role
    st.session_state.scored = False

# 显示聊天历史
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# 如果已经评分，不允许继续输入
if st.session_state.scored:
    st.warning("已评分，无法继续对话。")
else:
    # 用户输入
    if prompt := st.chat_input("请输入您的问题"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 调用API
        data = {
            "messages": st.session_state.messages,
            "role": st.session_state.role
        }
        logger.info("sending " + str(data) + "to " + API_URL)
        response = requests.post(API_URL, json=data, auth=AUTH)
        logger.info(str(response))
        # 处理流式响应
        assistant_response = ""
        with st.chat_message("assistant"):
            placeholder = st.empty()
            for line in response.iter_lines():
                if line:
                    decoded_line = line.decode('utf-8')
                    if decoded_line.startswith("data:"):
                        json_data = json.loads(decoded_line[5:])
                        if json_data["code"] == 200 and json_data["status"] == "success":
                            assistant_response += json_data["data"]["content"]
                            placeholder.markdown(assistant_response)

        st.session_state.messages.append({"role": "assistant", "content": assistant_response})
