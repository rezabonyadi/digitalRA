import streamlit as st
import datetime
import datetime
import json 
from PIL import Image
import os
import utils
import pandas as pd
import tiktoken
import openai

pricing_map = {'gpt-4o': [2.5/1000000, 1.25/1000000], 'gpt-4o-mini': [.15/1000000, 0.075/1000000], 
               'gpt-4': [0.03/1000, 0.06/1000], 'gpt-3.5-turbo': [0.001/1000, 0.002/1000]}
ra_image = Image.open('assets/ra_1_image.jpg')
user_logo = Image.open('assets/th.jpeg')

st.set_page_config(
    page_title="Digital Research Assistant",
    page_icon="assets/ra_1_image.jpg",
    layout="centered"    
)
col1, col2 = st.columns([0.15, 0.85])
col1.image(ra_image, use_column_width=True)
col2.header("""Digital Research Assistant""")
st.divider()

# Pick your samll GPT instance (used for research and extracting papers) and Large GPT instance (used for writing the litrature review)
large_mdl = st.sidebar.selectbox("Select the long context model", ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-4'])
small_mdl = st.sidebar.selectbox("Select the short context model", ['gpt-4o-mini', 'gpt-4o', 'gpt-3.5-turbo', 'gpt-4'])
chat_mdl = st.sidebar.selectbox("Select the chat model", ['gpt-4o', 'gpt-4o-mini', 'gpt-3.5-turbo', 'gpt-4'])
# gen_char_tab, inteview_tab = st.tabs(["Generate character", "Interview"])
# tabs = ["Hire", "Prepare", "Research", "Write", "Chat"]

# next_page_button = st.button

tabs = st.sidebar.radio(
    "Steps",
    ["Hire", "Prepare", "Research", "Write", "Chat"],
    captions = ["Hire your RA", "Prepare research", "Collect papers and rank", "Write the litrature review", "Chat with RA"])

st.sidebar.divider()
# We filter artilces with some spec. For example, only papers later than 2020, or if the papers had more than 100 citations, and their relevance score was at least medium.
if 'working_dir' not in st.session_state:
    st.session_state['working_dir'] = './results/review/'

st.session_state['working_dir'] = st.sidebar.text_input('Where to save the results', st.session_state['working_dir'])
if not os.path.exists(st.session_state['working_dir']):
    os.makedirs(st.session_state['working_dir'])

OPENAI_API_KEY = "XXX"

if not os.path.exists('settings.json'):
    data = {"OPENAI_API_KEY": OPENAI_API_KEY}
    with open('settings.json', 'w') as f:
        json.dump(data, f, indent=4) 

with open('settings.json', 'r') as file:
    data = json.load(file)
    field_name = "OPENAI_API_KEY"
    OPENAI_API_KEY = data[field_name]

OPENAI_API_KEY = st.sidebar.text_input("OpenAI key",value=OPENAI_API_KEY, type='password')

if st.sidebar.button('Renew connection'):
    st.session_state['short_context_model'] = utils.llmOperations(OPENAI_API_KEY, small_mdl, price_inp=pricing_map[small_mdl][0], 
                                                                  price_out=pricing_map[small_mdl][1])
    # long_context_model = llmOperations('gpt-3.5-turbo-16k', price_inp=0.003/1000, price_out=0.004/1000)
    st.session_state['long_context_model'] = utils.llmOperations(OPENAI_API_KEY, large_mdl, price_inp=pricing_map[large_mdl][0], 
                                                                 price_out=pricing_map[large_mdl][1])
    st.session_state['chat_model'] = utils.llmOperations(OPENAI_API_KEY, chat_mdl, price_inp=pricing_map[small_mdl][0], 
                                                                 price_out=pricing_map[small_mdl][1])
    


print('Loaded ' + small_mdl + ' for short context cases and ' + large_mdl + ' for long context inferences.')
############## Create the RA character
if 'researcher_spec' not in st.session_state:
    st.session_state['researcher_spec'] = "Not loaded yet!"

# Load short context and logn context models
if 'short_context_model' not in st.session_state:
    st.session_state['short_context_model'] = utils.llmOperations(OPENAI_API_KEY, small_mdl, price_inp=pricing_map[small_mdl][0], price_out=pricing_map[small_mdl][1])
    # long_context_model = llmOperations('gpt-3.5-turbo-16k', price_inp=0.003/1000, price_out=0.004/1000)
    st.session_state['long_context_model'] = utils.llmOperations(OPENAI_API_KEY, large_mdl, price_inp=pricing_map[large_mdl][0], price_out=pricing_map[large_mdl][1])
    st.session_state['chat_model'] = utils.llmOperations(OPENAI_API_KEY, chat_mdl, price_inp=pricing_map[small_mdl][0], 
                                                                 price_out=pricing_map[small_mdl][1])

if 'idea_text' not in st.session_state:
    st.session_state['idea_text'] = ""
if 'search_phrases' not in st.session_state:
    st.session_state['search_phrases'] = []
if 'research_summary' not in st.session_state:
    st.session_state['research_summary'] = ""
if 'litrature_review' not in st.session_state:
    st.session_state['litrature_review'] = ""
if 'papers_df' not in st.session_state:
    st.session_state['papers_df'] = pd.DataFrame()
if 'relevance_scores_df' not in st.session_state:
    st.session_state['relevance_scores_df'] = pd.DataFrame()

if tabs == "Hire":
    st.markdown("""Hello there!
                
Welcome to the first step of Digital Research assistant. In this step, you describe your research proposal and I will "hire" a research assistant for you with expertiese you will need to make that proposal a success.
                
Instruction: Describe your research idea below and click on "Hire your RA". You will be able to refine the description and competencies of the "hired" RA. 

Click on "Prepare" in the left menue once you are ready with your RA.""")
    
    st.divider()

    st.session_state['idea_text'] = st.text_area('Explain your research in a paragraph', st.session_state['idea_text'])

    button_generate_RA_character = st.button('Hire your RA')
    if button_generate_RA_character:
        
        print(st.session_state['idea_text'])
        researcher_spec = utils.get_research_assistant(st.session_state['idea_text'], st.session_state['short_context_model'])
        st.toast('Cost> your cost so far: ' + str(st.session_state['short_context_model'].get_current_cost()))
        
        st.session_state['researcher_spec'] = researcher_spec

    st.session_state['researcher_spec'] = st.text_area('Here is a descriotion of your RA: ', st.session_state['researcher_spec'])

if tabs == "Prepare":
    st.markdown("""Here, you will prepare your RA for the research to be done. The RA needs to perform internet search. To do so, it will generate some search phrases. 

1. CLick on "Generate summary" to get a summary of your research proposal. Double check to ensure all main points have been covered. Modify it if needed.
2. Tell me how many search phrases you want.
3. Click on "Generate search phrases". The RA will generate them for you based on its competencies and your research idea..
4. You can modify the phrases.
5. Click on "Research" once ready.""")
    st.divider()

    number_serach_phrases = st.slider('Number of search phrases', min_value=2, max_value=10, value=5)

    ############# Genrate summary
    button_generate_summary = st.button('Generate summary')

    if button_generate_summary:

        idea_text_summary = utils.get_idea_summary(st.session_state['idea_text'], st.session_state['short_context_model'], 
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

    # ############### Generate search phrases
    button_generate_search_phrases = st.button('Generate search phrases')

    if button_generate_search_phrases:
        researcher_spec = st.session_state['researcher_spec'] 
        
        search_phrases = utils.extract_search_phrases(st.session_state['working_dir'], st.session_state['idea_text'], st.session_state['short_context_model'], 
                                                      researcher_spec, number_serach_phrases)

        print('Here are search phrases I suggest: ', search_phrases)
        st.session_state['search_phrases'] = search_phrases

        with open(st.session_state['working_dir'] + 'search_phrases.txt', 'w') as f:
            f.write('\n'.join(search_phrases))
        st.toast('Digital RA> your cost so far: '+ str(st.session_state['short_context_model'].get_current_cost()))
        st.toast('Digital RA> Saved the results to '+st.session_state['working_dir']+'/file search_phrases.txt.')

    search_phrases = st.text_area('Here are my suggested search phrases:', '\n'.join(st.session_state['search_phrases']))
    st.session_state['search_phrases'] = search_phrases.split('\n')

if tabs == 'Research': 
    st.write("""Here, your RA is ready to perform the research on some scientific databases. 
Instruction: 
0. Click on "Renew connection" to ensure your API connection is up-to-date.
1. Pick the scientific websites to search in.
2. Pick the minimum number of citations and the minimum publication year to include a paper in final filter.
3. Click "Get papers". This will start performing the search on the engines specified.  
4. Once done, click on "Evaluate papers and rank". Your RA starts evaluating the papers against your proposal, and gives them a relevance score and a reason supporting the score. This will take a while!
6. Check the RA's scores and reasons. You can modify them!    
7. Click on "Filter papers for review", which will pick high-relevant papers for further review.  
8. Click on "Write" to go to the next step.                  
""")
    st.divider()
    ########## Get papers
    col1, col2 = st.columns(2)
    min_cite = col1.slider("Number of citations to include a paper", min_value=0, max_value=20000, value=100)
    min_year = col2.slider("Minimum year for papers", min_value=1900, max_value=2023, value=2020)
    
    selected_serch_engines = st.multiselect('Search engines', ['gscholar', 'pubmed', 'semscholar'], default=['semscholar'])

    st.divider()

    button_get_papers = st.button('Get papers')

    if button_get_papers:
        with st.spinner('Finding relevant articles'):
            print(selected_serch_engines)
            papers_df = utils.get_research_papers(st.session_state['working_dir'], st.session_state['search_phrases'], engines=selected_serch_engines)
            papers_df = papers_df[(papers_df['year']>min_year) | (papers_df['cites']>min_cite)]

            st.session_state['papers_df'] = papers_df
            st.data_editor(st.session_state['papers_df'])
            st.success(f'Loaded {papers_df.shape[0]} articles.')

    evaluate_papers = st.button('Evaluate papers and rank')

    if evaluate_papers:
        with st.spinner('Evaluating relevance'):
            relevance_scores_df = utils.papers_relevances(st.session_state['working_dir'], st.session_state['papers_df'], 
                                                          st.session_state['researcher_spec'], 
                                                        st.session_state['research_summary'], st.session_state['short_context_model'])
            st.session_state['relevance_scores_df'] = relevance_scores_df
            

            st.toast("Current total cost: " + str(st.session_state['short_context_model'].get_current_cost()+
                                                        st.session_state['long_context_model'].get_current_cost()))
            relevance_scores_df.to_csv(st.session_state['working_dir'] + '/first_level_analysis.csv')
            st.toast('Digital RA> I am ready with the papers now, also saved them in a file for you. These papers are going to be used for the litrature review I am writing.')            
            st.toast('Digital RA> Saved the results to '+st.session_state['working_dir']+'/first_level_analysis.txt.')
    
    st.session_state['relevance_scores_df'] = st.data_editor(st.session_state['relevance_scores_df'])
    button_filter_papers = st.button('Filter papers for review')

    if button_filter_papers:
        # min_cite = 50
        # min_year = 2010
        # litrature_review_len = 2000 # Tokens

        st.toast(f'Digital RA> I am now filtering the papers by {min_cite} min number of citations OR year of publications of {min_year} on-wards for the review')
        relevance_scores_df = st.session_state['relevance_scores_df']

        papers_df, concated_data = utils.filter_papers_for_review(min_year, min_cite, st.session_state['working_dir'], 
                                                                st.session_state['long_context_model'], relevance_scores_df)
        
        with open(st.session_state['working_dir'] + 'used_papers_review.txt', 'w', encoding="utf-8-sig") as f:
            f.write(concated_data)
        st.toast('Digital RA> Saved the results to '+st.session_state['working_dir']+'/used_papers_review.txt.')
    
        st.session_state['concated_data'] = concated_data
        st.session_state['papers_df'] = papers_df
        
        st.success(f'Selected {papers_df.shape[0]} papers for the review.')
        st.data_editor(papers_df)

if tabs == 'Write':
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
            st.session_state['litrature_review'] = utils.write_litrature_review(working_dir, long_context_model, researcher_spec, idea_text_summary, papers_df, concated_data)

            st.toast(f'Digital RA> Total cost: {str(long_context_model.get_current_cost()+short_context_model.get_current_cost())}')
            print('--------------')

    st.session_state['litrature_review'] = st.text_area('Here is the review', st.session_state['litrature_review'])

    # extra = input("Digital RA> Do you want to chat with the condensed data used for review (Y/n): ")
    # if extra.lower() == 'n':
    #     pass

    # utils.enable_chat(researcher_spec, concated_data, idea_text_summary, long_context_model.get_current_cost()+short_context_model.get_current_cost())

if tabs == 'Chat':
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
