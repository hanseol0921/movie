from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime, timedelta
import urllib.parse

app = Flask(__name__)

# API 키 설정 (실제 키로 교체해주세요)



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

@app.route('/api/search-boxoffice-all')
def search_boxoffice_all():
    movie_name = request.args.get('name', '')
    
    # 최근 30일간 검색
    from datetime import datetime, timedelta
    
    results = []
    found = False
    
    # 어제부터 30일 전까지 검색
    for i in range(30):
        target_date = datetime.now() - timedelta(days=i+1)
        formatted_date = target_date.strftime('%Y%m%d')
        
        url = 'http://www.kobis.or.kr/kobisopenapi/webservice/rest/boxoffice/searchDailyBoxOfficeList.json'
        params = {
            'key': KOBIS_API_KEY,
            'targetDt': formatted_date
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            
            movie_list = data.get('boxOfficeResult', {}).get('dailyBoxOfficeList', [])
            
            for movie in movie_list:
                if movie_name.lower() in movie['movieNm'].lower() or movie['movieNm'].lower() in movie_name.lower():
                    movie['searchDate'] = target_date.strftime('%Y-%m-%d')
                    results.append(movie)
                    found = True
                    break
            
            if found:
                break
                
        except Exception as e:
            continue
    
    if results:
        return jsonify({'boxoffice': results[0], 'found': True})
    else:
        return jsonify({'found': False, 'error': '최근 30일 내 박스오피스에서 해당 영화를 찾을 수 없습니다.'})

if __name__ == '__main__':
    app.run(debug=True)