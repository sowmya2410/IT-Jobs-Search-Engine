import streamlit as st
from pymongo import MongoClient
from fuzzywuzzy import fuzz

# MongoDB connection
client = MongoClient("mongodb://localhost:29017/")  # Replace with your MongoDB URI if needed
db = client["jobdatabase"]  # Database name
collection = db["job_listings"]  # Collection name

# Streamlit app
st.title("Job Search Application")
st.subheader("Search jobs with keywords using fuzzy matching")

# User input
query = st.text_input("Enter your job query (e.g., 'Software Engineer in Bangalore')", "")

# Process and search
if st.button("Search"):
    if not query.strip():
        st.warning("Please enter a query to search.")
    else:
        # Preprocess query
        query_tokens = query.lower().split()
        query_combined = " ".join(query_tokens)

        # Fetch data from MongoDB
        job_listings = collection.find()
        results = []

        # Perform fuzzy matching
        for job in job_listings:
            combined_tokens = job["combined_tokens"].lower()
            fuzzy_score = fuzz.token_sort_ratio(query_combined, combined_tokens)

            # Add result with score
            results.append({
                "position": job["position"],
                "location": job["location"],
                "education": job["education"],
                "experience": job["experience"],
                "salary": job["salary"],
                "fuzzy_score": fuzzy_score
            })

        # Sort results by fuzzy score in descending order
        sorted_results = sorted(results, key=lambda x: x["fuzzy_score"], reverse=True)

        # Display results
        if not sorted_results or sorted_results[0]["fuzzy_score"] == 0:
            st.error("No matching jobs found.")
        else:
            st.success(f"Found {len(sorted_results)} matching jobs. Displaying top results:")
            for result in sorted_results[:10]:  # Limit to top 10 results
                st.write(f"**Position**: {result['position']}")
                st.write(f"**Location**: {result['location']}")
                st.write(f"**Education**: {result['education']}")
                st.write(f"**Experience**: {result['experience']} years")
                st.write(f"**Salary**: ₹{result['salary']}")
                st.write(f"**Relevance Score**: {result['fuzzy_score']}")
                st.write("-" * 50)
