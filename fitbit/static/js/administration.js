/**
 * 대상자 관리 페이지 JavaScript
 * Ajax 비동기 방식으로 대상자 목록 조회 및 수정
 */

(function() {
    'use strict';

    let subjectsData = [];

    // 페이지 로드 시 실행
    document.addEventListener('DOMContentLoaded', function() {
        loadSubjects();
    });

    /**
     * 대상자 목록 불러오기
     */
    function loadSubjects() {
        showLoading();
        hideError();

        fetch('/manager/administration/subjects/')
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    subjectsData = data.subjects;
                    renderSubjects();
                } else {
                    showError('대상자 정보를 불러오는데 실패했습니다.');
                }
            })
            .catch(error => {
                console.error('Error loading subjects:', error);
                showError('대상자 정보를 불러오는 중 오류가 발생했습니다.');
            })
            .finally(() => {
                hideLoading();
            });
    }

    /**
     * 대상자 목록 렌더링
     */
    function renderSubjects() {
        const tbody = document.getElementById('subjectsTableBody');
        const noSubjects = document.getElementById('noSubjects');
        const table = document.getElementById('subjectsTable');

        if (subjectsData.length === 0) {
            table.classList.add('hidden');
            noSubjects.classList.remove('hidden');
            return;
        }

        table.classList.remove('hidden');
        noSubjects.classList.add('hidden');
        tbody.innerHTML = '';

        subjectsData.forEach(subject => {
            const row = createSubjectRow(subject);
            tbody.appendChild(row);
        });
    }

    /**
     * 대상자 행 생성
     */
    function createSubjectRow(subject) {
        const tr = document.createElement('tr');
        tr.className = 'hover:bg-gray-50 transition-colors';
        tr.dataset.subjectId = subject.username;

        tr.innerHTML = `
            <td class="px-4 py-3 whitespace-nowrap">
                <div class="text-sm font-medium text-gray-900 view-mode">${escapeHtml(subject.full_name)}</div>
                <div class="edit-mode hidden">
                    <input type="text" name="full_name" value="${escapeHtml(subject.full_name)}" class="text-sm">
                </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
                <div class="text-sm text-gray-900 view-mode">${escapeHtml(subject.gender)}</div>
                <div class="edit-mode hidden">
                    <select name="gender" class="text-sm">
                        <option value="MALE" ${subject.gender === 'MALE' ? 'selected' : ''}>남성</option>
                        <option value="FEMALE" ${subject.gender === 'FEMALE' ? 'selected' : ''}>여성</option>
                        <option value="NA" ${subject.gender === 'NA' || subject.gender === 'N/A' ? 'selected' : ''}>N/A</option>
                    </select>
                </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
                <div class="text-sm text-gray-900">${subject.age || 'N/A'}</div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
                <div class="text-sm text-gray-900 view-mode">${subject.height || 'N/A'}</div>
                <div class="edit-mode hidden">
                    <input type="number" name="height" value="${subject.height || ''}" min="0" max="300" step="0.1" class="text-sm">
                </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap">
                <div class="text-sm text-gray-900 view-mode">${subject.weight || 'N/A'}</div>
                <div class="edit-mode hidden">
                    <input type="number" name="weight" value="${subject.weight || ''}" min="0" max="500" step="0.1" class="text-sm">
                </div>
            </td>
            <td class="px-4 py-3 whitespace-nowrap text-center">
                <div class="view-mode">
                    <button onclick="editSubject('${subject.username}')" class="text-blue-600 hover:text-blue-800 font-medium text-sm">
                        수정
                    </button>
                </div>
                <div class="edit-mode hidden flex justify-center gap-2">
                    <button onclick="saveSubject('${subject.username}')" class="text-green-600 hover:text-green-800 font-medium text-sm">
                        저장
                    </button>
                    <button onclick="cancelEdit('${subject.username}')" class="text-gray-600 hover:text-gray-800 font-medium text-sm">
                        취소
                    </button>
                </div>
            </td>
        `;

        return tr;
    }

    /**
     * 대상자 수정 모드로 전환
     */
    window.editSubject = function(subjectId) {
        const row = document.querySelector(`tr[data-subject-id="${subjectId}"]`);
        if (!row) return;

        // 다른 행이 수정 중이면 취소
        const editingRow = document.querySelector('tr.editing');
        if (editingRow) {
            const editingId = editingRow.dataset.subjectId;
            cancelEdit(editingId);
        }

        row.classList.add('editing');
        row.querySelectorAll('.view-mode').forEach(el => el.classList.add('hidden'));
        row.querySelectorAll('.edit-mode').forEach(el => el.classList.remove('hidden'));
    };

    /**
     * 대상자 정보 저장
     */
    window.saveSubject = function(subjectId) {
        const row = document.querySelector(`tr[data-subject-id="${subjectId}"]`);
        if (!row) return;

        // 수정된 데이터 수집 (나이는 생년월일에서 자동 계산되므로 제외)
        const updatedData = {
            username: subjectId,
            full_name: row.querySelector('input[name="full_name"]').value,
            gender: row.querySelector('select[name="gender"]').value,
            height: row.querySelector('input[name="height"]').value ? parseFloat(row.querySelector('input[name="height"]').value) : null,
            weight: row.querySelector('input[name="weight"]').value ? parseFloat(row.querySelector('input[name="weight"]').value) : null,
        };

        // 로딩 표시
        const saveBtn = row.querySelector('.edit-mode button');
        const originalText = saveBtn.textContent;
        saveBtn.textContent = '저장 중...';
        saveBtn.disabled = true;

        // AJAX 요청
        fetch('/manager/administration/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(updatedData)
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // 로컬 데이터 업데이트
                const index = subjectsData.findIndex(s => s.username === subjectId);
                if (index !== -1) {
                    subjectsData[index] = data.subject;
                }

                // 화면 다시 렌더링
                renderSubjects();

                // 성공 메시지 (선택사항)
                showSuccess('대상자 정보가 수정되었습니다.');
            } else {
                showError(data.error || '대상자 정보 수정에 실패했습니다.');
                saveBtn.textContent = originalText;
                saveBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error saving subject:', error);
            showError('대상자 정보 저장 중 오류가 발생했습니다.');
            saveBtn.textContent = originalText;
            saveBtn.disabled = false;
        });
    };

    /**
     * 수정 취소
     */
    window.cancelEdit = function(subjectId) {
        const row = document.querySelector(`tr[data-subject-id="${subjectId}"]`);
        if (!row) return;

        row.classList.remove('editing');
        row.querySelectorAll('.view-mode').forEach(el => el.classList.remove('hidden'));
        row.querySelectorAll('.edit-mode').forEach(el => el.classList.add('hidden'));
    };

    /**
     * 로딩 표시
     */
    function showLoading() {
        document.getElementById('loadingIndicator').classList.remove('hidden');
    }

    function hideLoading() {
        document.getElementById('loadingIndicator').classList.add('hidden');
    }

    /**
     * 에러 메시지 표시
     */
    function showError(message) {
        const errorDiv = document.getElementById('errorMessage');
        const errorText = document.getElementById('errorText');
        errorText.textContent = message;
        errorDiv.classList.remove('hidden');

        // 5초 후 자동으로 숨김
        setTimeout(() => {
            errorDiv.classList.add('hidden');
        }, 5000);
    }

    function hideError() {
        document.getElementById('errorMessage').classList.add('hidden');
    }

    /**
     * 성공 메시지 표시
     */
    function showSuccess(message) {
        // 간단한 성공 알림 (선택사항)
        const successDiv = document.createElement('div');
        successDiv.className = 'fixed top-4 right-4 bg-green-50 border border-green-200 rounded-lg p-4 shadow-lg z-50';
        successDiv.innerHTML = `
            <div class="flex">
                <div class="flex-shrink-0">
                    <svg class="h-5 w-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                        <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clip-rule="evenodd"/>
                    </svg>
                </div>
                <div class="ml-3">
                    <p class="text-sm text-green-800">${escapeHtml(message)}</p>
                </div>
            </div>
        `;
        document.body.appendChild(successDiv);

        setTimeout(() => {
            successDiv.remove();
        }, 3000);
    }

    /**
     * HTML 이스케이프
     */
    function escapeHtml(unsafe) {
        if (unsafe === null || unsafe === undefined) return '';
        return String(unsafe)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    /**
     * 신규 사용자 동기화 (전역 함수) - Polar는 수동 등록 방식
     */
    window.syncNewUsers = function() {
        alert('Polar 사용자는 수동 등록 방식입니다.\n\nPolar 기기 연동 시 자동으로 등록됩니다.');
    };

})();
