import requests
import os
from dotenv import load_dotenv

load_dotenv()
KOBIS_KEY = os.getenv("KOBIS_KEY")

# 일일 박스오피스 TOP 10
def daily_boxoffice(date):
    url = "https://kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json"
    params = {
        "key": KOBIS_KEY,
        "targetDt": date
    }
    res = requests.get(url, params=params).json()
    return res["boxOfficeResult"]["dailyBoxOfficeList"]

# 영화 상세정보
def movie_info(movie_cd):
    url = "https://kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json"
    params = {
        "key": KOBIS_KEY,
        "movieCd": movie_cd
    }
    res = requests.get(url, params=params).json()
    return res["movieInfoResult"]["movieInfo"]
