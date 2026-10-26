/**
 * AI-Powered Hyperlocal Job Recommendation and Matching System for Fresh Graduates
 * Central API Client & Auth Utilities
 */

const API_BASE = '/api';

// Toast Notification System
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    document.body.appendChild(container);
  }

  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  
  const icon = type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ';
  toast.innerHTML = `<span style="font-weight:bold; font-size:1.1rem;">${icon}</span><span>${message}</span>`;
  
  container.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Unified API Fetcher
async function apiRequest(endpoint, options = {}) {
  const token = localStorage.getItem('token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers
    });

    const data = await response.json().catch(() => ({}));

    if (!response.ok) {
      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        // Token expired or invalid
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        window.location.href = 'login.html';
        return null;
      }
      throw new Error(data.message || data.error || `Request failed with status ${response.status}`);
    }

    return data;
  } catch (error) {
    showToast(error.message, 'error');
    throw error;
  }
}

// Resume Upload Helper
async function uploadResumeFile(file) {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Please login to upload your resume');
  }
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE}/students/resume`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Failed to upload resume');
  }
  return data;
}

// Profile Picture Upload Helper
async function uploadAvatarFile(file) {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Please login to upload your profile picture');
  }
  const formData = new FormData();
  formData.append('avatar', file);

  const response = await fetch(`${API_BASE}/users/avatar`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Failed to upload profile picture');
  }
  const user = getCurrentUser();
  if (user && data.avatar_url) {
    user.avatar_url = data.avatar_url;
    localStorage.setItem('user', JSON.stringify(user));
  }
  return data;
}

// Profile Picture Remove Helper
async function removeAvatarFile() {
  const token = localStorage.getItem('token');
  if (!token) {
    throw new Error('Please login to remove your profile picture');
  }
  const response = await fetch(`${API_BASE}/users/avatar`, {
    method: 'DELETE',
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });

  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(data.error || 'Failed to remove profile picture');
  }
  const user = getCurrentUser();
  if (user) {
    user.avatar_url = null;
    localStorage.setItem('user', JSON.stringify(user));
  }
  return data;
}

// User & Auth State
function getCurrentUser() {
  const userStr = localStorage.getItem('user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

function setAuthSession(user, token) {
  localStorage.setItem('user', JSON.stringify(user));
  localStorage.setItem('token', token);
}

function logout() {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  window.location.href = 'index.html';
}

function requireAuth(allowedRoles = []) {
  const user = getCurrentUser();
  const token = localStorage.getItem('token');

  if (!user || !token) {
    window.location.href = 'login.html';
    return false;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user.role)) {
    showToast('Unauthorized access for your account role.', 'error');
    if (user.role === 'student') window.location.href = 'dashboard.html';
    else if (user.role === 'employer') window.location.href = 'employer_dashboard.html';
    else if (user.role === 'admin') window.location.href = 'admin.html';
    else window.location.href = 'index.html';
    return false;
  }

  return true;
}

// Render dynamic navbar based on user session
function setupNavbar(activePage = '') {
  const user = getCurrentUser();
  const navContainer = document.querySelector('.nav-container');
  if (!navContainer) return;

  let menuHtml = '';
  let actionsHtml = '';

  if (!user) {
    menuHtml = `
      <ul class="nav-menu">
        <li><a href="index.html" class="nav-link ${activePage === 'home' ? 'active' : ''}">Home</a></li>
        <li><a href="jobs.html" class="nav-link ${activePage === 'jobs' ? 'active' : ''}">Find Jobs</a></li>
        <li><a href="ai_demo.html" class="nav-link ${activePage === 'ai_demo' ? 'active' : ''}">How AI Matches</a></li>
      </ul>
    `;
    actionsHtml = `
      <div class="nav-actions">
        <a href="login.html" class="btn btn-secondary btn-sm">Login</a>
        <a href="register.html" class="btn btn-primary btn-sm">Register as Fresh Graduate / Employer</a>
      </div>
    `;
  } else if (user.role === 'student') {
    menuHtml = `
      <ul class="nav-menu">
        <li><a href="dashboard.html" class="nav-link ${activePage === 'dashboard' ? 'active' : ''}">AI Recommendations</a></li>
        <li><a href="jobs.html" class="nav-link ${activePage === 'jobs' ? 'active' : ''}">Explore Jobs & Map</a></li>
        <li><a href="applications.html" class="nav-link ${activePage === 'applications' ? 'active' : ''}">My Applications</a></li>
        <li><a href="saved.html" class="nav-link ${activePage === 'saved' ? 'active' : ''}">Saved Jobs</a></li>
        <li><a href="notifications.html" class="nav-link ${activePage === 'notifications' ? 'active' : ''}">🔔 Alerts <span id="nav-notif-badge" style="display:none; background:var(--primary); color:#fff; border-radius:10px; padding:0.1rem 0.45rem; font-size:0.75rem; font-weight:700;"></span></a></li>
        <li><a href="profile.html" class="nav-link ${activePage === 'profile' ? 'active' : ''}">My Profile</a></li>
      </ul>
    `;
    const avatarImg = (user.avatar_url && user.avatar_url.trim()) 
      ? `<img src="${user.avatar_url}" style="width:24px; height:24px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:6px; border:1px solid var(--gray-300);">` 
      : '';
    actionsHtml = `
      <div class="nav-actions">
        <a href="profile.html" class="btn btn-secondary btn-sm ${activePage === 'profile' ? 'active' : ''}" title="My Profile" style="display:inline-flex; align-items:center;">
          ${avatarImg}<span>My Profile</span>
        </a>
        <button onclick="logout()" class="btn btn-outline btn-sm">Logout</button>
      </div>
    `;
  } else if (user.role === 'employer') {
    menuHtml = `
      <ul class="nav-menu">
        <li><a href="employer_dashboard.html" class="nav-link ${activePage === 'employer_dashboard' ? 'active' : ''}">Dashboard & Jobs</a></li>
        <li><a href="notifications.html" class="nav-link ${activePage === 'notifications' ? 'active' : ''}">🔔 Alerts <span id="nav-notif-badge" style="display:none; background:var(--primary); color:#fff; border-radius:10px; padding:0.1rem 0.45rem; font-size:0.75rem; font-weight:700;"></span></a></li>
        <li><a href="profile.html" class="nav-link ${activePage === 'profile' ? 'active' : ''}">My Profile</a></li>
      </ul>
    `;
    const empAvatarImg = (user.avatar_url && user.avatar_url.trim()) 
      ? `<img src="${user.avatar_url}" style="width:24px; height:24px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:6px; border:1px solid var(--gray-300);">` 
      : '';
    actionsHtml = `
      <div class="nav-actions">
        <a href="profile.html" class="btn btn-secondary btn-sm ${activePage === 'profile' ? 'active' : ''}" title="My Profile" style="display:inline-flex; align-items:center;">
          ${empAvatarImg}<span>My Profile</span>
        </a>
        <button onclick="logout()" class="btn btn-outline btn-sm">Logout</button>
      </div>
    `;
  } else if (user.role === 'admin') {
    menuHtml = `
      <ul class="nav-menu">
        <li><a href="admin.html" class="nav-link ${activePage === 'admin' ? 'active' : ''}">Admin Control & Analytics</a></li>
        <li><a href="jobs.html" class="nav-link ${activePage === 'jobs' ? 'active' : ''}">All Jobs</a></li>
        <li><a href="profile.html" class="nav-link ${activePage === 'profile' ? 'active' : ''}">My Profile</a></li>
      </ul>
    `;
    const adminAvatarImg = (user.avatar_url && user.avatar_url.trim()) 
      ? `<img src="${user.avatar_url}" style="width:24px; height:24px; border-radius:50%; object-fit:cover; vertical-align:middle; margin-right:6px; border:1px solid var(--gray-300);">` 
      : '';
    actionsHtml = `
      <div class="nav-actions">
        <a href="profile.html" class="btn btn-secondary btn-sm ${activePage === 'profile' ? 'active' : ''}" title="My Profile" style="display:inline-flex; align-items:center;">
          ${adminAvatarImg}<span>My Profile</span>
        </a>
        <button onclick="logout()" class="btn btn-outline btn-sm">Logout</button>
      </div>
    `;
  }

  navContainer.innerHTML = `
    <a href="index.html" class="nav-brand">
      <div class="brand-icon">🎓</div>
      <span>Grad<span style="color:var(--primary);">Match AI</span></span>
    </a>
    ${menuHtml}
    ${actionsHtml}
  `;

  // Fetch unread count if authenticated
  if (user) {
    const token = localStorage.getItem('token');
    if (token) {
      fetch('/api/notifications', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(data => {
        if (data && data.unread_count > 0) {
          const badge = document.getElementById('nav-notif-badge');
          if (badge) {
            badge.innerText = data.unread_count;
            badge.style.display = 'inline-block';
          }
        }
      })
      .catch(() => {});
    }
  }
}


