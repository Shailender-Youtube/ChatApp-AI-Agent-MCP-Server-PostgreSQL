import requests

response = requests.post(
    "http://localhost:8000/query_postgres",
    json={"query": "SELECT customer_name FROM orders;"}
)

print(response.json())
