import streamlit as st
import glob
from myagent import Agent, LlamaCPP, LlamaPrompt
import asyncio
import os

MODEL_PATH = './models'
model_list = glob.glob(os.path.join(MODEL_PATH, '*.gguf'))
server_path = [
    './run_server.py'
]

if "loop" not in st.session_state:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        print('LOOP CREATED')
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    st.session_state.loop = loop

if "messages" not in st.session_state:
    st.session_state.messages = []

if "agent" not in st.session_state:
    st.session_state.agent = None

if "llm_param" not in st.session_state:
    st.session_state.llm_param = {}

def generate_response(user_input):
    response_list = st.session_state.loop.run_until_complete(st.session_state.agent.chat(user_input, **st.session_state.llm_param))
    return response_list
    
st.subheader("🛠️ LLM Parameters")

model_name = st.selectbox(
    "LLM Model",
    list(map(lambda x:os.path.basename(x), model_list)),
)

col1, col2 = st.columns([0.5, 0.5])
with col1:
    temp = st.number_input("temperature", value=0.8)
    max_tokens = st.number_input("max_tokens", value=1024)
    top_p = st.number_input("top_p", value=0.95)

with col2:
    min_p = st.number_input("min_p", value=0.05)
    frequency_penalty = st.number_input("frequency_penalty", value=0.0)
    repeat_penalty = st.number_input("repeat_penalty", value=1.0)

st.session_state.llm_param['temperature'] = temp
st.session_state.llm_param['max_tokens'] = max_tokens
st.session_state.llm_param['top_p'] = top_p
st.session_state.llm_param['min_p'] = min_p
st.session_state.llm_param['frequency_penalty'] = frequency_penalty
st.session_state.llm_param['repeat_penalty'] = repeat_penalty

if st.button("Load", use_container_width=True):
    if not st.session_state.agent:
        model_path = os.path.join(MODEL_PATH, model_name)
        model = LlamaCPP.from_path(model_path)
        prompt = LlamaPrompt()

        agent = Agent(name="knowledge-agent", model=model, prompt=prompt)

        for path in server_path:
            agent.register_mcp(path=path)

        st.session_state.loop.run_until_complete(agent.init_agent())

        st.session_state.agent = agent

with st.container():
    agent = st.session_state.agent
    agent_name = f"`{agent.name}`" if agent else ""
    model_name = f"`{agent.model_name}`" if agent else ""
    status = '🟢 Ready' if agent else '🔴 Not Ready'
    server_list_html = "\n".join([f"\t- `{server_name}`" for server_name in agent.server_list]) if agent else ""

    tool_info = []
    if agent:
        for server_name, func_info in agent.mcp_manager.tool_info.items():
            tool_info.append(f"- **{server_name}**\n" + "\n".join([f"\t- `{tool_name}` : {description.strip()}" for tool_name, description in func_info.items()]))

    tool_info = '\n'.join(tool_info)

    st.subheader("🛠️ Agent Information")

    col1, col2 = st.columns([0.4,0.6])
    with col1:
        st.markdown(f"""
        - **Agent**: {agent_name}
        - **Model**: {model_name}
        - **Status**: {status}
        - **MCP Server**:
        {server_list_html}
        
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        {tool_info}
        """)

st.divider()

#Chat display
for i, msg in enumerate(st.session_state.messages):
    role = msg["role"]
    content = msg["content"]

    if role == "user":
        st.chat_message("user").markdown(content)
    else:
        st.chat_message("assistant").markdown(content)

# Chat input
if user_input := st.chat_input("Type your message...", disabled=False if st.session_state.agent else True):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.chat_message("user").markdown(user_input)

    # Generate response
    with st.spinner("Generating Response ..."):
        response_list = generate_response(user_input)

    for response in response_list:
        if response.type == 'text':
            content = response.data
            st.session_state.messages.append({"role": "assistant", "content": content})
            st.chat_message("assistant").markdown(content)

        elif response.type == 'tool-calling':
            content = f"tool calling ...\n```\n{response.data}\n```"
            st.session_state.messages.append({"role": "assistant", "content": content})
            st.chat_message("assistant").markdown(content)
        
        elif response.type == 'tool-result':
            content = f"```json\n{response.data}\n```"
            st.session_state.messages.append({"role": "assistant", "content": content})
            st.chat_message("assistant").markdown(content)
