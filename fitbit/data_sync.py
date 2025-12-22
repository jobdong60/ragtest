"""
Fitbit 데이터를 DB에 저장하는 함수들
"""
from datetime import datetime
from django.db import transaction
from django.utils import timezone
import pytz
from .models import (
    DailySummary, IntradayHeartRate, IntradaySteps, IntradayCalories,
    IntradayDistance, IntradayFloors, IntradayElevation,
    IntradaySpO2, IntradayHRV,
    SleepLog, BreathingRate, SkinTemperature
)
from .fitbit_api import (
    get_fitbit_heart_rate_data,
    get_activity_data,
    get_steps_intraday_data,
    get_calories_intraday_data,
    get_distance_intraday_data,
    get_floors_intraday_data,
    get_elevation_intraday_data,
    get_spo2_intraday_data,
    get_hrv_intraday_data,
    get_sleep_data,
    get_breathing_rate_data,
    get_skin_temperature_data,
    get_date_range
)


def parse_datetime_kst(date_str, time_str):
    """
    날짜와 시간 문자열을 KST timezone aware datetime으로 변환
    Fitbit API는 사용자 타임존(KST)으로 시간을 반환
    Django USE_TZ=True 설정으로 DB 저장 시 자동으로 UTC 변환됨

    Args:
        date_str: 날짜 (YYYY-MM-DD)
        time_str: 시간 (HH:MM:SS)

    Returns:
        timezone aware datetime (KST)
    """
    # naive datetime 생성
    dt_naive = datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    # KST timezone으로 localize (Fitbit API는 사용자 타임존으로 반환)
    kst = pytz.timezone('Asia/Seoul')
    dt_kst = kst.localize(dt_naive)
    return dt_kst


def save_daily_summary(fitbit_user_id, date, activity_data, heart_data):
    """
    일일 요약 데이터를 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        date: 날짜 (YYYY-MM-DD)
        activity_data: 활동 데이터 (API 응답)
        heart_data: 심박수 데이터 (API 응답)

    Returns:
        DailySummary 객체 또는 None
    """
    try:
        # 활동 데이터 파싱
        summary = activity_data.get('summary', {})
        steps = summary.get('steps', 0)
        distances = summary.get('distances', [])
        distance = next((d['distance'] for d in distances if d['activity'] == 'total'), 0)
        calories = summary.get('caloriesOut', 0)

        # 심박수 데이터 파싱
        resting_hr = None
        hr_zones = {}

        if heart_data and 'activities-heart' in heart_data:
            heart_list = heart_data['activities-heart']
            if heart_list:
                heart_value = heart_list[0].get('value', {})
                resting_hr = heart_value.get('restingHeartRate')

                # 심박수 존 파싱
                zones = heart_value.get('heartRateZones', [])
                for zone in zones:
                    zone_name = zone.get('name', '').lower()
                    if 'out of range' in zone_name:
                        hr_zones['out_of_range_minutes'] = zone.get('minutes', 0)
                    elif 'fat burn' in zone_name:
                        hr_zones['fat_burn_minutes'] = zone.get('minutes', 0)
                        hr_zones['fat_burn_min'] = zone.get('min', 0)
                        hr_zones['fat_burn_max'] = zone.get('max', 0)
                    elif 'cardio' in zone_name:
                        hr_zones['cardio_minutes'] = zone.get('minutes', 0)
                        hr_zones['cardio_min'] = zone.get('min', 0)
                        hr_zones['cardio_max'] = zone.get('max', 0)
                    elif 'peak' in zone_name:
                        hr_zones['peak_minutes'] = zone.get('minutes', 0)
                        hr_zones['peak_min'] = zone.get('min', 0)
                        hr_zones['peak_max'] = zone.get('max', 0)

        # DB에 저장 (update_or_create 사용)
        daily_summary, created = DailySummary.objects.update_or_create(
            fitbit_user_id=fitbit_user_id,
            date=date,
            defaults={
                'steps': steps,
                'distance': distance,
                'calories': calories,
                'resting_heart_rate': resting_hr,
                'hr_zone_out_of_range_minutes': hr_zones.get('out_of_range_minutes'),
                'hr_zone_fat_burn_minutes': hr_zones.get('fat_burn_minutes'),
                'hr_zone_cardio_minutes': hr_zones.get('cardio_minutes'),
                'hr_zone_peak_minutes': hr_zones.get('peak_minutes'),
                'hr_zone_fat_burn_min_hr': hr_zones.get('fat_burn_min'),
                'hr_zone_fat_burn_max_hr': hr_zones.get('fat_burn_max'),
                'hr_zone_cardio_min_hr': hr_zones.get('cardio_min'),
                'hr_zone_cardio_max_hr': hr_zones.get('cardio_max'),
                'hr_zone_peak_min_hr': hr_zones.get('peak_min'),
                'hr_zone_peak_max_hr': hr_zones.get('peak_max'),
            }
        )

        action = "생성" if created else "업데이트"
        print(f"[DailySummary] {fitbit_user_id} - {date} {action}")
        return daily_summary

    except Exception as e:
        print(f"일일 요약 저장 중 오류: {e}")
        return None


