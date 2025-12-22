"""
공통 views - 로그인, 로그아웃, 콜백, 약관 등
"""
from django.shortcuts import render, redirect
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User
from datetime import datetime
import base64
import requests
from ..models import FitbitUser


def refresh_fitbit_token(request):
    """Fitbit 토큰 갱신"""
    if 'refresh_token' not in request.session:
        return False

    auth_header = base64.b64encode(
        f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'refresh_token',
        'refresh_token': request.session['refresh_token']
    }

    token_response = requests.post(settings.FITBIT_TOKEN_URL, headers=headers, data=data)

    if token_response.status_code == 200:
        new_token_data = token_response.json()
        request.session['access_token'] = new_token_data['access_token']
        request.session['refresh_token'] = new_token_data['refresh_token']
        print("토큰이 성공적으로 갱신되었습니다.")
        return True
    else:
        print("토큰 갱신 실패:", token_response.text)
        return False


def login(request):
    """Fitbit 로그인"""
    redirect_uri = request.build_absolute_uri('/callback')

    auth_url = (
        f"{settings.FITBIT_AUTH_URL}?response_type=code"
        f"&client_id={settings.FITBIT_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={settings.FITBIT_SCOPE}"
        f"&expires_in=604800"
        f"&prompt=login"
    )

    return redirect(auth_url)


@csrf_exempt
def callback(request):
    """Fitbit OAuth 콜백"""
    auth_code = request.GET.get('code')
    if not auth_code:
        return HttpResponse("Error: Authorization code not found.", status=400)

    redirect_uri = request.build_absolute_uri('/callback')
    auth_header = base64.b64encode(
        f"{settings.FITBIT_CLIENT_ID}:{settings.FITBIT_CLIENT_SECRET}".encode()
    ).decode()

    headers = {
        'Authorization': f'Basic {auth_header}',
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    data = {
        'grant_type': 'authorization_code',
        'redirect_uri': redirect_uri,
        'code': auth_code
    }

    # 디버깅용 로그
    print(f"[DEBUG] Redirect URI: {redirect_uri}")
    print(f"[DEBUG] Auth code: {auth_code[:10]}...")
    print(f"[DEBUG] Token URL: {settings.FITBIT_TOKEN_URL}")

    token_response = requests.post(settings.FITBIT_TOKEN_URL, headers=headers, data=data)

    if token_response.status_code != 200:
        print(f"[ERROR] Token request failed: {token_response.status_code}")
        print(f"[ERROR] Response: {token_response.text}")
        return HttpResponse(f"Error getting token: {token_response.text}", status=400)

    token_data = token_response.json()

    request.session['access_token'] = token_data['access_token']
    request.session['refresh_token'] = token_data['refresh_token']
    request.session['user_id'] = token_data['user_id']

    # DB에 사용자 정보 저장
    try:
        fitbit_user, created = FitbitUser.objects.get_or_create(
            fitbit_user_id=token_data['user_id'],
            defaults={
                'access_token': token_data['access_token'],
                'refresh_token': token_data['refresh_token'],
                'granted_scope': token_data.get('scope', '')
            }
        )

        if not created:
            fitbit_user.access_token = token_data['access_token']
            fitbit_user.refresh_token = token_data['refresh_token']
            fitbit_user.granted_scope = token_data.get('scope', '')
            fitbit_user.save()

        # Fitbit 프로필 정보 가져오기
        profile_headers = {'Authorization': f'Bearer {token_data["access_token"]}'}
        profile_response = requests.get(
            f"{settings.FITBIT_API_BASE_URL}/1/user/-/profile.json",
            headers=profile_headers
        )

        if profile_response.status_code == 200:
            profile_data = profile_response.json().get('user', {})
            print(f"[DEBUG] Profile data: {profile_data}")

            # 프로필 정보 저장
            fitbit_user.full_name = profile_data.get('fullName')
            fitbit_user.display_name = profile_data.get('displayName')
            fitbit_user.gender = profile_data.get('gender')
            fitbit_user.age = profile_data.get('age')

            # 생년월일 파싱
            dob = profile_data.get('dateOfBirth')
            if dob:
                from datetime import datetime
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
                from datetime import datetime
                try:
                    fitbit_user.member_since = datetime.strptime(member_since, '%Y-%m-%d').date()
                except:
                    pass

            # 동기화 시간 기록
            from django.utils import timezone
            fitbit_user.profile_synced_at = timezone.now()
            fitbit_user.save()
            print("[DEBUG] Profile saved successfully")

            # 신규 사용자인 경우 fitbit_users_m에도 추가
            if created:
                from ..models import FitbitUserManagement
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
                print("[DEBUG] New user also added to fitbit_users_m")
        else:
            print(f"[WARNING] Failed to fetch profile: {profile_response.status_code}")

        if not fitbit_user.user:
            # Django User가 이미 존재하는지 확인
            from django.contrib.auth.hashers import make_password
            import secrets
            username = f'fitbit_{token_data["user_id"]}'
            random_password = secrets.token_urlsafe(32)
            django_user, user_created = User.objects.get_or_create(
                username=username,
                defaults={'password': make_password(random_password)}
            )
            fitbit_user.user = django_user
            fitbit_user.save()

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print("데이터베이스 오류:", e)
        print("상세 오류:", error_details)
        return HttpResponse(f"데이터베이스에 정보를 저장하는 중 오류가 발생했습니다: {str(e)}", status=500)

    return redirect('home')


def logout(request):
    """로그아웃"""
    request.session.flush()
    return redirect('login')


def terms(request):
    """이용약관"""
    return render(request, 'fitbit/user/terms.html')


def privacy(request):
    """개인정보 처리방침"""
    return render(request, 'fitbit/user/privacy.html')
