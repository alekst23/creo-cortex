import os, sys
import streamlit as st

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if src_path not in sys.path:
    sys.path.insert(0, src_path)

from agent.main import MainAgent
from agent.session_memory import get_session_memory


class StreamlitApp:
    def __init__(self):
        # Set page config at the very beginning
        if 'setup_complete' not in st.session_state:
            st.set_page_config(
                page_title="CREO-CORTEX",
                page_icon="⭐",
                layout="wide",  # This makes the app use the full width
                initial_sidebar_state="expanded"
            )
                
            self.state = st.session_state
            self.state.session_id="abc1234"
            self.mem = st.session_state.memory = get_session_memory(self.state.session_id)
            self.state.messages = self.clean_messages(self.mem.get_messages())
            self.agent = MainAgent(self.mem)
            self.state.setup_complete = True

    def clean_messages(self, messages):
        return [dict(role=msg["role"], content=msg["content"]) for msg in messages]

    def run(self):
        st.title("CREO-CORTEX")
        st.subheader("An assistant for building and deploying cloud applications.")
        st.markdown("<sup>streamlit | langchain | langgraph ReAct</sup>", unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            user_input = st.text_area("Input your message here:")
            st.markdown("<sup>CMD+ENTER to submit</sup>", unsafe_allow_html=True)
            if user_input:
                st.session_state.messages.append(dict(role="user", content=user_input))

                response = self.agent.generate_response(st.session_state.messages[-10:])
                st.session_state.messages.append(dict(role="assistant", content=response))

                self.mem.add_message("user", user_input)
                self.mem.add_message("assistant", response)

            with st.container(height=600):
                for msg in st.session_state.messages:
                    role = msg.get("role", "system")
                    prefix = "🐒 *user*: " if role == "user" else "⭐ agent: "
                    st.write(f"{prefix} {msg['content']}")
                        

        with col2:
            st.subheader("Notes")
            for note in st.session_state.memory.get_notes():
                st.markdown(f"### (note id: {note['id']})\n{note['text']}")
            st.text(st.session_state.memory.get_notes())


if __name__ == '__main__':
    if 'app' not in st.session_state:
        logging.info("\n\n>> Creating new app\n\n")
        st.session_state.app = StreamlitApp()
    st.session_state.app.run()