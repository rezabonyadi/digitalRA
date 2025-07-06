import streamlit as st
import pandas as pd
from utils import operations

def load_research_page(llm_object=None):
    '''This page is used to perform the research on the scientific databases.
    It gets the papers from various sources, and then uses LLM to evaluate their relevance, and filter them for the literature review.
    '''
    
    ########## Get papers
    st.markdown("## Get papers")
    st.markdown("""Here, your RA is ready to perform the research on some scientific databases. 
Instruction: 
- Click on **Renew connection** to ensure your API connection is up-to-date.
- Pick the scientific websites to search in.
- Pick the minimum number of citations and the minimum publication year to include a paper in final filter.
    This will be used to filter the papers for the review. A paper that is old and has lots of citations is likely to be relevant. Newer papers are included, given the minimum publication date.
- Click "Get papers". This will start performing the search on the engines specified.
                
                """)
    col1, col2 = st.columns(2)
    min_cite = col1.slider("Number of citations to include a paper", min_value=0, max_value=20000, value=100)
    min_year = col2.slider("Minimum year for papers", min_value=1900, max_value=2023, value=2020)
    
    selected_serch_engines = st.multiselect('Search engines', ['gscholar', 'pubmed', 'semscholar', 'arxiv', 'bioarxiv'], default=['arxiv'])

    button_get_papers = st.button('Get papers')

    if button_get_papers:
        with st.spinner('Finding relevant articles'):
            st.session_state['papers_df'] = pd.DataFrame()
            print(selected_serch_engines)
            papers_df = operations.get_research_papers(st.session_state['working_dir'], 
                                                       st.session_state['search_phrases'], 
                                                       engines=selected_serch_engines)
            papers_df = papers_df[(papers_df['year']>min_year) | (papers_df['cites']>min_cite)]
            papers_df.insert(loc=0, column='manual_pick', value=True)

            st.session_state['papers_df'] = papers_df
            st.success(f'Loaded {papers_df.shape[0]} articles.')

    selected_papers_to_evaluate = st.data_editor(st.session_state['papers_df'], key='selected_papers_to_evaluate')
    st.divider()
    st.markdown("## Evaluate papers")
    st.markdown("""- Once papers were loaded and you picked papers, click on "Evaluate papers and rank". Your RA starts evaluating the papers against your proposal, and gives them a relevance score and a reason supporting the score. This will take a while!
- Check the RA's scores and reasons. You can modify them!""")    

    evaluate_papers = st.button('Evaluate papers and rank')

    if evaluate_papers:
        with st.spinner('Evaluating relevance'):
            papers_to_evaluate = selected_papers_to_evaluate[selected_papers_to_evaluate['manual_pick']==True]
            st.session_state['relevance_scores_df']  = operations.papers_relevances(st.session_state['working_dir'], 
                                                                               papers_to_evaluate, 
                                                                               st.session_state['researcher_spec'],  
                                                                               st.session_state['research_summary'], 
                                                                               llm_object)
            
            st.session_state['relevance_scores_df'].to_csv(st.session_state['working_dir'] + '/first_level_analysis.csv')
            st.toast('Digital RA> I am ready with the papers now, also saved them in a file for you. These papers are going to be used for the litrature review I am writing.')            
            st.toast('Digital RA> Saved the results to '+st.session_state['working_dir']+'/first_level_analysis.txt.')
    
    relevance_scores_edited = st.data_editor(st.session_state['relevance_scores_df'], key='relevance_scores_editor')
    
    st.divider()
    st.markdown("## Filter papers for review")
    st.markdown("""- Click on "Filter papers for review", which will pick high-relevant papers for further review. 
                - If you are not happy with the relevance scores, you can modify them! Changing them to high or very high will ensure that paper will be included in the meta analysis. 
- Click on "Write" to go to the next step.                  
""")
    button_filter_papers = st.button('Filter papers for review')
    if button_filter_papers:
        # min_cite = 50
        # min_year = 2010
        # litrature_review_len = 2000 # Tokens

        st.toast(f'Digital RA> I am now filtering the papers by {min_cite} min number of citations OR year of publications of {min_year} on-wards for the review')
        # relevance_scores_df = st.session_state['relevance_scores_df']

        filtered_papers_df, concated_data = operations.filter_papers_for_review(min_year, min_cite, st.session_state['working_dir'], 
                                                                relevance_scores_edited)
        
        with open(st.session_state['working_dir'] + 'used_papers_review.txt', 'w', encoding="utf-8-sig") as f:
            f.write(concated_data)
        st.toast('Digital RA> Saved the results to '+st.session_state['working_dir']+'/used_papers_review.txt.')
    
        st.session_state['concated_data'] = concated_data
        st.session_state['papers_df'] = filtered_papers_df
        
        st.success(f'Selected {filtered_papers_df.shape[0]} papers for the review.')
        st.data_editor(filtered_papers_df)
