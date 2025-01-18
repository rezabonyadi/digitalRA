
import streamlit as st
from utils import operations
import pandas as pd

def load_write_review_page():

    st.markdown("""# Write the litrature review""")
    st.markdown("""Here, the RA is going to write the litrature review for you based on the papers selected in the previous step. 
1. Pay attention to the RA message on the estimated cost. 
2. Pick the length of the litrature review.
3. Click on "Write litrature review".
4. In case of any issue, try "Renew connection"."
             """)
    st.divider()
    # Write the litrature review
    working_dir = st.session_state['working_dir']
    long_context_model = st.session_state['long_context_model']
    researcher_spec = st.session_state['researcher_spec']
    idea_text_summary = st.session_state['research_summary']
    papers_df = st.session_state['papers_df'] 
    concated_data = st.session_state['concated_data'] 
    short_context_model = st.session_state['short_context_model']

    litrature_review_len = st.slider("Number of tokens for the litrature review generation", min_value=500, max_value=10000, value=2000) # Tokens
    estimated_cost = st.session_state['long_context_model'].get_estimated_cost(concated_data, litrature_review_len)
    st.toast(f'Digital RA> Estimated cost for litrature review: {estimated_cost} to write a review of around {litrature_review_len*3/4} words')

    st.write('Do yo uwant me to write litrature review? The cost would be around: ' + str(st.session_state['long_context_model'].get_estimated_cost(concated_data, litrature_review_len)))
    st.write('Your cost so far is ' + str(long_context_model.get_current_cost()+short_context_model.get_current_cost()))
    
    button_initiate_review = st.button('Write the litrature review')
    if button_initiate_review:
        with st.spinner('Writing the review'):
            st.session_state['litrature_review'] = operations.write_litrature_review(working_dir, long_context_model, researcher_spec, idea_text_summary, papers_df, concated_data)

            st.toast(f'Digital RA> Total cost: {str(long_context_model.get_current_cost()+short_context_model.get_current_cost())}')
            print('--------------')

    st.session_state['litrature_review'] = st.text_area('Here is the review', st.session_state['litrature_review'])

    # extra = input("Digital RA> Do you want to chat with the condensed data used for review (Y/n): ")
    # if extra.lower() == 'n':
    #     pass

    # utils.enable_chat(researcher_spec, concated_data, idea_text_summary, long_context_model.get_current_cost()+short_context_model.get_current_cost())
