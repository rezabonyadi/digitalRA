import streamlit as st
import openai
import tiktoken

def load_chat_page(user_logo, ra_image, chat_mdl):
    st.markdown("""# Chat with your Research Assistant""")
    st.markdown("""Hello there!
Your RA has read through lots of articles and is ready for you to chat with.
""")
    researcher_spec = st.session_state['researcher_spec']
    concated_data = st.session_state['concated_data'] 
    idea_text_summary = st.session_state['research_summary']

    if "chat_history" not in st.session_state:
        chat_data = [{'role': 'system', "content": 
                    f"""{researcher_spec} 
                    
                    You are my research assistant. 
                    
                    Here are some articles: 
                    
                    {concated_data} 
                    
                    Here is an idea I have I want to research on: {idea_text_summary}"""}]
        
        st.session_state.chat_history = chat_data
    
    cost = 0
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    user_input = st.chat_input("Digital assistant")
    # Redraw chat history with the new messages (in reverse order)
    for message in st.session_state.chat_history:
        if message['role'] == 'system':
            continue        
        avtr = user_logo if message['role']=='user' else ra_image

        with st.chat_message(message['role'], avatar=avtr):
            st.markdown(message['content'])

    # Handle user input
    if user_input:
        st.session_state.chat_history.append({
                    "role": "user",
                    "content": user_input
                })
        with st.chat_message("user", avatar=user_logo):
            st.markdown(user_input)           
        
        request_data = {"messages": st.session_state.chat_history}
        response = openai.ChatCompletion.create(model=chat_mdl, messages=st.session_state.chat_history)

        chatbot_reply = response['choices'][0]['message']['content']

        with st.chat_message("assistant", avatar=ra_image):
            st.markdown(chatbot_reply)              
        
        st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": chatbot_reply
                })
        
        
        user_input = ""