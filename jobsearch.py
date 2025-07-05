import streamlit as st
from whoosh.index import open_dir
from whoosh.qparser import MultifieldParser
from whoosh.query import Term, TermRange
import os
import re  # Make sure this line is present for regular expressions

# Define the path to the index directory
index_dir = "job_index"

# Load the Whoosh index
def load_index():
    if os.path.exists(index_dir):
        ix = open_dir(index_dir)
        return ix
    else:
        st.error("Index not found!")
        return None

# Helper function to dynamically identify fields based on keywords in the query
def identify_relevant_fields(query_string):
    fields = {
        "position": ["engineer", "developer", "manager", "scientist", "designer", "architect", "analyst"],
        "location": ["delhi", "bangalore", "hyderabad", "chennai", "mumbai", "pune"],
        "education": ["bachelor", "master", "phd", "diploma"],
        "experience": ["years", "experience", "freshers"],
        "salary": ["lpa", "salary", "package"]
    }

    matched_fields = []
    for field, keywords in fields.items():
        for keyword in keywords:
            if keyword.lower() in query_string.lower():
                matched_fields.append(field)
                break
    return matched_fields

# Function for full-text search across selected fields
def full_text_search(ix, query_string, fields):
    with ix.searcher() as searcher:
        parser = MultifieldParser(fields, schema=ix.schema)
        query = parser.parse(query_string)
        results = searcher.search(query, limit=10)
        return results

# Function to handle salary range query
def salary_range_query(ix, query_string):
    # Using regular expression to search for "greater than <salary>"
    salary_match = re.search(r'greater than (\d+)', query_string)
    if salary_match:
        salary = salary_match.group(1)
        with ix.searcher() as searcher:
            query = TermRange("salary_in_lpa", salary, None)  # Salary greater than the number
            results = searcher.search(query, limit=10)
            return results
    return None

# Function to display search results
def display_results(results):
    if results:
        for result in results:
            st.write("**Position**:", result['position'])
            st.write("**Location**:", result['location'])
            st.write("**Education**:", result['education'])
            st.write("**Experience (Years)**:", result['experience'])
            st.write("**Salary (in LPA)**:", result['salary_in_lpa'])
            st.write("-" * 40)
    else:
        st.write("No results found.")

# Streamlit interface
st.title("Job Search Engine")

# Query input
query = st.text_input("Enter your job search query:")

# Perform search when the user submits a query
if query:
    ix = load_index()
    if ix:
        # Identify relevant fields based on the query
        matched_fields = identify_relevant_fields(query)
        
        # If no specific fields match, search across all fields
        if not matched_fields:
            matched_fields = ["position", "location", "education", "experience", "salary_in_lpa"]
        
        # Perform a salary range query if applicable (e.g., "greater than 10 LPA")
        range_results = salary_range_query(ix, query)
        
        if range_results:
            display_results(range_results)
        else:
            # Perform a full-text search on the matched fields
            results = full_text_search(ix, query, matched_fields)
            display_results(results)
