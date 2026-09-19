import re

with open('tests/test_recommend.py', 'r') as f:
    content = f.read()

# Replace data with data["results"] where applicable
content = content.replace('names = [row["name"] for row in data]', 'names = [row["name"] for row in data["results"]]')
content = content.replace('assert len(data) <= 3', 'assert len(data["results"]) <= 3')
content = content.replace('retail_score = next(row["score"] for row in data if row["name"] == "Retail Sales Associate")', 'retail_score = next(row["score"] for row in data["results"] if row["name"] == "Retail Sales Associate")')
content = content.replace('general_score = next(row["score"] for row in data if row["name"] == "General Course")', 'general_score = next(row["score"] for row in data["results"] if row["name"] == "General Course")')

with open('tests/test_recommend.py', 'w') as f:
    f.write(content)
