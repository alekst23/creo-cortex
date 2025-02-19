import streamlit as st

from agent.main import MainAgent

from dotenv import load_dotenv
load_dotenv()

import logging
logging.basicConfig(level=logging.INFO)

class StreamlitApp:
    def __init__(self):
        self.agent = MainAgent()

    def run(self):
        st.title("Langchain Streamlit App")
        user_input = st.text_area("Input your message here:")
        if st.button("Submit"):
            response = self.agent.generate_response(user_input)
            st.write(response)


if __name__ == '__main__':
    if 'app' not in st.session_state:
        logging.info("\n\n>> Creating new app\n\n")
        st.session_state.app = StreamlitApp()
    st.session_state.app.run()