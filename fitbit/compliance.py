"""
데이터 충족률 계산 함수
"""
from datetime import datetime, date, time, timedelta
from django.db.models import Count, Q
from django.utils import timezone
import pytz
from .models import IntradayHeartRate, PolarHeartRate


def calculate_compliance_rate(fitbit_user_id, start_date, end_date, start_time="00:00", end_time="23:59", bucket_size=1):
    """
    지정된 기간과 시간대의 데이터 충족률을 계산합니다.

    Args:
        fitbit_user_id: Fitbit 사용자 ID
        start_date: 시작 날짜 (date 객체 또는 'YYYY-MM-DD' 문자열)
        end_date: 종료 날짜 (date 객체 또는 'YYYY-MM-DD' 문자열)
        start_time: 시작 시간 (기본값: "00:00", 형식: "HH:MM")
        end_time: 종료 시간 (기본값: "23:59", 형식: "HH:MM")
        bucket_size: 버킷 크기 (분 단위, 기본값: 1)
                    1 = 1분 단위, 5 = 5분 단위, 60 = 1시간 단위

    Returns:
        float: 충족률 (0-100)
    """
    # 날짜 변환
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()

    # 시간 파싱
    start_hour, start_minute = map(int, start_time.split(':'))
    end_hour, end_minute = map(int, end_time.split(':'))

    # 일수 계산
    days = (end_date - start_date).days + 1

    # 하루당 분 수 계산
    # 종료 시간은 미포함 (예: 21시 선택 시 20:59까지)
    # 시작 시간은 포함 (예: 9시 선택 시 9:00부터)
    end_minutes_total = end_hour * 60 + end_minute
    start_minutes_total = start_hour * 60 + start_minute
    daily_minutes = end_minutes_total - start_minutes_total

    # 하루당 버킷 수 계산
    daily_buckets = daily_minutes // bucket_size

    # 총 버킷 수 (분모)
    total_buckets = days * daily_buckets

    if total_buckets == 0:
        return 0.0

    # 실제 데이터가 있는 버킷 수 계산 (분자)
    # 각 날짜별로 시간 범위 내의 고유한 버킷 개수를 세어야 함
    actual_buckets = 0

    # 한국 시간대 설정
    kst = pytz.timezone('Asia/Seoul')

    current_date = start_date
    while current_date <= end_date:
        # 해당 날짜의 시작/종료 datetime 생성 (KST 시간대)
        # 시작 시간은 포함 (>=), 종료 시간은 미포함 (<)
        day_start_naive = datetime.combine(current_date, time(start_hour, start_minute))
        day_start = kst.localize(day_start_naive)

        # 24:00은 다음날 00:00으로 처리
        if end_hour == 24 and end_minute == 0:
            day_end_naive = datetime.combine(current_date, time(23, 59)) + timedelta(minutes=1)
        else:
            day_end_naive = datetime.combine(current_date, time(end_hour, end_minute))
        day_end = kst.localize(day_end_naive)

        # 해당 시간대의 데이터 조회
        # gte (>=) 시작 포함, lt (<) 종료 미포함
        records = IntradayHeartRate.objects.filter(
            fitbit_user_id=fitbit_user_id,
            datetime__gte=day_start,
            datetime__lt=day_end
        ).values('datetime').distinct()

        # 고유한 버킷 개수 계산
        unique_buckets = set()
        for record in records:
            dt = record['datetime']
            # UTC -> KST 변환
            dt_kst = dt.astimezone(kst)
            # 시작 시간으로부터 경과한 분 수 계산
            minutes_from_start = (dt_kst.hour - start_hour) * 60 + (dt_kst.minute - start_minute)
            # 버킷 인덱스 계산 (bucket_size로 나눈 몫)
            bucket_index = minutes_from_start // bucket_size
            unique_buckets.add(bucket_index)

        actual_buckets += len(unique_buckets)
        current_date += timedelta(days=1)

    # 충족률 계산
    compliance_rate = (actual_buckets / total_buckets) * 100

    return round(compliance_rate, 2)


def calculate_compliance_rate_polar(username, date_of_birth, start_date, end_date, start_time="00:00", end_time="23:59", bucket_size=1):
    """
    Polar 데이터의 충족률을 계산합니다. (username + date_of_birth 기반)

    Args:
        username: Polar 사용자명
        date_of_birth: 생년월일 (date 객체 또는 'YYYY-MM-DD' 문자열)
        start_date: 시작 날짜 (date 객체 또는 'YYYY-MM-DD' 문자열)
        end_date: 종료 날짜 (date 객체 또는 'YYYY-MM-DD' 문자열)
        start_time: 시작 시간 (기본값: "00:00", 형식: "HH:MM")
        end_time: 종료 시간 (기본값: "23:59", 형식: "HH:MM")
        bucket_size: 버킷 크기 (분 단위, 기본값: 1)
                    1 = 1분 단위, 5 = 5분 단위, 60 = 1시간 단위

    Returns:
        float: 충족률 (0-100)
    """
    # 날짜 변환
    if isinstance(start_date, str):
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
    if isinstance(end_date, str):
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    if isinstance(date_of_birth, str):
        date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()

    # 시간 파싱
    start_hour, start_minute = map(int, start_time.split(':'))
    end_hour, end_minute = map(int, end_time.split(':'))

    # 일수 계산
    days = (end_date - start_date).days + 1

    # 하루당 분 수 계산
    end_minutes_total = end_hour * 60 + end_minute
    start_minutes_total = start_hour * 60 + start_minute
    daily_minutes = end_minutes_total - start_minutes_total

    # 하루당 버킷 수 계산
    daily_buckets = daily_minutes // bucket_size

    # 총 버킷 수 (분모)
    total_buckets = days * daily_buckets

    if total_buckets == 0:
        return 0.0

    # 실제 데이터가 있는 버킷 수 계산 (분자)
    actual_buckets = 0

    # 한국 시간대 설정
    kst = pytz.timezone('Asia/Seoul')

    current_date = start_date
    while current_date <= end_date:
        # 해당 날짜의 시작/종료 datetime 생성 (KST 시간대)
        day_start_naive = datetime.combine(current_date, time(start_hour, start_minute))
        day_start = kst.localize(day_start_naive)

        # 24:00은 다음날 00:00으로 처리
        if end_hour == 24 and end_minute == 0:
            day_end_naive = datetime.combine(current_date, time(23, 59)) + timedelta(minutes=1)
        else:
            day_end_naive = datetime.combine(current_date, time(end_hour, end_minute))
        day_end = kst.localize(day_end_naive)

        # 해당 시간대의 Polar 데이터 조회
        records = PolarHeartRate.objects.filter(
            username=username,
            date_of_birth=date_of_birth,
            datetime__gte=day_start,
            datetime__lt=day_end
        ).values('datetime').distinct()

        # 고유한 버킷 개수 계산
        unique_buckets = set()
        for record in records:
            dt = record['datetime']
            # UTC -> KST 변환
            dt_kst = dt.astimezone(kst)
            # 시작 시간으로부터 경과한 분 수 계산
            minutes_from_start = (dt_kst.hour - start_hour) * 60 + (dt_kst.minute - start_minute)
            # 버킷 인덱스 계산 (bucket_size로 나눈 몫)
            bucket_index = minutes_from_start // bucket_size
            unique_buckets.add(bucket_index)

        actual_buckets += len(unique_buckets)
        current_date += timedelta(days=1)

    # 충족률 계산
    compliance_rate = (actual_buckets / total_buckets) * 100

    return round(compliance_rate, 2)
