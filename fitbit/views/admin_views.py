"""
관리자 views - 전체 대상자 현황, 관리자 대시보드
"""
import json
import logging
import requests
import pytz
from datetime import datetime, date, timedelta, time
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Count, Max, OuterRef, Subquery
from django.db.models.functions import TruncDate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
import numpy as np
import pandas as pd
from scipy.signal import savgol_filter
import ruptures as rpt

from ..models import (
    FitbitUser, FitbitUserManagement, DailySummary, 
    IntradayHeartRate, IntradaySteps, IntradayDistance, IntradayCalories
)
from ..compliance import calculate_compliance_rate, calculate_compliance_rate_polar
from ..data_sync import sync_fitbit_data_for_date
from ..token_refresh import refresh_access_token

# KST Timezone 설정
KST = pytz.timezone('Asia/Seoul')
logger = logging.getLogger(__name__)

def admin_login(request):
    """관리자 로그인 페이지"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('admin_dashboard')
        else:
            return render(request, 'fitbit/admin/login.html', {
                'error': '관리자 권한이 없거나 로그인 정보가 올바르지 않습니다.'
            })

    return render(request, 'fitbit/admin/login.html')


@staff_member_required
def admin_dashboard(request):
    """관리자 대시보드 페이지 (HTML만 반환)"""
    return render(request, 'fitbit/admin/admin_dashboard.html', {
        'active_menu': 'dashboard'
    })


@staff_member_required
def get_dashboard_data(request):
    """대시보드 데이터 API (JSON 반환) - Polar 데이터 기반"""
    
    # 파라미터 받기 (버킷 크기는 1분 고정)
    start_time = request.GET.get('start_time', '09:00')  # 기본값: 09:00
    end_time = request.GET.get('end_time', '21:00')  # 기본값: 21:00

    # Polar 등록된 사용자 목록 (polar_users 테이블에서)
    from ..models import PolarUser, PolarHeartRate
    
    # PolarUser에서 모든 등록 사용자 가져오기
    all_users = PolarUser.objects.filter(is_active=True).order_by('full_name')
    total_users = all_users.count()

    # 날짜 계산 (KST 기준)
    now_kst = timezone.now().astimezone(KST)
    today = now_kst.date()
    yesterday = today - timedelta(days=1)
    seven_days_ago = today - timedelta(days=7)
    six_days_ago = today - timedelta(days=6)

    # 한국 시간대 설정 (통계용)
    kst = pytz.timezone('Asia/Seoul')
    start_hour_stat, start_minute_stat = map(int, start_time.split(':'))
    end_hour_stat, end_minute_stat = map(int, end_time.split(':'))
    
    # 오늘/어제/7일간 데이터가 있는 사용자 수 (polar_heart_rate 기반)
    # 지정된 시간대 내에 데이터가 있는 username + date_of_birth 조합 카운트
    today_start_stat = kst.localize(datetime.combine(today, time(start_hour_stat, start_minute_stat)))
    today_end_stat = kst.localize(datetime.combine(today, time(end_hour_stat, end_minute_stat)))
    users_with_data_today = PolarHeartRate.objects.filter(
        datetime__gte=today_start_stat,
        datetime__lt=today_end_stat
    ).values('username', 'date_of_birth').order_by('username', 'date_of_birth').distinct().count()

    yesterday_start_stat = kst.localize(datetime.combine(yesterday, time(start_hour_stat, start_minute_stat)))
    yesterday_end_stat = kst.localize(datetime.combine(yesterday, time(end_hour_stat, end_minute_stat)))
    users_with_data_yesterday = PolarHeartRate.objects.filter(
        datetime__gte=yesterday_start_stat,
        datetime__lt=yesterday_end_stat
    ).values('username', 'date_of_birth').order_by('username', 'date_of_birth').distinct().count()

    # 최근 7일: 6일 전부터 오늘까지 (총 7일)
    users_with_data_7days = PolarHeartRate.objects.filter(
        datetime__date__gte=six_days_ago
    ).values('username', 'date_of_birth').order_by('username','date_of_birth').distinct().count()

    # 각 사용자별 최근 7일 충족률 데이터
    user_stats = []
    
    for polar_user in all_users:
        username = polar_user.username
        date_of_birth = polar_user.date_of_birth
        
        if not username or not date_of_birth:
            continue

        # 최근 7일 충족률 계산 (버킷 기반)
        compliance_rate_7days = calculate_compliance_rate_polar(
            username,
            date_of_birth,
            six_days_ago,
            today,
            start_time=start_time,
            end_time=end_time,
            bucket_size=1  # 1분 단위
        )
        
        # 오늘 충족률
        compliance_rate_today = calculate_compliance_rate_polar(
            username,
            date_of_birth,
            today,
            today,
            start_time=start_time,
            end_time=end_time,
            bucket_size=1
        )
        
        # 어제 충족률
        compliance_rate_yesterday = calculate_compliance_rate_polar(
            username,
            date_of_birth,
            yesterday,
            yesterday,
            start_time=start_time,
            end_time=end_time,
            bucket_size=1
        )

        # 일별 충족률 배열 생성 (와플 차트용)
        daily_compliance = []
        current_date = six_days_ago
        while current_date <= today:
            daily_rate = calculate_compliance_rate_polar(
                username,
                date_of_birth,
                current_date,
                current_date,
                start_time=start_time,
                end_time=end_time,
                bucket_size=1
            )
            
            daily_compliance.append({
                'date': current_date.isoformat(),
                'rate': daily_rate
            })
            current_date += timedelta(days=1)

        # 순서 반전 (가장 최근 날짜가 왼쪽에 오도록)
        daily_compliance.reverse()

        # 가장 최근 데이터 날짜
        last_hr_record = PolarHeartRate.objects.filter(
            username=username,
            date_of_birth=date_of_birth
        ).order_by('-datetime').first()
        
        last_sync_date = None
        if last_hr_record:
            # UTC -> KST 변환 후 날짜 추출
            last_sync_date = last_hr_record.datetime.astimezone(KST).date().isoformat()

        # Polar 사용자 정보
        user_stats.append({
            'fitbit_user_id': f"{username}_{date_of_birth.isoformat()}",  # 고유 식별자 생성
            'username': username,
            'full_name': polar_user.full_name or username,
            'display_name': polar_user.full_name or username,
            'gender': polar_user.gender,
            'age': polar_user.age,
            'height': polar_user.height,
            'weight': polar_user.weight,
            'avatar_url': None,
            'profile_synced_at': polar_user.updated_at.isoformat() if polar_user.updated_at else None,
            'is_staff': False,
            'compliance_rate_7days': compliance_rate_7days,
            'compliance_rate_today': compliance_rate_today,
            'compliance_rate_yesterday': compliance_rate_yesterday,
            'daily_compliance': daily_compliance,  # 와플 차트 데이터
            'last_sync': last_sync_date,
        })

    return JsonResponse({
        'total_users': total_users,
        'users_with_data_today': users_with_data_today,
        'users_with_data_yesterday': users_with_data_yesterday,
        'users_with_data_7days': users_with_data_7days,
        'user_stats': user_stats,
    })


@staff_member_required
def admin_subjects(request):
    """관리자용 대상자 현황 페이지 (HTML만 반환)"""
    return render(request, 'fitbit/admin/subjects.html', {
        'active_menu': 'subjects'
    })


@staff_member_required
def admin_polar_heart_rate(request):
    """심박수 탭 페이지 (HTML 렌더링) - Polar 전용"""
    from ..models import PolarUser

    # PolarUser에서 활성 사용자 목록 가져오기 (단일 쿼리)
    users = PolarUser.objects.filter(is_active=True).order_by('full_name')

    return render(request, 'fitbit/admin/polar_heart_rate.html', {
        'active_menu': 'heart_rate',
        'users': users
    })


@staff_member_required
def get_fitbit_heart_rate_data(request):
    """심박수/걸음수 Intraday 데이터 API (JSON 반환)"""
    user_id = request.GET.get('user_id')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not all([user_id, start_date_str, end_date_str]):
        return JsonResponse({'success': False, 'error': 'user_id, start_date, end_date는 필수 파라미터입니다.'}, status=400)

    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        if start_date > end_date:
            return JsonResponse({'success': False, 'error': '시작 날짜는 종료 날짜보다 이전이어야 합니다.'}, status=400)

        # KST 기준으로 datetime 범위 생성
        # start_date 00:00:00 부터 end_date 다음날 00:00:00 직전까지
        start_datetime_kst = KST.localize(datetime.combine(start_date, datetime.min.time()))
        end_datetime_kst = KST.localize(datetime.combine(end_date + timedelta(days=1), datetime.min.time()))

        # 심박수 데이터 조회
        hr_records = IntradayHeartRate.objects.filter(
            fitbit_user_id=user_id,
            datetime__gte=start_datetime_kst,
            datetime__lt=end_datetime_kst  # end_date 다음날 00:00:00 미만
        ).order_by('datetime').values('datetime', 'heart_rate')

        # 걸음수 데이터 조회
        steps_records = IntradaySteps.objects.filter(
            fitbit_user_id=user_id,
            datetime__gte=start_datetime_kst,
            datetime__lt=end_datetime_kst  # end_date 다음날 00:00:00 미만
        ).values('datetime', 'steps')

        # 걸음수 데이터를 5분 단위로 리샘플링
        steps_df = pd.DataFrame(list(steps_records))
        steps_5min_dict = {}

        if not steps_df.empty:
            # datetime을 인덱스로 설정하고 KST로 변환
            steps_df['datetime'] = pd.to_datetime(steps_df['datetime']).dt.tz_convert(KST)
            steps_df.set_index('datetime', inplace=True)

            # 5분 단위로 리샘플링 (합계)
            steps_5min = steps_df['steps'].resample('5T').sum()

            # 딕셔너리로 변환 (5분 단위 타임스탬프가 키)
            steps_5min_dict = steps_5min.to_dict()

        chart_data = {
            'labels': [],
            'hr_data': [],
            'steps_data': []
        }

        for hr_record in hr_records:
            dt_kst = hr_record['datetime'].astimezone(KST)
            chart_data['labels'].append(dt_kst.strftime('%Y-%m-%d %H:%M'))
            chart_data['hr_data'].append(hr_record['heart_rate'])

            # 해당 시간을 5분 단위로 내림
            dt_5min = dt_kst.replace(second=0, microsecond=0)
            minute = (dt_5min.minute // 5) * 5
            dt_5min = dt_5min.replace(minute=minute)

            # 5분 단위 걸음수 가져오기 (없으면 0)
            steps_value = steps_5min_dict.get(pd.Timestamp(dt_5min), 0)
            chart_data['steps_data'].append(steps_value)

        # 데이터 스무딩 (Savitzky-Golay Filter)
        # 생체 신호 처리에 최적화된 파라미터 사용
        # window_length는 홀수여야 하며, 데이터의 노이즈 특성에 따라 조정
        # polyorder는 window_length보다 작아야 함

        # 파라미터를 요청에서 받을 수 있도록 설정 (기본값 제공)
        window_length = int(request.GET.get('window_length', 31))  # 기본값: 31 (약 30초 ~ 5분 범위)
        polyorder = int(request.GET.get('polyorder', 3))  # 기본값: 3 (3차 다항식)

        # window_length는 반드시 홀수여야 함
        if window_length % 2 == 0:
            window_length += 1

        # polyorder는 window_length보다 작아야 함
        if polyorder >= window_length:
            polyorder = window_length - 1

        # 원본 데이터 백업 (비교용)
        chart_data['hr_data_raw'] = chart_data['hr_data'].copy()
        chart_data['steps_data_raw'] = chart_data['steps_data'].copy()

        # 심박수 데이터 스무딩
        if len(chart_data['hr_data']) > window_length:
            hr_np = np.array(chart_data['hr_data'])
            chart_data['hr_data_smoothed'] = savgol_filter(hr_np, window_length, polyorder).tolist()
        else:
            chart_data['hr_data_smoothed'] = chart_data['hr_data'].copy()

        # 걸음수 데이터 스무딩
        if len(chart_data['steps_data']) > window_length:
            steps_np = np.array(chart_data['steps_data'])
            steps_smoothed = savgol_filter(steps_np, window_length, polyorder)
            # 걸음수는 음수가 될 수 없으므로 0 이하의 값을 0으로 클리핑
            steps_smoothed = np.maximum(steps_smoothed, 0)
            chart_data['steps_data_smoothed'] = steps_smoothed.tolist()
        else:
            chart_data['steps_data_smoothed'] = chart_data['steps_data'].copy()

        # 필터 파라미터 정보 추가
        chart_data['filter_params'] = {
            'window_length': window_length,
            'polyorder': polyorder,
            'filter_type': 'Savitzky-Golay'
        }

        # 변곡점 탐지 (Change Point Detection)
        enable_cpd = request.GET.get('enable_cpd', 'false').lower() == 'true'
        cpd_hr_enabled = request.GET.get('cpd_hr', 'true').lower() == 'true'
        cpd_steps_enabled = request.GET.get('cpd_steps', 'true').lower() == 'true'
        change_points_hr = []
        change_points_steps = []

        if enable_cpd:
            # 파라미터 가져오기
            cpd_penalty = int(request.GET.get('cpd_penalty', 10))
            cpd_min_size = int(request.GET.get('cpd_min_size', 20))

            # 심박수 변곡점 탐지
            if cpd_hr_enabled and len(chart_data['hr_data_smoothed']) > 50:
                try:
                    hr_signal = np.array(chart_data['hr_data_smoothed']).reshape(-1, 1)

                    # Pelt 알고리즘 사용 (빠르고 정확)
                    # min_size: 최소 세그먼트 크기 (너무 작은 변화는 무시)
                    # pen: 페널티 (높을수록 변곡점이 적어짐)
                    algo_hr = rpt.Pelt(model="rbf", min_size=cpd_min_size, jump=5).fit(hr_signal)
                    result_hr = algo_hr.predict(pen=cpd_penalty)

                    # 마지막 인덱스 제거 (전체 데이터 끝을 가리킴)
                    if result_hr and result_hr[-1] == len(chart_data['hr_data_smoothed']):
                        result_hr = result_hr[:-1]

                    change_points_hr = result_hr
                except Exception as e:
                    logger.error(f"심박수 변곡점 탐지 오류: {e}")

            # 걸음수 변곡점 탐지
            if cpd_steps_enabled and len(chart_data['steps_data_smoothed']) > 50:
                try:
                    steps_signal = np.array(chart_data['steps_data_smoothed']).reshape(-1, 1)
                    algo_steps = rpt.Pelt(model="rbf", min_size=cpd_min_size, jump=5).fit(steps_signal)
                    result_steps = algo_steps.predict(pen=cpd_penalty)

                    if result_steps and result_steps[-1] == len(chart_data['steps_data_smoothed']):
                        result_steps = result_steps[:-1]

                    change_points_steps = result_steps
                except Exception as e:
                    logger.error(f"걸음수 변곡점 탐지 오류: {e}")

            # 변곡점 정보를 시간 레이블로 변환
            chart_data['change_points'] = {
                'hr_indices': change_points_hr,
                'steps_indices': change_points_steps,
                'hr_labels': [chart_data['labels'][i] for i in change_points_hr if i < len(chart_data['labels'])],
                'steps_labels': [chart_data['labels'][i] for i in change_points_steps if i < len(chart_data['labels'])]
            }

        return JsonResponse({
            'success': True,
            'chart_data': chart_data
        })

    except ValueError:
        return JsonResponse({'success': False, 'error': '날짜 형식이 올바르지 않습니다. (YYYY-MM-DD)'}, status=400)
    except Exception as e:
        logger.error(f"심박수 데이터 조회 오류: {e}")
        return JsonResponse({'success': False, 'error': f'서버 오류 발생: {e}'}, status=500)


@staff_member_required
def get_last_hour_data(request):
    """최근 1시간 데이터 API (JSON 반환) - 시간별 심박수"""
    # 현재 시간 기준 1시간 전
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)

    # 최근 1시간 심박수 데이터 조회
    heart_rate_records = IntradayHeartRate.objects.filter(
        datetime__gte=one_hour_ago,
        datetime__lte=now
    ).order_by('-datetime')

    # 사용자 정보 미리 로드
    user_ids = set(record.fitbit_user_id for record in heart_rate_records)
    users_dict = {user.fitbit_user_id: user for user in FitbitUser.objects.filter(fitbit_user_id__in=user_ids)}

    records = []
    for record in heart_rate_records:
        fitbit_user = users_dict.get(record.fitbit_user_id)
        if fitbit_user:
            # UTC -> KST 변환
            dt_kst = record.datetime.astimezone(KST)
            
            records.append({
                'datetime': dt_kst.strftime('%Y-%m-%d %H:%M:%S'),
                'fitbit_user_id': fitbit_user.fitbit_user_id,
                'full_name': fitbit_user.full_name,
                'display_name': fitbit_user.display_name,
                'gender': fitbit_user.gender,
                'date_of_birth': fitbit_user.date_of_birth.isoformat() if fitbit_user.date_of_birth else None,
                'heart_rate': record.heart_rate,
            })

    return JsonResponse({
        'success': True,
        'records': records
    })


@staff_member_required
def get_date_range_data(request):
    """날짜 범위 데이터 API (JSON 반환) - 심박수, 걸음수, 칼로리 데이터 (심박수 기준 조인)"""
    # 파라미터 받기
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    logger.error(f'[DATE_DEBUG] 받은 파라미터: start_date={start_date_str}, end_date={end_date_str}')

    if not start_date_str or not end_date_str:
        return JsonResponse({'success': False, 'error': '시작 날짜와 종료 날짜를 지정해주세요.'}, status=400)

    try:
        # 날짜 파싱
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # 디버그 로그
        logger.error(f'[DATE_DEBUG] 파싱된 날짜: start_date={start_date}, end_date={end_date}')

        # 날짜 범위 검증
        if start_date > end_date:
            return JsonResponse({'success': False, 'error': '시작 날짜는 종료 날짜보다 앞서야 합니다.'}, status=400)

        # 최대 7일 제한
        days_diff = (end_date - start_date).days
        if days_diff > 6:
            return JsonResponse({'success': False, 'error': '최대 7일까지만 조회할 수 있습니다.'}, status=400)

        # datetime 변환 (KST)
        # KST 00:00:00 ~ KST 23:59:59.999
        start_datetime = KST.localize(datetime.combine(start_date, datetime.min.time()))
        end_datetime = KST.localize(datetime.combine(end_date, datetime.max.time()))

        logger.error(f'[DATE_DEBUG] KST 범위: {start_datetime} ~ {end_datetime}')
        logger.error(f'[DATE_DEBUG] UTC 범위: {start_datetime.astimezone(pytz.UTC)} ~ {end_datetime.astimezone(pytz.UTC)}')

        # 심박수 데이터 조회
        heart_rate_records = IntradayHeartRate.objects.filter(
            datetime__gte=start_datetime,
            datetime__lte=end_datetime
        ).order_by('-datetime')

        # 사용자 정보 미리 로드
        user_ids = set(record.fitbit_user_id for record in heart_rate_records)
        users_dict = {user.fitbit_user_id: user for user in FitbitUser.objects.filter(fitbit_user_id__in=user_ids)}

        # fitbit_users_m에서 프로필 정보 (최신 행)
        users_m_dict = {}
        for user_id in user_ids:
            latest_m = FitbitUserManagement.objects.filter(
                fitbit_user_id=user_id
            ).order_by('-created_at').first()
            if latest_m:
                users_m_dict[user_id] = latest_m

        # Steps 데이터 조회 (심박수와 같은 시간대만)
        steps_records = IntradaySteps.objects.filter(
            datetime__gte=start_datetime,
            datetime__lte=end_datetime,
            fitbit_user_id__in=user_ids
        )
        steps_dict = {(r.fitbit_user_id, r.datetime): r.steps for r in steps_records}

        # Calories 데이터 조회 (심박수와 같은 시간대만)
        calories_records = IntradayCalories.objects.filter(
            datetime__gte=start_datetime,
            datetime__lte=end_datetime,
            fitbit_user_id__in=user_ids
        )
        calories_dict = {(r.fitbit_user_id, r.datetime): r.calories for r in calories_records}

        records = []
        for record in heart_rate_records:
            fitbit_user = users_dict.get(record.fitbit_user_id)
            user_m = users_m_dict.get(record.fitbit_user_id)

            if fitbit_user:
                # 프로필 정보는 m 테이블 우선, 없으면 fitbit_users 사용
                full_name = user_m.full_name if user_m else fitbit_user.full_name
                display_name = user_m.display_name if user_m else fitbit_user.display_name
                gender = user_m.gender if user_m else fitbit_user.gender
                date_of_birth = user_m.date_of_birth if user_m else fitbit_user.date_of_birth

                # UTC -> KST 변환
                datetime_kst = record.datetime.astimezone(KST)

                # 같은 시간대의 steps, calories 가져오기
                key = (record.fitbit_user_id, record.datetime)
                steps = steps_dict.get(key)
                calories = calories_dict.get(key)

                records.append({
                    'datetime': datetime_kst.strftime('%Y-%m-%d %H:%M:%S'),
                    'fitbit_user_id': fitbit_user.fitbit_user_id,
                    'full_name': full_name,
                    'display_name': display_name,
                    'gender': gender,
                    'date_of_birth': date_of_birth.isoformat() if date_of_birth else None,
                    'heart_rate': record.heart_rate,
                    'steps': steps if steps is not None else '-',
                    'calories': round(calories, 2) if calories is not None else '-',
                })

        return JsonResponse({
            'success': True,
            'records': records,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'total_records': len(records)
        })

    except ValueError as e:
        return JsonResponse({'success': False, 'error': f'날짜 형식이 올바르지 않습니다: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'오류 발생: {str(e)}'}, status=500)


@staff_member_required
@csrf_exempt
def sync_last_hour(request):
    """최근 1시간 데이터 동기화"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다'}, status=405)

    # 한국 시간대 설정 (KST)
    # 현재 한국 시간 기준 1시간 전 (Fitbit API 지연 3분 고려)
    now = datetime.now(KST) - timedelta(minutes=3)
    one_hour_ago = now - timedelta(hours=1)

    # 시작/종료 시간 (HH:MM 형식)
    start_time = one_hour_ago.strftime('%H:%M')
    end_time = now.strftime('%H:%M')
    today = now.strftime('%Y-%m-%d')

    users = FitbitUser.objects.all()
    success_count = 0
    fail_count = 0

    for fitbit_user in users:
        try:
            # 토큰 갱신
            if not refresh_access_token(fitbit_user):
                fail_count += 1
                continue

            # 최근 1시간 데이터 동기화
            result = sync_fitbit_data_for_date(
                fitbit_user.fitbit_user_id,
                fitbit_user.access_token,
                date=today,
                start_time=start_time,
                end_time=end_time
            )

            if result['success']:
                success_count += 1
            else:
                fail_count += 1

        except Exception as e:
            fail_count += 1
            print(f"최근 1시간 데이터 동기화 오류 ({fitbit_user.fitbit_user_id}): {e}")

    return JsonResponse({
        'success': True,
        'success_count': success_count,
        'fail_count': fail_count,
        'start_time': start_time,
        'end_time': end_time
    })


