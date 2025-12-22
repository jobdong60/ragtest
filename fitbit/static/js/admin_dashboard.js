/**
 * 관리자 대시보드 AJAX 스크립트
 */

// 버킷 크기 고정 (1분)
let currentBucketSize = 1;

// 페이지 로드 시 데이터 가져오기
document.addEventListener('DOMContentLoaded', function() {
    loadDashboardData();
});

// 대시보드 데이터 로드
function loadDashboardData() {
    showLoading();

    // 시간 값 가져오기 (시간만, 분은 00으로 고정)
    const startHour = document.getElementById('startHour')?.value || '9';
    const endHour = document.getElementById('endHour')?.value || '21';
    const startTime = startHour.padStart(2, '0') + ':00';
    const endTime = endHour.padStart(2, '0') + ':00';

    fetch(`/manager/dashboard/data/?bucket_size=${currentBucketSize}&start_time=${startTime}&end_time=${endTime}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            updateDashboard(data);
            showContent();
        })
        .catch(error => {
            console.error('데이터 로드 실패:', error);
            showError(error.message);
        });
}

// 대시보드 새로고침
function refreshDashboard() {
    const refreshIcon = document.getElementById('refreshIcon');
    refreshIcon.classList.add('animate-spin');

    loadDashboardData();

    setTimeout(() => {
        refreshIcon.classList.remove('animate-spin');
    }, 1000);
}

// 대시보드 UI 업데이트
function updateDashboard(data) {
    // 통계 카드 업데이트 - 오늘/어제/7일간
    const usersTodayEl = document.getElementById('usersToday');
    const totalUsersTodayEl = document.getElementById('totalUsersToday');
    const usersYesterdayEl = document.getElementById('usersYesterday');
    const totalUsersYesterdayEl = document.getElementById('totalUsersYesterday');
    const users7DaysEl = document.getElementById('users7Days');
    const totalUsers7DaysEl = document.getElementById('totalUsers7Days');

    if (usersTodayEl) usersTodayEl.textContent = data.users_with_data_today;
    if (totalUsersTodayEl) totalUsersTodayEl.textContent = data.total_users;

    if (usersYesterdayEl) usersYesterdayEl.textContent = data.users_with_data_yesterday;
    if (totalUsersYesterdayEl) totalUsersYesterdayEl.textContent = data.total_users;

    if (users7DaysEl) users7DaysEl.textContent = data.users_with_data_7days;
    if (totalUsers7DaysEl) totalUsers7DaysEl.textContent = data.total_users;

    // 사용자 테이블 업데이트
    updateUserTable(data.user_stats);
}

// 사용자 테이블 업데이트
function updateUserTable(userStats) {
    const tbody = document.getElementById('userTableBody');
    tbody.innerHTML = '';

    if (userStats.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center text-gray-500">
                    <div class="flex flex-col items-center">
                        <svg class="w-12 h-12 text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"></path>
                        </svg>
                        <p>등록된 사용자가 없습니다</p>
                    </div>
                </td>
            </tr>
        `;
        return;
    }

    userStats.forEach(stat => {
        const row = createUserRow(stat);
        tbody.appendChild(row);
    });
}

// 와플 차트 생성 함수
function createWaffleChart(dailyCompliance) {
    if (!dailyCompliance || dailyCompliance.length === 0) {
        return '<div class="flex gap-1"><span class="text-gray-400 text-xs">데이터 없음</span></div>';
    }

    const boxes = dailyCompliance.map(day => {
        const rate = day.rate;
        let bgColor;
        let title;

        if (rate === 0) {
            bgColor = 'bg-gray-300';
            title = `${day.date}: 데이터 없음`;
        } else if (rate >= 80) {
            bgColor = 'bg-green-500';
            title = `${day.date}: ${rate}%`;
        } else if (rate >= 50) {
            bgColor = 'bg-yellow-500';
            title = `${day.date}: ${rate}%`;
        } else {
            bgColor = 'bg-red-500';
            title = `${day.date}: ${rate}%`;
        }

        return `<div class="w-6 h-6 ${bgColor} rounded" title="${title}"></div>`;
    }).join('');

    return `<div class="flex gap-1">${boxes}</div>`;
}

