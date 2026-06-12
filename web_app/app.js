// ParrotCare AI - Frontend Application (V0.4 Sprint 1)
// 原生 JavaScript 实现，无框架依赖

// ==================== 全局配置 ====================
const API_BASE_URL = 'http://localhost:8000/api';
let currentToken = localStorage.getItem('access_token') || null;
let currentParrotId = null;

// ==================== 工具函数 ====================
// API 请求封装
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
            throw new Error(errorData.detail || '请求失败');
        }
        
        return await response.json();
    } catch (error) {
        console.error('API请求失败:', error);
        throw error;
    }
}

// 密码强度校验（前端）
function validatePasswordStrength(password) {
    if (password.length < 8) {
        return { valid: false, message: '密码长度至少8位' };
    }
    
    const hasLetter = /[a-zA-Z]/.test(password);
    const hasNumber = /[0-9]/.test(password);
    
    if (!hasLetter || !hasNumber) {
        return { valid: false, message: '密码必须包含字母和数字' };
    }
    
    return { valid: true, message: '密码强度合格' };
}

// 显示提示信息
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

// ==================== 1. 用户认证 ====================
// 登录
async function login(phone, password) {
    try {
        const response = await apiRequest('/users/login', 'POST', 
            { phone, password }, false);
        
        currentToken = response.access_token;
        localStorage.setItem('access_token', currentToken);
        
        showAlert('登录成功！', 'success');
        showHomePage();
        
        // 加载首页数据
        await loadHomePageData();
    } catch (error) {
        showAlert(`登录失败: ${error.message}`, 'danger');
    }
}

// 注册
async function register(phone, password, nickname, email) {
    try {
        const response = await apiRequest('/users/register', 'POST', 
            { phone, password, nickname, email }, false);
        
        currentToken = response.access_token;
        localStorage.setItem('access_token', currentToken);
        
        showAlert('注册成功！', 'success');
        showHomePage();
        await loadHomePageData();
    } catch (error) {
        showAlert(`注册失败: ${error.message}`, 'danger');
    }
}

// 退出登录
function logout() {
    currentToken = null;
    localStorage.removeItem('access_token');
    currentParrotId = null;
    
    showAlert('已退出登录', 'info');
    showLoginPage();
}

// ==================== 2. 密码重置（REQ-PARROT-011） ====================
// 发起重置
async function requestPasswordReset(email) {
    try {
        await apiRequest('/users/reset-password', 'POST', { email }, false);
        
        showAlert('重置邮件已发送，请检查邮箱', 'success');
        showResetSuccess();
    } catch (error) {
        showAlert(`请求失败: ${error.message}`, 'danger');
    }
}

// 确认重置（从URL获取token）
async function confirmPasswordReset(token, newPassword) {
    // 前端密码强度校验
    const validation = validatePasswordStrength(newPassword);
    if (!validation.valid) {
        showAlert(validation.message, 'warning');
        return false;
    }
    
    try {
        await apiRequest(`/users/reset-password/${token}`, 'POST', 
            { token, new_password: newPassword }, false);
        
        showAlert('密码已重置，请使用新密码登录', 'success');
        showLoginPage();
        return true;
    } catch (error) {
        if (error.message.includes('频繁')) {
            showAlert('操作过于频繁，请稍后再试', 'warning');
        } else {
            showAlert(`重置失败: ${error.message}`, 'danger');
        }
        return false;
    }
}

// ==================== 3. 站内消息中心（REQ-PARROT-005） ====================
// 加载消息列表（分页、筛选）
async function loadNotifications(page = 1, pageSize = 20, unreadOnly = false, notificationType = null) {
    try {
        let endpoint = `/notifications?page=${page}&page_size=${pageSize}`;
        if (unreadOnly) endpoint += '&unread_only=true';
        if (notificationType) endpoint += `&notification_type=${notificationType}`;
        
        const response = await apiRequest(endpoint, 'GET');
        
        renderNotificationsList(response.notifications);
        
        // 更新总数显示
        document.getElementById('notification-total').textContent = response.total;
        document.getElementById('notification-unread').textContent = response.unread_count;
        
        return response;
    } catch (error) {
        showAlert(`加载消息失败: ${error.message}`, 'danger');
    }
}

// 未读计数（更新导航栏红点）
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
        console.error('更新红点失败:', error);
    }
}

