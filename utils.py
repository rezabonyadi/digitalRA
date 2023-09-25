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

pricing_map = {'gpt-4-0613': [0.03/1000, 0.06/1000], 'gpt-3.5-turbo-16k': [0.003/1000, 0.004/1000], 'gpt-3.5-turbo-0613': [0.0015/1000, 0.002/1000]}

def run_pop8query(keywords, datasource, max_results, output_format, output_file):
    cmd = [
        "./assets/pop8query",
        "--keywords={}".format(keywords),
        "--{}".format(datasource),
        "--max={}".format(max_results),
        "--format={}".format(output_format),
        output_file
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print("Error occurred:", result.stderr)
    else:
        print("Command executed successfully!")
        print("Output:", result.stdout)

def get_papers(search_phrase, dataset="semscholar", max_papers=5):
    try:
        run_pop8query(search_phrase, dataset, max_papers, "json", "output.json")
        
        # Check if output.json was created and is not empty
        if not os.path.exists("output.json") or os.path.getsize("output.json") == 0:
            print(f"Error: Output file for '{search_phrase}' not created or is empty.")
            return pd.DataFrame()  # Return empty dataframe

        with open("output.json", "r", encoding="utf-8-sig") as file:
            data = json.load(file)

        if not data:
            print(f"No data found in the JSON file for '{search_phrase}'.")
            return pd.DataFrame()  # Return empty dataframe

        df = pd.DataFrame(data)

        return df

    except Exception as e:
        print(f"Error processing '{search_phrase}': {e}")
        return pd.DataFrame()  # Return empty dataframe in case of any other unexpected errors


class llmOperations:    
    total_prompt_tokens = 0
    total_cmpl_tokens = 0

    openai.api_key = 'XXX'
    def __init__(self, OPENAI_API_KEY, language_model="gpt-3.5-turbo-0613", price_inp=0.0015/1000, price_out=0.002/1000):
        self.language_model=language_model
        self.price_inp=price_inp
        self.price_out=price_out    
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        openai.api_key = OPENAI_API_KEY

    
    def get_llm_response(self, prompt, system_prompt = "You are a smart, very knowledgable, research assistant."):
        chat_data = [{'role': 'system', "content": system_prompt}, {'role': 'user', 'content': prompt}]
        # print(chat_data)
        
        response = openai.ChatCompletion.create(model=self.language_model, messages=chat_data)
        final_response = response['choices'][0]['message']['content']
        
        self.total_prompt_tokens += response['usage']['prompt_tokens']
        self.total_cmpl_tokens += response['usage']['completion_tokens']

        # print(self.get_current_cost())
        
        return final_response, response

    def get_current_cost(self):
        return self.total_prompt_tokens*self.price_inp + self.total_cmpl_tokens*self.price_out
        
    def get_estimated_cost(self, prompt, completion_estimate_len=100):
        # Assumes the system prompt is small, and prompt variable contains all text to be processed by LLM        
        return len(self.tokenizer.encode(prompt))*self.price_inp + completion_estimate_len*self.price_out


def get_research_papers(working_dir, search_phrases, engines = ['gscholar', 'pubmed', 'semscholar'], num_papers_by_eng=20):
    combined_df = pd.DataFrame()
    # engines = ['gscholar', 'pubmed', 'semscholar']
    # engines = ['pubmed']

    for search_phrase in search_phrases:
        for engine in engines:
            print(f"Extracting papers with search phrase: {search_phrase} from {engine}")
            df = get_papers(search_phrase, engine, num_papers_by_eng)
            combined_df = pd.concat([combined_df, df])
            time.sleep(1)    
    combined_df = combined_df.drop_duplicates(subset=['abstract'])
    clean_df = combined_df.dropna(subset= ['abstract'])

    # Save the found papers
    clean_df.to_csv(working_dir+'papers_found.csv')

    return clean_df

def papers_relevances(working_dir, clean_df, researcher_spec, idea_text_summary, short_context_model):
    relevance_scores = []
    real_cost = 0

    for i in tqdm(range(clean_df.shape[0])):
        abstract = clean_df['abstract'].values[i]
        
        prompt = researcher_spec + '\n\nHere is an idea: ' + idea_text_summary + '\n' + "How relevant this idea is to the following abstract of a paper:\n" + abstract + """\n \nPick the relevance score from very low, low, medium, high, and very high. Output format as json, with fields "relevance" and "reason", which would look like:\n
        {"relevance": "RELEVANCE", "reason": "THE REASON"}. Include nothing but this json format output in your response."""

        parsed_response, response = short_context_model.get_llm_response(prompt)

        try:
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
    relevance_scores_df.to_csv(working_dir + '/first_level_analysis.csv')
    return relevance_scores_df

def get_llm_models(small_mdl, large_mdl):
    OPENAI_API_KEY = "XXX"

    if not os.path.exists('settings.json'):
        OPENAI_API_KEY = input("Please enter your OPENAI Key: ")

        data = {"OPENAI_API_KEY": OPENAI_API_KEY}
        with open('settings.json', 'w') as f:
            json.dump(data, f, indent=4) 

    with open('settings.json', 'r') as file:
        data = json.load(file)
        field_name = "OPENAI_API_KEY"
        OPENAI_API_KEY = data[field_name]

    short_context_model = llmOperations(OPENAI_API_KEY, small_mdl, price_inp=pricing_map[small_mdl][0], price_out=pricing_map[small_mdl][1])
    long_context_model = llmOperations(OPENAI_API_KEY, large_mdl, price_inp=pricing_map[large_mdl][0], price_out=pricing_map[large_mdl][1])

    return short_context_model, long_context_model

def get_research_assistant(idea_text, short_context_model):
    prompt = "Here is a research proposal:\n"+idea_text+'\n If a professor is going to research this propsoal, what would the professor be expert at? Generate the answer in the format of "You are an expeert in the field of XXX"'
    researcher_spec, response = short_context_model.get_llm_response(prompt)

    print("Digital RA> Hi, I am your research assistant. Here is what I am expert at:\n\n" + researcher_spec)
    print('Do you want me to acquire other capability?')
    extra = input("Please enter extra capabilities: ")

    researcher_spec = researcher_spec + ' ' + extra + " You are the best in the world in this field. "
    print('\n Digital RA> My capabilities: \n\n' + researcher_spec)
    return researcher_spec

def extract_search_phrases(working_dir, idea_text, short_context_model, researcher_spec, num_search_phrases=5):
    prompt = f'{researcher_spec} \n\nHere is a description of an idea: {idea_text}. \n Generate {num_search_phrases} search phrases to search in Google for related articles. Generate the search phrases in a json format, with fields of "search phrase X", where X is the number. Include nothing but this json format output in your response.'
    final_response, response = short_context_model.get_llm_response(prompt)

    parsed_data = json.loads(final_response)
    search_phrases = []
    for i in parsed_data.keys():
        search_phrases.append(parsed_data[i])
    return search_phrases

def get_curated_summary(working_dir, idea_text, short_context_model, researcher_spec):
    prompt = researcher_spec+"\n\nSummarize this research idea to a concise paragraph while make sure it does not loose any important message or question:\n"+idea_text
    idea_text_summary, response = short_context_model.get_llm_response(prompt)
    print('Here is a summary of your idea: \n', idea_text_summary)
    extra = input("Is this a fair summary (if yes, press enter, if no, enter a new summary): ")

    if extra != "":
        idea_text_summary = extra

    with open(working_dir + 'idea_summary.txt', 'w') as f:
        f.write('Idea: \n\n')
        f.write(idea_text)
        f.write('\n\n idea summary:\n\n')
        f.write(idea_text_summary)
    return idea_text_summary


def write_litrature_review(working_dir, long_context_model, researcher_spec, idea_text_summary, papers_df, concated_data):
    prompt = researcher_spec+'\n \n Here is an idea: ' + idea_text_summary + '\n' + "and here are some paper abstracts that are relevant to this idea:\n\n" + concated_data + """\n\n END OF PAPER ABSTRACT PROVIDED.\n \nWrite a litrature review section, which I will be using for my paper in the background section, using these papers about the idea. Use as much as these papers as you can. Ensure the review is engaging and compares the ideas, rather than a flat list of papers. Also, the review makes reference back to my idea where relevant. Use Paper IDs for referencing, for example [Paper ID 3]. Also, at the very end, add one short and condensed paragraph and discuss how my idea is going to advance the field further and what gaps it will be filling."""
    litrature_review, response = long_context_model.get_llm_response(prompt)

    print('your cost so far: ', long_context_model.get_current_cost())

    refs = [''.join(['[', str(i), '], ', p]) for i, p in enumerate((papers_df['title']+ ', (' + papers_df['year'].astype(str) + ')\n').values.tolist())]
    print(litrature_review)
    print(''.join(refs))

    with open(working_dir + 'litrature_review_final.txt', 'w') as f:
        f.write(litrature_review)
        f.write('\n\nReferences:\n')
        f.write(''.join(refs))
    
    return litrature_review

def filter_papers_for_review(min_year, min_cite, working_dir, long_context_model, relevance_scores_df):
    filtered_df = relevance_scores_df[relevance_scores_df["relevance"].str.lower().isin(["high", "very high"])]
    papers_df = filtered_df[(filtered_df['year']>min_year) | (filtered_df['cites']>min_cite)]
    print(f'Selected {papers_df.shape[0]} papers for the review.')

    concated_data = [('Paper ID '+ str(i) + ': \n' + p + '\n\n') for i, p in enumerate(papers_df['abstract'].values.tolist())]
    concated_data = ''.join(concated_data)

    with open(working_dir + 'used_papers_review.txt', 'w', encoding="utf-8-sig") as f:
        f.write(concated_data)

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

        print(f'Digital RA> ------- cost so far {total_cost} plus {cost} \n')
