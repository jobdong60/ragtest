import os
import json
import logging
from datetime import datetime, timedelta
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Avg, Max, Min, Count
from django.utils import timezone
import pytz
from ..models import PolarHeartRate, PolarUser, PolarHeartRateIndex5

logger = logging.getLogger(__name__)

# .env에서 API 키 로드
API_KEY = os.getenv('DATA_POLAR_ENDPOINT_API_KEY', 'datapolarendpointapikey')


def verify_api_key(request):
    """API 키 검증"""
    # Header에서 API 키 확인 (X-API-Key 또는 Authorization)
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization')

    # Authorization Bearer 형식 처리
    if api_key and api_key.startswith('Bearer '):
        api_key = api_key[7:]

    return api_key == API_KEY


@csrf_exempt
@require_http_methods(["POST"])
def receive_polar_data(request):
    """
    Polar 기기로부터 실시간 심박수 및 RR 간격 데이터 수신

    Expected JSON format (single object):
    {
        "hr": 75,
        "rr": 800,
        "timestamp": 1678886400000,
        "deviceId": "00:22:D0:8A:47:7A",
        "username": "john",
        "dateofbirth": "1993-01-30"
    }

    Or JSON array (multiple objects):
    [
        {"hr": 75, "rr": 800, "timestamp": 1678886400000, "deviceId": "00:22:D0:8A:47:7A", "username": "john", "dateofbirth": "1993-01-30"},
        {"hr": 76, "rr": 790, "timestamp": 1678886401000, "deviceId": "00:22:D0:8A:47:7A", "username": "john", "dateofbirth": "1993-01-30"}
    ]
    """
    try:
        # 요청 수신 로그
        logger.info(f"[POLAR] Received POST request from {request.META.get('REMOTE_ADDR')}")
        logger.info(f"[POLAR] Request body: {request.body.decode('utf-8', errors='ignore')[:500]}")

        # API 키 검증
        if not verify_api_key(request):
            logger.warning(f"Unauthorized access attempt from {request.META.get('REMOTE_ADDR')}")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid or missing API key'
            }, status=401)

        # JSON 데이터 파싱
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON format received")
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid JSON format'
            }, status=400)

        # 배열인지 단일 객체인지 확인
        if isinstance(data, list):
            # 배열 처리
            if not data:
                logger.error("Empty array received")
                return JsonResponse({
                    'status': 'error',
                    'message': 'Empty array'
                }, status=400)

            data_list = data
            logger.info(f"[POLAR] Processing array with {len(data_list)} items")
        else:
            # 단일 객체를 배열로 변환
            data_list = [data]
            logger.info("[POLAR] Processing single object")

        # 저장된 데이터 목록
        saved_data = []
        errors = []

        # 각 데이터 항목 처리
        for idx, item in enumerate(data_list):
            try:
                # 필수 필드 검증
                required_fields = ['hr', 'timestamp', 'deviceId', 'username', 'dateofbirth']
                missing_fields = [field for field in required_fields if field not in item]

                if missing_fields:
                    error_msg = f"Item {idx}: Missing required fields: {', '.join(missing_fields)}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                # 데이터 추출
                hr = item['hr']
                rr = item.get('rr')  # Optional
                timestamp = item['timestamp']
                device_id = item['deviceId']
                username = item['username']
                dateofbirth_str = item['dateofbirth']

                # 타임스탬프 변환 (milliseconds to datetime)
                try:
                    dt = datetime.fromtimestamp(timestamp / 1000.0)
                except (ValueError, OSError) as e:
                    error_msg = f"Item {idx}: Invalid timestamp: {timestamp}, error: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                # 생년월일 변환 (YYYY-MM-DD to date)
                try:
                    date_of_birth = datetime.strptime(dateofbirth_str, '%Y-%m-%d').date()
                except (ValueError, TypeError) as e:
                    error_msg = f"Item {idx}: Invalid dateofbirth format: {dateofbirth_str}, expected YYYY-MM-DD"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                # 데이터 유효성 검증
                if not isinstance(hr, (int, float)) or hr < 0 or hr > 300:
                    error_msg = f"Item {idx}: Invalid heart rate value: {hr}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                if rr is not None and (not isinstance(rr, (int, float)) or rr < 0):
                    error_msg = f"Item {idx}: Invalid RR interval value: {rr}"
                    logger.error(error_msg)
                    errors.append(error_msg)
                    continue

                # 데이터베이스에 저장
                polar_data = PolarHeartRate.objects.create(
                    device_id=device_id,
                    datetime=dt,
                    hr=int(hr),
                    rr=int(rr) if rr is not None else None,
                    username=username,
                    date_of_birth=date_of_birth
                )

                saved_data.append({
                    'id': polar_data.id,
                    'device_id': polar_data.device_id,
                    'datetime': polar_data.datetime.isoformat(),
                    'hr': polar_data.hr,
                    'rr': polar_data.rr,
                    'username': polar_data.username,
                    'date_of_birth': polar_data.date_of_birth.isoformat()
                })

                logger.info(f"Polar data saved: Device={device_id}, User={username}, DOB={date_of_birth}, HR={hr}, RR={rr}, Time={dt}")

            except Exception as e:
                error_msg = f"Item {idx}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                errors.append(error_msg)

        # 응답 생성
        if saved_data:
            response = {
                'status': 'success',
                'message': f'{len(saved_data)} record(s) saved successfully',
                'saved_count': len(saved_data),
                'data': saved_data
            }
            if errors:
                response['errors'] = errors
                response['error_count'] = len(errors)

            logger.info(f"[POLAR] Saved {len(saved_data)} records, {len(errors)} errors")
            return JsonResponse(response, status=201)
        else:
            logger.error(f"[POLAR] No data saved. Errors: {errors}")
            return JsonResponse({
                'status': 'error',
                'message': 'No data saved',
                'errors': errors
            }, status=400)

    except Exception as e:
        logger.error(f"Error processing Polar data: {str(e)}", exc_info=True)
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@staff_member_required
def get_polar_devices(request):
    """
    Polar 기기 목록 조회
    """
    try:
        devices = PolarHeartRate.objects.values('device_id').annotate(
            data_count=Count('id')
        ).order_by('device_id')

        return JsonResponse({
            'success': True,
            'devices': list(devices)
        })

    except Exception as e:
        logger.error(f"Error fetching Polar devices: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to fetch devices'
        }, status=500)