// 标记单条已读
async function markNotificationRead(notificationId) {
    try {
        await apiRequest(`/notifications/${notificationId}/read`, 'PATCH');
        
        // 刷新列表和红点
        await updateNotificationBadge();
        await loadNotifications();
    } catch (error) {
        showAlert(`标记失败: ${error.message}`, 'danger');
    }
}

// 全部标记已读
async function markAllNotificationsRead() {
    try {
        // 获取所有未读消息ID
        const response = await apiRequest('/notifications?unread_only=true&page_size=100', 'GET');
        
        if (response.notifications.length === 0) {
            showAlert('没有未读消息', 'info');
            return;
        }
        
        const notificationIds = response.notifications.map(n => n.notification_id);
        await apiRequest('/notifications/mark-read', 'PATCH', 
            { notification_ids: notificationIds });
        
        showAlert('全部标记已读', 'success');
        await updateNotificationBadge();
        await loadNotifications();
    } catch (error) {
        showAlert(`操作失败: ${error.message}`, 'danger');
    }
}

// 删除消息
async function deleteNotification(notificationId) {
    try {
        await apiRequest(`/notifications/${notificationId}`, 'DELETE');
        
        showAlert('消息已删除', 'success');
        await updateNotificationBadge();
        await loadNotifications();
    } catch (error) {
        showAlert(`删除失败: ${error.message}`, 'danger');
    }
}

// 按类型筛选消息
async function filterNotificationsByType(type) {
    await loadNotifications(1, 20, false, type);
}

// 渲染消息列表
function renderNotificationsList(notifications) {
    const listDiv = document.getElementById('notification-list');
    if (!listDiv) return;
    
    listDiv.innerHTML = '';
    
    if (notifications.length === 0) {
        listDiv.innerHTML = '<div class="text-center text-muted">暂无消息</div>';
        return;
    }
    
    notifications.forEach(n => {
        const item = document.createElement('div');
        item.className = n.is_read ? 'notification-read' : 'notification-unread';
        item.style.className = 'p-3 mb-2 rounded border';
        
        const typeIcon = {
            'system': '🔔',
            'health_alert': '⚠️',
            'parrot_reminder': '🐦',
            'feature_update': '✨'
        }[n.notification_type] || '📌';
        
        const readBtn = !n.is_read ? 
            '<button class="btn btn-sm btn-outline-primary" onclick="markNotificationRead('' + n.notification_id + '')">标记已读</button>' : '';
        
        item.innerHTML = `
            <div class="d-flex justify-content-between">
                <div>
                    <strong>${typeIcon} ${n.title}</strong>
                    <p class="mb-1">${n.content}</p>
                    <small class="text-muted">${new Date(n.created_at).toLocaleString()}</small>
                </div>
                <div>
                    ${readBtn}
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteNotification('${n.notification_id}')">删除</button>
                </div>
            </div>
        `;
        
        listDiv.appendChild(item);
    });
}

// ==================== 4. 健康档案总览（REQ-PARROT-009） ====================
// 加载所有鹦鹉健康数据
async function loadAllHealthOverview() {
    try {
        const overviews = await apiRequest('/parrots/health-overview', 'GET');
        
        renderHealthCards(overviews);
        return overviews;
    } catch (error) {
        showAlert(`加载健康档案失败: ${error.message}`, 'danger');
    }
}

