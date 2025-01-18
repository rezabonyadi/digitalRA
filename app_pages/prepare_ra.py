
import streamlit as st
from utils import operations

def load_prepare_ra_page():
    st.markdown("""# Prepare your Research Assistant""")
    st.markdown("""Here, you will prepare your RA for the research to be done. The RA needs to perform internet search. To do so, it will generate some search phrases. 
5. Click on "Research" once ready.""")
    st.divider()

    st.markdown("""## Generate summary
Here, you will generate a summary of your research idea. 
CLick on "Generate summary" to get a summary of your research proposal. Double check to ensure all main points have been covered. Modify it if needed.
You can revise the summary.
    """)
    ############# Genrate summary
    button_generate_summary = st.button('Generate summary')

    if button_generate_summary:

        idea_text_summary = operations.get_idea_summary(st.session_state['idea_text'], st.session_state['short_context_model'], 
                                                st.session_state['researcher_spec'] )
        print('Digital RA> Here is a summary of your idea: \n', idea_text_summary)

        with open(st.session_state['working_dir'] + 'idea_summary.txt', 'w') as f:
            f.write('Idea: \n\n')
            f.write(st.session_state['idea_text'])
            f.write('\n\n idea summary:\n\n')
            f.write(idea_text_summary)

        st.toast('Digital RA> your cost so far: ' + str(st.session_state['short_context_model'].get_current_cost()))
        st.toast('Digital RA> Saved the results to '+st.session_state['working_dir']+'/file idea_summary.txt.')
        st.session_state['research_summary'] = idea_text_summary

    st.session_state['research_summary'] = st.text_area('Here is your research summary:', st.session_state['research_summary'])

    st.divider()
    st.markdown("""## Generate search phrases
Here, you will generate search phrases for your research proposal.
Click on "Generate search phrases" to get the search phrases.
You can modify the search phrases if needed.
Click on "Research" on the left menue once ready.
                """)
    number_serach_phrases = st.slider('Number of search phrases', min_value=2, max_value=10, value=5)

    # ############### Generate search phrases
    button_generate_search_phrases = st.button('Generate search phrases')

    if button_generate_search_phrases:
        researcher_spec = st.session_state['researcher_spec'] 
        
        search_phrases = operations.extract_search_phrases(st.session_state['working_dir'], st.session_state['idea_text'], st.session_state['short_context_model'], 
                                                      researcher_spec, number_serach_phrases)

        print('Here are search phrases I suggest: ', search_phrases)
        st.session_state['search_phrases'] = search_phrases

        with open(st.session_state['working_dir'] + 'search_phrases.txt', 'w') as f:
            f.write('\n'.join(search_phrases))
        st.toast('Digital RA> your cost so far: '+ str(st.session_state['short_context_model'].get_current_cost()))
        st.toast('Digital RA> Saved the results to '+st.session_state['working_dir']+'/file search_phrases.txt.')

    search_phrases = st.text_area('Here are my suggested search phrases:', '\n'.join(st.session_state['search_phrases']))
    st.session_state['search_phrases'] = search_phrases.split('\n')
