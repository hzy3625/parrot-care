// ParrotCare AI - Frontend Application (V0.4 Sprint 1)
// 鍘熺敓 JavaScript 瀹炵幇锛屾棤妗嗘灦渚濊禆

// ==================== 鍏ㄥ眬閰嶇疆 ====================
const API_BASE_URL = 'http://localhost:8000/api';
let currentToken = localStorage.getItem('access_token') || null;
let currentParrotId = null;

// ==================== 宸ュ叿鍑芥暟 ====================
// API 璇锋眰灏佽
async function apiRequest(endpoint, method = 'GET', data = null, requiresAuth = true) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = {
        'Content-Type': 'application/json'
    };
    
    if (requiresAuth && currentToken) {
        headers['Authorization'] = `Bearer ${currentToken}`;
    }
    
    const options = {
        method,
        headers
    };
    
    if (data && method !== 'GET') {
        options.body = JSON.stringify(data);
    }
    
    try {
        const response = await fetch(url, options);
        
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || '璇锋眰澶辫触');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API璇锋眰澶辫触:', error);
        throw error;
    }
}

// 瀵嗙爜寮哄害鏍￠獙锛堝墠绔級
function validatePasswordStrength(password) {
    if (password.length < 8) {
        return { valid: false, message: '瀵嗙爜闀垮害鑷冲皯8浣? };
    }
    
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    
    if (!hasLetter || !hasNumber) {
        return { valid: false, message: '瀵嗙爜蹇呴』鍖呭惈瀛楁瘝鍜屾暟瀛? };
    }
    
    return { valid: true, message: '瀵嗙爜寮哄害鍚堟牸' };
}

// 鏄剧ず鎻愮ず淇℃伅
function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    document.body.appendChild(alertDiv);
    
    setTimeout(() => alertDiv.remove(), 5000);
}

// ==================== 1. 鐢ㄦ埛璁よ瘉 ====================
// 鐧诲綍
async function login(phone, password) {
    try {
        const response = await apiRequest('/users/login', 'POST', 
            { phone, password }, false);
        
        currentToken = response.access_token;
        localStorage.setItem('access_token', currentToken);
        
        showAlert('鐧诲綍鎴愬姛锛?, 'success');
        showHomePage();
        
        // 鍔犺浇棣栭〉鏁版嵁
        await loadHomePageData();
    } catch (error) {
        showAlert(`鐧诲綍澶辫触: ${error.message}`, 'danger');
    }
}

// 娉ㄥ唽
async function register(phone, password, nickname, email) {
    try {
        const response = await apiRequest('/users/register', 'POST', 
            { phone, password, nickname, email }, false);
        
        currentToken = response.access_token;
        localStorage.setItem('access_token', currentToken);
        
        showAlert('娉ㄥ唽鎴愬姛锛?, 'success');
        showHomePage();
        await loadHomePageData();
    } catch (error) {
        showAlert(`娉ㄥ唽澶辫触: ${error.message}`, 'danger');
    }
}

// 閫€鍑虹櫥褰?
function logout() {
    currentToken = null;
    localStorage.removeItem('access_token');
    currentParrotId = null;
    
    showAlert('宸查€€鍑虹櫥褰?, 'info');
    showLoginPage();
}

// ==================== 2. 瀵嗙爜閲嶇疆锛圧EQ-PARROT-011锛?====================
// 鍙戣捣閲嶇疆
async function requestPasswordReset(email) {
    try {
        await apiRequest('/users/reset-password', 'POST', { email }, false);
        
        showAlert('閲嶇疆閭欢宸插彂閫侊紝璇锋鏌ラ偖绠?, 'success');
        showResetSuccess();
    } catch (error) {
        showAlert(`璇锋眰澶辫触: ${error.message}`, 'danger');
    }
}

// 纭閲嶇疆锛堜粠URL鑾峰彇token锛?
async function confirmPasswordReset(token, newPassword) {
    // 鍓嶇瀵嗙爜寮哄害鏍￠獙
    const validation = validatePasswordStrength(newPassword);
    if (!validation.valid) {
        showAlert(validation.message, 'warning');
        return false;
    }
    
    try {
        await apiRequest(`/users/reset-password/${token}`, 'POST', 
            { token, new_password: newPassword }, false);
        
        showAlert('瀵嗙爜宸查噸缃紝璇蜂娇鐢ㄦ柊瀵嗙爜鐧诲綍', 'success');
        showLoginPage();
        return true;
    } catch (error) {
        if (error.message.includes('棰戠箒')) {
            showAlert('鎿嶄綔杩囦簬棰戠箒锛岃绋嶅悗鍐嶈瘯', 'warning');
        } else {
            showAlert(`閲嶇疆澶辫触: ${error.message}`, 'danger');
        }
        return false;
    }
}

// ==================== 3. 绔欏唴娑堟伅涓績锛圧EQ-PARROT-005锛?====================
// 鍔犺浇娑堟伅鍒楄〃锛堝垎椤点€佺瓫閫夛級
async function loadNotifications(page = 1, pageSize = 20, unreadOnly = false, notificationType = null) {
    try {
        let endpoint = `/notifications?page=${page}&page_size=${pageSize}`;
        if (unreadOnly) endpoint += '&unread_only=true';
        if (notificationType) endpoint += `&notification_type=${notificationType}`;
        
        const response = await apiRequest(endpoint, 'GET');
        
        renderNotificationsList(response.notifications);
        
        // 鏇存柊鎬绘暟鏄剧ず
        document.getElementById('notification-total').textContent = response.total;
        document.getElementById('notification-unread').textContent = response.unread_count;
        
        return response;
    } catch (error) {
        showAlert(`鍔犺浇娑堟伅澶辫触: ${error.message}`, 'danger');
    }
}

// 鏈璁℃暟锛堟洿鏂板鑸爮绾㈢偣锛?
async function updateNotificationBadge() {
    try {
        const response = await apiRequest('/notifications/unread-count', 'GET');
        
        const badge = document.getElementById('notification-badge');
        if (response.unread_count > 0) {
            badge.style.display = 'flex';
            badge.textContent = response.unread_count > 99 ? '99+' : response.unread_count;
        } else {
            badge.style.display = 'none';
        }
    } catch (error) {
        console.error('鏇存柊绾㈢偣澶辫触:', error);
    }
}

// 鏍囪鍗曟潯宸茶
async function markNotificationRead(notificationId) {
    try {
        await apiRequest(`/notifications/${notificationId}/read`, 'PATCH');
        
        // 鍒锋柊鍒楄〃鍜岀孩鐐?
        await updateNotificationBadge();
        await loadNotifications();
    } catch (error) {
        showAlert(`鏍囪澶辫触: ${error.message}`, 'danger');
    }
}

// 鍏ㄩ儴鏍囪宸茶
async function markAllNotificationsRead() {
    try {
        // 鑾峰彇鎵€鏈夋湭璇绘秷鎭疘D
        const response = await apiRequest('/notifications?unread_only=true&page_size=100', 'GET');
        
        if (response.notifications.length === 0) {
            showAlert('娌℃湁鏈娑堟伅', 'info');
            return;
        }
        
        const notificationIds = response.notifications.map(n => n.notification_id);
        await apiRequest('/notifications/mark-read', 'PATCH', 
            { notification_ids: notificationIds });
        
        showAlert('鍏ㄩ儴鏍囪宸茶', 'success');
        await updateNotificationBadge();
        await loadNotifications();
    } catch (error) {
        showAlert(`鎿嶄綔澶辫触: ${error.message}`, 'danger');
    }
}

// 鍒犻櫎娑堟伅
async function deleteNotification(notificationId) {
    try {
        await apiRequest(`/notifications/${notificationId}`, 'DELETE');
        
        showAlert('娑堟伅宸插垹闄?, 'success');
        await updateNotificationBadge();
        await loadNotifications();
    } catch (error) {
        showAlert(`鍒犻櫎澶辫触: ${error.message}`, 'danger');
    }
}

// 鎸夌被鍨嬬瓫閫夋秷鎭?
async function filterNotificationsByType(type) {
    await loadNotifications(1, 20, false, type);
}

// 娓叉煋娑堟伅鍒楄〃
function renderNotificationsList(notifications) {
    const listDiv = document.getElementById('notification-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = '';
    
    if (notifications.length === 0) {
        listDiv.innerHTML = '<div class="text-center text-muted">鏆傛棤娑堟伅</div>';
        return;
    }
    
    notifications.forEach(n => {
        const item = document.createElement('div');
        item.className = n.is_read ? 'notification-read' : 'notification-unread';
        item.style.className = 'p-3 mb-2 rounded border';
        
        const typeIcon = {
            'system': '馃敂',
            'health_alert': '鈿狅笍',
            'parrot_reminder': '馃惁',
            'feature_update': '鉁?
        }[n.notification_type] || '馃搶';
        
        const readBtn = !n.is_read ? 
            '<button class="btn btn-sm btn-outline-primary" onclick="markNotificationRead('' + n.notification_id + '')">鏍囪宸茶</button>' : '';
        
        item.innerHTML = `
            <div class="d-flex justify-content-between">
                <div>
                    <strong>${typeIcon} ${n.title}</strong>
                    <p class="mb-1">${n.content}</p>
                    <small class="text-muted">${new Date(n.created_at).toLocaleString()}</small>
                </div>
                <div>
                    ${readBtn}
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteNotification('${n.notification_id}')">鍒犻櫎</button>
                </div>
            </div>
        `;
        
        listDiv.appendChild(item);
    });
}

// ==================== 4. 鍋ュ悍妗ｆ鎬昏锛圧EQ-PARROT-009锛?====================
// 鍔犺浇鎵€鏈夐功楣夊仴搴锋暟鎹?
async function loadAllHealthOverview() {
    try {
        const overviews = await apiRequest('/parrots/health-overview', 'GET');
        
        renderHealthCards(overviews);
        return overviews;
    } catch (error) {
        showAlert(`鍔犺浇鍋ュ悍妗ｆ澶辫触: ${error.message}`, 'danger');
    }
}

// 娓叉煋鍋ュ悍鍗＄墖锛堣瘎鍒嗛鑹叉爣璇嗭級
function renderHealthCards(overviews) {
    const container = document.getElementById('health-overview-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (overviews.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">鏆傛棤楣﹂箟</div>';
        return;
    }
    
    overviews.forEach(overview => {
        const card = document.createElement('div');
        card.className = 'col-md-4 mb-3';
        
        // 璇勫垎棰滆壊锛?=80 缁胯壊銆?0-79 榛勮壊銆?60 鐓冭壊
        let scoreColor = '';
        let scoreClass = '';
        if (overview.current_health_score >= 80) {
            scoreColor = '#28a745';
            scoreClass = 'status-healthy';
        } else if (overview.current_health_score >= 60) {
            scoreColor = '#ffc107';
            scoreClass = 'status-warning';
        } else {
            scoreColor = '#dc3545';
            scoreClass = 'status-danger';
        }
        
        // 瓒嬪娍鍥炬爣
        let trendIcon = '';
        let trendClass = '';
        if (overview.health_trend === 'improving') {
            trendIcon = '馃搱';
            trendClass = 'health-trend-up';
        } else if (overview.health_trend === 'declining') {
            trendIcon = '馃搲';
            trendClass = 'health-trend-down';
        } else {
            trendIcon = '鉃★笍';
            trendClass = 'health-trend-stable';
        }
        
        card.innerHTML = `
            <div class="card card-hover shadow h-100" onclick="viewParrotDetail('${overview.parrot_id}')">
                <div class="card-body">
                    <h5 class="card-title">馃 ${overview.parrot_name}</h5>
                    <p class="text-muted">${overview.species}</p>
                    <div class="display-4 ${scoreClass}" style="color: ${scoreColor}">
                        ${overview.current_health_score}
                    </div>
                    <small class="text-muted">鍋ュ悍璇勫垎</small>
                    <div class="mt-2">
                        <span class="${trendClass}">${trendIcon} ${overview.health_status}</span>
                    </div>
                    <div class="row mt-3 text-center">
                        <div class="col-6">
                            <strong>${overview.avg_health_score_7days}</strong>
                            <small class="text-muted">7鏃ュ钩鍧?/small>
                        </div>
                        <div class="col-6">
                            <strong>${overview.total_abnormal_events_7days}</strong>
                            <small class="text-muted">7鏃ュ紓甯?/small>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

// 鐐瑰嚮璺宠浆鍒板崟涓功楣夎鎯呴〉
function viewParrotDetail(parrotId) {
    currentParrotId = parrotId;
    // TODO: 瀹炵幇璇︽儏椤佃烦杞€昏緫
    showAlert('姝ｅ湪鍔犺浇楣﹂箟 ' + parrotId + ' 鐨勮鎯?..', 'info');
}

// ==================== 5. 涓汉淇℃伅绠＄悊锛圧EQ-PARROT-012锛?====================
// 鍔犺浇涓汉淇℃伅
async function loadUserProfile() {
    try {
        const profile = await apiRequest('/users/profile', 'GET');
        
        document.getElementById('profile-nickname').value = profile.nickname || '';
        document.getElementById('profile-email').value = profile.email || '';
        document.getElementById('profile-phone').value = profile.phone || '';
        
        return profile;
    } catch (error) {
        showAlert(`鍔犺浇涓汉淇℃伅澶辫触: ${error.message}`, 'danger');
    }
}

// 鏇存柊涓汉淇℃伅
async function updateProfile(nickname, email, phone) {
    try {
        const profile = await apiRequest('/users/profile', 'PUT', 
            { nickname, email, phone });
        
        showAlert('涓汉淇℃伅宸叉洿鏂?, 'success');
        return profile;
    } catch (error) {
        showAlert(`鏇存柊澶辫触: ${error.message}`, 'danger');
    }
}

// 淇敼瀵嗙爜
async function changePassword(oldPassword, newPassword) {
    // 鍓嶇瀵嗙爜寮哄害鏍￠獙
    const validation = validatePasswordStrength(newPassword);
    if (!validation.valid) {
        showAlert(validation.message, 'warning');
        return false;
    }
    
    try {
        await apiRequest('/users/me/change-password', 'POST', 
            { old_password: oldPassword, new_password: newPassword });
        
        showAlert('瀵嗙爜宸蹭慨鏀癸紝璇烽噸鏂扮櫥褰?, 'success');
        logout();
        return true;
    } catch (error) {
        showAlert(`淇敼澶辫触: ${error.message}`, 'danger');
        return false;
    }
}

// 閫氱煡鍋忓ソ璁剧疆锛堝瓨鍌ㄥ埌localStorage锛?
function saveNotificationPreferences(emailNotify, browserNotify) {
    localStorage.setItem('notification_email', emailNotify);
    localStorage.setItem('notification_browser', browserNotify);
    showAlert('閫氱煡鍋忓ソ宸蹭繚瀛?, 'success');
}

// ==================== 椤甸潰鍒囨崲閫昏緫 ====================
function showLoginPage() {
    hideAllPages();
    document.getElementById('login-page').style.display = 'flex';
}

function showRegisterPage() {
    hideAllPages();
    document.getElementById('register-page').style.display = 'flex';
}

function showResetPasswordPage() {
    hideAllPages();
    document.getElementById('reset-password-page').style.display = 'flex';
    document.getElementById('reset-request-form').style.display = 'block';
    document.getElementById('reset-success-msg').style.display = 'none';
}

function showResetSuccess() {
    document.getElementById('reset-request-form').style.display = 'none';
    document.getElementById('reset-success-msg').style.display = 'block';
}

function showHomePage() {
    hideAllPages();
    document.getElementById('home-page').style.display = 'block';
}

function hideAllPages() {
    document.getElementById('login-page').style.display = 'none';
    document.getElementById('register-page').style.display = 'none';
    document.getElementById('reset-password-page').style.display = 'none';
    document.getElementById('home-page').style.display = 'none';
}

// 鍔犺浇棣栭〉鏁版嵁
async function loadHomePageData() {
    // 鍔犺浇楣﹂箟鍒楄〃
    await loadParrotsList();
    
    // 鏇存柊娑堟伅绾㈢偣
    await updateNotificationBadge();
    
    // 鍔犺浇鍋ュ悍鎬昏
    await loadAllHealthOverview();
}

// 鍔犺浇楣﹂箟鍒楄〃
async function loadParrotsList() {
    try {
        const parrots = await apiRequest('/parrots', 'GET');
        
        const listDiv = document.getElementById('parrots-list');
        if (!listDiv) return;
        
        listDiv.innerHTML = '';
        
        if (parrots.length === 0) {
            listDiv.innerHTML = '<div class="text-muted">鏆傛棤楣﹂箟锛岃娣诲姞</div>';
            return;
        }
        
        parrots.forEach(p => {
            const item = document.createElement('div');
            item.className = 'mb-2 p-2 border rounded';
            item.innerHTML = `
                <strong>馃 ${p.name}</strong>
                <span class="text-muted ml-2">${p.species}</span>
                <button class="btn btn-sm btn-outline-secondary float-right" 
                    onclick="selectParrot('${p.parrot_id}', '${p.name}')">
                    閫夋嫨
                </button>
            `;
            listDiv.appendChild(item);
        });
    } catch (error) {
        console.error('鍔犺浇楣﹂箟鍒楄〃澶辫触:', error);
    }
}

// 閫夋嫨楣﹂箟
function selectParrot(parrotId, parrotName) {
    currentParrotId = parrotId;
    document.getElementById('parrot-name').textContent = parrotName;
    
    // 鍔犺浇浠婃棩鎽樿
    loadTodaySummary(parrotId);
}

// 鍔犺浇浠婃棩鎽樿
async function loadTodaySummary(parrotId) {
    try {
        const summary = await apiRequest(`/parrots/${parrotId}/today-summary`, 'GET');
        
        document.getElementById('health-score').textContent = summary.health_score;
        document.getElementById('chirp-count').textContent = summary.chirp_count;
        document.getElementById('scream-count').textContent = summary.scream_count;
        document.getElementById('status-summary').textContent = summary.summary;
        
        // 鏍规嵁璇勫垎璁剧疆棰滆壊
        const scoreDiv = document.getElementById('health-score');
        if (summary.health_score >= 80) {
            scoreDiv.className = 'display-4 status-healthy';
        } else if (summary.health_score >= 60) {
            scoreDiv.className = 'display-4 status-warning';
        } else {
            scoreDiv.className = 'display-4 status-danger';
        }
    } catch (error) {
        console.error('鍔犺浇浠婃棩鎽樿澶辫触:', error);
    }
}

// ==================== 浜嬩欢缁戝畾 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 妫€鏌ユ槸鍚﹀凡鐧诲綍
    if (currentToken) {
        showHomePage();
        loadHomePageData();
    } else {
        showLoginPage();
    }
    
    // 鐧诲綍琛ㄥ崟
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            await login(phone, password);
        });
    }
    
    // 娉ㄥ唽琛ㄥ崟
    const registerForm = document.getElementById('register-form');
    if (registerForm) {
        registerForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const phone = document.getElementById('reg-phone').value;
            const password = document.getElementById('reg-password').value;
            const nickname = document.getElementById('reg-nickname').value;
            const email = document.getElementById('reg-email').value;
            await register(phone, password, nickname, email);
        });
    }
    
    // 娉ㄥ唽閾炬帴
    const registerLink = document.getElementById('register-link');
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            showRegisterPage();
        });
    }
    
    // 杩斿洖鐧诲綍閾炬帴
    const backLoginLink = document.getElementById('back-login-link');
    if (backLoginLink) {
        backLoginLink.addEventListener('click', function(e) {
            e.preventDefault();
            showLoginPage();
        });
    }
    
    // 蹇樿瀵嗙爜閾炬帴
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            showResetPasswordPage();
        });
    }
    
    // 鍙戣捣閲嶇疆鎸夐挳
    const requestResetBtn = document.getElementById('request-reset-btn');
    if (requestResetBtn) {
        requestResetBtn.addEventListener('click', async function() {
            const email = document.getElementById('reset-email').value;
            await requestPasswordReset(email);
        });
    }
    
    // 杩斿洖鐧诲綍锛堜粠閲嶇疆椤碉級
    const backLoginFromReset = document.getElementById('back-login-from-reset');
    if (backLoginFromReset) {
        backLoginFromReset.addEventListener('click', function(e) {
            e.preventDefault();
            showLoginPage();
        });
    }
    
    // 杩斿洖鐧诲綍锛堜粠鎴愬姛椤碉級
    const backLoginFromSuccess = document.getElementById('back-login-from-success');
    if (backLoginFromSuccess) {
        backLoginFromSuccess.addEventListener('click', function(e) {
            e.preventDefault();
            showLoginPage();
        });
    }
    
    // 閫€鍑虹櫥褰曟寜閽?
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // 娑堟伅涓績鎸夐挳
    const notificationBtn = document.getElementById('notification-btn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', async function() {
            const modal = new bootstrap.Modal(document.getElementById('notification-modal'));
            modal.show();
            await loadNotifications();
        });
    }
    
    // 涓汉淇℃伅鎸夐挳
    const profileBtn = document.getElementById('profile-btn');
    if (profileBtn) {
        profileBtn.addEventListener('click', async function() {
            const modal = new bootstrap.Modal(document.getElementById('profile-modal'));
            modal.show();
            await loadUserProfile();
        });
    }
    
    // 鍋ュ悍鎬昏鎸夐挳
    const healthOverviewBtn = document.getElementById('health-overview-btn');
    if (healthOverviewBtn) {
        healthOverviewBtn.addEventListener('click', async function() {
            document.getElementById('health-overview-card').style.display = 'block';
            await loadAllHealthOverview();
        });
    }
    
    // 妫€鏌RL涓槸鍚︽湁瀵嗙爜閲嶇疆token
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('token');
    if (resetToken) {
        showResetPasswordPage();
        // 鏄剧ず纭閲嶇疆琛ㄥ崟
        // TODO: 瀹炵幇纭閲嶇疆UI
    }
});

// ==================== 瀵煎嚭鍏ㄥ眬鍑芥暟锛堜緵HTML璋冪敤锛?====================
window.markNotificationRead = markNotificationRead;
window.deleteNotification = deleteNotification;
window.viewParrotDetail = viewParrotDetail;
window.selectParrot = selectParrot;
window.filterNotificationsByType = filterNotificationsByType;
window.markAllNotificationsRead = markAllNotificationsRead;
