
from xml.parsers.expat import model
import openai
import tiktoken
import json
import os
from openai import OpenAI
from google import genai
from google.genai import types

# from utils import llm_price_maps

pricing_map = {'openai:gpt-4.1': [2.0/1000000, 8.0/1000000],
               'openai:gpt-4.1-mini': [.40/1000000, 1.6/1000000], 
               'openai:gpt-4o': [0.03/1000, 0.06/1000],
               'openai:gpt-4o-mini': [0.003/1000, 0.004/1000],
               'gemini:gemini-2.5-flash': [0.0001, 0.0001],
               'local:qwen3-0.6b': [0.000, 0.000],
               'local:qwen2.5-1.5b-instruct': [0.000, 0.000],
               "local:deepseek/deepseek-r1-0528-qwen3-8b": [0.000, 0.000]}

# pricing_map = llm_price_maps.pricing_map

# def get_llm_models(small_mdl, large_mdl):
#     OPENAI_API_KEY = "XXX"

#     if not os.path.exists('settings.json'):
#         OPENAI_API_KEY = input("Please enter your OPENAI Key: ")

#         data = {"OPENAI_API_KEY": OPENAI_API_KEY}
#         with open('settings.json', 'w') as f:
#             json.dump(data, f, indent=4) 

#     with open('settings.json', 'r') as file:
#         data = json.load(file)
#         field_name = "OPENAI_API_KEY"
#         OPENAI_API_KEY = data[field_name]

#     short_context_model = llmOperations(OPENAI_API_KEY, small_mdl, price_inp=pricing_map[small_mdl][0], price_out=pricing_map[small_mdl][1])
#     long_context_model = llmOperations(OPENAI_API_KEY, large_mdl, price_inp=pricing_map[large_mdl][0], price_out=pricing_map[large_mdl][1])

#     return short_context_model, long_context_model

class llmOperations:    
    total_prompt_tokens = 0
    total_cmpl_tokens = 0

    # openai.api_key = 'XXX'
    def __init__(self, API_KEY, language_model, price_inp, price_out):
        print("Initializing LLM connection with model: ", language_model)
        self.language_model = language_model.split(':')[1]  # Remove any version suffix if present
        self.model_type = language_model.split(':')[0] # Get the model type (e.g., 'gpt', 'gemini')
        # if 'gemini' in language_model:
        #     model_type = 'gemini'
        # elif 'gpt' in language_model:
        #     model_type = 'openai'
        # else:
        #     raise ValueError("Unsupported model type. Please use 'gemini' or 'gpt' models.")
        
        self.price_inp=price_inp
        self.price_out=price_out    
        self.tokenizer = tiktoken.encoding_for_model("gpt-4o")
        # self.model_type = model_type
        # openai.api.key = OPENAI_API_KEY
        if self.model_type == 'openai':
            self.llm_client = OpenAI(
                api_key=API_KEY,  # this is also the default, it can be omitted
            )
        if self.model_type == 'local':
            self.llm_client = OpenAI(
                base_url="http://localhost:1234/v1",   # default port in LM Studio “Developer → Server”
                api_key="lm-studio"                    # any non-empty string is accepted
            )
        if self.model_type == 'gemini':
            self.llm_client = genai.Client(api_key=API_KEY)

    def get_llm_response(self, prompt, system_prompt = "You are a smart, very knowledgable, research assistant."):
        print('Using model: ', self.language_model)
        print('Using client: ', self.llm_client)

        try:
            if self.model_type == 'openai' or self.model_type == 'local':
                chat_data = [{'role': 'system', "content": system_prompt}, 
                     {'role': 'user', 'content': prompt}]
                # print("Using OpenAI API")
                response = self.llm_client.chat.completions.create(
                    model=self.language_model, messages=chat_data)
                print("OpenAI response: ", response)
                final_response = response.choices[0].message.content

                self.total_prompt_tokens += response.usage.prompt_tokens
                self.total_cmpl_tokens += response.usage.completion_tokens

            elif self.model_type == 'gemini':
                response = self.llm_client.models.generate_content(
                    model=self.language_model,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt),
                    contents=prompt
                )
                final_response = response.text
                self.total_prompt_tokens = 0
                self.total_cmpl_tokens = 0

        except Exception as e:
            print("Error in getting response from LLM: ", e)
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