@staff_member_required
@csrf_exempt
def sync_today_data(request):
    """모든 사용자의 오늘 데이터 전체 동기화"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다'}, status=405)

    # KST 기준 오늘 날짜
    today = datetime.now(KST).strftime('%Y-%m-%d')
    
    users = FitbitUser.objects.all()
    success_count = 0
    fail_count = 0
    failed_items = set()  # 실패한 데이터 타입 추적

    for fitbit_user in users:
        try:
            # 토큰 갱신
            if not refresh_access_token(fitbit_user):
                fail_count += 1
                continue

            # 오늘 데이터 전체 동기화
            result = sync_fitbit_data_for_date(
                fitbit_user.fitbit_user_id,
                fitbit_user.access_token,
                date=today,
                start_time=None,  # 하루 전체
                end_time=None
            )

            if result['success']:
                success_count += 1
            else:
                fail_count += 1

            # 실패한 항목 수집
            for key, value in result.items():
                if key.startswith('intraday_') or key == 'daily_summary':
                    if value is False:
                        # 데이터 타입 이름 변환
                        item_name = {
                            'daily_summary': '일일 요약',
                            'intraday_heart_rate': '심박수',
                            'intraday_steps': '걸음수',
                            'intraday_calories': '칼로리',
                            'intraday_distance': '거리',
                            'intraday_floors': '층수',
                            'intraday_elevation': '고도',
                            'intraday_spo2': 'SpO2',
                            'intraday_hrv': 'HRV'
                        }.get(key, key)
                        failed_items.add(item_name)

        except Exception as e:
            fail_count += 1
            print(f"오늘 데이터 동기화 오류 ({fitbit_user.fitbit_user_id}): {e}")

    return JsonResponse({
        'success': True,
        'success_count': success_count,
        'fail_count': fail_count,
        'date': today,
        'failed_items': list(failed_items) if failed_items else []
    })


@staff_member_required
@csrf_exempt
def sync_profiles(request):
    """모든 사용자의 프로필 정보 동기화"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다'}, status=405)

    users = FitbitUser.objects.all()
    success_count = 0
    fail_count = 0

    for fitbit_user in users:
        try:
            # Fitbit 프로필 API 호출
            headers = {'Authorization': f'Bearer {fitbit_user.access_token}'}
            response = requests.get(
                f"{settings.FITBIT_API_BASE_URL}/1/user/-/profile.json",
                headers=headers
            )

            if response.status_code == 200:
                profile_data = response.json().get('user', {})

                # 프로필 정보 저장
                fitbit_user.full_name = profile_data.get('fullName')
                fitbit_user.display_name = profile_data.get('displayName')
                fitbit_user.gender = profile_data.get('gender')
                fitbit_user.age = profile_data.get('age')

                # 생년월일 파싱
                dob = profile_data.get('dateOfBirth')
                if dob:
                    try:
                        fitbit_user.date_of_birth = datetime.strptime(dob, '%Y-%m-%d').date()
                    except:
                        pass

                fitbit_user.height = profile_data.get('height')
                fitbit_user.weight = profile_data.get('weight')
                fitbit_user.avatar_url = profile_data.get('avatar')

                # 가입일 파싱
                member_since = profile_data.get('memberSince')
                if member_since:
                    try:
                        fitbit_user.member_since = datetime.strptime(member_since, '%Y-%m-%d').date()
                    except:
                        pass

                # 동기화 시간 기록
                fitbit_user.profile_synced_at = timezone.now()
                fitbit_user.save()

                # 신규 사용자인 경우에만 fitbit_users_m 동기화
                # (fitbit_users_m에 없으면 신규로 간주)
                existing_in_m = FitbitUserManagement.objects.filter(
                    fitbit_user_id=fitbit_user.fitbit_user_id
                ).exists()

                if not existing_in_m:
                    # 신규 사용자 → fitbit_users_m에 추가
                    FitbitUserManagement.objects.create(
                        fitbit_user_id=fitbit_user.fitbit_user_id,
                        full_name=fitbit_user.full_name,
                        display_name=fitbit_user.display_name,
                        gender=fitbit_user.gender,
                        age=fitbit_user.age,
                        date_of_birth=fitbit_user.date_of_birth,
                        height=fitbit_user.height,
                        weight=fitbit_user.weight,
                        avatar_url=fitbit_user.avatar_url,
                        member_since=fitbit_user.member_since,
                        profile_synced_at=fitbit_user.profile_synced_at,
                    )
                    print(f"신규 사용자 {fitbit_user.fitbit_user_id}를 fitbit_users_m에 추가")
                
                success_count += 1
            else:
                fail_count += 1

        except Exception as e:
            fail_count += 1
            print(f"프로필 동기화 오류 ({fitbit_user.fitbit_user_id}): {e}")

    return JsonResponse({
        'success': True,
        'success_count': success_count,
        'fail_count': fail_count
    })


