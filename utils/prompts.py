

def get_researcher_prompt(idea_text):
    prompt = f"""Here is a research proposal:\n{idea_text} 
If a professor is going to research this propsoal, what would the professor be expert at? 
List 3-5 main competencies needed to be world-class successful in this research. 
Generate the answer in the format of "You are an expeert in the field of XXX, with following competencies: """
    return prompt

def get_search_phrases_prompt(idea_text, researcher_spec, num_search_phrases):
    prompt = f"""Extract search phrases for the following research proposal:\n{idea_text}\n\nResearcher expertise: {researcher_spec}\n\nExtract {num_search_phrases} search phrases that can be used to find relevant papers for this research proposal."""
    return prompt

def get_idea_summary_prompt(idea_text, researcher_spec):
    prompt = f"""Summarize the following research proposal:\n{idea_text}\n\nResearcher expertise: {researcher_spec}\n\nSummarize this research idea to a concise paragraph while make sure it does not loose any important message or question."""
    return prompt   

def get_papers_relevance_prompt(idea_text_summary, abstract):
    prompt = f"""Here is an idea:  

{idea_text_summary}

END OF IDEA

How relevant this idea is to the following abstract of a paper: 

{abstract} 

END OF ABSTRACT

Pick the relevance score is either "very low", "low", "medium", "high", or "very high". 
You always output as JSON, with fields "relevance" and "reason", which would look like:

{{"relevance": "RELEVANCE", "reason": "THE REASON"}} 

Include nothing but this json format output in your response."""
    
    return prompt