import requests
import os
from dotenv import load_dotenv

load_dotenv()

def search_review(query):
    url = "https://openapi.naver.com/v1/search/blog.json"
    headers = {
        "X-Naver-Client-Id": os.getenv("NAVER_ID"),
        "X-Naver-Client-Secret": os.getenv("NAVER_SECRET")
    }
    params = {
        "query": query,
        "display": 5,
        "sort": "sim"
    }
    res = requests.get(url, headers=headers, params=params).json()
    return res["items"]
