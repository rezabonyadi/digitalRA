
import openai
import tiktoken
import json
import os
# from utils import llm_price_maps

pricing_map = {'gpt-4-0613': [0.03/1000, 0.06/1000], 
               'gpt-3.5-turbo-16k': [0.003/1000, 0.004/1000], 
               'gpt-3.5-turbo-0613': [0.0015/1000, 0.002/1000],
               'gpt-4o': [0.03/1000, 0.06/1000],
               'gpt-4o-mini': [0.003/1000, 0.004/1000]}

# pricing_map = llm_price_maps.pricing_map

def get_llm_models(small_mdl='gpt-4o-mini', large_mdl='gpt-4o'):
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

class llmOperations:    
    total_prompt_tokens = 0
    total_cmpl_tokens = 0

    openai.api_key = 'XXX'
    def __init__(self, OPENAI_API_KEY, language_model="gpt-4o-mini", price_inp=0.0015/1000, price_out=0.002/1000):
        self.language_model=language_model
        self.price_inp=price_inp
        self.price_out=price_out    
        self.tokenizer = tiktoken.encoding_for_model("gpt-3.5-turbo")
        openai.api_key = OPENAI_API_KEY

    def get_llm_response(self, prompt, system_prompt = "You are a smart, very knowledgable, research assistant."):
        chat_data = [{'role': 'system', "content": system_prompt}, {'role': 'user', 'content': prompt}]
        try:
            response = openai.ChatCompletion.create(model=self.language_model, messages=chat_data)
            # print(chat_data)
            print(response)

            final_response = response['choices'][0]['message']['content']
        
            self.total_prompt_tokens += response['usage']['prompt_tokens']
            self.total_cmpl_tokens += response['usage']['completion_tokens']
        except Exception as e:
            final_response = ""
            response = None
            print(e)

        # print(self.get_current_cost())
        
        return final_response, response

    def get_current_cost(self):
        return self.total_prompt_tokens*self.price_inp + self.total_cmpl_tokens*self.price_out
        
    def get_estimated_cost(self, prompt, completion_estimate_len=100):
        # Assumes the system prompt is small, and prompt variable contains all text to be processed by LLM        
        return len(self.tokenizer.encode(prompt))*self.price_inp + completion_estimate_len*self.price_out
