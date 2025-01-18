
import os
import json
import subprocess
import requests
import pandas as pd


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

import arxiv

# def get_arxiv_papers(query: str, max_results: int=10):
#     """
#     Fetch papers from arXiv using the `arxiv` library with the updated `Client.results`.

#     Parameters:
#     - query (str): Search query for arXiv.
#     - max_results (int): Number of results to fetch (default: 10).

#     Returns:
#     - List of dictionaries with titles, abstracts, date, and URLs of papers.
#     """
#     print("Called with " + query + " and " + str(max_results))
#     # Initialize the search query
#     search = arxiv.Search(
#         query=query,
#         max_results=max_results,
#         sort_by=arxiv.SortCriterion.Relevance
#     )

#     # Initialize the client
#     client = arxiv.Client()

#     # Fetch results using the client
#     papers = []
#     print(search)

#     for result in client.results(search):
#         papers.append({
#             "title": result.title,
#             "abstract": result.summary.replace("\n", " "),  # Clean up formatting
#             "date": result.published,
#             "url": result.entry_id,
#         })
#     # print(papers)
#     return papers

import datetime

def get_arxiv_papers(query: str, max_results: int = 10):
    """
    Fetch papers from arXiv using the `arxiv` library and format the output
    in a specific structure.

    Parameters:
    - query (str): Search query for arXiv.
    - max_results (int): Number of results to fetch (default: 10).

    Returns:
    - List of dictionaries formatted with specific fields.
    """
    # Initialize the search query
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance
    )

    # Initialize the client
    client = arxiv.Client()

    # Fetch results using the client
    papers = []
    
    for rank, result in enumerate(client.results(search), start=1):
        # Extract authors
        authors = [author.name for author in result.authors]

        # Format the output
        paper = {
            "uid": f"ARXIV:{rank}",  # Generate a unique identifier for each paper
            "title": result.title,
            "source": result.journal_ref or f"arXiv preprint {result.entry_id.split('/')[-1]}",
            "publisher": "arxiv.org",
            "article_url": result.entry_id,
            "cites_url": "",  # Placeholder (arXiv does not provide citation data directly)
            "fulltext_url": result.pdf_url or "",  # PDF URL if available
            "related_url": "",  # Placeholder (not provided by arXiv API)
            "abstract": result.summary.replace("\n", " "),  # Clean up formatting
            "rank": rank,
            "year": result.published.year if result.published else 0,
            "volume": 0,  # Placeholder (arXiv does not have volume information)
            "issue": 0,  # Placeholder (arXiv does not have issue information)
            "startpage": 0,  # Placeholder (not available from arXiv API)
            "endpage": 0,  # Placeholder (not available from arXiv API)
            "cites": 0,  # Placeholder (arXiv does not provide citation data directly)
            "ecc": 0,  # Placeholder (not available from arXiv API)
            "use": 1,  # Arbitrary default value
            "authors": authors
        }

        papers.append(paper)

    return papers

def get_biorxiv_papers(query: str, max_results: int = 10):
    """
    Fetch papers from bioRxiv using the Europe PMC API and format the output
    in a specific structure.

    Parameters:
    - query (str): Search query for bioRxiv.
    - max_results (int): Number of results to fetch (default: 10).

    Returns:
    - List of dictionaries formatted with specific fields.
    """
    url = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
    params = {
        "query": f"{query} AND SRC:PPR",  # Filter for preprints
        "resultType": "core",
        "pageSize": max_results,
        "format": "json",
    }
    response = requests.get(url, params=params)
    response.raise_for_status()

    data = response.json()
    papers = []
    
    for rank, result in enumerate(data.get("resultList", {}).get("result", []), start=1):
        authors = result.get("authorString", "").split(", ")

        paper = {
            "uid": f"BIORXIV:{rank}",
            "title": result.get("title", ""),
            "source": result.get("source", "bioRxiv"),
            "publisher": "bioRxiv",
            "article_url": result.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", ""),
            "cites_url": "",  # Placeholder (not provided by Europe PMC API)
            "fulltext_url": result.get("fullTextUrlList", {}).get("fullTextUrl", [{}])[0].get("url", ""),
            "related_url": "",  # Placeholder (not provided by Europe PMC API)
            "abstract": result.get("abstractText", ""),
            "rank": rank,
            "year": int(result.get("firstPublicationDate", "0-0-0").split("-")[0]) if result.get("firstPublicationDate") else 0,
            "volume": 0,  # Placeholder (bioRxiv does not have volume information)
            "issue": 0,  # Placeholder (bioRxiv does not have issue information)
            "startpage": 0,  # Placeholder (not available from Europe PMC API)
            "endpage": 0,  # Placeholder (not available from Europe PMC API)
            "cites": 0,  # Placeholder (not provided by Europe PMC API)
            "ecc": 0,  # Placeholder (not available from Europe PMC API)
            "use": 1,  # Arbitrary default value
            "authors": authors
        }

        papers.append(paper)

    return papers

def get_papers(search_phrase, dataset="semscholar", max_papers=5):
    if dataset in ["semscholar", "gscholar", "pubmed"]:
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
    
    if dataset == "arxiv":
        print(search_phrase)
        papers = get_arxiv_papers(search_phrase, max_results=max_papers)
        # print(papers[0])
        # print(len(papers))
        # print(all_papers)
        return pd.DataFrame(papers)
    
    if dataset == "bioarxiv":
        print(search_phrase)
        papers = get_biorxiv_papers(search_phrase, max_results=max_papers)
        # print(papers[0])
        # print(len(papers))
        # print(all_papers)
        return pd.DataFrame(papers)
