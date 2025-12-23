@staff_member_required
@csrf_exempt
def create_subject(request):
    """대상자 신규 등록 API - PolarUser 생성"""
    from ..models import PolarUser
    import random
    import string

    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST 요청만 허용됩니다'}, status=405)

    try:
        data = json.loads(request.body)
        
        # 필수 필드 추출
        full_name = data.get('full_name')
        phone_number = data.get('phone_number')
        birth_year = data.get('birth_year')
        gender = data.get('gender')
        height = data.get('height')
        weight = data.get('weight')

        if not all([full_name, phone_number, birth_year, gender]):
            return JsonResponse({'success': False, 'error': '이름, 전화번호, 출생연도, 성별은 필수 항목입니다.'}, status=400)

        # 생년월일 생성 (YYYY-01-01)
        try:
            date_of_birth = date(int(birth_year), 1, 1)
        except ValueError:
             return JsonResponse({'success': False, 'error': '올바른 출생연도를 입력해주세요.'}, status=400)

        # 사용자명 생성 (이름 + 전화번호 뒤 4자리)
        # 중복 시 랜덤 문자 추가
        base_username = f"user_{phone_number[-4:]}"
        username = base_username
        counter = 1
        while PolarUser.objects.filter(username=username).exists():
            username = f"{base_username}_{counter}"
            counter += 1

        # 비밀번호는 전화번호 뒤 4자리로 설정
        password = phone_number[-4:]

        # PolarUser 생성
        new_subject = PolarUser(
            username=username,
            full_name=full_name,
            phone_number=phone_number,
            gender=gender,
            date_of_birth=date_of_birth,
            height=float(height) if height else None,
            weight=float(weight) if weight else None,
            age=date.today().year - int(birth_year),
            is_active=True
        )
        new_subject.set_password(password)
        new_subject.save()

        return JsonResponse({
            'success': True,
            'message': '대상자가 성공적으로 등록되었습니다.',
            'subject': {
                'username': new_subject.username,
                'full_name': new_subject.full_name,
                'phone_number': new_subject.phone_number,
                'gender': new_subject.gender,
                'age': new_subject.age,
                'date_of_birth': new_subject.date_of_birth.isoformat()
            }
        })

    except Exception as e:
        logger.error(f"대상자 등록 오류: {e}")
        return JsonResponse({'success': False, 'error': f'서버 오류: {str(e)}'}, status=500)
