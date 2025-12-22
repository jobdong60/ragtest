from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password, check_password

class FitbitUser(models.Model):
    """Fitbit 사용자 정보"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True, related_name='fitbit_user')
    fitbit_user_id = models.CharField(max_length=255, unique=True)
    access_token = models.TextField()
    refresh_token = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    granted_scope = models.TextField(null=True, blank=True)

    # Fitbit 프로필 정보
    full_name = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)  # cm
    weight = models.FloatField(null=True, blank=True)  # kg
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    member_since = models.DateField(null=True, blank=True)
    profile_synced_at = models.DateTimeField(null=True, blank=True)  # 프로필 마지막 동기화 시간

    class Meta:
        db_table = 'fitbit_users'

    def __str__(self):
        return f"FitbitUser({self.fitbit_user_id})"


class FitbitUserManagement(models.Model):
    """Fitbit 사용자 관리용 테이블 (프로필 정보 히스토리)"""
    id = models.AutoField(primary_key=True)
    fitbit_user_id = models.CharField(max_length=255, db_index=True)  # unique 제거, index 추가

    # 프로필 정보
    full_name = models.CharField(max_length=255, null=True, blank=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    height = models.FloatField(null=True, blank=True)  # cm
    weight = models.FloatField(null=True, blank=True)  # kg
    avatar_url = models.URLField(max_length=500, null=True, blank=True)
    member_since = models.DateField(null=True, blank=True)

    # 타임스탬프
    created_at = models.DateTimeField(auto_now_add=True)  # 이 행이 생성된 시간
    updated_at = models.DateTimeField(auto_now=True)  # 이 행이 마지막으로 수정된 시간
    profile_synced_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'fitbit_users_m'
        ordering = ['-created_at']  # 최신 순으로 정렬
        indexes = [
            models.Index(fields=['fitbit_user_id', '-created_at']),  # 사용자별 최신 조회용
        ]

    def __str__(self):
        return f"FitbitUserManagement({self.fitbit_user_id}, {self.created_at})"


class DailySummary(models.Model):
    """일일 활동 요약 정보"""
    fitbit_user_id = models.CharField(max_length=255)
    date = models.DateField()
    steps = models.IntegerField(null=True, blank=True)
    distance = models.FloatField(null=True, blank=True)
    calories = models.IntegerField(null=True, blank=True)
    resting_heart_rate = models.IntegerField(null=True, blank=True)
    hr_zone_out_of_range_minutes = models.IntegerField(null=True, blank=True)
    hr_zone_fat_burn_minutes = models.IntegerField(null=True, blank=True)
    hr_zone_cardio_minutes = models.IntegerField(null=True, blank=True)
    hr_zone_peak_minutes = models.IntegerField(null=True, blank=True)
    hr_zone_fat_burn_min_hr = models.IntegerField(null=True, blank=True)
    hr_zone_fat_burn_max_hr = models.IntegerField(null=True, blank=True)
    hr_zone_cardio_min_hr = models.IntegerField(null=True, blank=True)
    hr_zone_cardio_max_hr = models.IntegerField(null=True, blank=True)
    hr_zone_peak_min_hr = models.IntegerField(null=True, blank=True)
    hr_zone_peak_max_hr = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'daily_summaries'
        unique_together = ('fitbit_user_id', 'date')
        ordering = ['-date']

    def __str__(self):
        return f"DailySummary({self.fitbit_user_id}, {self.date})"


class IntradayHeartRate(models.Model):
    """1분 단위 심박수 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    heart_rate = models.IntegerField()  # 심박수 (bpm)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_heart_rate'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradayHeartRate({self.fitbit_user_id}, {self.datetime}, {self.heart_rate}bpm)"


class IntradaySteps(models.Model):
    """5분 단위 걸음 수 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    steps = models.IntegerField()  # 걸음 수
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_steps'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradaySteps({self.fitbit_user_id}, {self.datetime}, {self.steps})"


class IntradayCalories(models.Model):
    """5분 단위 칼로리 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    calories = models.FloatField()  # 칼로리
    level = models.IntegerField(null=True, blank=True)  # 활동 강도 레벨 (0-3)
    mets = models.IntegerField(null=True, blank=True)  # METs (Metabolic Equivalent)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_calories'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradayCalories({self.fitbit_user_id}, {self.datetime}, {self.calories}kcal)"


class IntradayDistance(models.Model):
    """1분 단위 거리 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    distance = models.FloatField()  # 거리 (km)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_distance'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradayDistance({self.fitbit_user_id}, {self.datetime}, {self.distance}km)"


class IntradayFloors(models.Model):
    """1분 단위 층수 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    floors = models.IntegerField()  # 오른 층수
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_floors'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradayFloors({self.fitbit_user_id}, {self.datetime}, {self.floors})"