@staff_member_required
def get_polar_heart_rate_data(request):
    """
    Polar 데이터 조회 및 차트 데이터 생성 (username + date_of_birth 기반)
    """
    try:
        username = request.GET.get('username')
        date_of_birth_str = request.GET.get('date_of_birth')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')

        if not username or not start_date or not end_date:
            return JsonResponse({
                'success': False,
                'message': 'Missing required parameters'
            }, status=400)

        # 생년월일 파싱
        date_of_birth = None
        if date_of_birth_str:
            try:
                date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            except ValueError:
                logger.warning(f"[POLAR_QUERY] Invalid date_of_birth format received: {date_of_birth_str}")

        if date_of_birth is None:
            polar_user = PolarUser.objects.filter(username=username).only('date_of_birth').first()
            if polar_user and polar_user.date_of_birth:
                date_of_birth = polar_user.date_of_birth
                logger.info(f"[POLAR_QUERY] Fallback date_of_birth fetched from PolarUser for {username}")

        if date_of_birth is None:
            return JsonResponse({
                'success': False,
                'message': 'date_of_birth is required for Polar data lookup'
            }, status=400)

        # KST timezone 설정
        kst = pytz.timezone('Asia/Seoul')

        # 날짜 파싱 (KST 기준)
        start_datetime = datetime.strptime(start_date, '%Y-%m-%d')
        end_datetime = datetime.strptime(end_date, '%Y-%m-%d')

        # KST 00:00:00 ~ 다음날 00:00:00 직전 범위 설정
        start_datetime = kst.localize(start_datetime.replace(hour=0, minute=0, second=0))
        end_datetime = kst.localize((end_datetime + timedelta(days=1)).replace(hour=0, minute=0, second=0))

        # UTC로 변환하여 DB 조회
        start_utc = start_datetime.astimezone(pytz.UTC)
        end_utc = end_datetime.astimezone(pytz.UTC)

        logger.info(f"[POLAR_QUERY] Username: {username}, DOB: {date_of_birth}")
        logger.info(f"[POLAR_QUERY] KST: {start_datetime} ~ {end_datetime}")
        logger.info(f"[POLAR_QUERY] UTC: {start_utc} ~ {end_utc}")

        # 데이터 조회 (username + date_of_birth 기반)
        query = PolarHeartRate.objects.filter(
            username=username,
            date_of_birth=date_of_birth,
            datetime__gte=start_utc,
            datetime__lt=end_utc
        ).order_by('datetime')

        data = list(query.values('datetime', 'hr', 'rr', 'device_id'))

        logger.info(f"[POLAR_QUERY] Found {len(data)} records")

        if not data:
            return JsonResponse({
                'success': True,
                'chart_data': {'labels': [], 'hr_data': [], 'rr_data': []},
                'stats': {'avg_hr': 0, 'max_hr': 0, 'min_hr': 0, 'avg_rr': 0}
            })

        # 차트 데이터 생성 (KST로 표시)
        labels = []
        hr_data = []
        rr_data = []

        for item in data:
            # UTC를 KST로 변환하여 표시
            dt_kst = item['datetime'].astimezone(kst)
            labels.append(dt_kst.strftime('%Y-%m-%d %H:%M:%S'))
            hr_data.append(item['hr'])
            rr_data.append(item['rr'] if item['rr'] is not None else None)

        # 통계 계산
        hr_values = [d['hr'] for d in data]
        rr_values = [d['rr'] for d in data if d['rr'] is not None]

        stats = {
            'avg_hr': round(sum(hr_values) / len(hr_values), 1) if hr_values else 0,
            'max_hr': max(hr_values) if hr_values else 0,
            'min_hr': min(hr_values) if hr_values else 0,
            'avg_rr': round(sum(rr_values) / len(rr_values), 1) if rr_values else 0
        }

        return JsonResponse({
            'success': True,
            'chart_data': {
                'labels': labels,
                'hr_data': hr_data,
                'rr_data': rr_data
            },
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error fetching Polar data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to fetch data'
        }, status=500)


