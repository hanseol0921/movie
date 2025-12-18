from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import urllib.parse

app = Flask(__name__)

# API 키 설정 (실제 키로 교체해주세요)
KOBIS_API_KEY = '0dfd8752d1b4b76ed1d45011c6607d56'  # 영화진흥위원회 API 키
NAVER_CLIENT_ID = 'm6nZpyW187lm1c7iMKSH'  # 네이버 API 클라이언트 ID
NAVER_CLIENT_SECRET = '6yXrem4rjM'  # 네이버 API 시크릿

@app.route('/')
def index():
    return render_template('main.html')

@app.route('/api/boxoffice')
def get_boxoffice():
    target_date = request.args.get('date', '')
    
    # 날짜 형식 변환 (YYYY-MM-DD -> YYYYMMDD)
    formatted_date = target_date.replace('-', '')
    
    url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
    params = {
        'key': KOBIS_API_KEY,
        'targetDt': formatted_date
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movie-detail')
def get_movie_detail():
    movie_name = request.args.get('name', '')
    target_date = request.args.get('date', '')
    
    formatted_date = target_date.replace('-', '')
    
    # 일일 박스오피스에서 영화 정보 가져오기
    url = f'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
    params = {
        'key': KOBIS_API_KEY,
        'targetDt': formatted_date
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        # 해당 영화 찾기
        movie_list = data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
        movie_info = None
        
        for movie in movie_list:
            if movie['movieNm'] == movie_name:
                movie_info = movie
                break
        
        if movie_info:
            # 영화 상세정보 API 호출
            movie_cd = movie_info.get('movieCd')
            detail_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json'
            detail_params = {
                'key': KOBIS_API_KEY,
                'movieCd': movie_cd
            }
            
            detail_response = requests.get(detail_url, params=detail_params)
            detail_data = detail_response.json()
            
            # 박스오피스 정보와 상세정보 결합
            result = {
                'boxoffice': movie_info,
                'detail': detail_data.get('movieInfoResult', {}).get('movieInfo', {})
            }
            
            return jsonify(result)
        else:
            return jsonify({'error': '영화를 찾을 수 없습니다'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/search-movie')
def search_movie():
    movie_name = request.args.get('name', '')
    
    # 영화 목록 검색 API (itemPerPage를 100으로 늘려서 더 많은 결과 가져오기)
    url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json'
    params = {
        'key': KOBIS_API_KEY,
        'movieNm': movie_name,
        'itemPerPage': 100
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        movie_list = data.get('movieListResult', {}).get('movieList', [])
        
        if movie_list:
            # 영화 제목이 정확히 일치하거나 가장 유사한 영화 찾기
            exact_match = None
            best_match = None
            
            for movie in movie_list:
                if movie.get('movieNm', '').lower() == movie_name.lower():
                    exact_match = movie
                    break
                elif movie_name.lower() in movie.get('movieNm', '').lower():
                    if not best_match:
                        best_match = movie
            
            target_movie = exact_match or best_match or movie_list[0]
            
            # 선택된 영화의 상세정보 가져오기
            movie_cd = target_movie.get('movieCd')
            detail_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieInfo.json'
            detail_params = {
                'key': KOBIS_API_KEY,
                'movieCd': movie_cd
            }
            
            detail_response = requests.get(detail_url, params=detail_params)
            detail_data = detail_response.json()
            
            return jsonify(detail_data)
        else:
            return jsonify({'error': '검색 결과가 없습니다'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movie-reviews')
def get_movie_reviews():
    movie_name = request.args.get('name', '')
    
    url = 'https://openapi.naver.com/v1/search/blog.json'
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
    }
    params = {
        'query': f'{movie_name} 영화 후기',
        'display': 10,
        'sort': 'sim'
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/movie-poster')
def get_movie_poster():
    movie_name = request.args.get('name', '')
    
    url = 'https://openapi.naver.com/v1/search/movie.json'
    headers = {
        'X-Naver-Client-Id': NAVER_CLIENT_ID,
        'X-Naver-Client-Secret': NAVER_CLIENT_SECRET
    }
    params = {
        'query': movie_name,
        'display': 5  # 여러 결과를 가져와서 매칭
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        data = response.json()
        
        # 영화 제목이 가장 일치하는 것 찾기
        if data.get('items'):
            best_match = None
            for item in data['items']:
                title = item['title'].replace('<b>', '').replace('</b>', '')
                if movie_name in title or title in movie_name:
                    best_match = item
                    break
            
            if not best_match:
                best_match = data['items'][0]
            
            return jsonify({'items': [best_match]})
        
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/period-analysis')
def period_analysis():
    weeks = request.args.get('weeks', '1')  # 1, 2, 4
    
    from datetime import datetime, timedelta
    
    days = int(weeks) * 7
    movie_counts = {}  # {movie_cd: {'name': name, 'count': count, 'dates': []}}
    
    try:
        for i in range(days):
            target_date = datetime.now() - timedelta(days=i+1)
            formatted_date = target_date.strftime('%Y%m%d')
            
            url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
            params = {
                'key': KOBIS_API_KEY,
                'targetDt': formatted_date
            }
            
            response = requests.get(url, params=params)
            data = response.json()
            
            movies = data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
            
            for movie in movies:
                movie_cd = movie['movieCd']
                movie_nm = movie['movieNm']
                
                if movie_cd not in movie_counts:
                    movie_counts[movie_cd] = {
                        'name': movie_nm,
                        'count': 0,
                        'dates': [],
                        'openDt': movie.get('openDt', '')
                    }
                
                movie_counts[movie_cd]['count'] += 1
                movie_counts[movie_cd]['dates'].append(target_date.strftime('%Y-%m-%d'))
        
        # 등장 횟수로 정렬
        sorted_movies = sorted(movie_counts.items(), key=lambda x: x[1]['count'], reverse=True)
        
        result = {
            'period': f'{weeks}주',
            'total_days': days,
            'rankings': [
                {
                    'movieNm': item[1]['name'],
                    'count': item[1]['count'],
                    'openDt': item[1]['openDt'],
                    'percentage': round(item[1]['count'] / days * 100, 1)
                }
                for item in sorted_movies[:20]  # 상위 20개
            ]
        }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/random-movie')
def random_movie():
    from datetime import datetime, timedelta
    import random
    
    try:
        # 최근 30일 중 랜덤한 날짜 선택
        random_days = random.randint(1, 30)
        target_date = datetime.now() - timedelta(days=random_days)
        formatted_date = target_date.strftime('%Y%m%d')
        
        url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
        params = {
            'key': KOBIS_API_KEY,
            'targetDt': formatted_date
        }
        
        response = requests.get(url, params=params)
        data = response.json()
        
        movies = data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
        
        if movies:
            random_movie = random.choice(movies)
            return jsonify({
                'movie': random_movie,
                'date': target_date.strftime('%Y-%m-%d')
            })
        else:
            return jsonify({'error': '영화를 찾을 수 없습니다'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
def search_boxoffice_all():
    movie_name = request.args.get('name', '')
    
    # 먼저 영화 코드 찾기
    search_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/movie/searchMovieList.json'
    search_params = {
        'key': KOBIS_API_KEY,
        'movieNm': movie_name,
        'itemPerPage': 100
    }
    
    try:
        # 영화 검색
        search_response = requests.get(search_url, params=search_params)
        search_data = search_response.json()
        
        movie_list = search_data.get('movieListResult', {}).get('movieList', [])
        
        if not movie_list:
            return jsonify({'found': False, 'error': '해당 영화를 찾을 수 없습니다.'})
        
        # 가장 일치하는 영화 찾기
        target_movie = None
        for movie in movie_list:
            if movie.get('movieNm', '').lower() == movie_name.lower():
                target_movie = movie
                break
            elif movie_name.lower() in movie.get('movieNm', '').lower():
                if not target_movie:
                    target_movie = movie
        
        if not target_movie:
            target_movie = movie_list[0]
        
        movie_cd = target_movie.get('movieCd')
        open_dt = target_movie.get('openDt', '')
        movie_nm = target_movie.get('movieNm', movie_name)
        
        # 주간/주말 박스오피스도 검색 (더 넓은 범위)
        from datetime import datetime, timedelta
        
        # 1. 일별 박스오피스 검색 (최근 180일)
        if open_dt and len(open_dt) == 8:
            start_date = datetime.strptime(open_dt, '%Y%m%d')
        else:
            start_date = datetime.now() - timedelta(days=365)
        
        # 최근 180일간 검색 (약 6개월)
        for i in range(0, 180, 3):  # 3일 간격으로 검색 (속도 개선)
            target_date = datetime.now() - timedelta(days=i+1)
            
            if target_date < start_date:
                break
            
            formatted_date = target_date.strftime('%Y%m%d')
            
            # 일별 박스오피스 검색
            boxoffice_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
            boxoffice_params = {
                'key': KOBIS_API_KEY,
                'targetDt': formatted_date
            }
            
            try:
                boxoffice_response = requests.get(boxoffice_url, params=boxoffice_params)
                boxoffice_data = boxoffice_response.json()
                
                daily_list = boxoffice_data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
                
                for movie in daily_list:
                    if movie.get('movieCd') == movie_cd:
                        movie['searchDate'] = target_date.strftime('%Y-%m-%d')
                        return jsonify({'boxoffice': movie, 'found': True})
            except:
                continue
        
        # 2. 주간 박스오피스도 검색 (더 긴 기간)
        for i in range(0, 52):  # 약 1년치 주간 데이터
            target_date = datetime.now() - timedelta(weeks=i+1)
            
            # 해당 주의 월요일로 설정
            days_since_monday = target_date.weekday()
            monday = target_date - timedelta(days=days_since_monday)
            formatted_date = monday.strftime('%Y%m%d')
            
            weekly_url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchWeeklyBoxOfficeList.json'
            weekly_params = {
                'key': KOBIS_API_KEY,
                'targetDt': formatted_date,
                'weekGb': '0'  # 0: 주간, 1: 주말, 2: 주중
            }
            
            try:
                weekly_response = requests.get(weekly_url, params=weekly_params)
                weekly_data = weekly_response.json()
                
                weekly_list = weekly_data.get('boxOfficeResult', {}).get('weeklyBoxOfficeList', [])
                
                for movie in weekly_list:
                    if movie.get('movieCd') == movie_cd:
                        movie['searchDate'] = formatted_date[:4] + '-' + formatted_date[4:6] + '-' + formatted_date[6:8] + ' (주간)'
                        movie['isWeekly'] = True
                        return jsonify({'boxoffice': movie, 'found': True})
            except:
                continue
        
        # 박스오피스에서 못 찾았지만 영화 정보는 있음
        return jsonify({
            'found': False, 
            'error': f'"{movie_nm}" 영화는 최근 박스오피스 기록이 없습니다. 개봉일이 오래되었거나 아직 개봉하지 않은 영화일 수 있습니다.',
            'movieInfo': target_movie
        })
            
    except Exception as e:
        return jsonify({'found': False, 'error': f'검색 중 오류 발생: {str(e)}'})



if __name__ == '__main__':
    app.run(debug=True)