class IntradayElevation(models.Model):
    """1분 단위 고도 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    elevation = models.FloatField()  # 고도 (m)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_elevation'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradayElevation({self.fitbit_user_id}, {self.datetime}, {self.elevation}m)"


class IntradaySpO2(models.Model):
    """SpO2 (혈중 산소 포화도) 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    spo2 = models.FloatField()  # SpO2 (%)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_spo2'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradaySpO2({self.fitbit_user_id}, {self.datetime}, {self.spo2}%)"


class IntradayHRV(models.Model):
    """HRV (심박 변이도) 데이터"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    datetime = models.DateTimeField()  # 날짜 + 시간
    rmssd = models.FloatField()  # RMSSD (ms)
    coverage = models.FloatField(null=True, blank=True)  # 데이터 완전성
    hf = models.FloatField(null=True, blank=True)  # High Frequency
    lf = models.FloatField(null=True, blank=True)  # Low Frequency
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'intraday_hrv'
        unique_together = ('fitbit_user_id', 'datetime')
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-datetime']),
        ]

    def __str__(self):
        return f"IntradayHRV({self.fitbit_user_id}, {self.datetime}, RMSSD:{self.rmssd}ms)"


class SleepLog(models.Model):
    """수면 로그 (하루 1-2회)"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    log_id = models.BigIntegerField(unique=True)  # Fitbit sleep log ID
    date = models.DateField()  # 수면 날짜
    start_time = models.DateTimeField()  # 수면 시작
    end_time = models.DateTimeField()  # 수면 종료
    duration = models.IntegerField()  # 총 수면 시간 (ms)
    minutes_asleep = models.IntegerField()  # 실제 수면 시간 (분)
    minutes_awake = models.IntegerField()  # 깨어있던 시간 (분)
    minutes_deep = models.IntegerField(null=True, blank=True)  # 깊은 수면 (분)
    minutes_light = models.IntegerField(null=True, blank=True)  # 얕은 수면 (분)
    minutes_rem = models.IntegerField(null=True, blank=True)  # 렘 수면 (분)
    minutes_wake = models.IntegerField(null=True, blank=True)  # 깸 (분)
    efficiency = models.IntegerField(null=True, blank=True)  # 수면 효율성 (%)
    sleep_score = models.IntegerField(null=True, blank=True)  # 수면 점수 (0-100)
    is_main_sleep = models.BooleanField(default=False)  # 메인 수면 여부
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'sleep_logs'
        ordering = ['-date', '-start_time']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-date']),
        ]

    def __str__(self):
        return f"SleepLog({self.fitbit_user_id}, {self.date}, {self.minutes_asleep}min)"


