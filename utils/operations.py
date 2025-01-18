import subprocess
import os
import time
import json
import pandas as pd
import openai
import time
import tiktoken
import pandas as pd
from tqdm import tqdm
import requests
# from utils import llmOperations
from utils import papers_interactions
from utils import prompts
from utils import llm_connection

pricing_map = llm_connection.pricing_map

def get_research_papers(working_dir, search_phrases, engines = ['gscholar', 'pubmed', 'semscholar'], num_papers_by_eng=20):
    combined_df = pd.DataFrame()
    # engines = ['gscholar', 'pubmed', 'semscholar']
    # engines = ['pubmed']

    for search_phrase in search_phrases:
        for engine in engines:
            print(f"Extracting papers with search phrase: {search_phrase} from {engine}")
            df = papers_interactions.get_papers(search_phrase, engine, num_papers_by_eng)
            combined_df = pd.concat([combined_df, df])
            time.sleep(1)    
    combined_df = combined_df.drop_duplicates(subset=['abstract'])
    clean_df = combined_df.dropna(subset= ['abstract'])    

    return clean_df

def papers_relevances(working_dir, clean_df, researcher_spec, idea_text_summary, short_context_model):
    relevance_scores = []
    real_cost = 0

    for i in tqdm(range(clean_df.shape[0])):
        abstract = clean_df['abstract'].values[i]
        
        # assistant_message = "Ok, I will follow your instrcution EXACTLY and provide the response in JSON format mentioned."
        prompt = prompts.get_papers_relevance_prompt(idea_text_summary, abstract)
        # print(prompt)
        parsed_response, response = short_context_model.get_llm_response(prompt, system_prompt=researcher_spec)
        
        try:
            parsed_response = parsed_response.replace("```json\n", "").replace("```", "")
            # print(parsed_response)
            parsed_data = json.loads(parsed_response)
        except:
            parsed_data = {"relevance": "unknown", "reason": parsed_response}
        columns_to_pass = ['authors', 'abstract', 'doi', 'cites', 'year', 'title']
        for c in columns_to_pass:
            try:
                parsed_data[c] = clean_df[c].values[i]
            except:
                parsed_data[c] = "NONE"
        
        relevance_scores.append(parsed_data)
                
    # Save the results
    relevance_scores_df = pd.DataFrame(relevance_scores)
    
    return relevance_scores_df

def get_research_assistant(idea_text, short_context_model):
    prompt = "Here is a research proposal:\n"+idea_text+'\n If a professor is going to research this propsoal, what would the professor be expert at? List 3-5 main competencies needed to be world-class successful in this research. Format it as: Generate the answer in the format of "You are an expeert in the field of XXX, with following competencies: "'
    researcher_spec, response = short_context_model.get_llm_response(prompt)

    if response is None:
        print('ATTENTION: OpenAI response error!!!')
        researcher_spec = "You are an expert researcher in all fields."

    return researcher_spec

def extract_search_phrases(working_dir, idea_text, short_context_model, researcher_spec, num_search_phrases=5):
    prompt = f'{researcher_spec} \n\nHere is a description of an idea: {idea_text}. \n Generate {num_search_phrases} search phrases to search in Google for related articles. The phrases need to be short, in the oder of 5 words or so. Generate the search phrases in a json format, with fields of "search phrase X", where X is the number. Do not include any extra text, explanations, or formatting such as `json` tags or comments. Respond with nothing but the json object.'
    final_response, response = short_context_model.get_llm_response(prompt)
    print('****************')
    
    print(final_response)
    if response is None:
        print('ATTENTION: OpenAI response error!!!')
        search_phrases = ""
    else:
        parsed_data = json.loads(final_response)
        search_phrases = []
        for i in parsed_data.keys():
            search_phrases.append(parsed_data[i])
    return search_phrases

def get_idea_summary(idea_text, short_context_model, researcher_spec):
    prompt = researcher_spec+"\n\nSummarize this research idea to a concise paragraph while make sure it does not loose any important message or question:\n"+idea_text
    idea_text_summary, response = short_context_model.get_llm_response(prompt)

    if response is None:
        print('ATTENTION: OpenAI response error!!!')
        idea_text_summary = idea_text
    
    return idea_text_summary

def write_litrature_review(working_dir, long_context_model, researcher_spec, idea_text_summary, papers_df, concated_data):
    prompt = researcher_spec+'\n \n Here is an idea: ' + idea_text_summary + '\n' + "and here are some paper abstracts that are relevant to this idea:\n\n" + concated_data + """\n\n END OF PAPER ABSTRACT PROVIDED.\n \nWrite a litrature review section, which I will be using for my paper in the background section, using these papers about the idea. Use as much as these papers as you can. Ensure the review is engaging and compares the ideas, rather than a flat list of papers. Also, the review makes reference back to my idea where relevant. Use Paper IDs for referencing, for example [Paper ID 3]. Also, at the very end, add one short and condensed paragraph and discuss how my idea is going to advance the field further and what gaps it will be filling."""
    litrature_review, response = long_context_model.get_llm_response(prompt)

    if response is None:
        print('ATTENTION: OpenAI response error!!!')
        litrature_review = concated_data

    print('your cost so far: ', long_context_model.get_current_cost())

    refs = [''.join(['[', str(i), '], ', p]) for i, p in enumerate((papers_df['title']+ ', (' + papers_df['year'].astype(str) + ')\n').values.tolist())]
    all_ref = ''.join(refs)
    litrature_review = ''.join([litrature_review, '\n\nReferences:\n', all_ref])
    print(litrature_review)

    with open(working_dir + 'litrature_review_final.txt', 'w', encoding="utf-8-sig") as f:
        f.write(litrature_review)
    
    return litrature_review

def filter_papers_for_review(min_year, min_cite, working_dir, long_context_model, relevance_scores_df):
    filtered_df = relevance_scores_df[relevance_scores_df["relevance"].str.lower().isin(["high", "very high"])]
    papers_df = filtered_df[(filtered_df['year']>min_year) | (filtered_df['cites']>min_cite)]
    print(f'Selected {papers_df.shape[0]} papers for the review.')

    concated_data = [('Paper ID '+ str(i) + ': \n' + p + '\n\n') for i, p in enumerate(papers_df['abstract'].values.tolist())]
    concated_data = ''.join(concated_data)

    # print(concated_data)
    return papers_df, concated_data

def enable_chat(researcher_spc, concated_data, idea_summary, total_cost):
    model = 'gpt-3.5-turbo-16k'
    chat_data = [{'role': 'system', "content": researcher_spc + "\n\n You are my research assistant. \n\nHere are some articles: \n\n"+concated_data + '\n\n Here is an idea I have I want to research on: \n\n' + idea_summary}]
    # print(chat_data)
    cost = 0
    tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
    
    while True:
        prompt = input('user> ')
        chat_data.append({'role': 'user', 'content': prompt})
        full_response = "Digital RA> "
        print(full_response, end='')
        for response in openai.ChatCompletion.create(model=model, messages=chat_data, stream=True):
            gen = response.choices[0].delta.get("content", "")
            full_response += gen
            print(gen, end='')
        
        chat_data.append({'role': 'assistant', 'content': full_response})
        print('')
        # print('Digital RA> ' + final_response)
    
        total_prompt_tokens = len(tokenizer.encode(prompt))
        total_cmpl_tokens = len(tokenizer.encode(full_response))
        cost += pricing_map[model][0]*total_prompt_tokens + pricing_map[model][1]*total_cmpl_tokens

        print(f'\nDigital RA> ------- cost so far {total_cost} plus {cost} \n')
