# 스포티파이 API를 통한 한국 음악차트 크롤링
![spotify_image](https://github.com/user-attachments/assets/8dc7e794-9868-4860-a0aa-069f0d68f1fb)

# Spotify API 사용을 위한 Client ID, Client Secret 발급 방법

## 사전 준비
Spotify Chart 코드를 사용하기 위해서는 Spotify Developer Dashboard에서 Client ID와 Client Secret을 발급받아야 합니다.

## 발급 절차

1. **Spotify Developer 접속**
   - https://developer.spotify.com 에 접속하여 로그인합니다.

2. **앱 생성하기**
   - 우측 상단의 사용자 이름을 클릭하여 대시보드로 이동합니다.
   - `Create App` 버튼을 클릭합니다.

3. **필수 정보 입력**
   - App name: 앱의 이름을 입력합니다.
   - App description: 앱 설명 (선택사항).
   - Website: 웹사이트 주소 (선택사항).
   - Redirect URI: 콜백 페이지 주소 입력 (필수).

4. **Client ID, Client Secret 확인**
   - 생성된 앱의 Settings 메뉴에서 Client ID와 Client Secret을 확인할 수 있습니다.

## 참고사항
이 발급받은 인증 정보는 spotify_chart.py 코드에서 사용됩니다. 발급받은 Client ID와 Client Secret을 안전하게 보관하시기 바랍니다.
