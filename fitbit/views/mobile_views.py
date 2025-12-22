"""
모바일 앱 API views - JWT 인증 기반
"""
import logging
from datetime import datetime
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from ..models import PolarUser
from ..authentication import PolarJWTAuthentication

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    모바일 사용자 회원가입

    POST /api/mobile/register/
    {
        "username": "user123",
        "password": "password123",
        "email": "user@example.com",
        "full_name": "홍길동",
        "phone_number": "010-1234-5678",
        "gender": "MALE",
        "date_of_birth": "1990-01-01",
        "age": 35,
        "height": 175.5,
        "weight": 70.2,
        "polar_device_id": "24:AC:AC:0C:D8:6A"
    }
    """
    try:
        # 필수 필드 검증
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'success': False,
                'message': 'username과 password는 필수입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 사용자명 중복 확인
        if PolarUser.objects.filter(username=username).exists():
            return Response({
                'success': False,
                'message': '이미 존재하는 사용자명입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 이메일 중복 확인 (선택)
        email = request.data.get('email')
        if email and PolarUser.objects.filter(email=email).exists():
            return Response({
                'success': False,
                'message': '이미 존재하는 이메일입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 생성
        user = PolarUser(
            username=username,
            email=email,
            full_name=request.data.get('full_name'),
            phone_number=request.data.get('phone_number'),
            gender=request.data.get('gender'),
            age=request.data.get('age'),
            height=request.data.get('height'),
            weight=request.data.get('weight'),
            polar_device_id=request.data.get('polar_device_id'),
        )

        # 생년월일 처리
        date_of_birth = request.data.get('date_of_birth')
        if date_of_birth:
            try:
                user.date_of_birth = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': '생년월일 형식이 올바르지 않습니다. (YYYY-MM-DD)'
                }, status=status.HTTP_400_BAD_REQUEST)

        # 비밀번호 해시화
        user.set_password(password)
        user.save()

        logger.info(f"New mobile user registered: {username}")

        return Response({
            'success': True,
            'message': '회원가입이 완료되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Registration error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'회원가입 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    모바일 사용자 로그인

    POST /api/mobile/login/
    {
        "username": "user123",
        "password": "password123"
    }
    """
    try:
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({
                'success': False,
                'message': 'username과 password는 필수입니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        # 사용자 조회
        try:
            user = PolarUser.objects.get(username=username)
        except PolarUser.DoesNotExist:
            return Response({
                'success': False,
                'message': '사용자를 찾을 수 없습니다.'
            }, status=status.HTTP_404_NOT_FOUND)

        # 비활성화된 계정 체크
        if not user.is_active:
            return Response({
                'success': False,
                'message': '비활성화된 계정입니다.'
            }, status=status.HTTP_403_FORBIDDEN)

        # 비밀번호 검증
        if not user.check_password(password):
            return Response({
                'success': False,
                'message': '비밀번호가 올바르지 않습니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

        # JWT 토큰 생성
        refresh = RefreshToken()
        refresh['user_id'] = user.id
        refresh['username'] = user.username

        # 마지막 로그인 시간 업데이트
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        logger.info(f"Mobile user logged in: {username}")

        return Response({
            'success': True,
            'message': '로그인에 성공했습니다.',
            'tokens': {
                'access': str(refresh.access_token),
                'refresh': str(refresh),
            },
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'gender': user.gender,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'age': user.age,
                'height': user.height,
                'weight': user.weight,
                'polar_device_id': user.polar_device_id,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': f'로그인 중 오류가 발생했습니다: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Refresh Token으로 새로운 Access Token 발급

    POST /api/mobile/token/refresh/
    {
        "refresh": "eyJ0eXAiOiJKV1Qi..."
    }
    """
    try:
        refresh_token_str = request.data.get('refresh')

        if not refresh_token_str:
            return Response({
                'success': False,
                'message': 'refresh token이 필요합니다.'
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Refresh Token 검증 및 새 토큰 생성
            refresh = RefreshToken(refresh_token_str)

            # 토큰에서 user_id 추출
            user_id = refresh.get('user_id')

            # 사용자 확인
            user = PolarUser.objects.get(id=user_id)

            if not user.is_active:
                return Response({
                    'success': False,
                    'message': '비활성화된 계정입니다.'
                }, status=status.HTTP_403_FORBIDDEN)

            # 새로운 Access Token 생성
            new_access = refresh.access_token

            logger.info(f"Access token refreshed for user: {user.username}")

            return Response({
                'success': True,
                'message': '토큰이 갱신되었습니다.',
                'tokens': {
                    'access': str(new_access),
                    'refresh': str(refresh),  # 새로운 refresh token도 발급 (ROTATE_REFRESH_TOKENS=True)
                }
            }, status=status.HTTP_200_OK)

        except Exception as token_error:
            logger.error(f"Invalid refresh token: {str(token_error)}")
            return Response({
                'success': False,
                'message': '유효하지 않거나 만료된 refresh token입니다.'
            }, status=status.HTTP_401_UNAUTHORIZED)

    except PolarUser.DoesNotExist:
        return Response({
            'success': False,
            'message': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': 'Token 갱신 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@authentication_classes([PolarJWTAuthentication])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """
    사용자 프로필 조회

    GET /api/mobile/profile/
    Headers: Authorization: Bearer <access_token>
    """
    try:
        # 인증된 사용자 가져오기 (PolarJWTAuthentication에서 자동으로 설정됨)
        user = request.user

        return Response({
            'success': True,
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'gender': user.gender,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'age': user.age,
                'height': user.height,
                'weight': user.weight,
                'polar_device_id': user.polar_device_id,
                'created_at': user.created_at.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
            }
        }, status=status.HTTP_200_OK)

    except PolarUser.DoesNotExist:
        return Response({
            'success': False,
            'message': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Get profile error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': '프로필 조회 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@authentication_classes([PolarJWTAuthentication])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """
    사용자 프로필 수정

    PUT /api/mobile/profile/
    Headers: Authorization: Bearer <access_token>
    {
        "full_name": "홍길동",
        "email": "new@example.com",
        "phone_number": "010-9999-8888",
        "gender": "MALE",
        "date_of_birth": "1990-01-01",
        "age": 35,
        "height": 175.5,
        "weight": 70.2,
        "polar_device_id": "24:AC:AC:0C:D8:6A"
    }
    """
    try:
        # 인증된 사용자 가져오기 (PolarJWTAuthentication에서 자동으로 설정됨)
        user = request.user

        # 업데이트 가능한 필드
        if 'full_name' in request.data:
            user.full_name = request.data['full_name']
        if 'email' in request.data:
            email = request.data['email']
            # 이메일 중복 체크 (자신 제외)
            if email and PolarUser.objects.filter(email=email).exclude(id=user.id).exists():
                return Response({
                    'success': False,
                    'message': '이미 사용 중인 이메일입니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            user.email = email
        if 'phone_number' in request.data:
            user.phone_number = request.data['phone_number']
        if 'gender' in request.data:
            user.gender = request.data['gender']
        if 'date_of_birth' in request.data:
            try:
                user.date_of_birth = datetime.strptime(request.data['date_of_birth'], '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'success': False,
                    'message': '생년월일 형식이 올바르지 않습니다. (YYYY-MM-DD)'
                }, status=status.HTTP_400_BAD_REQUEST)
        if 'age' in request.data:
            user.age = request.data['age']
        if 'height' in request.data:
            user.height = request.data['height']
        if 'weight' in request.data:
            user.weight = request.data['weight']
        if 'polar_device_id' in request.data:
            user.polar_device_id = request.data['polar_device_id']

        user.save()

        logger.info(f"Mobile user profile updated: {user.username}")

        return Response({
            'success': True,
            'message': '프로필이 수정되었습니다.',
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'full_name': user.full_name,
                'phone_number': user.phone_number,
                'gender': user.gender,
                'date_of_birth': user.date_of_birth.isoformat() if user.date_of_birth else None,
                'age': user.age,
                'height': user.height,
                'weight': user.weight,
                'polar_device_id': user.polar_device_id,
            }
        }, status=status.HTTP_200_OK)

    except PolarUser.DoesNotExist:
        return Response({
            'success': False,
            'message': '사용자를 찾을 수 없습니다.'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Update profile error: {str(e)}", exc_info=True)
        return Response({
            'success': False,
            'message': '프로필 수정 중 오류가 발생했습니다.'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
