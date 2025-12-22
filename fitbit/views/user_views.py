"""
사용자 views - 홈, 대상자 현황, 기기 관리, 도움말, 데이터 동기화
"""
import requests
import pytz
from datetime import datetime
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import JsonResponse
from django.db.models import Avg, Max

from ..models import FitbitUser, DailySummary
from ..data_sync import sync_fitbit_data_range, sync_fitbit_data_for_date
from .common_views import refresh_fitbit_token

# KST Timezone 설정
KST = pytz.timezone('Asia/Seoul')

def home(request):
    """홈 페이지"""
    profile_data = None
    activity_data = None

    # 세션에 user_id가 있으면 DB에서 토큰 확인
    if 'user_id' in request.session:
        try:
            fitbit_user = FitbitUser.objects.get(fitbit_user_id=request.session['user_id'])
            # DB에 토큰이 비어있으면 재인증 필요
            if not fitbit_user.access_token or not fitbit_user.refresh_token:
                request.session.flush()  # 세션 삭제
                return redirect('login')
        except FitbitUser.DoesNotExist:
            pass

    if 'access_token' in request.session:
        access_token = request.session['access_token']
        headers = {'Authorization': f'Bearer {access_token}'}

        profile_response = requests.get(
            f"{settings.FITBIT_API_BASE_URL}/1/user/-/profile.json",
            headers=headers
        )

        if profile_response.status_code == 200:
            profile_data = profile_response.json()
            
            # KST 기준 오늘 날짜
            today = datetime.now(KST).strftime('%Y-%m-%d')
            
            activity_response = requests.get(
                f"{settings.FITBIT_API_BASE_URL}/1/user/-/activities/date/{today}.json",
                headers=headers
            )
            if activity_response.status_code == 200:
                activity_data = activity_response.json()

        elif profile_response.status_code == 401:
            if refresh_fitbit_token(request):
                return redirect('home')
            else:
                return redirect('logout')

    return render(request, 'fitbit/user/index.html', {
        'profile_data': profile_data,
        'activity_data': activity_data
    })


def subjects(request):
    """대상자 현황 페이지 - 사용자용"""
    if 'user_id' not in request.session:
        return redirect('login')

    # 현재 로그인한 사용자만 표시
    user_id = request.session['user_id']

    try:
        fitbit_user = FitbitUser.objects.get(fitbit_user_id=user_id)
        summaries = DailySummary.objects.filter(
            fitbit_user_id=user_id
        ).order_by('-date')[:7]

        user_stats = []
        if summaries.exists():
            stats = summaries.aggregate(
                avg_steps=Avg('steps'),
                avg_hr=Avg('resting_heart_rate'),
                last_date=Max('date')
            )

            user_stats.append({
                'fitbit_user_id': fitbit_user.fitbit_user_id,
                'username': fitbit_user.user.username if fitbit_user.user else 'N/A',
                'avg_steps': round(stats['avg_steps']) if stats['avg_steps'] else 0,
                'avg_hr': round(stats['avg_hr']) if stats['avg_hr'] else 0,
                'last_sync': stats['last_date'],
                'total_days': summaries.count()
            })

        return render(request, 'fitbit/user/subjects.html', {
            'total_users': 1,
            'user_stats': user_stats,
            'global_avg_steps': user_stats[0]['avg_steps'] if user_stats else 0,
            'global_avg_hr': user_stats[0]['avg_hr'] if user_stats else 0,
            'total_records': summaries.count()
        })

    except FitbitUser.DoesNotExist:
        return redirect('login')


def devices(request):
    """기기 등록 관리 페이지"""
    return render(request, 'fitbit/user/devices.html')


def help_page(request):
    """도움말 페이지"""
    return render(request, 'fitbit/user/help.html')


def dashboard(request):
    """대시보드"""
    if 'user_id' not in request.session:
        return redirect('login')

    user_id = request.session['user_id']
    summary_data = []
    avg_steps = 0
    avg_resting_hr = 0
    avg_exercise_minutes = 0

    try:
        summaries = DailySummary.objects.filter(
            fitbit_user_id=user_id
        ).order_by('-date')[:7]

        summary_data = list(summaries.values(
            'date', 'steps', 'distance', 'resting_heart_rate',
            'hr_zone_fat_burn_minutes', 'hr_zone_cardio_minutes', 'hr_zone_peak_minutes'
        ))

        if summary_data:
            total_steps = sum(day.get('steps') or 0 for day in summary_data)
            hr_data = [day.get('resting_heart_rate') for day in summary_data if day.get('resting_heart_rate')]
            total_resting_hr = sum(hr_data)

            total_exercise_minutes = sum(
                (day.get('hr_zone_fat_burn_minutes') or 0) +
                (day.get('hr_zone_cardio_minutes') or 0) +
                (day.get('hr_zone_peak_minutes') or 0)
                for day in summary_data
            )

            avg_steps = total_steps / len(summary_data)
            avg_resting_hr = total_resting_hr / len(hr_data) if hr_data else 0
            avg_exercise_minutes = total_exercise_minutes / len(summary_data)

    except Exception as e:
        print(f"대시보드 데이터 조회 오류: {e}")

    return render(request, 'fitbit/user/dashboard.html', {
        'summary_data': summary_data,
        'avg_steps': avg_steps,
        'avg_resting_hr': avg_resting_hr,
        'avg_exercise_minutes': avg_exercise_minutes
    })


def sync_data(request):
    """Fitbit 데이터 동기화 (최근 7일)"""
    if 'access_token' not in request.session or 'user_id' not in request.session:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)

    fitbit_user_id = request.session['user_id']
    access_token = request.session['access_token']

    days_back = int(request.GET.get('days', 7))

    try:
        results = sync_fitbit_data_range(fitbit_user_id, access_token, days_back)

        success_count = sum(1 for r in results if r['success'])
        total_hr = sum(r['intraday_hr'] for r in results)
        total_steps = sum(r['intraday_steps'] for r in results)
        total_calories = sum(r['intraday_calories'] for r in results)

        return JsonResponse({
            'success': True,
            'message': f'{days_back}일치 데이터 동기화 완료',
            'summary': {
                'total_days': len(results),
                'success_days': success_count,
                'failed_days': len(results) - success_count,
                'total_hr_records': total_hr,
                'total_steps_records': total_steps,
                'total_calories_records': total_calories
            },
            'details': results
        })

    except Exception as e:
        print(f"동기화 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


def sync_data_by_date(request):
    """특정 날짜의 Fitbit 데이터 동기화"""
    if 'access_token' not in request.session or 'user_id' not in request.session:
        return JsonResponse({'error': '로그인이 필요합니다.'}, status=401)

    fitbit_user_id = request.session['user_id']
    access_token = request.session['access_token']

    date = request.GET.get('date')
    if not date:
        return JsonResponse({'error': 'date 파라미터가 필요합니다. (YYYY-MM-DD)'}, status=400)

    try:
        result = sync_fitbit_data_for_date(fitbit_user_id, access_token, date)

        if result['success']:
            return JsonResponse({
                'success': True,
                'message': f'{date} 데이터 동기화 완료',
                'result': result
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Unknown error')
            }, status=500)

    except Exception as e:
        print(f"동기화 오류: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