// 渲染健康卡片（评分颜色标识）
function renderHealthCards(overviews) {
    const container = document.getElementById('health-overview-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (overviews.length === 0) {
        container.innerHTML = '<div class="text-center text-muted">暂无鹦鹉</div>';
        return;
    }
    
    overviews.forEach(overview => {
        const card = document.createElement('div');
        card.className = 'col-md-4 mb-3';
        
        // 评分颜色：>=80 绿色、60-79 黄色、<60 煃色
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
        
        // 趋势图标
        let trendIcon = '';
        let trendClass = '';
        if (overview.health_trend === 'improving') {
            trendIcon = '📈';
            trendClass = 'health-trend-up';
        } else if (overview.health_trend === 'declining') {
            trendIcon = '📉';
            trendClass = 'health-trend-down';
        } else {
            trendIcon = '➡️';
            trendClass = 'health-trend-stable';
        }
        
        card.innerHTML = `
            <div class="card card-hover shadow h-100" onclick="viewParrotDetail('${overview.parrot_id}')">
                <div class="card-body">
                    <h5 class="card-title">🦜 ${overview.parrot_name}</h5>
                    <p class="text-muted">${overview.species}</p>
                    <div class="display-4 ${scoreClass}" style="color: ${scoreColor}">
                        ${overview.current_health_score}
                    </div>
                    <small class="text-muted">健康评分</small>
                    <div class="mt-2">
                        <span class="${trendClass}">${trendIcon} ${overview.health_status}</span>
                    </div>
                    <div class="row mt-3 text-center">
                        <div class="col-6">
                            <strong>${overview.avg_health_score_7days}</strong>
                            <small class="text-muted">7日平均</small>
                        </div>
                        <div class="col-6">
                            <strong>${overview.total_abnormal_events_7days}</strong>
                            <small class="text-muted">7日异常</small>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        container.appendChild(card);
    });
}

// 点击跳转到单个鹦鹉详情页
function viewParrotDetail(parrotId) {
    currentParrotId = parrotId;
    // TODO: 实现详情页跳转逻辑
    showAlert('正在加载鹦鹉 ' + parrotId + ' 的详情...', 'info');
}

// ==================== 5. 个人信息管理（REQ-PARROT-012） ====================
// 加载个人信息
async function loadUserProfile() {
    try {
        const profile = await apiRequest('/users/profile', 'GET');
        
        document.getElementById('profile-nickname').value = profile.nickname || '';
        document.getElementById('profile-email').value = profile.email || '';
        document.getElementById('profile-phone').value = profile.phone || '';
        
        return profile;
    } catch (error) {
        showAlert(`加载个人信息失败: ${error.message}`, 'danger');
    }
}

// 更新个人信息
async function updateProfile(nickname, email, phone) {
    try {
        const profile = await apiRequest('/users/profile', 'PUT', 
            { nickname, email, phone });
        
        showAlert('个人信息已更新', 'success');
        return profile;
    } catch (error) {
        showAlert(`更新失败: ${error.message}`, 'danger');
    }
}

// 修改密码
async function changePassword(oldPassword, newPassword) {
    // 前端密码强度校验
    const validation = validatePasswordStrength(newPassword);
    if (!validation.valid) {
        showAlert(validation.message, 'warning');
        return false;
    }
    
    try {
        await apiRequest('/users/me/change-password', 'POST', 
            { old_password: oldPassword, new_password: newPassword });
        
        showAlert('密码已修改，请重新登录', 'success');
        logout();
        return true;
    } catch (error) {
        showAlert(`修改失败: ${error.message}`, 'danger');
        return false;
    }
}

// 通知偏好设置（存储到localStorage）
function saveNotificationPreferences(emailNotify, browserNotify) {
    localStorage.setItem('notification_email', emailNotify);
    localStorage.setItem('notification_browser', browserNotify);
    showAlert('通知偏好已保存', 'success');
}

// ==================== 页面切换逻辑 ====================
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

// 加载首页数据
async function loadHomePageData() {
    // 加载鹦鹉列表
    await loadParrotsList();
    
    // 更新消息红点
    await updateNotificationBadge();
    
    // 加载健康总览
    await loadAllHealthOverview();
}

// 加载鹦鹉列表
async function loadParrotsList() {
    try {
        const parrots = await apiRequest('/parrots', 'GET');
        
        const listDiv = document.getElementById('parrots-list');
        if (!listDiv) return;
        
        listDiv.innerHTML = '';
        
        if (parrots.length === 0) {
            listDiv.innerHTML = '<div class="text-muted">暂无鹦鹉，请添加</div>';
            return;
        }
        
        parrots.forEach(p => {
            const item = document.createElement('div');
            item.className = 'mb-2 p-2 border rounded';
            item.innerHTML = `
                <strong>🦜 ${p.name}</strong>
                <span class="text-muted ml-2">${p.species}</span>
                <button class="btn btn-sm btn-outline-secondary float-right" 
                    onclick="selectParrot('${p.parrot_id}', '${p.name}')">
                    选择
                </button>
            `;
            listDiv.appendChild(item);
        });
    } catch (error) {
        console.error('加载鹦鹉列表失败:', error);
    }
}

// 选择鹦鹉
function selectParrot(parrotId, parrotName) {
    currentParrotId = parrotId;
    document.getElementById('parrot-name').textContent = parrotName;
    
    // 加载今日摘要
    loadTodaySummary(parrotId);
}

// 加载今日摘要
async function loadTodaySummary(parrotId) {
    try {
        const summary = await apiRequest(`/parrots/${parrotId}/today-summary`, 'GET');
        
        document.getElementById('health-score').textContent = summary.health_score;
        document.getElementById('chirp-count').textContent = summary.chirp_count;
        document.getElementById('scream-count').textContent = summary.scream_count;
        document.getElementById('status-summary').textContent = summary.summary;
        
        // 根据评分设置颜色
        const scoreDiv = document.getElementById('health-score');
        if (summary.health_score >= 80) {
            scoreDiv.className = 'display-4 status-healthy';
        } else if (summary.health_score >= 60) {
            scoreDiv.className = 'display-4 status-warning';
        } else {
            scoreDiv.className = 'display-4 status-danger';
        }
    } catch (error) {
        console.error('加载今日摘要失败:', error);
    }
}

// ==================== 事件绑定 ====================
document.addEventListener('DOMContentLoaded', function() {
    // 检查是否已登录
    if (currentToken) {
        showHomePage();
        loadHomePageData();
    } else {
        showLoginPage();
    }
    
    // 登录表单
    const loginForm = document.getElementById('login-form');
    if (loginForm) {
        loginForm.addEventListener('submit', async function(e) {
            e.preventDefault();
            const phone = document.getElementById('phone').value;
            const password = document.getElementById('password').value;
            await login(phone, password);
        });
    }
    
    // 注册表单
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
    
    // 注册链接
    const registerLink = document.getElementById('register-link');
    if (registerLink) {
        registerLink.addEventListener('click', function(e) {
            e.preventDefault();
            showRegisterPage();
        });
    }
    
    // 返回登录链接
    const backLoginLink = document.getElementById('back-login-link');
    if (backLoginLink) {
        backLoginLink.addEventListener('click', function(e) {
            e.preventDefault();
            showLoginPage();
        });
    }
    
    // 忘记密码链接
    const forgotPasswordLink = document.getElementById('forgot-password-link');
    if (forgotPasswordLink) {
        forgotPasswordLink.addEventListener('click', function(e) {
            e.preventDefault();
            showResetPasswordPage();
        });
    }
    
    // 发起重置按钮
    const requestResetBtn = document.getElementById('request-reset-btn');
    if (requestResetBtn) {
        requestResetBtn.addEventListener('click', async function() {
            const email = document.getElementById('reset-email').value;
            await requestPasswordReset(email);
        });
    }
    
    // 返回登录（从重置页）
    const backLoginFromReset = document.getElementById('back-login-from-reset');
    if (backLoginFromReset) {
        backLoginFromReset.addEventListener('click', function(e) {
            e.preventDefault();
            showLoginPage();
        });
    }
    
    // 返回登录（从成功页）
    const backLoginFromSuccess = document.getElementById('back-login-from-success');
    if (backLoginFromSuccess) {
        backLoginFromSuccess.addEventListener('click', function(e) {
            e.preventDefault();
            showLoginPage();
        });
    }
    
    // 退出登录按钮
    const logoutBtn = document.getElementById('logout-btn');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
    
    // 消息中心按钮
    const notificationBtn = document.getElementById('notification-btn');
    if (notificationBtn) {
        notificationBtn.addEventListener('click', async function() {
            const modal = new bootstrap.Modal(document.getElementById('notification-modal'));
            modal.show();
            await loadNotifications();
        });
    }
    
    // 个人信息按钮
    const profileBtn = document.getElementById('profile-btn');
    if (profileBtn) {
        profileBtn.addEventListener('click', async function() {
            const modal = new bootstrap.Modal(document.getElementById('profile-modal'));
            modal.show();
            await loadUserProfile();
        });
    }
    
    // 健康总览按钮
    const healthOverviewBtn = document.getElementById('health-overview-btn');
    if (healthOverviewBtn) {
        healthOverviewBtn.addEventListener('click', async function() {
            document.getElementById('health-overview-card').style.display = 'block';
            await loadAllHealthOverview();
        });
    }
    
    // 检查URL中是否有密码重置token
    const urlParams = new URLSearchParams(window.location.search);
    const resetToken = urlParams.get('token');
    if (resetToken) {
        showResetPasswordPage();
        // 显示确认重置表单
        // TODO: 实现确认重置UI
    }
});

// ==================== 导出全局函数（供HTML调用） ====================
window.markNotificationRead = markNotificationRead;
window.deleteNotification = deleteNotification;
window.viewParrotDetail = viewParrotDetail;
window.selectParrot = selectParrot;
window.filterNotificationsByType = filterNotificationsByType;
window.markAllNotificationsRead = markAllNotificationsRead;
