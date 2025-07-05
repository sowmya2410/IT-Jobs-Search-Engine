import csv
import spacy
from whoosh.index import create_in
from whoosh.fields import Schema, TEXT, ID, NUMERIC
from whoosh.qparser import MultifieldParser
from fuzzywuzzy import fuzz
import os

# Load spaCy model for tokenization and Named Entity Recognition (NER)
nlp = spacy.load("en_core_web_sm")

# Step 1: Define the schema for the index
schema = Schema(
    id=ID(stored=True, unique=True),
    combined_tokens=TEXT(stored=True),  # Combined tokens column from the CSV
    position=TEXT(stored=True),
    location=TEXT(stored=True),
    education=TEXT(stored=True),
    experience=NUMERIC(stored=True),
    salary=NUMERIC(stored=True),
    skills=TEXT(stored=True)
)

# Step 2: Create the index directory
index_dir = "job_index"
if not os.path.exists(index_dir):
    os.mkdir(index_dir)

# Create an index in the directory
ix = create_in(index_dir, schema)

# Step 3: Add CSV data to the index
csv_file = "position_salary_combined_tokenized_with_numbers.csv"  # Tokenized CSV
with ix.writer() as writer:
    with open(csv_file, "r", encoding="ISO-8859-1") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            writer.add_document(
                id=str(i),
                combined_tokens=' '.join(eval(row.get("Combined_Tokens", "[]"))),  # Evaluate tokens
                position=row.get("Position", ""),
                location=row.get("Location", ""),
                education=row.get("Education", ""),
                experience=int(row.get("Experience (Years)", 0)),
                salary=int(row.get("Salary", 0)),
                skills=row.get("Skills", "")
            )
print("Indexing completed.")

# Define synonyms for locations
location_synonyms = {
    "bengaluru": "bangalore",
    "chennai": "chennai",
    "delhi": "new delhi",
    "mumbai": "mumbai"
}

# Function to preprocess user query with spaCy
def preprocess_query(query):
    doc = nlp(query)
    tokens = []
    location = None
    experience = None
    salary = None

    # Extract meaningful information from the query
    for token in doc:
        if token.ent_type_ == "GPE":  # Location
            location = location_synonyms.get(token.text.lower(), token.text.lower())
        elif token.ent_type_ == "CARDINAL":  # Numbers for experience or salary
            if "year" in query or "experience" in query:
                experience = int(token.text)
            elif "lpa" in query or "lakh" in query:
                salary = int(token.text)
        elif token.is_alpha:
            tokens.append(token.text)

    return tokens, location, experience, salary

# Function for combined search with fuzzy matching
def combined_search(query_string):
    tokens, location, experience, salary = preprocess_query(query_string)
    query_tokens = ' '.join(tokens)

    with ix.searcher() as searcher:
        parser = MultifieldParser(["combined_tokens"], schema=ix.schema)
        parsed_query = parser.parse(query_tokens)

        # Search with BM25 ranking
        bm25_results = searcher.search(parsed_query, limit=20)
        
        # Perform fuzzy matching for location, position, and skills
        results_with_scores = []
        for result in bm25_results:
            combined_tokens = result['combined_tokens'].lower()
            fuzzy_score = fuzz.partial_ratio(query_tokens, combined_tokens)

            # Apply additional matching for numeric fields
            if location and location in combined_tokens:
                fuzzy_score += 10
            if experience and str(experience) in combined_tokens:
                fuzzy_score += 10
            if salary and str(salary) in combined_tokens:
                fuzzy_score += 10

            results_with_scores.append((result, fuzzy_score))

        # Sort results by combined fuzzy scores
        results_with_scores.sort(key=lambda x: x[1], reverse=True)

        # Display results
        print(f"Results for '{query_string}':")
        for result, score in results_with_scores:
            print("Position:", result['position'])
            print("Location:", result['location'])
            print("Education:", result['education'])
            print("Experience (Years):", result['experience'])
            print("Salary:", result['salary'])
            print("Skills:", result['skills'])
            print("Combined Tokens:", result['combined_tokens'])
            print("Relevance Score (Fuzzy + BM25):", score)
            print("-" * 40)

# Example searches
search_query = "show me job roles for engineer in bengaluru for 11 years of experience"
combined_search(search_query)

search_query = "show me jobs with 21LPA"
combined_search(search_query)
