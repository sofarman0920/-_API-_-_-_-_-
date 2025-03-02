import spotipy  # Spotify API를 사용하기 위한 라이브러리
import requests  # HTTP 요청을 보내기 위한 라이브러리
from spotipy.oauth2 import SpotifyClientCredentials  # Spotify 인증을 위한 모듈
import pandas as pd  # 데이터 분석 및 CSV 저장을 위한 라이브러리
import json  # JSON 형식의 데이터 처리를 위한 모듈
import time  # 시간 지연을 위한 모듈
import random  # 무작위 수 생성을 위한 모듈
import logging  # 로그 출력을 위한 모듈
from datetime import datetime, timedelta  # 날짜 및 시간 계산을 위한 모듈
from tqdm import tqdm  # 진행 상황 표시를 위한 모듈
from typing import List, Dict, Any  # 타입 힌팅을 위한 모듈
from requests.adapters import HTTPAdapter  # HTTP 어댑터 설정을 위한 모듈
from urllib3.util.retry import Retry  # 재시도 로직을 설정하기 위한 모듈

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SpotifyChartHistory:
    def __init__(self, client_id: str, client_secret: str, max_retries=5, backoff_factor=1, delay_seconds: int = 2):
        self.client_id = client_id
        self.client_secret = client_secret
        self.max_retries = max_retries  # 최대 재시도 횟수 설정
        self.backoff_factor = backoff_factor  # 재시도 간격 증가율 설정
        self.delay_seconds = delay_seconds  # 요청 간 대기 시간 설정
        self.sp = self._create_spotify_client()  # Spotify 클라이언트 생성

    def _create_spotify_client(self):
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],  # 재시도할 HTTP 상태 코드 목록
            allowed_methods=["GET", "POST"]  # 재시도가 허용된 HTTP 메소드 목록
        )

        auth_manager = SpotifyClientCredentials(
            client_id=self.client_id,
            client_secret=self.client_secret
        )

        session = requests.Session()
        session.mount("https://", HTTPAdapter(max_retries=retry_strategy))
        
        return spotipy.Spotify(auth_manager=auth_manager, requests_timeout=10, requests_session=session)

    def make_api_request(self, func, *args, **kwargs):
        max_attempts = 5
        base_delay = 2

        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except spotipy.exceptions.SpotifyException as e:
                if e.http_status == 429:
                    retry_after = int(e.headers.get('Retry-After', 5))
                    wait_time = base_delay * (2 ** attempt) + random.uniform(0, 2)
                    wait_time = min(wait_time, max(retry_after, 5))
                    logging.warning(f"Rate limit exceeded. Waiting {wait_time} seconds...")
                    time.sleep(wait_time)
                    continue

                raise e

            except Exception as e:
                logging.error(f"Unexpected error: {str(e)}")
                if attempt < max_attempts - 1:
                    time.sleep(base_delay * (2 ** attempt))
                    continue

                raise e

    def get_track_genres(self, artist_id: str) -> list:
        try:
            artist = self.make_api_request(self.sp.artist, artist_id)
            return artist['genres'] if artist else []
        except:
            return []

    def get_chart_by_date(self, target_date: datetime) -> list:
        formatted_date = target_date.strftime('%Y%m%d')

        try:
            track_ids = []
            tracks_info = []

            playlist = self.make_api_request(self.sp.playlist_tracks, '37i9dQZEVXbNxXF4SkHj9F')

            for idx, item in enumerate(playlist['items'], 1):
                track = item['track']
                track_ids.append(track['id'])
                tracks_info.append({'idx': idx, 'track': track})

            chart_data = []

            for i in range(0, len(track_ids), 100):
                batch_ids = track_ids[i:i+100]
                audio_features_batch = self.make_api_request(self.sp.audio_features, batch_ids)
                
                time.sleep(self.delay_seconds)
                
                for j, features in enumerate(audio_features_batch):
                    if not features:
                        continue
                    
                    track_info = tracks_info[i+j]
                    track = track_info['track']
                    artist_id = track['artists'][0]['id']
                    
                    time.sleep(1)
                    
                    genres = self.get_track_genres(artist_id)
                    
                    chart_data.append({
                        '날짜': formatted_date,
                        '시간': target_date.strftime('%H:%M'),
                        '순위': track_info['idx'],
                        '제목': track['name'],
                        '아티스트': ', '.join([artist['name'] for artist in track['artists']]),
                        '앨범': track['album']['name'],
                        '발매일': track['album']['release_date'],
                        '장르': ', '.join(genres) if genres else 'Unknown',
                        '인기도': track['popularity'],
                        '댄스성': features['danceability'],
                        '에너지': features['energy'],
                        '키': features['key'],
                        '템포': features['tempo'],
                        '음향도': features['acousticness'],
                        '악기비율': features['instrumentalness'],
                        '라이브성': features['liveness'],
                        '긍정도': features['valence'],
                        '앨범이미지': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    })
            
            return chart_data
        
        except Exception as e:
            logging.error(f"차트 데이터 수집 실패: {str(e)}")
            return []

    def get_charts_by_period(self, start_date: datetime, end_date: datetime, interval: str = 'hour') -> List[Dict[str, Any]]:
        all_charts = []
        
        current_date = start_date
        
        interval_timedelta = {
            'hour': timedelta(hours=1),
            'day': timedelta(days=1),
            'week': timedelta(weeks=1),
            'month': timedelta(days=30),
            'year': timedelta(days=365),
        }
        
        delta = interval_timedelta.get(interval, timedelta(hours=1))
        
        total_iterations = int((end_date - start_date) / delta) + 1
        
        with tqdm(total=total_iterations, desc=f"{interval} 단위 차트 데이터 수집") as pbar:
            
            while current_date <= end_date:
                
                daily_chart = self.get_chart_by_date(current_date)
                
                all_charts.extend(daily_chart)
                
                if len(all_charts) % 100 == 0:
                    
                    self.save_intermediate_data(all_charts, current_date)
                    
                current_date += delta
                
                pbar.update(1)
        
        return all_charts
    
    def save_intermediate_data(self, data: list, current_date: datetime):
        
        filename = f"spotify_chart_data_{current_date.strftime('%Y%m%d_%H%M')}.json"
        
        try:
            
            with open(filename, 'w', encoding='utf-8') as f:
                
                json.dump(data, f, ensure_ascii=False, indent=2)
                
                logging.info(f"중간 데이터 저장 완료: {filename}")
        
        except Exception as e:
            
            logging.error(f"데이터 저장 실패: {str(e)}")
    
    @staticmethod
    def verify_spotify_credentials(client_id: str, client_secret: str) -> bool:
        
        try:
            
            client_credentials_manager = SpotifyClientCredentials(
                
                client_id=client_id,
                
                client_secret=client_secret,
                
            )
            
            sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            
            sp.playlist('37i9dQZEVXbNxXF4SkHj9F')
            
            return True
        
        except Exception as e:
            
            logging.error(f"인증 실패: {str(e)}")
            
            return False
    
