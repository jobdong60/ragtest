"""
5분마다 모든 Fitbit 사용자의 Intraday 데이터 수집

사용법:
    python manage.py collect_intraday_data
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import requests
import base64
import time
from fitbit.models import FitbitUser, IntradayHeartRate, IntradaySteps, IntradayCalories
from django.conf import settings


class Command(BaseCommand):
    help = '모든 Fitbit 사용자의 최근 5분 Intraday 데이터 수집'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=5,
            help='수집할 과거 분 수 (기본값: 5분)'
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        self.stdout.write(f'\n=== Intraday 데이터 수집 시작 (최근 {minutes}분) ===\n')

        # 모든 Fitbit 사용자 조회
        users = FitbitUser.objects.all()

        if not users.exists():
            self.stdout.write(self.style.WARNING('수집할 사용자가 없습니다.'))
            return

        self.stdout.write(f'총 {users.count()}명의 사용자 데이터 수집 중...\n')

        # 각 사용자별로 데이터 수집
        for user in users:
            self.stdout.write(f'\n[{user.fitbit_user_id}] 데이터 수집 시작...')

            try:
                # 1. 심박수 수집 (1분 단위)
                hr_count = self.collect_heart_rate(user, minutes)
                self.stdout.write(self.style.SUCCESS(f'  ✓ 심박수: {hr_count}개 저장'))

                # 2. 걸음 수 수집 (5분 단위)
                steps_count = self.collect_steps(user, minutes)
                self.stdout.write(self.style.SUCCESS(f'  ✓ 걸음 수: {steps_count}개 저장'))

                # 3. 칼로리 수집 (5분 단위)
                calories_count = self.collect_calories(user, minutes)
                self.stdout.write(self.style.SUCCESS(f'  ✓ 칼로리: {calories_count}개 저장'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ 오류: {str(e)}'))
                continue

        self.stdout.write(self.style.SUCCESS('\n=== 데이터 수집 완료 ===\n'))

    def refresh_token_if_needed(self, user):
        """토큰 갱신"""
        auth_header = base64.b64encode(
            f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}".encode()
        ).decode()

        headers = {
            'Authorization': f'Basic {auth_header}',
            'Content-Type': 'application/x-www-form-urlencoded'
        }

        data = {
            'grant_type': 'refresh_token',
            'refresh_token': user.refresh_token
        }

        response = requests.post(settings.FITBIT_TOKEN_URL, headers=headers, data=data)

        if response.status_code == 200:
            token_data = response.json()
            user.access_token = token_data['access_token']
            user.refresh_token = token_data['refresh_token']
            user.save()
            return True
        else:
            raise Exception(f"토큰 갱신 실패: {response.text}")

    def make_api_request(self, user, url, retry=True):
        """Fitbit API 요청 (자동 토큰 갱신 포함)"""
        headers = {'Authorization': f'Bearer {user.access_token}'}
        response = requests.get(url, headers=headers)

        # 401 에러 시 토큰 갱신 후 재시도
        if response.status_code == 401 and retry:
            self.stdout.write('  토큰 갱신 중...')
            self.refresh_token_if_needed(user)
            return self.make_api_request(user, url, retry=False)

        if response.status_code != 200:
            raise Exception(f"API 요청 실패 ({response.status_code}): {response.text}")

        return response.json()

    def collect_heart_rate(self, user, minutes):
        """심박수 데이터 수집 (1분 단위)"""
        now = timezone.localtime(timezone.now())
        end_time = now.strftime('%H:%M')
        start_time = (now - timedelta(minutes=minutes)).strftime('%H:%M')
        date = now.strftime('%Y-%m-%d')

        url = (
            f"{settings.FITBIT_API_BASE_URL}/1/user/-/activities/heart/date/{date}/1d/1min/"
            f"time/{start_time}/{end_time}.json"
        )

        data = self.make_api_request(user, url)

        count = 0
        if 'activities-heart-intraday' in data and 'dataset' in data['activities-heart-intraday']:
            for entry in data['activities-heart-intraday']['dataset']:
                dt = timezone.make_aware(
                    datetime.strptime(f"{date} {entry['time']}", '%Y-%m-%d %H:%M:%S')
                )

                IntradayHeartRate.objects.update_or_create(
                    fitbit_user_id=user.fitbit_user_id,
                    datetime=dt,
                    defaults={'heart_rate': entry['value']}
                )
                count += 1

        return count

    def collect_steps(self, user, minutes):
        """걸음 수 데이터 수집 (5분 단위)"""
        now = timezone.localtime(timezone.now())
        end_time = now.strftime('%H:%M')
        start_time = (now - timedelta(minutes=minutes)).strftime('%H:%M')
        date = now.strftime('%Y-%m-%d')

        url = (
            f"{settings.FITBIT_API_BASE_URL}/1/user/-/activities/steps/date/{date}/1d/5min/"
            f"time/{start_time}/{end_time}.json"
        )

        data = self.make_api_request(user, url)

        count = 0
        if 'activities-steps-intraday' in data and 'dataset' in data['activities-steps-intraday']:
            for entry in data['activities-steps-intraday']['dataset']:
                dt = timezone.make_aware(
                    datetime.strptime(f"{date} {entry['time']}", '%Y-%m-%d %H:%M:%S')
                )

                IntradaySteps.objects.update_or_create(
                    fitbit_user_id=user.fitbit_user_id,
                    datetime=dt,
                    defaults={'steps': entry['value']}
                )
                count += 1

        return count

    def collect_calories(self, user, minutes):
        """칼로리 데이터 수집 (5분 단위)"""
        now = timezone.localtime(timezone.now())
        end_time = now.strftime('%H:%M')
        start_time = (now - timedelta(minutes=minutes)).strftime('%H:%M')
        date = now.strftime('%Y-%m-%d')

        url = (
            f"{settings.FITBIT_API_BASE_URL}/1/user/-/activities/calories/date/{date}/1d/5min/"
            f"time/{start_time}/{end_time}.json"
        )

        data = self.make_api_request(user, url)

        count = 0
        if 'activities-calories-intraday' in data and 'dataset' in data['activities-calories-intraday']:
            for entry in data['activities-calories-intraday']['dataset']:
                dt = timezone.make_aware(
                    datetime.strptime(f"{date} {entry['time']}", '%Y-%m-%d %H:%M:%S')
                )

                IntradayCalories.objects.update_or_create(
                    fitbit_user_id=user.fitbit_user_id,
                    datetime=dt,
                    defaults={
                        'calories': entry['value'],
                        'level': entry.get('level'),
                        'mets': entry.get('mets')
                    }
                )
                count += 1

        return count
