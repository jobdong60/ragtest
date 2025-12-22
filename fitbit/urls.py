from django.urls import path
from .views import user_views, admin_views, common_views, polar_views, mobile_views

urlpatterns = [
    # 공통 (로그인, 로그아웃 등)
    path('login/', common_views.login, name='login'),
    path('callback/', common_views.callback, name='callback'),
    path('logout/', common_views.logout, name='logout'),
    path('terms/', common_views.terms, name='terms'),
    path('privacy/', common_views.privacy, name='privacy'),

    # 사용자 페이지
    path('', user_views.home, name='home'),
    path('dashboard/', user_views.dashboard, name='dashboard'),
    path('subjects/', user_views.subjects, name='subjects'),
    path('devices/', user_views.devices, name='devices'),
    path('help/', user_views.help_page, name='help'),
    path('sync/', user_views.sync_data, name='sync_data'),
    path('sync/date/', user_views.sync_data_by_date, name='sync_data_by_date'),

    # 관리자 페이지
    path('manager/login/', admin_views.admin_login, name='admin_login'),
    path('manager/dashboard/', admin_views.admin_dashboard, name='admin_dashboard'),
    path('manager/dashboard/data/', admin_views.get_dashboard_data, name='get_dashboard_data'),
    path('manager/subjects/', admin_views.admin_subjects, name='admin_subjects'),
    path('manager/subjects/last-hour-data/', admin_views.get_last_hour_data, name='get_last_hour_data'),
    path('manager/subjects/date-range-data/', admin_views.get_date_range_data, name='get_date_range_data'),
    path('manager/subjects/sync-last-hour/', admin_views.sync_last_hour, name='sync_last_hour'),
    
    # 심박수 탭
    path('manager/polar-heart-rate/', admin_views.admin_polar_heart_rate, name='admin_polar_heart_rate'),
    path('manager/fitbit-heart-rate/data/', admin_views.get_fitbit_heart_rate_data, name='get_fitbit_heart_rate_data'),

    path('manager/sync-profiles/', admin_views.sync_profiles, name='sync_profiles'),
    path('manager/sync-today/', admin_views.sync_today_data, name='sync_today_data'),
    path('manager/administration/', admin_views.admin_administration, name='admin_administration'),
    path('manager/administration/subjects/', admin_views.get_subjects_list, name='get_subjects_list'),
    path('manager/administration/update/', admin_views.update_subject, name='update_subject'),
    path('manager/administration/sync-new-users/', admin_views.sync_new_users_to_management, name='sync_new_users_to_management'),

    # Polar 데이터 수신 엔드포인트
    path('data/polar/heartrate/', polar_views.receive_polar_data, name='receive_polar_data'),

    # Polar 데이터 조회 (관리자용)
    path('manager/polar/devices/', polar_views.get_polar_devices, name='get_polar_devices'),
    path('manager/polar/data/', polar_views.get_polar_heart_rate_data, name='get_polar_data'),
    path('manager/polar/hrv-index/', polar_views.get_polar_hrv_index_data, name='get_polar_hrv_index'),
    path('manager/polar/search-users/', admin_views.search_polar_users, name='search_polar_users'),
    path('manager/polar/realtime-data/', admin_views.get_polar_realtime_data, name='get_polar_realtime_data'),

    # 모바일 앱 API (JWT 인증)
    path('api/mobile/register/', mobile_views.register, name='mobile_register'),
    path('api/mobile/login/', mobile_views.login, name='mobile_login'),
    path('api/mobile/token/refresh/', mobile_views.refresh_token_view, name='mobile_token_refresh'),
    path('api/mobile/profile/', mobile_views.get_profile, name='mobile_get_profile'),
    path('api/mobile/profile/update/', mobile_views.update_profile, name='mobile_update_profile'),

]
