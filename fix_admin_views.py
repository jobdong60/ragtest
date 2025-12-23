
import os

file_path = 'fitbit/views/admin_views.py'

# The clean code for the new function
clean_function = '''
@staff_member_required
@csrf_exempt
def create_subject(request):
    """대상자 신규 등록 API - PolarUser 생성"""
    from ..models import PolarUser
    import random
    import string
    import json
    from datetime import date

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
        # logger.error(f"대상자 등록 오류: {e}")
        return JsonResponse({'success': False, 'error': f'서버 오류: {str(e)}'}, status=500)
'''

# Read original file, ignoring errors
with open(file_path, 'rb') as f:
    content = f.read()

# Try to decode as utf-8, replacing errors
text = content.decode('utf-8', errors='replace')

# Find where the corrupted function starts (likely where create_subject is defined)
# Prior to my edit, the file ended with get_polar_realtime_data function.
# I will look for the line before I appended.
delimiter = "def get_polar_realtime_data(request):"

if delimiter in text:
    # Find the end of this function. It ends around line 1013 in original.
    # A safe bet is to assume the corruption is at the very end.
    # I'll search for the LAST valid function and truncate after it.
    
    # Actually, simpler: I'll locate "def create_subject" (or what remains of it) and cut there.
    # Or just replace the whole file content if I had it. 
    # But I don't have the full previous content.
    
    # Strategy: Find "def get_polar_realtime_data" and keep everything until the end of that function.
    # Then append my clean function.
    
    split_index = text.rfind(delimiter)
    if split_index != -1:
        # Keep text starting from delimiter
        # But wait, I need the text BEFORE that too.
        # So I keep text[:split_index] + ...
        
        # Actually, let's look for where the corruption starts.
        # It's likely after the last 'except Exception as e:' of get_polar_realtime_data
        
        # Let's find the end of get_polar_realtime_data.
        # It has `return JsonResponse({'success': False, 'error': str(e)}, status=500)`
        
        last_valid_block = "return JsonResponse({'success': False, 'error': str(e)}, status=500)"
        last_occurrence = text.rfind(last_valid_block)
        
        # If I found it, and it's near the end, I can truncate after it.
        # But wait, create_subject ALSO has that line.
        # The prompt says `get_polar_realtime_data` was the last one.
        # I'll find the SECOND TO LAST occurrence if create_subject is there, or LAST if it's garbled.
        
        # Safer bet: regex or just manual check.
        # I will iterate lines.
        lines = text.splitlines()
        clean_lines = []
        param_seen = False
        for line in lines:
            if "def create_subject" in line:
                break # Stop here
            if "def create_subject" in line.replace("?", ""): # Handle garbled text
                break
                
            # If line looks like garbage (lots of questions marks or replacement chars), stop
            if line.count('\ufffd') > 5:
                break
                
            clean_lines.append(line)
            
        # Reassemble
        fixed_content = "\n".join(clean_lines) + "\n\n" + clean_function
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        print("Fixed admin_views.py")
    else:
        print("Could not find delimiter")
else:
    print("Could not find delimiter")
