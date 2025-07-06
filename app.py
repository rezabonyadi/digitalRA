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
available_models = list(pricing_map.keys())

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
small_mdl = st.sidebar.selectbox("Select the short context model", available_models, help="Model for short context tasks, such as all hiring tasks and preparations tasks.")
large_mdl = st.sidebar.selectbox("Select the long context model", available_models, help="Model for long context tasks which is writing the litrature review.")
eval_mdl = st.sidebar.selectbox("Select the evaluation model", available_models, help="Model for research tasks (evaluating the relevance of papers).")
chat_mdl = st.sidebar.selectbox("Select the chat model", available_models, help="Model for chat tasks. This is used to chat with your RA and ask questions about the litrature review and research summary.")

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
GEMINI_API_KEY = "XXX"

if not os.path.exists('settings.json'):
    data = {"OPENAI_API_KEY": OPENAI_API_KEY, "GEMINI_API_KEY": GEMINI_API_KEY}
    with open('settings.json', 'w') as f:
        json.dump(data, f, indent=4) 

with open('settings.json', 'r') as file:
    data = json.load(file)
    field_name = "OPENAI_API_KEY"
    OPENAI_API_KEY = data[field_name]
    field_name = "GEMINI_API_KEY"
    GEMINI_API_KEY = data[field_name]

OPENAI_API_KEY = st.sidebar.text_input("OpenAI key",value=OPENAI_API_KEY, type='password')
GEMINI_API_KEY = st.sidebar.text_input("Gemini key",value=GEMINI_API_KEY, type='password')

def load_llm_models(pricing_map, large_mdl, small_mdl, chat_mdl, eval_mdl, OPENAI_API_KEY, GEMINI_API_KEY):  
    small_mdl_type = small_mdl.split(':')[0] # Get the model type (e.g., 'gpt', 'gemini')
    large_mdl_type = large_mdl.split(':')[0] # Get the model type (e.g., 'gpt', 'gemini')
    chat_mdl_type = chat_mdl.split(':')[0] # Get the model type (e.g., 'gpt', 'gemini')
    eval_mdl_type = eval_mdl.split(':')[0] # Assuming eval model is the same as small context model
    # small_mdl_name = small_mdl.split(':')[1]  # Remove any version suffix if present
    # large_mdl_name = large_mdl.split(':')[1]  # Remove any version suffix if present
    # chat_mdl_name = chat_mdl.split(':')[1]  # Remove any version suffix if present

    api_key = OPENAI_API_KEY if small_mdl_type == 'openai' else GEMINI_API_KEY 
    st.session_state['short_context_model'] = llm_connection.llmOperations(api_key, small_mdl, price_inp=pricing_map[small_mdl][0], 
                                                                  price_out=pricing_map[small_mdl][1])
    api_key = OPENAI_API_KEY if eval_mdl_type == 'openai' else GEMINI_API_KEY 
    st.session_state['eval_model'] = llm_connection.llmOperations(api_key, eval_mdl, price_inp=pricing_map[eval_mdl][0], 
                                                                  price_out=pricing_map[eval_mdl][1])

    api_key = OPENAI_API_KEY if large_mdl_type == 'openai' else GEMINI_API_KEY 
    st.session_state['long_context_model'] = llm_connection.llmOperations(api_key, large_mdl, price_inp=pricing_map[large_mdl][0],
                                                                 price_out=pricing_map[large_mdl][1])
    api_key = OPENAI_API_KEY if chat_mdl_type == 'openai' else GEMINI_API_KEY
    st.session_state['chat_model'] = llm_connection.llmOperations(api_key, chat_mdl, price_inp=pricing_map[small_mdl][0],
                                                                 price_out=pricing_map[small_mdl][1])

if st.sidebar.button('Renew connection'):
    load_llm_models(pricing_map, large_mdl, small_mdl, chat_mdl, eval_mdl, OPENAI_API_KEY, GEMINI_API_KEY)

# print('Loaded ' + small_mdl + ' for short context cases and ' + large_mdl + ' for long context inferences.')
############## Create the RA character

# Load short context and long context models
if 'short_context_model' not in st.session_state:
    load_llm_models(pricing_map, large_mdl, small_mdl, chat_mdl, eval_mdl, OPENAI_API_KEY, GEMINI_API_KEY)
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
    app_pages.hire_page.load_hire_page(st.session_state['short_context_model'])

if tabs == "Prepare":
    app_pages.prepare_ra.load_prepare_ra_page(st.session_state['short_context_model'])

if tabs == 'Research': 
    app_pages.research.load_research_page(st.session_state['eval_model'])

st.toast("Current total cost: " + str(st.session_state['short_context_model'].get_current_cost()+ 
                                      st.session_state['long_context_model'].get_current_cost() + 
                                      st.session_state['eval_model'].get_current_cost()))
if tabs == 'Write':
    app_pages.write_review.load_write_review_page(st.session_state['long_context_model'])
    
if tabs == 'Chat':
    app_pages.chat.load_chat_page(user_logo, ra_image, st.session_state['chat_model'])
