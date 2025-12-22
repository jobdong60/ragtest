"""
Fitbit Access Token 자동 갱신 함수
"""
import requests
import base64
from django.conf import settings


def refresh_access_token(fitbit_user):
    """
    Fitbit access token을 갱신하고 DB에 저장

    Args:
        fitbit_user: FitbitUser 모델 인스턴스

    Returns:
        bool: 성공 여부
    """
    auth_header = base64.b64encode(
        f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': fitbit_user.refresh_token
    }

    try:
        response = requests.post(settings.FITBIT_TOKEN_URL, headers=headers, data=data)

        if response.status_code == 200:
            token_data = response.json()

            # DB에 새 토큰 저장
            fitbit_user.access_token = token_data['access_token']
            fitbit_user.refresh_token = token_data['refresh_token']
            fitbit_user.save()

            print(f"[{fitbit_user.fitbit_user_id}] 토큰 갱신 성공")
            return True
        else:
            print(f"[{fitbit_user.fitbit_user_id}] 토큰 갱신 실패: {response.status_code} - {response.text}")
            return False

    except Exception as e:
        print(f"[{fitbit_user.fitbit_user_id}] 토큰 갱신 중 예외 발생: {e}")
        return False