// 사용자 행 생성
function createUserRow(stat) {
    const tr = document.createElement('tr');
    tr.className = 'hover:bg-gray-50 transition-colors';

    tr.innerHTML = `
        <td class="px-6 py-4 whitespace-nowrap">
            <div class="text-sm font-medium text-gray-900">${stat.full_name}</div>
            <div class="text-xs text-gray-500">
                ${stat.is_staff ?
                    '<span class="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800">관리자</span>' :
                    '<span class="px-2 py-0.5 rounded-full bg-blue-100 text-blue-800">일반</span>'
                }
            </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            ${stat.gender ? `<div>${stat.gender}</div>` : ''}
            ${stat.age ? `<div class="text-xs text-gray-500">${stat.age}세</div>` : ''}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            ${stat.height ? `<div class="text-xs">키: ${stat.height}cm</div>` : ''}
            ${stat.weight ? `<div class="text-xs">몸무게: ${stat.weight}kg</div>` : ''}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <div class="flex items-center">
                <span class="font-semibold ${stat.compliance_rate_7days >= 80 ? 'text-green-600' : stat.compliance_rate_7days >= 50 ? 'text-yellow-600' : 'text-red-600'}">
                    ${stat.compliance_rate_7days}%
                </span>
            </div>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <span class="font-semibold ${stat.compliance_rate_today >= 80 ? 'text-green-600' : stat.compliance_rate_today >= 50 ? 'text-yellow-600' : 'text-red-600'}">
                ${stat.compliance_rate_today}%
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
            <span class="font-semibold ${stat.compliance_rate_yesterday >= 80 ? 'text-green-600' : stat.compliance_rate_yesterday >= 50 ? 'text-yellow-600' : 'text-red-600'}">
                ${stat.compliance_rate_yesterday}%
            </span>
        </td>
        <td class="px-6 py-4 whitespace-nowrap">
            ${createWaffleChart(stat.daily_compliance)}
        </td>
        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
            ${stat.last_sync ? formatDate(stat.last_sync) : '<span class="text-gray-400">없음</span>'}
        </td>
    `;

    return tr;
}

// 날짜 포맷 (YYYY-MM-DD)
function formatDate(dateString) {
    if (!dateString) return '';
    const date = new Date(dateString);
    return date.toLocaleDateString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
    }).replace(/\. /g, '-').replace('.', '');
}

// 날짜/시간 포맷 (MM/DD HH:mm)
function formatDateTime(dateTimeString) {
    if (!dateTimeString) return '';
    const date = new Date(dateTimeString);
    return date.toLocaleString('ko-KR', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        hour12: false
    }).replace(/\. /g, '/').replace('.', '').replace(', ', ' ');
}