@staff_member_required
def admin_administration(request):
    """대상자 관리 페이지 (HTML만 반환)"""
    return render(request, 'fitbit/admin/administration.html', {
        'active_menu': 'management'
    })


@staff_member_required
def get_subjects_list(request):
    """대상자 목록 조회 API (JSON 반환) - polar_users 테이블 사용"""
    from ..models import PolarUser
    from datetime import date
    
    subjects = PolarUser.objects.filter(is_active=True).exclude(username='testuser').order_by('full_name')

    subjects_data = []
    today = date.today()
    
    for subject in subjects:
        # 생년월일에서 나이 자동 계산
        age = None
        if subject.date_of_birth:
            age = today.year - subject.date_of_birth.year
            # 생일이 지나지 않았으면 1 빼기
            if (today.month, today.day) < (subject.date_of_birth.month, subject.date_of_birth.day):
                age -= 1
        
        subjects_data.append({
            'username': subject.username,
            'full_name': subject.full_name or 'N/A',
            'gender': subject.gender or 'N/A',
            'age': age,
            'height': subject.height,
            'weight': subject.weight,
            'date_of_birth': subject.date_of_birth.isoformat() if subject.date_of_birth else None,
        })

    return JsonResponse({
        'success': True,
        'subjects': subjects_data
    })


