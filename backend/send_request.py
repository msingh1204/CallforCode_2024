"""Run this to see how the response from the flask apps shortest_path route looks

    python send_request.py
"""

import requests

url = "http://localhost:8100/geocode_address"

response = requests.get(url, params={ "address": "20 W 34th St., New York, NY 10001"})

# Print the response
print("Status Code:", response.status_code)
print("Response Text:", response.text)
