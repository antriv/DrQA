# USAGE
# python simple_request.py arg1

# import the necessary packages
import requests
import sys
import json

REST_API_URL = "http://104.41.140.195:5000/predict"

question = sys.argv[1]
print(question)

# load the input and construct the payload for the request
payload = {"question": question}

# submit the request
r = requests.post(REST_API_URL, json=payload).json()
# ensure the request was sucessful
if r["success"]:
	print(r["predictions"][0])

# otherwise, the request failed
else:
	print("Request failed")