// 로딩 상태 표시
function showLoading() {
    const tbody = document.getElementById('userTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-12 text-center">
                    <svg class="animate-spin h-8 w-8 mx-auto text-green-600" viewBox="0 0 24 24">
                        <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle>
                        <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                    </svg>
                    <p class="mt-3 text-gray-600">데이터를 불러오는 중...</p>
                </td>
            </tr>
        `;
    }

    // 통계 카드와 테이블은 항상 표시
    document.getElementById('statsCards')?.classList.remove('hidden');
    document.getElementById('userTable')?.classList.remove('hidden');
    document.getElementById('loadingState')?.classList.add('hidden');
    document.getElementById('errorState')?.classList.add('hidden');
}

// 콘텐츠 표시
function showContent() {
    document.getElementById('loadingState')?.classList.add('hidden');
    document.getElementById('errorState')?.classList.add('hidden');
    document.getElementById('statsCards')?.classList.remove('hidden');
    document.getElementById('userTable')?.classList.remove('hidden');
}

// 에러 상태 표시
function showError(message) {
    const tbody = document.getElementById('userTableBody');
    if (tbody) {
        tbody.innerHTML = `
            <tr>
                <td colspan="8" class="px-6 py-8 text-center">
                    <div class="flex flex-col items-center text-red-600">
                        <svg class="w-12 h-12 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
                        </svg>
                        <p class="text-red-800 font-medium">데이터를 불러올 수 없습니다</p>
                        <p class="text-red-700 text-sm mt-1">${message}</p>
                    </div>
                </td>
            </tr>
        `;
    }

    // 통계 카드와 테이블은 항상 표시
    document.getElementById('statsCards')?.classList.remove('hidden');
    document.getElementById('userTable')?.classList.remove('hidden');
}

// 오늘 데이터 전체 동기화
function syncTodayData() {
    if (!confirm('모든 사용자의 오늘 데이터 전체를 Fitbit에서 가져오시겠습니까?\n(시간이 걸릴 수 있습니다)')) {
        return;
    }

    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2 inline" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> 동기화 중...';

    console.log('[오늘 데이터 동기화] 시작...');

    fetch('/manager/sync-today/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => {
        console.log('[오늘 데이터 동기화] Response status:', response.status);
        console.log('[오늘 데이터 동기화] Response headers:', response.headers);

        // 응답 텍스트 먼저 확인
        return response.text().then(text => {
            console.log('[오늘 데이터 동기화] Response text:', text);
            try {
                return JSON.parse(text);
            } catch (e) {
                console.error('[오늘 데이터 동기화] JSON 파싱 실패:', e);
                console.error('[오늘 데이터 동기화] 원본 응답:', text);
                throw new Error('서버에서 잘못된 응답을 받았습니다. 콘솔을 확인하세요.');
            }
        });
    })
    .then(data => {
        console.log('[오늘 데이터 동기화] 파싱된 데이터:', data);
        button.disabled = false;
        button.innerHTML = originalHTML;

        if (data.success) {
            let message = `오늘(${data.date}) 데이터 동기화 완료!\n성공: ${data.success_count}명\n실패: ${data.fail_count}명`;

            // 실패한 항목이 있으면 표시
            if (data.failed_items && data.failed_items.length > 0) {
                message += `\n\n불러오지 못한 항목:\n- ${data.failed_items.join('\n- ')}`;
            }

            alert(message);
            refreshDashboard();
        } else {
            console.error('[오늘 데이터 동기화] 실패:', data.error);
            alert('동기화 실패: ' + data.error);
        }
    })
    .catch(error => {
        console.error('[오늘 데이터 동기화] 에러 발생:', error);
        button.disabled = false;
        button.innerHTML = originalHTML;
        alert('오류가 발생했습니다. 자세한 내용은 콘솔을 확인하세요.');
    });
}

// 프로필 전체 동기화
function syncAllProfiles() {
    if (!confirm('모든 사용자의 프로필 정보를 Fitbit에서 가져오시겠습니까?')) {
        return;
    }

    const button = event.target.closest('button');
    const originalHTML = button.innerHTML;
    button.disabled = true;
    button.innerHTML = '<svg class="animate-spin h-5 w-5 mr-2 inline" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg> 동기화 중...';

    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
                      document.querySelector('input[name="csrfmiddlewaretoken"]')?.value;

    fetch('/manager/sync-profiles/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json'
        }
    })
    .then(response => response.json())
    .then(data => {
        button.disabled = false;
        button.innerHTML = originalHTML;

        if (data.success) {
            alert(`동기화 완료!\n성공: ${data.success_count}명\n실패: ${data.fail_count}명`);
            refreshDashboard();
        } else {
            alert('동기화 실패: ' + data.error);
        }
    })
    .catch(error => {
        button.disabled = false;
        button.innerHTML = originalHTML;
        alert('오류가 발생했습니다: ' + error);
    });
}

// CSRF 토큰 가져오기
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 버킷 크기 변경 (1분 고정으로 사용 안 함)
function changeBucketSize(bucketSize) {
    // 버킷 크기는 1분 고정
    console.log('버킷 크기는 1분으로 고정되어 있습니다.');
}

// 시간 설정 변경 (시작/종료 시간)
function updateDashboardSettings() {
    // 데이터 다시 로드
    loadDashboardData();
}
