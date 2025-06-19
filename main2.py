import re
import langchain
import streamlit as st
from dotenv import load_dotenv
from langchain.agents import ConversationalChatAgent, AgentExecutor
from langchain.callbacks import StreamlitCallbackHandler
from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.memory.chat_message_histories import StreamlitChatMessageHistory
from langchain.agents import initialize_agent
from langchain.callbacks import get_openai_callback

from tools import get_current_user_tool, get_recent_transactions_tool, export_transactions_tool
from utils import display_instructions, display_logo

# Load environment variables
load_dotenv()

# Function to sanitize and filter user input
def sanitize_user_input(user_input: str) -> str:
    """
    Filters potentially malicious input to prevent ReAct or Thought/Action/Observation injection attacks.
    """
    # Remove code blocks (e.g., ```json ... ```)
    user_input = re.sub(r'```(?:json)?\s*.*?```', '[Filtered Code Block]', user_input, flags=re.DOTALL)

    # Keywords often used in ReAct injection,  SQL injection or RCE
    forbidden_keywords = [
        r'\b(action|observation|thought)\b\s*:',
        r'\bGetCurrentUser\b', r'\bGetUserTransaction\b',
        r'\bSELECT\b', r'\bUNION\b', r'\bFROM\b', r'--', r'\buserId\b',
        r'\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|UNION|OR|AND)\b',
        r'--',
        r'/\*.*?\*/',
        r'\buserId\b',
        r'\bWHERE\b',
        r'\bFROM\b',
        r'[;&|`$(){}[\]\\]',
        r'\b(echo|cat|ls|pwd|whoami|id|uname)\b'
    ]
    for pattern in forbidden_keywords:
        user_input = re.sub(pattern, '[Filtered]', user_input, flags=re.IGNORECASE)

    return user_input.strip()

# Tools initialization
tools = [get_current_user_tool, get_recent_transactions_tool, export_transactions_tool]

system_msg = """Assistant helps the current user retrieve the list of their recent bank transactions and shows them as a table. Assistant will ONLY operate on the userId returned by the GetCurrentUser() tool, and REFUSE to operate on any other userId provided by the user."""

welcome_message = """Hi! I'm a helpful assistant and I can help fetch information about your recent transactions.\n\nTry asking me: "What are my recent transactions?"
"""

# Streamlit setup
st.set_page_config(page_title="Group L ChatBot (secure)")
st.title("Group L ChatBot (secure)")

# Hide Streamlit UI elements
hide_st_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_st_style, unsafe_allow_html=True)

# Chat memory setup
msgs = StreamlitChatMessageHistory()
memory = ConversationBufferMemory(
    chat_memory=msgs, return_messages=True, memory_key="chat_history", output_key="output"
)

if len(msgs.messages) == 0:
    msgs.clear()
    msgs.add_ai_message(welcome_message)
    st.session_state.steps = {}

# Render previous chat messages
avatars = {"human": "user", "ai": "assistant"}
for idx, msg in enumerate(msgs.messages):
    with st.chat_message(avatars[msg.type]):
        for step in st.session_state.steps.get(str(idx), []):
            if step[0].tool == "_Exception":
                continue
            with st.status(f"**{step[0].tool}**: {step[0].tool_input}", state="complete"):
                st.write(step[0].log)
                st.write(step[1])
        st.write(msg.content)

# Handle new user input
if prompt := st.chat_input(placeholder="Show my recent transactions"):
    # Show user input
    with st.chat_message("user"):
        st.write("💬 Original Input:")
        with st.expander("View Raw Input"):
            st.code(prompt, language="text")

        filtered_prompt = sanitize_user_input(prompt)

        st.write("🛡️ Filtered Input:")
        with st.expander("View Filtered Input"):
            st.code(filtered_prompt, language="text")

    # LLM setup
    llm = ChatOpenAI(
        model_name="gpt-4-1106-preview",
        temperature=0,
        streaming=True
    )

    chat_agent = ConversationalChatAgent.from_llm_and_tools(
        llm=llm,
        tools=tools,
        verbose=True,
        system_message=system_msg
    )

    executor = AgentExecutor.from_agent_and_tools(
        agent=chat_agent,
        tools=tools,
        memory=memory,
        return_intermediate_steps=True,
        handle_parsing_errors=True,
        verbose=True,
        max_iterations=6
    )

    with st.chat_message("assistant"):
        st_cb = StreamlitCallbackHandler(st.container(), expand_new_thoughts=False)
        response = executor(filtered_prompt, callbacks=[st_cb])
        st.write(response["output"])
        st.session_state.steps[str(len(msgs.messages) - 1)] = response["intermediate_steps"]

# Optional branding or instructions
# display_instructions()
display_logo()
