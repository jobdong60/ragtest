#!/bin/bash
# Fitbit 데이터 동기화 cron job 설정 스크립트

SCRIPT_PATH="/home/sehnr_kdca1885/myhealth-app/sync_all_users.py"
PYTHON_PATH="/home/sehnr_kdca1885/myhealth-app/venv/bin/python"
LOG_PATH="/home/sehnr_kdca1885/myhealth-app/logs/sync.log"

# cron job 추가 (5분마다 실행)
CRON_JOB="*/5 * * * * $PYTHON_PATH $SCRIPT_PATH >> $LOG_PATH 2>&1"

# 기존 cron 목록 가져오기
crontab -l > /tmp/current_cron 2>/dev/null || true

# 이미 등록되어 있는지 확인
if grep -q "sync_all_users.py" /tmp/current_cron; then
    echo "Cron job이 이미 등록되어 있습니다."
else
    # 새로운 cron job 추가
    echo "$CRON_JOB" >> /tmp/current_cron
    crontab /tmp/current_cron
    echo "Cron job이 성공적으로 등록되었습니다."
    echo "설정: 5분마다 모든 사용자 데이터 동기화"
fi

# 현재 cron 목록 출력
echo ""
echo "현재 등록된 cron jobs:"
crontab -l

rm /tmp/current_cron