@staff_member_required
def get_polar_hrv_index_data(request):
    """
    특정 유저의 특정 날짜의 HRV Index 데이터 조회 (5분 단위)
    """
    try:
        username = request.GET.get('username')
        date_of_birth_str = request.GET.get('date_of_birth')
        selected_date_str = request.GET.get('date')

        if not all([username, date_of_birth_str, selected_date_str]):
            return JsonResponse({
                'success': False,
                'message': 'username, date_of_birth, date are required'
            }, status=400)

        # 날짜 파싱
        try:
            date_of_birth = datetime.strptime(date_of_birth_str, '%Y-%m-%d').date()
            selected_date = datetime.strptime(selected_date_str, '%Y-%m-%d').date()
        except ValueError:
            return JsonResponse({
                'success': False,
                'message': 'Invalid date format. Use YYYY-MM-DD'
            }, status=400)

        # 한국 시간대 설정
        kst = pytz.timezone('Asia/Seoul')
        
        # 해당 날짜의 시작과 끝 (KST 기준)
        start_datetime = kst.localize(datetime.combine(selected_date, datetime.min.time()))
        end_datetime = kst.localize(datetime.combine(selected_date, datetime.max.time()))

        # HRV Index 데이터 조회
        hrv_data = PolarHeartRateIndex5.objects.filter(
            username=username,
            date_of_birth=date_of_birth,
            datetime_start__gte=start_datetime,
            datetime_start__lt=end_datetime
        ).order_by('datetime_start')

        if not hrv_data.exists():
            return JsonResponse({
                'success': True,
                'message': 'No HRV index data found for the selected date',
                'chart_data': {
                    'labels': [],
                    'mean_hr_data': [],
                    'rmssd_data': []
                },
                'stats': {}
            })

        # 차트 데이터 생성
        labels = []
        mean_hr_data = []
        hr_upper_data = []
        hr_lower_data = []
        mean_rr_data = []
        rmssd_data = []
        sdnn_data = []
        hf_power_data = []
        lf_power_data = []
        lf_hf_ratio_data = []

        for record in hrv_data:
            # KST로 변환
            time_kst = record.datetime_start.astimezone(kst)
            labels.append(time_kst.strftime('%H:%M'))
            
            # HR 및 95% CI
            mean_hr_data.append(round(record.mean_hr, 1) if record.mean_hr else None)
            hr_upper_data.append(round(record.hr_upper, 1) if record.hr_upper else None)
            hr_lower_data.append(round(record.hr_lower, 1) if record.hr_lower else None)
            
            # RR 통계
            mean_rr_data.append(round(record.mean_rr, 1) if record.mean_rr else None)
            
            # HRV 지표들
            rmssd_data.append(round(record.rmssd, 1) if record.rmssd else None)
            sdnn_data.append(round(record.sdnn, 1) if record.sdnn else None)
            hf_power_data.append(round(record.hf_power, 1) if record.hf_power else None)
            lf_power_data.append(round(record.lf_power, 1) if record.lf_power else None)
            lf_hf_ratio_data.append(round(record.lf_hf_ratio, 2) if record.lf_hf_ratio else None)

        # 통계 계산
        valid_hr = [x for x in mean_hr_data if x is not None]
        valid_rr = [x for x in mean_rr_data if x is not None]
        valid_rmssd = [x for x in rmssd_data if x is not None]
        valid_sdnn = [x for x in sdnn_data if x is not None]
        valid_hf = [x for x in hf_power_data if x is not None]
        valid_lf = [x for x in lf_power_data if x is not None]
        valid_lf_hf = [x for x in lf_hf_ratio_data if x is not None]

        stats = {
            'avg_mean_hr': round(sum(valid_hr) / len(valid_hr), 1) if valid_hr else 0,
            'max_mean_hr': round(max(valid_hr), 1) if valid_hr else 0,
            'min_mean_hr': round(min(valid_hr), 1) if valid_hr else 0,
            'avg_mean_rr': round(sum(valid_rr) / len(valid_rr), 1) if valid_rr else 0,
            'avg_rmssd': round(sum(valid_rmssd) / len(valid_rmssd), 1) if valid_rmssd else 0,
            'avg_sdnn': round(sum(valid_sdnn) / len(valid_sdnn), 1) if valid_sdnn else 0,
            'avg_hf_power': round(sum(valid_hf) / len(valid_hf), 1) if valid_hf else 0,
            'avg_lf_power': round(sum(valid_lf) / len(valid_lf), 1) if valid_lf else 0,
            'avg_lf_hf_ratio': round(sum(valid_lf_hf) / len(valid_lf_hf), 2) if valid_lf_hf else 0,
            'data_points': len(labels)
        }

        return JsonResponse({
            'success': True,
            'chart_data': {
                'labels': labels,
                'mean_hr_data': mean_hr_data,
                'hr_upper_data': hr_upper_data,
                'hr_lower_data': hr_lower_data,
                'mean_rr_data': mean_rr_data,
                'rmssd_data': rmssd_data,
                'sdnn_data': sdnn_data,
                'hf_power_data': hf_power_data,
                'lf_power_data': lf_power_data,
                'lf_hf_ratio_data': lf_hf_ratio_data
            },
            'stats': stats
        })

    except Exception as e:
        logger.error(f"Error fetching HRV index data: {str(e)}", exc_info=True)
        return JsonResponse({
            'success': False,
            'message': 'Failed to fetch HRV index data'
        }, status=500)
