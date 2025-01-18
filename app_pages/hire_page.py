
import streamlit as st
from utils import operations

def load_hire_page():
    st.markdown("""# Hire your Research Assistant""")
    st.markdown("""Hello there!
                
Welcome to the first step of Digital Research Assistant. 
""")
    
    st.divider()

    st.markdown("""## Describe your research idea
                
In this step, you describe your research proposal and click "Hire your RA". 
I will "hire" a research assistant for you with expertiese you will need to make that proposal a success.""")

    st.session_state['idea_text'] = st.text_area('Explain your research in a paragraph', st.session_state['idea_text'])

    button_generate_RA_character = st.button('Hire your RA')
    if button_generate_RA_character:
        
        print(st.session_state['idea_text'])
        researcher_spec = operations.get_research_assistant(st.session_state['idea_text'], st.session_state['short_context_model'])
        st.toast('Cost> your cost so far: ' + str(st.session_state['short_context_model'].get_current_cost()))
        
        st.session_state['researcher_spec'] = researcher_spec
    st.divider()

    st.markdown("""## Your RA Competencies
You will see the competence of the RA in the box below. You can revise the comptence, add to it, etc.
It is important to make sure the RA has the right competencies to perform the research.
Click on "Prepare" in the left menue once you are ready with your RA.
""")
    st.session_state['researcher_spec'] = st.text_area('Here is a descriotion of your RA: ', st.session_state['researcher_spec'])
    st.info('You can modify the competencies of the RA here.')