class BreathingRate(models.Model):
    """호흡수 데이터 (하루 1회)"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    date = models.DateField()  # 날짜
    breathing_rate = models.FloatField()  # 평균 호흡수 (회/분)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'breathing_rates'
        unique_together = ('fitbit_user_id', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-date']),
        ]

    def __str__(self):
        return f"BreathingRate({self.fitbit_user_id}, {self.date}, {self.breathing_rate}/min)"


class SkinTemperature(models.Model):
    """피부 온도 데이터 (하루 1회)"""
    fitbit_user_id = models.CharField(max_length=255, db_index=True)
    date = models.DateField()  # 날짜
    relative_temp = models.FloatField()  # 상대적 온도 변화 (°C)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'skin_temperatures'
        unique_together = ('fitbit_user_id', 'date')
        ordering = ['-date']
        indexes = [
            models.Index(fields=['fitbit_user_id', '-date']),
        ]

    def __str__(self):
        return f"SkinTemperature({self.fitbit_user_id}, {self.date}, {self.relative_temp}°C)"


class PolarHeartRate(models.Model):
    """Polar 기기 실시간 심박수 및 RR 간격 데이터"""
    device_id = models.CharField(max_length=255, db_index=True)  # Polar 기기 MAC 주소
    datetime = models.DateTimeField(db_index=True)  # 데이터 시각 (timestamp에서 변환)
    hr = models.IntegerField()  # 심박수 (bpm)
    rr = models.IntegerField(null=True, blank=True)  # RR 간격 (ms)
    username = models.CharField(max_length=150, null=True, blank=True)  # 사용자명
    date_of_birth = models.DateField(null=True, blank=True)  # 생년월일
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'polar_heart_rate'
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['device_id', '-datetime']),
            models.Index(fields=['-datetime']),
        ]

    def __str__(self):
        return f"PolarHeartRate({self.device_id}, {self.datetime}, HR:{self.hr}bpm, RR:{self.rr}ms)"


class PolarHeartRateNN(models.Model):
    """Polar 심박수 이상치 제거 데이터 (NN = Normal-to-Normal)"""
    device_id = models.CharField(max_length=255, db_index=True)  # Polar 기기 MAC 주소
    datetime = models.DateTimeField(db_index=True)  # 데이터 시각
    hr = models.IntegerField()  # 심박수 (bpm) - 이상치 제거됨
    rr = models.IntegerField(null=True, blank=True)  # RR 간격 (ms) - 이상치 제거됨
    username = models.CharField(max_length=150, null=True, blank=True)  # 사용자명
    date_of_birth = models.DateField(null=True, blank=True)  # 생년월일
    is_outlier_removed = models.BooleanField(default=False)  # 이상치가 제거되었는지 여부
    original_hr = models.IntegerField(null=True, blank=True)  # 원본 HR (이상치인 경우)
    original_rr = models.IntegerField(null=True, blank=True)  # 원본 RR (이상치인 경우)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'polar_heart_rate_nn'
        ordering = ['-datetime']
        indexes = [
            models.Index(fields=['device_id', '-datetime']),
            models.Index(fields=['-datetime']),
            models.Index(fields=['username', 'date_of_birth', '-datetime']),
        ]

    def __str__(self):
        return f"PolarHeartRateNN({self.device_id}, {self.datetime}, HR:{self.hr}bpm, RR:{self.rr}ms)"


class PolarHeartRateIndex5(models.Model):
    """Polar HRV 지표 (5분 단위 계산)"""
    username = models.CharField(max_length=150, db_index=True)  # 사용자명
    date_of_birth = models.DateField(db_index=True)  # 생년월일
    datetime_start = models.DateTimeField(db_index=True)  # 5분 구간 시작 시각
    datetime_end = models.DateTimeField()  # 5분 구간 종료 시각
    
    # HRV 지표 (RR 간격 기반)
    rmssd = models.FloatField(null=True, blank=True)  # RMSSD (ms)
    sdnn = models.FloatField(null=True, blank=True)  # SDNN (ms)
    hf_power = models.FloatField(null=True, blank=True)  # HF Power (ms²)
    lf_power = models.FloatField(null=True, blank=True)  # LF Power (ms²)
    lf_hf_ratio = models.FloatField(null=True, blank=True)  # LF/HF ratio
    
    # HR 통계
    mean_hr = models.FloatField(null=True, blank=True)  # 평균 HR (bpm)
    sd_hr = models.FloatField(null=True, blank=True)  # HR 표준편차 (bpm)
    hr_upper = models.FloatField(null=True, blank=True)  # mean + 1.96*SD
    hr_lower = models.FloatField(null=True, blank=True)  # mean - 1.96*SD
    
    # RR 통계
    mean_rr = models.FloatField(null=True, blank=True)  # 평균 RR 간격 (ms)
    
    # 메타 정보
    data_count = models.IntegerField(default=0)  # 해당 5분간 데이터 개수
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'polar_heart_rate_index_5'
        ordering = ['-datetime_start']
        indexes = [
            models.Index(fields=['username', 'date_of_birth', '-datetime_start']),
            models.Index(fields=['-datetime_start']),
        ]
        unique_together = ('username', 'date_of_birth', 'datetime_start')

    def __str__(self):
        return f"PolarHRVIndex5({self.username}, {self.datetime_start}, RMSSD:{self.rmssd}ms)"


class PolarUser(models.Model):
    """Polar 앱 사용자"""
    username = models.CharField(max_length=150, unique=True, db_index=True)  # 로그인 ID
    password = models.CharField(max_length=128)  # 해시된 비밀번호
    email = models.EmailField(unique=True, null=True, blank=True)

    # 프로필 정보
    full_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    gender = models.CharField(max_length=20, null=True, blank=True)  # MALE, FEMALE, OTHER
    date_of_birth = models.DateField(null=True, blank=True)
    age = models.IntegerField(null=True, blank=True)  # 연령
    height = models.FloatField(null=True, blank=True)  # 키 (cm)
    weight = models.FloatField(null=True, blank=True)  # 몸무게 (kg)

    # Polar 기기 정보
    polar_device_id = models.CharField(max_length=255, null=True, blank=True, db_index=True)

    # 계정 상태
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'polar_users'
        ordering = ['-created_at']

    def set_password(self, raw_password):
        """비밀번호 해시화"""
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        """비밀번호 검증"""
        return check_password(raw_password, self.password)

    @property
    def is_authenticated(self):
        """
        항상 True를 반환 (Django의 User 모델 호환성을 위한 속성)
        이 속성은 AnonymousUser와 구분하기 위해 사용됨
        """
        return True

    @property
    def is_anonymous(self):
        """
        항상 False를 반환 (Django의 User 모델 호환성을 위한 속성)
        """
        return False

    def __str__(self):
        return f"PolarUser({self.username})"


# Backward compatibility alias
MobileUser = PolarUser
