from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# API 키 설정
KOBIS_API_KEY = '0dfd8752d1b4b76ed1d45011c6607d56'  # 영화진흥위원회 API 키
NAVER_CLIENT_ID = 'm6nZpyW187lm1c7iMKSH'  # 네이버 API 클라이언트 ID
NAVER_CLIENT_SECRET = '6yXrem4rjM'  # 네이버 API 시크릿

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/daily-boxoffice')
def daily_boxoffice():
    """일간 박스오피스 TOP 10 (순위 변동 포함)"""
    target_date = request.args.get('date')
    
    if not target_date:
        yesterday = datetime.now() - timedelta(days=1)
        target_date = yesterday.strftime('%Y%m%d')
    else:
        target_date = target_date.replace('-', '')
    
    url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
    params = {
        'key': KOBIS_API_KEY,
        'targetDt': target_date
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'boxOfficeResult' in data:
            movies = data['boxOfficeResult']['dailyBoxOfficeList']
            # 각 영화에 순위 변동 정보 추가
            for movie in movies:
                rank_change = int(movie.get('rankOldAndNew', '0'))
                rank_inten = int(movie.get('rankInten', 0))
                
                movie['rankStatus'] = 'new' if rank_change == 1 else 'old'
                movie['rankChange'] = rank_inten
                
            return jsonify({'success': True, 'movies': movies})
        else:
            return jsonify({'success': False, 'message': '데이터를 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/weekly-boxoffice')
def weekly_boxoffice():
    """주간 박스오피스 TOP 10"""
    weeks_ago = request.args.get('weeks', 1, type=int)
    
    # 지정된 주차 전의 일요일 날짜 계산
    today = datetime.now()
    days_since_sunday = (today.weekday() + 1) % 7
    target_sunday = today - timedelta(days=days_since_sunday + (7 * weeks_ago))
    target_date = target_sunday.strftime('%Y%m%d')
    
    url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchWeeklyBoxOfficeList.json'
    params = {
        'key': KOBIS_API_KEY,
        'targetDt': target_date,
        'weekGb': '0'
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'boxOfficeResult' in data:
            movies = data['boxOfficeResult']['weeklyBoxOfficeList']
            return jsonify({'success': True, 'movies': movies})
        else:
            return jsonify({'success': False, 'message': '데이터를 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/movie-detail/<movie_code>')
def movie_detail(movie_code):
    """영화 상세 정보 조회"""
    url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json'
    params = {
        'key': KOBIS_API_KEY,
        'movieCd': movie_code
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'movieInfoResult' in data and 'movieInfo' in data['movieInfoResult']:
            movie_info = data['movieInfoResult']['movieInfo']
            return jsonify({'success': True, 'movie': movie_info})
        else:
            return jsonify({'success': False, 'message': '영화 정보를 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/random-movie')
def random_movie():
    """랜덤 영화 추천"""
    yesterday = datetime.now() - timedelta(days=1)
    target_date = yesterday.strftime('%Y%m%d')
    
    url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
    params = {
        'key': KOBIS_API_KEY,
        'targetDt': target_date
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if 'boxOfficeResult' in data:
            movies = data['boxOfficeResult']['dailyBoxOfficeList']
            if movies:
                random_movie = random.choice(movies)
                return jsonify({'success': True, 'movie': random_movie})
        
        return jsonify({'success': False, 'message': '영화를 찾을 수 없습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/search-blog')
def search_blog():
    """네이버 블로그 후기 검색"""
    keyword = request.args.get('keyword', '')
    display = request.args.get('display', 10)
    
    if not keyword:
        return jsonify({'success': False, 'message': '검색어를 입력해주세요.'})
    
    url = 'https://openapi.naver.com/v1/search/blog.json'
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
    }
    params = {
        'query': keyword + ' 영화 후기',
        'display': display,
        'sort': 'sim'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        if 'items' in data:
            return jsonify({'success': True, 'items': data['items'], 'total': data['total']})
        else:
            return jsonify({'success': False, 'message': '검색 결과가 없습니다.'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    app.run(debug=True)