@staff_member_required
@csrf_exempt
def update_subject(request):
    """대상자 정보 수정 API - polar_users 테이블 업데이트"""
    from ..models import PolarUser
    
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다'}, status=405)

    try:
        data = json.loads(request.body)
        username = data.get('username')

        if not username:
            return JsonResponse({'success': False, 'error': '사용자명이 필요합니다'}, status=400)

        # Polar 사용자 가져오기
        subject = PolarUser.objects.filter(username=username).first()

        if not subject:
            return JsonResponse({'success': False, 'error': '대상자를 찾을 수 없습니다'}, status=404)

        # 정보 업데이트 (나이는 생년월일에서 자동 계산되므로 업데이트 제외)
        if 'full_name' in data:
            subject.full_name = data['full_name']
        if 'gender' in data:
            subject.gender = data['gender']
        if 'height' in data and data['height']:
            subject.height = data['height']
        if 'weight' in data and data['weight']:
            subject.weight = data['weight']

        # date_of_birth 처리
        if 'date_of_birth' in data and data['date_of_birth']:
            try:
                subject.date_of_birth = datetime.strptime(data['date_of_birth'], '%Y-%m-%d').date()
            except:
                pass

        subject.save()

        # 나이 자동 계산
        from datetime import date
        today = date.today()
        age = None
        if subject.date_of_birth:
            age = today.year - subject.date_of_birth.year
            if (today.month, today.day) < (subject.date_of_birth.month, subject.date_of_birth.day):
                age -= 1

        return JsonResponse({
            'success': True,
            'message': '대상자 정보가 수정되었습니다',
            'subject': {
                'username': subject.username,
                'full_name': subject.full_name,
                'gender': subject.gender,
                'age': age,
                'height': subject.height,
                'weight': subject.weight,
                'date_of_birth': subject.date_of_birth.isoformat() if subject.date_of_birth else None,
            }
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@staff_member_required
@csrf_exempt
def sync_new_users_to_management(request):
    """Polar 사용자 동기화 (더미 함수 - Polar는 자동 동기화 불필요)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다'}, status=405)

    try:
        # Polar 사용자는 수동 등록이므로 동기화 불필요
        return JsonResponse({
            'success': True,
            'message': 'Polar 사용자는 수동 등록 방식입니다',
            'new_users_count': 0
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@staff_member_required
def search_polar_users(request):
    """Polar 사용자 검색 API - 이름으로 검색"""
    from ..models import PolarUser

    query = request.GET.get('q', '').strip()

    if not query:
        return JsonResponse({'success': False, 'error': '검색어를 입력해주세요'}, status=400)

    # 사용자 이름으로 검색
    users = PolarUser.objects.filter(
        full_name__icontains=query,
        is_active=True
    ).values('id', 'username', 'full_name', 'polar_device_id', 'gender', 'date_of_birth')[:10]

    users_list = list(users)

    return JsonResponse({
        'success': True,
        'users': users_list
    })


@staff_member_required
def get_polar_realtime_data(request):
    """Polar 실시간 데이터 스트리밍 API - 신규 데이터만 반환 (username + date_of_birth 기반)"""
    from ..models import PolarHeartRate

    user_id = request.GET.get('user_id')
    last_timestamp = request.GET.get('last_timestamp')  # 마지막 조회 시점
    initial_minutes = int(request.GET.get('initial_minutes', 10))  # 초기 로드 시 조회 기간

    if not user_id:
        return JsonResponse({'success': False, 'error': 'user_id는 필수입니다'}, status=400)

    try:
        # 사용자 조회
        from ..models import PolarUser
        polar_user = PolarUser.objects.filter(id=user_id).first()

        if not polar_user:
            return JsonResponse({'success': False, 'error': '사용자를 찾을 수 없습니다'}, status=404)

        username = polar_user.username
        date_of_birth = polar_user.date_of_birth

        # 초기 로드인지 신규 데이터 조회인지 구분
        if last_timestamp:
            # 실시간 스트리밍: 마지막 타임스탬프 이후의 데이터만 조회
            from dateutil import parser
            last_dt = parser.isoparse(last_timestamp)
            hr_data = PolarHeartRate.objects.filter(
                username=username,
                date_of_birth=date_of_birth,
                datetime__gt=last_dt  # 마지막 시점 이후만
            ).order_by('datetime').values('datetime', 'hr', 'rr', 'device_id')
        else:
            # 초기 로드: 최근 N분 데이터 조회
            time_threshold = timezone.now() - timedelta(minutes=initial_minutes)
            hr_data = PolarHeartRate.objects.filter(
                username=username,
                date_of_birth=date_of_birth,
                datetime__gte=time_threshold
            ).order_by('datetime').values('datetime', 'hr', 'rr', 'device_id')

        data_list = []
        for item in hr_data:
            data_list.append({
                'timestamp': item['datetime'].isoformat(),
                'hr': item['hr'],
                'rr': item['rr']
            })

        return JsonResponse({
            'success': True,
            'user': {
                'id': polar_user.id,
                'name': polar_user.full_name,
                'username': username,
                'date_of_birth': date_of_birth.isoformat() if date_of_birth else None
            },
            'data': data_list,
            'count': len(data_list),
            'is_initial': last_timestamp is None
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
