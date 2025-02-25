import os, sys
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from agent.main import MainAgent, MODEL_BOOST
from agent.session_memory import get_session_memory

CONVERSATION_LENGTH=50

class StreamlitApp:
    def __init__(self):
        # Set page config at the very beginning
        if 'setup_complete' not in st.session_state:
            st.set_page_config(
                page_title="CREO-CORTEX",
                page_icon="⭐",
                layout="wide",
                initial_sidebar_state="expanded"
            )
            logging.info(f">>> params: {st.query_params}")
            session_id = st.query_params.get("session_id", "default")
            logging.info(f">>> session_id: {session_id}")
            logging.info(f">>> debug: {session_id=='abc1234'}")
            
            # Initialize session state
            self.state = st.session_state
            self.load_session(session_id)
            # self.state.session_id = session_id
            # self.mem = st.session_state.memory = get_session_memory(self.state.session_id)
            # self.state.messages = self.clean_messages(self.mem.get_messages())
            # self.agent = MainAgent(self.mem)
            self.state.boost_option = False
            self.state.setup_complete = True
            
            # Initialize input state
            if 'user_input' not in self.state:
                self.state.user_input = ""
    
    def load_session(self, session_id):
        logging.info(f">>> loading session: {session_id}")
        self.state.session_id = session_id
        self.mem = st.session_state.memory = get_session_memory(self.state.session_id)
        self.state.messages = self.clean_messages(self.mem.get_messages())
        self.agent = MainAgent(self.mem)

    def clean_messages(self, messages):
        return [dict(role=msg["role"], content=msg["content"]) for msg in messages]

    def handle_submit(self):
        if self.state.user_input.strip():
            user_input = self.state.user_input
            self.state.messages.append(dict(role="user", content=user_input))

            response = self.agent.generate_response(self.state.messages[-CONVERSATION_LENGTH:])
            self.state.messages.append(dict(role="assistant", content=response))

            self.mem.add_message("user", user_input)
            self.mem.add_message("assistant", response)
            
            # Clear the input after processing
            self.state.user_input = ""

    def run(self):
        col1, col2 = st.columns(2)
        with col1:
            st.title("CREO-CORTEX")
            st.subheader("An assistant for building and deploying cloud applications.")
            st.markdown("<sup>streamlit | langchain | langgraph ReAct</sup>", unsafe_allow_html=True)
        with col2:
            if new_session_id := st.text_input("session_id", self.state.session_id):
                if new_session_id != self.state.session_id:
                    self.load_session(new_session_id)
                    st.rerun()
            
            if st.button(f"toggle boost: {self.mem.get_boost_state()}"):
                self.mem.set_boost_state(not self.mem.get_boost_state())
                st.rerun()

        col1, col2 = st.columns(2)
        with col1:
            user_input = st.text_area(
                "Input your message here (Use TAB+ENTER to submit):",
                key="input_area"
            )
            
            # Update session state
            self.state.user_input = user_input
            
            if st.button("Submit"):
                self.handle_submit()

            with st.popover("all chat history"):
                for msg in self.state.messages:
                    role = msg.get("role", "system")
                    prefix = "🐒 *user*: " if role == "user" else "⭐ agent: "
                    st.write(f"{prefix} {msg['content']}")
                    
            with st.container(height=600):
                for msg in self.state.messages[:-CONVERSATION_LENGTH:-1]:
                    role = msg.get("role", "system")
                    prefix = "🐒 *user*: " if role == "user" else "⭐ agent: "
                    st.write(f"{prefix} {msg['content']}")

        with col2:
            st.subheader("Goal")
            st.markdown(self.mem.get_goal())

            st.subheader("Tasks")
            for task in self.mem.get_tasks():
                st.markdown(f"{task['sort_order']}) [{task['status']}] {task['task']}\n{task.get('result', '')}")

            st.subheader("Working Directory")
            if new_working_dir := st.text_input("path", self.mem.get_working_dir()):
                if new_working_dir != self.mem.get_working_dir():
                    self.mem.set_working_dir(new_working_dir)
                    st.rerun()

            st.subheader("Open Files")
            for file in self.mem.get_open_files():
                st.markdown(f"File: {file['file_path']}")

            st.subheader("Notes")
            for note in self.mem.get_notes():
                st.markdown(f"(note id: {note['_id']})\n{note['note']}")


if __name__ == '__main__':
    if 'app' not in st.session_state:
        logging.info("\n\n>> Creating new app\n\n")
        st.session_state.app = StreamlitApp()
    st.session_state.app.run()