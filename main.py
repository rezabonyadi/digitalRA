import datetime
import json 
from PIL import Image
import os
import utils.operations as operations
import argparse

def multi_choice(prompt, available_choices):
    print(prompt)

    for idx, a in enumerate(available_choices):
        print(f"{idx+1}. {a}")
    # print("2. 'gpt-3.5-turbo-16k'")
    # print("3. 'gpt-4-0613'")
    while True:
        choice = input(f"Enter your choice (1-{len(available_choices)}): ")
        choice = int(choice)
        
        if choice < len(available_choices)+1:
            return available_choices[choice-1]
        else:
            print("Invalid choice. Please try again.")

def parse_arguments():
    parser = argparse.ArgumentParser(description="Digital Research Assistant")
    parser.add_argument('-w', '--work_dir', type=str, help='Your working directory', default='./results/litrature_revie/')
    parser.add_argument('-s', '--num_search_phrases', type=str, help='Number of search phrases', default='5')
    parser.add_argument('-p', '--num_papers_by_eng', type=str, help='Number of papers to get per search engine', default='20')
    parser.add_argument('-c', '--citations', type=int, help='Min number of citations to consider a paper for review IF the paper is older than the min year', default=100)
    parser.add_argument('-y', '--year', type=int, help='Min publication year to consider a paper for review', default=100)
    parser.add_argument('-l', '--len', type=int, help='Length of the final litrature review', default=1500)
    

    return parser.parse_args()

