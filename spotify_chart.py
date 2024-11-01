import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import pandas as pd
import json
import time
from datetime import datetime, timedelta
from tqdm import tqdm
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SpotifyChartHistory:
    def __init__(self, client_id: str, client_secret: str, delay_seconds: int = 2):
        self.delay_seconds = delay_seconds
        self.sp = spotipy.Spotify(
            client_credentials_manager=SpotifyClientCredentials(
                client_id=client_id,
                client_secret=client_secret
            )
        )
    
    def get_track_genres(self, artist_id: str) -> list:
        """아티스트의 장르 정보를 가져옵니다."""
        try:
            artist = self.sp.artist(artist_id)
            return artist['genres']
        except:
            return []

    def get_chart_by_date(self, target_date: datetime) -> list:
        """특정 날짜의 스포티파이 차트 데이터를 가져옵니다."""
        formatted_date = target_date.strftime('%Y%m%d')
        try:
            # 한국 TOP 50 플레이리스트 ID
            playlist_id = '37i9dQZEVXbNxXF4SkHj9F'
            playlist = self.sp.playlist_tracks(playlist_id)
            
            chart_data = []
            for idx, item in enumerate(playlist['items'], 1):
                track = item['track']
                album = track['album']
                artist_id = track['artists'][0]['id']
                
                # 오디오 특성 가져오기
                audio_features = self.sp.audio_features(track['id'])[0]
                
                # 장르 정보 가져오기
                genres = self.get_track_genres(artist_id)
                
                chart_data.append({
                    '날짜': formatted_date,
                    '시간': target_date.strftime('%H:%M'),
                    '순위': idx,
                    '제목': track['name'],
                    '아티스트': ', '.join([artist['name'] for artist in track['artists']]),
                    '앨범': album['name'],
                    '발매일': album['release_date'],
                    '장르': ', '.join(genres) if genres else 'Unknown',
                    '인기도': track['popularity'],
                    '댄스성': audio_features['danceability'],
                    '에너지': audio_features['energy'],
                    '키': audio_features['key'],
                    '템포': audio_features['tempo'],
                    '음향도': audio_features['acousticness'],
                    '악기비율': audio_features['instrumentalness'],
                    '라이브성': audio_features['liveness'],
                    '긍정도': audio_features['valence'],
                    '앨범이미지': album['images'][0]['url'] if album['images'] else None
                })
            
            time.sleep(self.delay_seconds)
            return chart_data
            
        except Exception as e:
            logging.error(f"차트 데이터 수집 실패: {str(e)}")
            return []

    def save_intermediate_data(self, data: list, current_date: datetime):
        """중간 데이터 저장"""
        filename = f"spotify_chart_data_{current_date.strftime('%Y%m%d_%H%M')}.json"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logging.info(f"중간 데이터 저장 완료: {filename}")
        except Exception as e:
            logging.error(f"데이터 저장 실패: {str(e)}")

def get_charts_for_period(client_id: str, client_secret: str, 
                         start_date: datetime, end_date: datetime, 
                         delay_seconds: int = 2) -> list:
    """기간별 차트 데이터를 수집합니다."""
    all_charts = []
    total_hours = int((end_date - start_date).total_seconds() / 3600) + 1
    chart_collector = SpotifyChartHistory(client_id, client_secret, delay_seconds)
    
    try:
        current_date = start_date
        with tqdm(total=total_hours, desc="차트 데이터 수집", unit="hour") as pbar:
            while current_date <= end_date:
                daily_chart = chart_collector.get_chart_by_date(current_date)
                all_charts.extend(daily_chart)
                
                # 100개 데이터마다 중간 저장
                if len(all_charts) % 100 == 0:
                    chart_collector.save_intermediate_data(all_charts, current_date)
                
                current_date += timedelta(hours=1)
                pbar.update(1)
                
        # 최종 데이터 CSV 저장
        df = pd.DataFrame(all_charts)
        df.to_csv(f'spotify_charts_{start_date.strftime("%Y%m%d")}_{end_date.strftime("%Y%m%d")}.csv', 
                 index=False, encoding='utf-8-sig')
        
    except Exception as e:
        logging.error(f"오류 발생: {str(e)}")
        
    return all_charts

def verify_spotify_credentials(client_id: str, client_secret: str) -> bool:
    """Spotify API 인증 확인"""
    try:
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        # 테스트로 한국 차트 접근 시도
        sp.playlist('37i9dQZEVXbNxXF4SkHj9F')
        return True
    except Exception as e:
        logging.error(f"인증 실패: {str(e)}")
        return False

if __name__ == "__main__":
    try:
        # Spotify 인증 정보 입력
        print("Spotify API 인증 정보를 입력해주세요.")
        client_id = input("Client ID: ")
        client_secret = input("Client Secret: ")
        
        # 인증 확인
        print("\n인증 확인 중...")
        if not verify_spotify_credentials(client_id, client_secret):
            print("인증에 실패했습니다. Client ID와 Client Secret을 확인해주세요.")
            exit()
        
        print("인증이 성공적으로 완료되었습니다.\n")
        
        # 날짜 입력 받기
        while True:
            try:
                # 시작 날짜 입력
                start_date_input = input("시작 날짜를 년도, 월, 일, 시간 순으로 공백으로 구분하여 입력해주세요 (예: 2024 1 1 0): ")
                start_date_list = list(map(int, start_date_input.split()))
                
                # 종료 날짜 입력
                end_date_input = input("종료 날짜를 년도, 월, 일, 시간 순으로 공백으로 구분하여 입력해주세요 (예: 2024 1 7 23): ")
                end_date_list = list(map(int, end_date_input.split()))
                
                # datetime 객체 생성
                start_date = datetime(*start_date_list)
                end_date = datetime(*end_date_list)
                
                if end_date < start_date:
                    print("종료 날짜가 시작 날짜보다 앞설 수 없습니다.")
                    continue
                    
                break
            except ValueError:
                print("올바른 날짜 형식으로 입력해주세요.")
                continue
        
        # 입력된 날짜 확인
        print(f"\n데이터 수집 기간:")
        print(f"시작: {start_date.strftime('%Y년 %m월 %d일 %H시')}")
        print(f"종료: {end_date.strftime('%Y년 %m월 %d일 %H시')}")
        
        # 데이터 수집 기간 계산
        collection_hours = int((end_date - start_date).total_seconds() / 3600) + 1
        print(f"총 수집 시간: {collection_hours}시간")
        
        # 사용자 확인
        confirm = input("\n데이터 수집을 시작하시겠습니까? (y/n): ")
        
        if confirm.lower() == 'y':
            charts = get_charts_for_period(
                client_id=client_id,
                client_secret=client_secret,
                start_date=start_date,
                end_date=end_date,
                delay_seconds=2
            )
            print("\n데이터 수집이 완료되었습니다.")
        else:
            print("데이터 수집이 취소되었습니다.")
            
    except Exception as e:
        print(f"오류 발생: {str(e)}")