def save_intraday_heart_rate(fitbit_user_id, date, heart_data):
    """
    1분 단위 심박수 데이터를 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        date: 날짜 (YYYY-MM-DD)
        heart_data: 심박수 데이터 (API 응답)

    Returns:
        저장된 레코드 수
    """
    if not heart_data or 'activities-heart-intraday' not in heart_data:
        return 0

    intraday_data = heart_data['activities-heart-intraday'].get('dataset', [])
    if not intraday_data:
        return 0

    saved_count = 0

    try:
        with transaction.atomic():
            for item in intraday_data:
                time_str = item.get('time')
                heart_rate = item.get('value')

                if not time_str or not heart_rate:
                    continue

                # datetime 생성 (UTC timezone aware)
                dt = parse_datetime_kst(date, time_str)

                # DB에 저장
                _, created = IntradayHeartRate.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    datetime=dt,
                    defaults={'heart_rate': heart_rate}
                )

                if created:
                    saved_count += 1

        print(f"[IntradayHeartRate] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count

    except Exception as e:
        print(f"Intraday 심박수 저장 중 오류: {e}")
        return 0


def save_intraday_steps(fitbit_user_id, date, steps_data):
    """
    1분 단위 걸음 수 데이터를 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        date: 날짜 (YYYY-MM-DD)
        steps_data: 걸음 수 데이터 (API 응답)

    Returns:
        저장된 레코드 수
    """
    if not steps_data or 'activities-steps-intraday' not in steps_data:
        return 0

    intraday_data = steps_data['activities-steps-intraday'].get('dataset', [])
    if not intraday_data:
        return 0

    saved_count = 0

    try:
        with transaction.atomic():
            for item in intraday_data:
                time_str = item.get('time')
                steps = item.get('value', 0)

                if not time_str:
                    continue

                # datetime 생성
                dt = parse_datetime_kst(date, time_str)

                # DB에 저장
                _, created = IntradaySteps.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    datetime=dt,
                    defaults={'steps': steps}
                )

                if created:
                    saved_count += 1

        print(f"[IntradaySteps] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count

    except Exception as e:
        print(f"Intraday 걸음 수 저장 중 오류: {e}")
        return 0


def save_intraday_calories(fitbit_user_id, date, calories_data):
    """
    1분 단위 칼로리 데이터를 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        date: 날짜 (YYYY-MM-DD)
        calories_data: 칼로리 데이터 (API 응답)

    Returns:
        저장된 레코드 수
    """
    if not calories_data or 'activities-calories-intraday' not in calories_data:
        return 0

    intraday_data = calories_data['activities-calories-intraday'].get('dataset', [])
    if not intraday_data:
        return 0

    saved_count = 0

    try:
        with transaction.atomic():
            for item in intraday_data:
                time_str = item.get('time')
                calories = item.get('value', 0)
                level = item.get('level', 0)
                mets = item.get('mets', 0)

                if not time_str:
                    continue

                # datetime 생성
                dt = parse_datetime_kst(date, time_str)

                # DB에 저장
                _, created = IntradayCalories.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    datetime=dt,
                    defaults={
                        'calories': calories,
                        'level': level,
                        'mets': mets
                    }
                )

                if created:
                    saved_count += 1

        print(f"[IntradayCalories] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count

    except Exception as e:
        print(f"Intraday 칼로리 저장 중 오류: {e}")
        return 0


def save_intraday_distance(fitbit_user_id, date, distance_data):
    """
    1분 단위 거리 데이터를 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        date: 날짜 (YYYY-MM-DD)
        distance_data: 거리 데이터 (API 응답)

    Returns:
        저장된 레코드 수
    """
    if not distance_data or 'activities-distance-intraday' not in distance_data:
        return 0

    intraday_data = distance_data['activities-distance-intraday'].get('dataset', [])
    if not intraday_data:
        return 0

    saved_count = 0

    try:
        with transaction.atomic():
            for item in intraday_data:
                time_str = item.get('time')
                distance = item.get('value', 0)

                if not time_str:
                    continue

                # datetime 생성
                dt = parse_datetime_kst(date, time_str)

                # DB에 저장
                _, created = IntradayDistance.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    datetime=dt,
                    defaults={'distance': distance}
                )

                if created:
                    saved_count += 1

        print(f"[IntradayDistance] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count

    except Exception as e:
        print(f"Intraday 거리 저장 중 오류: {e}")
        return 0


def save_intraday_floors(fitbit_user_id, date, floors_data):
    """
    1분 단위 층수 데이터를 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        date: 날짜 (YYYY-MM-DD)
        floors_data: 층수 데이터 (API 응답)

    Returns:
        저장된 레코드 수
    """
    if not floors_data or 'activities-floors-intraday' not in floors_data:
        return 0

    intraday_data = floors_data['activities-floors-intraday'].get('dataset', [])
    if not intraday_data:
        return 0

    saved_count = 0

    try:
        with transaction.atomic():
            for item in intraday_data:
                time_str = item.get('time')
                floors = item.get('value', 0)

                if not time_str:
                    continue

                # datetime 생성
                dt = parse_datetime_kst(date, time_str)

                # DB에 저장
                _, created = IntradayFloors.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    datetime=dt,
                    defaults={'floors': floors}
                )

                if created:
                    saved_count += 1

        print(f"[IntradayFloors] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count

    except Exception as e:
        print(f"Intraday 층수 저장 중 오류: {e}")
        return 0


def save_intraday_elevation(fitbit_user_id, date, elevation_data):
    """
    1분 단위 고도 데이터를 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        date: 날짜 (YYYY-MM-DD)
        elevation_data: 고도 데이터 (API 응답)

    Returns:
        저장된 레코드 수
    """
    if not elevation_data or 'activities-elevation-intraday' not in elevation_data:
        return 0

    intraday_data = elevation_data['activities-elevation-intraday'].get('dataset', [])
    if not intraday_data:
        return 0

    saved_count = 0

    try:
        with transaction.atomic():
            for item in intraday_data:
                time_str = item.get('time')
                elevation = item.get('value', 0)

                if not time_str:
                    continue

                # datetime 생성
                dt = parse_datetime_kst(date, time_str)

                # DB에 저장
                _, created = IntradayElevation.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    datetime=dt,
                    defaults={'elevation': elevation}
                )

                if created:
                    saved_count += 1

        print(f"[IntradayElevation] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count

    except Exception as e:
        print(f"Intraday 고도 저장 중 오류: {e}")
        return 0


def sync_fitbit_data_for_date(fitbit_user_id, access_token, date, start_time=None, end_time=None):
    """
    특정 날짜의 Fitbit 데이터를 API에서 가져와 DB에 저장

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD)
        start_time: 시작 시간 (HH:MM 형식, 선택)
        end_time: 종료 시간 (HH:MM 형식, 선택)

    Returns:
        dict: 동기화 결과 (성공 여부, 저장된 레코드 수 등)
    """
    result = {
        'date': date,
        'success': False,
        'daily_summary': False,
        'intraday_hr': 0,
        'intraday_steps': 0,
        'intraday_calories': 0,
        'intraday_distance': 0,
        'intraday_floors': 0,
        'intraday_elevation': 0,
        'intraday_spo2': 0,
        'intraday_hrv': 0,
        'sleep_logs': 0,
        'breathing_rate': 0,
        'skin_temperature': 0,
        'error': None
    }

    try:
        # API에서 데이터 가져오기
        activity_data = get_activity_data(access_token, date)
        heart_data = get_fitbit_heart_rate_data(access_token, date, start_time, end_time)
        steps_data = get_steps_intraday_data(access_token, date, start_time, end_time)
        calories_data = get_calories_intraday_data(access_token, date, start_time, end_time)
        distance_data = get_distance_intraday_data(access_token, date, start_time, end_time)
        floors_data = get_floors_intraday_data(access_token, date, start_time, end_time)
        elevation_data = get_elevation_intraday_data(access_token, date, start_time, end_time)
        spo2_data = get_spo2_intraday_data(access_token, date, start_time, end_time)
        hrv_data = get_hrv_intraday_data(access_token, date, start_time, end_time)

        # 일일 요약 저장 (시간 범위 지정 시에는 스킵)
        if activity_data and not start_time:
            summary = save_daily_summary(fitbit_user_id, date, activity_data, heart_data)
            result['daily_summary'] = summary is not None

        # Intraday 데이터 저장
        if heart_data:
            result['intraday_hr'] = save_intraday_heart_rate(fitbit_user_id, date, heart_data)

        if steps_data:
            result['intraday_steps'] = save_intraday_steps(fitbit_user_id, date, steps_data)

        if calories_data:
            result['intraday_calories'] = save_intraday_calories(fitbit_user_id, date, calories_data)

        if distance_data:
            result['intraday_distance'] = save_intraday_distance(fitbit_user_id, date, distance_data)

        if floors_data:
            result['intraday_floors'] = save_intraday_floors(fitbit_user_id, date, floors_data)

        if elevation_data:
            result['intraday_elevation'] = save_intraday_elevation(fitbit_user_id, date, elevation_data)

        if spo2_data:
            result['intraday_spo2'] = save_intraday_spo2(fitbit_user_id, date, spo2_data)

        if hrv_data:
            result['intraday_hrv'] = save_intraday_hrv(fitbit_user_id, date, hrv_data)

        # 수면 관련 데이터 저장 (시간 범위 지정 시에는 스킵)
        if not start_time:
            sleep_data = get_sleep_data(access_token, date)
            if sleep_data:
                result['sleep_logs'] = save_sleep_log(fitbit_user_id, date, sleep_data)

            br_data = get_breathing_rate_data(access_token, date)
            if br_data:
                result['breathing_rate'] = save_breathing_rate(fitbit_user_id, date, br_data)

            temp_data = get_skin_temperature_data(access_token, date)
            if temp_data:
                result['skin_temperature'] = save_skin_temperature(fitbit_user_id, date, temp_data)

        result['success'] = True
        time_range = f" ({start_time}-{end_time})" if start_time else ""
        print(f"[Sync Success] {fitbit_user_id} - {date}{time_range}")

    except Exception as e:
        result['error'] = str(e)
        print(f"[Sync Error] {fitbit_user_id} - {date}: {e}")

    return result


def sync_fitbit_data_range(fitbit_user_id, access_token, days_back=7):
    """
    최근 N일간의 Fitbit 데이터를 동기화

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        access_token: Fitbit access token
        days_back: 몇 일 전까지 가져올지 (기본 7일)

    Returns:
        list: 각 날짜별 동기화 결과 리스트
    """
    dates = get_date_range(days_back)
    results = []

    for date in dates:
        result = sync_fitbit_data_for_date(fitbit_user_id, access_token, date)
        results.append(result)

    return results


def sync_recent_intraday_data(fitbit_user_id, access_token, minutes_back=5):
    """
    최근 N분간의 Intraday 데이터만 동기화 (cron용)

    예: 10:00에 실행 시 09:55, 09:56, 09:57, 09:58, 09:59 (5개)

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        access_token: Fitbit access token
        minutes_back: 몇 분 전까지 가져올지 (기본 5분)

    Returns:
        dict: 동기화 결과
    """
    from datetime import datetime, timedelta
    from django.utils import timezone as django_tz
    import pytz

    # 한국 시간대 설정
    kst = pytz.timezone('Asia/Seoul')

    # 현재 한국 시간 (초/마이크로초 제거)
    now = datetime.now(kst).replace(second=0, microsecond=0)

    # 종료 시간 = 현재 시간 - 10분 (Fitbit API 지연 고려)
    end_dt = now - timedelta(minutes=10)

    # 시작 시간 = 종료 시간 - (N-1)분 (예: 5분이면 5분 전부터)
    start_dt = end_dt - timedelta(minutes=minutes_back - 1)

    # 날짜와 시간 포맷팅
    date = now.strftime('%Y-%m-%d')
    start_time = start_dt.strftime('%H:%M')
    end_time = end_dt.strftime('%H:%M')

    # 시간 범위를 지정해서 데이터 가져오기
    return sync_fitbit_data_for_date(
        fitbit_user_id,
        access_token,
        date,
        start_time,
        end_time
    )


def save_intraday_spo2(fitbit_user_id, date, spo2_data):
    """SpO2 데이터를 DB에 저장"""
    if not spo2_data:
        return 0

    saved_count = 0
    try:
        with transaction.atomic():
            # SpO2 데이터는 리스트 형식일 수 있음
            if isinstance(spo2_data, list):
                # 리스트의 첫 번째 항목에서 minutes 추출
                for day_data in spo2_data:
                    if 'minutes' in day_data:
                        for item in day_data['minutes']:
                            minute = item.get('minute')
                            value = item.get('value')

                            if not minute or value is None:
                                continue

                            dt = datetime.fromisoformat(minute.replace('Z', '+00:00'))

                            _, created = IntradaySpO2.objects.update_or_create(
                                fitbit_user_id=fitbit_user_id,
                                datetime=dt,
                                defaults={'spo2': value}
                            )

                            if created:
                                saved_count += 1
            elif 'minutes' in spo2_data:
                # dict 형식인 경우
                for item in spo2_data['minutes']:
                    minute = item.get('minute')
                    value = item.get('value')

                    if not minute or value is None:
                        continue

                    dt = datetime.fromisoformat(minute.replace('Z', '+00:00'))

                    _, created = IntradaySpO2.objects.update_or_create(
                        fitbit_user_id=fitbit_user_id,
                        datetime=dt,
                        defaults={'spo2': value}
                    )

                    if created:
                        saved_count += 1

        print(f"[IntradaySpO2] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count
    except Exception as e:
        print(f"Intraday SpO2 저장 중 오류: {e}")
        import traceback
        traceback.print_exc()
        return 0


def save_intraday_hrv(fitbit_user_id, date, hrv_data):
    """HRV 데이터를 DB에 저장"""
    if not hrv_data or 'hrv' not in hrv_data:
        return 0
    
    saved_count = 0
    try:
        with transaction.atomic():
            for item in hrv_data['hrv']:
                minutes = item.get('minutes', [])
                
                for minute_data in minutes:
                    minute = minute_data.get('minute')
                    value = minute_data.get('value', {})
                    
                    if not minute:
                        continue
                    
                    dt = datetime.fromisoformat(minute.replace('Z', '+00:00'))
                    
                    _, created = IntradayHRV.objects.update_or_create(
                        fitbit_user_id=fitbit_user_id,
                        datetime=dt,
                        defaults={
                            'rmssd': value.get('rmssd', 0),
                            'coverage': value.get('coverage'),
                            'hf': value.get('hf'),
                            'lf': value.get('lf')
                        }
                    )
                    
                    if created:
                        saved_count += 1
        
        print(f"[IntradayHRV] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count
    except Exception as e:
        print(f"Intraday HRV 저장 중 오류: {e}")
        return 0


def save_sleep_log(fitbit_user_id, date, sleep_data):
    """수면 로그 데이터를 DB에 저장"""
    if not sleep_data or 'sleep' not in sleep_data:
        return 0

    saved_count = 0
    try:
        with transaction.atomic():
            for sleep in sleep_data['sleep']:
                log_id = sleep.get('logId')
                if not log_id:
                    continue

                # 수면 시작/종료 시간 파싱 (ISO format)
                start_time = datetime.fromisoformat(sleep.get('startTime', '').replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(sleep.get('endTime', '').replace('Z', '+00:00'))

                # 수면 단계별 시간
                levels = sleep.get('levels', {})
                summary = levels.get('summary', {})

                _, created = SleepLog.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    log_id=log_id,
                    defaults={
                        'date': date,
                        'start_time': start_time,
                        'end_time': end_time,
                        'duration': sleep.get('duration', 0),
                        'minutes_asleep': sleep.get('minutesAsleep', 0),
                        'minutes_awake': sleep.get('minutesAwake', 0),
                        'minutes_deep': summary.get('deep', {}).get('minutes'),
                        'minutes_light': summary.get('light', {}).get('minutes'),
                        'minutes_rem': summary.get('rem', {}).get('minutes'),
                        'minutes_wake': summary.get('wake', {}).get('minutes'),
                        'efficiency': sleep.get('efficiency'),
                        'sleep_score': sleep.get('sleepScore'),
                        'is_main_sleep': sleep.get('isMainSleep', False)
                    }
                )

                if created:
                    saved_count += 1

        print(f"[SleepLog] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count
    except Exception as e:
        print(f"Sleep Log 저장 중 오류: {e}")
        return 0


def save_breathing_rate(fitbit_user_id, date, br_data):
    """호흡수 데이터를 DB에 저장"""
    if not br_data or 'br' not in br_data:
        return 0

    saved_count = 0
    try:
        with transaction.atomic():
            for item in br_data['br']:
                item_date = item.get('dateTime')
                breathing_rate = item.get('value', {}).get('breathingRate')

                if not item_date or breathing_rate is None:
                    continue

                _, created = BreathingRate.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    date=item_date,
                    defaults={'breathing_rate': breathing_rate}
                )

                if created:
                    saved_count += 1

        print(f"[BreathingRate] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count
    except Exception as e:
        print(f"Breathing Rate 저장 중 오류: {e}")
        return 0


def save_skin_temperature(fitbit_user_id, date, temp_data):
    """피부 온도 데이터를 DB에 저장"""
    if not temp_data or 'tempSkin' not in temp_data:
        return 0

    saved_count = 0
    try:
        with transaction.atomic():
            for item in temp_data['tempSkin']:
                item_date = item.get('dateTime')
                relative_temp = item.get('value', {}).get('nightlyRelative')

                if not item_date or relative_temp is None:
                    continue

                _, created = SkinTemperature.objects.update_or_create(
                    fitbit_user_id=fitbit_user_id,
                    date=item_date,
                    defaults={'relative_temp': relative_temp}
                )

                if created:
                    saved_count += 1

        print(f"[SkinTemperature] {fitbit_user_id} - {date}: {saved_count}개 저장")
        return saved_count
    except Exception as e:
        print(f"Skin Temperature 저장 중 오류: {e}")
        return 0


def sync_daily_health_data(fitbit_user_id, access_token, date):
    """
    하루 1-2회 수집되는 건강 데이터 동기화 (Sleep, Breathing Rate, Skin Temperature)

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        access_token: Fitbit access token
        date: 날짜 (YYYY-MM-DD)

    Returns:
        dict: 동기화 결과
    """
    result = {
        'date': date,
        'success': False,
        'sleep_logs': 0,
        'breathing_rate': 0,
        'skin_temperature': 0,
        'error': None
    }

    try:
        # API에서 데이터 가져오기
        sleep_data = get_sleep_data(access_token, date)
        br_data = get_breathing_rate_data(access_token, date)
        temp_data = get_skin_temperature_data(access_token, date)

        # 각 데이터 저장
        if sleep_data:
            result['sleep_logs'] = save_sleep_log(fitbit_user_id, date, sleep_data)

        if br_data:
            result['breathing_rate'] = save_breathing_rate(fitbit_user_id, date, br_data)

        if temp_data:
            result['skin_temperature'] = save_skin_temperature(fitbit_user_id, date, temp_data)

        result['success'] = True
        print(f"[Daily Health Sync Success] {fitbit_user_id} - {date}")

    except Exception as e:
        result['error'] = str(e)
        print(f"[Daily Health Sync Error] {fitbit_user_id} - {date}: {e}")

    return result