def main():
    args = parse_arguments()
    print(f"Your working directory, {args.work_dir}, min number of citations {args.citations}, and min year {args.year}, to write a litrature review of the length {args.len}.")

    litrature_review_len = int(args.len)
    min_year = int(args.year)
    min_cite = int(args.citations)
    working_dir = args.work_dir
    num_search_phrases = int(args.num_search_phrases)
    num_papers_by_eng = int(args.num_papers_by_eng)

    if not os.path.exists(working_dir):
        os.makedirs(working_dir)

    small_mdl = multi_choice("Please select a brain for short context tasks:", ['gpt-3.5-turbo-0613', 'gpt-3.5-turbo-16k'])
    large_mdl = multi_choice("Please select a brain for long context tasks:", ['gpt-3.5-turbo-16k', 'gpt-4-0613'])
    short_context_model, long_context_model = operations.get_llm_models(small_mdl, large_mdl)
    print('info> Loaded ' + small_mdl + ' for short context cases and ' + large_mdl + ' for long context inferences.')

    print('-------------- Hiring your digital Research Assistant\n')
    idea_text = input("> Please insert a paragraph describing your idea: ")
    researcher_spec = operations.get_research_assistant(idea_text, short_context_model)
    print('Cost> your cost so far: ', short_context_model.get_current_cost())
    print('')

    print("Digital RA> Hi, I am your research assistant. Here is what I am expert at:\n\n" + researcher_spec)

    print('Do you want me to acquire other capability?')
    extra = input("Please enter extra capabilities if you do, or just Enter if you are satisfied with my expertiese: ")
    researcher_spec = researcher_spec + ' ' + extra + " You are the best in the world in this field. "
    print('\n Digital RA> My capabilities: \n\n' + researcher_spec)

    print('-------------- Extracts search phrases')
    print('Digital RA> Extracting search phrases for your idea above ...\n')

    search_phrases = operations.extract_search_phrases(working_dir, idea_text, short_context_model, researcher_spec, num_search_phrases)
    # print(search_phrases)
    print('Digital RA> Here are search phrases I suggest: \n', '\n'.join(search_phrases))
    extra = input("Digital RA> Any other search phrase you want to add (seperate with ';'). Hit Enter if you are happy with the search phrases above: ")

    if extra != '':
        for i in extra.split(';'):
            search_phrases.append(i)

    with open(working_dir + 'search_phrases.txt', 'w') as f:
        f.write('\n'.join(search_phrases))

    print('Digital RA> The final search phrases are: ', search_phrases)    
    print('Digital RA> your cost so far: ', short_context_model.get_current_cost())
    print('Digital RA> you can go to '+working_dir+' and change the file search_phrases.txt if you want to change the phrases further.')
    
    print('-------------- Preparing the idea')
    print('Digital RA> Let me summarize your research idea ...\n\n')

    idea_text_summary = operations.get_idea_summary(idea_text, short_context_model, researcher_spec)
    print('Digital RA> Here is a summary of your idea: \n', idea_text_summary)
    extra = input("Digital RA> Is this a fair summary (if yes, press enter, if no, enter a new summary): ")

    if extra != "":
        idea_text_summary = extra
    with open(working_dir + 'idea_summary.txt', 'w') as f:
        f.write('Idea: \n\n')
        f.write(idea_text)
        f.write('\n\n idea summary:\n\n')
        f.write(idea_text_summary)

    print('Digital RA> your cost so far: ', short_context_model.get_current_cost())
    print('Digital RA> you can go to '+working_dir+' and change the file idea_summary.txt if you want to change the summary further.')
    
    print('-------------- Finding papers')
    print('Digital RA> Lets get some papers ...\n\n')

    engines = multi_choice("Digital RA> From which search engine do yo uwant me to get the papers: ", ['gscholar', 'pubmed', 'semscholar'])

    print('Digital RA> Here are my research parameters:\n')
    print(engines)
    print(search_phrases)
    print(working_dir)
    
    papers_df = operations.get_research_papers(working_dir, search_phrases, engines=[engines], num_papers_by_eng=num_papers_by_eng)
    papers_df.to_csv(working_dir+'papers_found.csv')

    print(f'Digital RA> Found  {papers_df.shape[0]} articles.')
    print('Digital RA> Let me go through these and rank them by relevance to our research idea')

    relevance_scores_df = operations.papers_relevances(working_dir, papers_df, researcher_spec, 
                                                        idea_text_summary, short_context_model)
    relevance_scores_df.to_csv(working_dir + '/first_level_analysis.csv')
    print('')
    print('Digital RA> I am ready with the papers now, also saved them in a file for you. These papers are going to be used for the litrature review I am writing.')            
    print('Digital RA> you can go to '+working_dir+' and change the file first_level_analysis.txt if you want to change the papers or add/remove.')
    input('Hit Enter to continue')

    print('-------------- Filtering papers to prepare for the review ')
    
    print(f'Digital RA> I am now filtering the papers by {min_cite} min number of citations OR year of publications of {min_year} on-wards for the review')

    papers_df, concated_data = operations.filter_papers_for_review(min_year, min_cite, working_dir, 
                                                              long_context_model, relevance_scores_df)
    
    with open(working_dir + 'used_papers_review.txt', 'w', encoding="utf-8-sig") as f:
        f.write(concated_data)
    print('Digital RA> you can go to '+working_dir+' and change the file used_papers_review.txt if you want to change the papers or add/remove.')

    estimated_cost = long_context_model.get_estimated_cost(concated_data, litrature_review_len)

    print(f'Digital RA> Estimated cost for litrature review: {estimated_cost} to write a review of around {litrature_review_len*3/4} words')

    extra = input("Digital RA> are you ok with the cost (Y/n): ")
    if extra.lower() == 'n':
        pass

    # Write the litrature review
    litrature_review = operations.write_litrature_review(working_dir, long_context_model, researcher_spec, idea_text_summary, papers_df, concated_data)

    print(f'Digital RA> Total cost: {long_context_model.get_current_cost()+short_context_model.get_current_cost()}')
    print('--------------')

    extra = input("Digital RA> Do you want to chat with the condensed data used for review (Y/n): ")
    if extra.lower() == 'n':
        pass

    operations.enable_chat(researcher_spec, concated_data, idea_text_summary, long_context_model.get_current_cost()+short_context_model.get_current_cost())

if __name__ == "__main__":    
    main()