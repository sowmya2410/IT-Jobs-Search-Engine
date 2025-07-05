import csv
from pymongo import MongoClient

# MongoDB connection
client = MongoClient("mongodb://localhost:29017/")  # Replace with your MongoDB URI if hosted remotely
db = client["jobdatabase"]  # Database name
collection = db["job_listings"]  # Collection name

# CSV file to read data
csv_file = "position_salary_combined_tokenized_with_numbers.csv"

# Function to insert data into MongoDB
def insert_jobs_to_mongodb(csv_file):
    with open(csv_file, "r", encoding="ISO-8859-1") as f:
        reader = csv.DictReader(f)
        job_entries = []

        for row in reader:
            # Create a dictionary to insert into MongoDB
            job_entry = {
                "position": row.get("Position", ""),
                "combined_tokens": row.get("Combined_Tokens", ""),
                "location": row.get("Location", ""),
                "education": row.get("Education", ""),
                "experience": int(row.get("Experience (Years)", 0)),
                "salary": int(row.get("Salary", 0)),
                "skills": row.get("Skills", "").split(",")  # Convert skills to a list
            }
            job_entries.append(job_entry)

        # Insert all entries in bulk
        if job_entries:
            collection.insert_many(job_entries)
            print(f"Inserted {len(job_entries)} job records into MongoDB.")
        else:
            print("No job records found in the CSV file.")

# Call the function to insert jobs into MongoDB
insert_jobs_to_mongodb(csv_file)
