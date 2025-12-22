"""
Fitbit API 호출 관련 함수들
"""
import requests
from datetime import datetime, timedelta
from django.conf import settings


def get_fitbit_data(access_token, endpoint):
    """
    Fitbit API에서 데이터 가져오기

    Args:
        access_token: Fitbit access token
        endpoint: API endpoint (예: '/1/user/-/profile.json')

    Returns:
        dict: API 응답 데이터 또는 None
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    url = f"{settings.FITBIT_API_BASE_URL}{endpoint}"

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            error_msg = f"API 요청 실패 ({endpoint}): {response.status_code} - {response.text}"

            # 429 에러 시 rate limit 정보 출력
            if response.status_code == 429:
                rate_limit_reset = response.headers.get('Fitbit-Rate-Limit-Reset')
                rate_limit_remaining = response.headers.get('Fitbit-Rate-Limit-Remaining')
                rate_limit_limit = response.headers.get('Fitbit-Rate-Limit-Limit')

                if rate_limit_reset:
                    error_msg += f"\n⚠️  Rate Limit 초과! {rate_limit_reset}초 후 리셋"
                if rate_limit_remaining is not None:
                    error_msg += f"\n   남은 요청: {rate_limit_remaining}/{rate_limit_limit}"

            print(error_msg)
            return None
    except Exception as e:
        print(f"API 요청 중 오류 발생 ({endpoint}): {e}")
        return None


def get_fitbit_heart_rate_data(access_token, date, start_time=None, end_time=None, end_date=None):
    """
    특정 날짜(또는 날짜 범위)의 심박수 데이터 가져오기 (일일 요약 + 1분 단위 데이터)

    Args:
        access_token: Fitbit access token
        date: 시작 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택)
        end_time: 종료 시간 (HH:MM 형식, 선택)
        end_date: 종료 날짜 (YYYY-MM-DD 형식, 선택) - 날짜 범위 조회 시 사용

    Returns:
        dict: 심박수 데이터
    """
    if start_time and end_time:
        endpoint = f"/1/user/-/activities/heart/date/{date}/{date}/1min/time/{start_time}/{end_time}.json"
    elif end_date:
        # 날짜 범위 조회
        endpoint = f"/1/user/-/activities/heart/date/{date}/{end_date}/1min.json"
    else:
        endpoint = f"/1/user/-/activities/heart/date/{date}/1d/1min.json"
    return get_fitbit_data(access_token, endpoint)


def get_activity_data(access_token, date):
    """
    특정 날짜의 활동 데이터 가져오기

    Args:
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD 형식)

    Returns:
        dict: 활동 데이터 (걸음 수, 거리, 칼로리 등)
    """
    endpoint = f"/1/user/-/activities/date/{date}.json"
    return get_fitbit_data(access_token, endpoint)


def get_steps_intraday_data(access_token, date, start_time=None, end_time=None, end_date=None):
    """
    특정 날짜(또는 날짜 범위)의 걸음 수 intraday 데이터 가져오기 (1분 단위)

    Args:
        access_token: Fitbit access token
        date: 시작 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택)
        end_time: 종료 시간 (HH:MM 형식, 선택)
        end_date: 종료 날짜 (YYYY-MM-DD 형식, 선택)

    Returns:
        dict: 걸음 수 intraday 데이터
    """
    if start_time and end_time:
        endpoint = f"/1/user/-/activities/steps/date/{date}/{date}/1min/time/{start_time}/{end_time}.json"
    elif end_date:
        endpoint = f"/1/user/-/activities/steps/date/{date}/{end_date}/1min.json"
    else:
        endpoint = f"/1/user/-/activities/steps/date/{date}/1d/1min.json"
    return get_fitbit_data(access_token, endpoint)


def get_calories_intraday_data(access_token, date, start_time=None, end_time=None, end_date=None):
    """
    특정 날짜(또는 날짜 범위)의 칼로리 intraday 데이터 가져오기 (1분 단위)

    Args:
        access_token: Fitbit access token
        date: 시작 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택)
        end_time: 종료 시간 (HH:MM 형식, 선택)
        end_date: 종료 날짜 (YYYY-MM-DD 형식, 선택)

    Returns:
        dict: 칼로리 intraday 데이터
    """
    if start_time and end_time:
        endpoint = f"/1/user/-/activities/calories/date/{date}/{date}/1min/time/{start_time}/{end_time}.json"
    elif end_date:
        endpoint = f"/1/user/-/activities/calories/date/{date}/{end_date}/1min.json"
    else:
        endpoint = f"/1/user/-/activities/calories/date/{date}/1d/1min.json"
    return get_fitbit_data(access_token, endpoint)


def get_distance_intraday_data(access_token, date, start_time=None, end_time=None, end_date=None):
    """
    특정 날짜(또는 날짜 범위)의 거리 intraday 데이터 가져오기 (1분 단위)

    Args:
        access_token: Fitbit access token
        date: 시작 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택)
        end_time: 종료 시간 (HH:MM 형식, 선택)
        end_date: 종료 날짜 (YYYY-MM-DD 형식, 선택)

    Returns:
        dict: 거리 intraday 데이터
    """
    if start_time and end_time:
        endpoint = f"/1/user/-/activities/distance/date/{date}/{date}/1min/time/{start_time}/{end_time}.json"
    elif end_date:
        endpoint = f"/1/user/-/activities/distance/date/{date}/{end_date}/1min.json"
    else:
        endpoint = f"/1/user/-/activities/distance/date/{date}/1d/1min.json"
    return get_fitbit_data(access_token, endpoint)


def get_floors_intraday_data(access_token, date, start_time=None, end_time=None, end_date=None):
    """
    특정 날짜(또는 날짜 범위)의 층수 intraday 데이터 가져오기 (1분 단위)

    Args:
        access_token: Fitbit access token
        date: 시작 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택)
        end_time: 종료 시간 (HH:MM 형식, 선택)
        end_date: 종료 날짜 (YYYY-MM-DD 형식, 선택)

    Returns:
        dict: 층수 intraday 데이터
    """
    if start_time and end_time:
        endpoint = f"/1/user/-/activities/floors/date/{date}/{date}/1min/time/{start_time}/{end_time}.json"
    elif end_date:
        endpoint = f"/1/user/-/activities/floors/date/{date}/{end_date}/1min.json"
    else:
        endpoint = f"/1/user/-/activities/floors/date/{date}/1d/1min.json"
    return get_fitbit_data(access_token, endpoint)


def get_elevation_intraday_data(access_token, date, start_time=None, end_time=None, end_date=None):
    """
    특정 날짜(또는 날짜 범위)의 고도 intraday 데이터 가져오기 (1분 단위)

    Args:
        access_token: Fitbit access token
        date: 시작 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택)
        end_time: 종료 시간 (HH:MM 형식, 선택)
        end_date: 종료 날짜 (YYYY-MM-DD 형식, 선택)

    Returns:
        dict: 고도 intraday 데이터
    """
    if start_time and end_time:
        endpoint = f"/1/user/-/activities/elevation/date/{date}/{date}/1min/time/{start_time}/{end_time}.json"
    elif end_date:
        endpoint = f"/1/user/-/activities/elevation/date/{date}/{end_date}/1min.json"
    else:
        endpoint = f"/1/user/-/activities/elevation/date/{date}/1d/1min.json"
    return get_fitbit_data(access_token, endpoint)


def get_spo2_intraday_data(access_token, date, start_time=None, end_time=None):
    """
    특정 날짜의 SpO2 intraday 데이터 가져오기 (5분 단위)

    Args:
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택) - 사용 안 함
        end_time: 종료 시간 (HH:MM 형식, 선택) - 사용 안 함

    Returns:
        dict: SpO2 intraday 데이터
    """
    # SpO2 Intraday는 날짜 범위 형식으로 요청 (시작일/종료일 동일)
    endpoint = f"/1/user/-/spo2/date/{date}/{date}/all.json"
    return get_fitbit_data(access_token, endpoint)


def get_hrv_intraday_data(access_token, date, start_time=None, end_time=None):
    """
    특정 날짜의 HRV intraday 데이터 가져오기 (수면 중)

    Args:
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD 형식)
        start_time: 시작 시간 (HH:MM 형식, 선택) - 사용 안 함
        end_time: 종료 시간 (HH:MM 형식, 선택) - 사용 안 함

    Returns:
        dict: HRV intraday 데이터
    """
    # HRV Intraday는 날짜 범위 형식으로 요청 (시작일/종료일 동일)
    endpoint = f"/1/user/-/hrv/date/{date}/{date}/all.json"
    return get_fitbit_data(access_token, endpoint)


def get_sleep_data(access_token, date):
    """
    특정 날짜의 수면 데이터 가져오기

    Args:
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD 형식)

    Returns:
        dict: 수면 데이터
    """
    endpoint = f"/1.2/user/-/sleep/date/{date}.json"
    return get_fitbit_data(access_token, endpoint)


def get_breathing_rate_data(access_token, date):
    """
    특정 날짜의 호흡수 데이터 가져오기

    Args:
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD 형식)

    Returns:
        dict: 호흡수 데이터
    """
    endpoint = f"/1/user/-/br/date/{date}.json"
    return get_fitbit_data(access_token, endpoint)


def get_skin_temperature_data(access_token, date):
    """
    특정 날짜의 피부 온도 데이터 가져오기

    Args:
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD 형식)

    Returns:
        dict: 피부 온도 데이터
    """
    endpoint = f"/1/user/-/temp/skin/date/{date}.json"
    return get_fitbit_data(access_token, endpoint)


def get_date_range(days_back=7):
    """
    오늘부터 days_back 일 전까지의 날짜 리스트 생성

    Args:
        days_back: 몇 일 전까지 가져올지 (기본 7일)

    Returns:
        list: 날짜 문자열 리스트 (YYYY-MM-DD 형식)
    """
    dates = []
    today = datetime.now().date()

    for i in range(days_back):
        date = today - timedelta(days=i)
        dates.append(date.strftime('%Y-%m-%d'))

    return dates
