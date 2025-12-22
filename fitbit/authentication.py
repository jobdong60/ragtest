"""
모바일 앱용 JWT 인증 클래스
PolarUser 모델을 사용하는 커스텀 인증
"""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from fitbit.models import PolarUser


class PolarJWTAuthentication(JWTAuthentication):
    """
    PolarUser 모델을 사용하는 JWT 인증 클래스
    """

    def get_user(self, validated_token):
        """
        JWT 토큰에서 user_id를 추출하여 PolarUser 객체를 반환
        """
        try:
            user_id = validated_token.get('user_id')
            if user_id is None:
                raise InvalidToken('Token contained no recognizable user identification')

            user = PolarUser.objects.get(id=user_id)

            if not user.is_active:
                raise AuthenticationFailed('User is inactive')

            return user

        except PolarUser.DoesNotExist:
            raise AuthenticationFailed('User not found')
        except Exception as e:
            raise AuthenticationFailed(f'Authentication failed: {str(e)}')
