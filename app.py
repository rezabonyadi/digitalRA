import streamlit as st
import datetime
import datetime
import json 
from PIL import Image
import os
import app_pages.chat
import app_pages.hire_page
import app_pages.prepare_ra
import app_pages.research
import app_pages.write_review
from utils import llm_connection
import app_pages

import pandas as pd
import tiktoken
import openai

pricing_map = llm_connection.pricing_map

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

def load_llm_models(pricing_map, large_mdl, small_mdl, chat_mdl, OPENAI_API_KEY):
    st.session_state['short_context_model'] = llm_connection.llmOperations(OPENAI_API_KEY, small_mdl, price_inp=pricing_map[small_mdl][0], 
                                                                  price_out=pricing_map[small_mdl][1])
    st.session_state['long_context_model'] = llm_connection.llmOperations(OPENAI_API_KEY, large_mdl, price_inp=pricing_map[large_mdl][0], 
                                                                 price_out=pricing_map[large_mdl][1])
    st.session_state['chat_model'] = llm_connection.llmOperations(OPENAI_API_KEY, chat_mdl, price_inp=pricing_map[small_mdl][0], 
                                                                 price_out=pricing_map[small_mdl][1])

if st.sidebar.button('Renew connection'):
    load_llm_models(pricing_map, large_mdl, small_mdl, chat_mdl, OPENAI_API_KEY)
    

# print('Loaded ' + small_mdl + ' for short context cases and ' + large_mdl + ' for long context inferences.')
############## Create the RA character

# Load short context and logn context models
if 'short_context_model' not in st.session_state:
    load_llm_models(pricing_map, large_mdl, small_mdl, chat_mdl, OPENAI_API_KEY)

    # st.session_state['short_context_model'] = llm_connection.llmOperations(OPENAI_API_KEY, small_mdl, price_inp=pricing_map[small_mdl][0], price_out=pricing_map[small_mdl][1])
    # st.session_state['long_context_model'] = llm_connection.llmOperations(OPENAI_API_KEY, large_mdl, price_inp=pricing_map[large_mdl][0], price_out=pricing_map[large_mdl][1])
    # st.session_state['chat_model'] = llm_connection.llmOperations(OPENAI_API_KEY, chat_mdl, price_inp=pricing_map[small_mdl][0], 
    #                                                              price_out=pricing_map[small_mdl][1])
if 'researcher_spec' not in st.session_state:
    st.session_state['researcher_spec'] = "Not loaded yet!"
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
    app_pages.hire_page.load_hire_page()

if tabs == "Prepare":
    app_pages.prepare_ra.load_prepare_ra_page()

if tabs == 'Research': 
    app_pages.research.load_research_page()

if tabs == 'Write':
    app_pages.write_review.load_write_review_page()
    
if tabs == 'Chat':
    app_pages.chat.load_chat_page(user_logo, ra_image, chat_mdl)