if __name__ == "__main__":
    try:
        print("Spotify API 인증 정보를 입력해주세요.")
        client_id = input("Client ID: ")
        client_secret = input("Client Secret: ")

        if not SpotifyChartHistory.verify_spotify_credentials(client_id, client_secret):
            print("인증에 실패했습니다. Client ID와 Client Secret을 확인해주세요.")
            exit()

        print("인증이 성공적으로 완료되었습니다.\n")
        print("데이터 수집 주기를 선택해주세요:")
        print("1. 시간별")
        print("2. 일별")
        print("3. 주별")
        print("4. 월별")
        print("5. 연별")

        interval_choice = input("선택 (1-5): ")
        
        # Correctly formatted interval map and assignment
        interval_map = {
            '1': 'hour',
            '2': 'day',
            '3': 'week',
            '4': 'month',
            '5': 'year'
        }
        
        interval = interval_map.get(interval_choice, 'hour')

        while True:
            try:
                start_date_input = input("시작 날짜 (YYYY MM DD HH): ")
                start_date_list = list(map(int, start_date_input.split()))
                end_date_input = input("종료 날짜 (YYYY MM DD HH): ")
                end_date_list = list(map(int, end_date_input.split()))
                
                start_date = datetime(*start_date_list)
                end_date = datetime(*end_date_list)

                if end_date < start_date:
                    print("종료 날짜가 시작 날짜보다 앞설 수 없습니다.")
                    continue

                break

            except ValueError:
                print("올바른 날짜 형식으로 입력해주세요.")
                continue

        print(f"\n데이터 수집 정보:")
        print(f"시작: {start_date.strftime('%Y년 %m월 %d일 %H시')}")
        print(f"종료: {end_date.strftime('%Y년 %m월 %d일 %H시')}")
        print(f"수집 주기: {interval}")

        confirm = input("\n데이터 수집을 시작하시겠습니까? (y/n): ")

        if confirm.lower() == 'y':
            chart_collector = SpotifyChartHistory(client_id, client_secret)
            charts = chart_collector.get_charts_by_period(
                start_date=start_date,
                end_date=end_date,
                interval=interval
            )

            df = pd.DataFrame(charts)
            filename = f'spotify_charts_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}_{interval}.csv'
            df.to_csv(filename, index=False, encoding='utf-8-sig')

            print(f"\n데이터 수집이 완료되었습니다. 파일명: {filename}")

        else:
            print("데이터 수집이 취소되었습니다.")

    except Exception as e:
        print(f"오류 발생: {str(e)}")

