"""
기존 사용자들의 Fitbit 프로필 정보를 가져오는 Django 관리 명령
"""
from django.core.management.base import BaseCommand
from django.conf import settings
from fitbit.models import FitbitUser
import requests
from datetime import datetime


class Command(BaseCommand):
    help = '기존 사용자들의 Fitbit 프로필 정보를 가져옵니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=str,
            help='특정 Fitbit User ID의 프로필만 가져오기',
        )

    def handle(self, *args, **options):
        user_id = options.get('user_id')

        if user_id:
            users = FitbitUser.objects.filter(fitbit_user_id=user_id)
            if not users.exists():
                self.stdout.write(self.style.ERROR(f'사용자 {user_id}를 찾을 수 없습니다.'))
                return
        else:
            users = FitbitUser.objects.all()

        self.stdout.write(f'총 {users.count()}명의 프로필을 가져옵니다...\n')

        success_count = 0
        fail_count = 0

        for fitbit_user in users:
            self.stdout.write(f'처리중: {fitbit_user.fitbit_user_id}... ', ending='')

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
                    from django.utils import timezone
                    fitbit_user.profile_synced_at = timezone.now()
                    fitbit_user.save()

                    self.stdout.write(self.style.SUCCESS(f'성공 ({fitbit_user.full_name or fitbit_user.display_name})'))
                    success_count += 1

                elif response.status_code == 401:
                    self.stdout.write(self.style.WARNING('토큰 만료 (재로그인 필요)'))
                    fail_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f'실패 (HTTP {response.status_code})'))
                    fail_count += 1

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'오류: {str(e)}'))
                fail_count += 1

        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS(f'완료: {success_count}명 성공'))
        if fail_count > 0:
            self.stdout.write(self.style.WARNING(f'실패: {fail_count}명'))
