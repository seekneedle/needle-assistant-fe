import streamlit as st
import requests
from requests.auth import HTTPBasicAuth
import json

# 定义API的URL和认证信息
API_URL = "http://127.0.0.1:8510/assistant/trainer"
SCORE_API_URL = "http://127.0.0.1:8510/assistant/trainer_score"
AUTH = HTTPBasicAuth('needle_assistant', 'needle_assistant')

# 初始化session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
if 'role' not in st.session_state:
    st.session_state.role = "medium"
if 'scored' not in st.session_state:
    st.session_state.scored = False

# 标题
st.title("Trainer")

# 选择role
role = st.selectbox("选择角色", ["easy", "medium", "hard"], index=["easy", "medium", "hard"].index(st.session_state.role))

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
        response = requests.post(API_URL, json=data, auth=AUTH)

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

# 评分按钮
if st.button("评分") and not st.session_state.scored:
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
if st.button("清除聊天历史"):
    st.session_state.messages = []
    st.session_state.scored = False
    st.rerun()