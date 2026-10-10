/**
 * Cognimap AI - Shared Client-side Logic & Interactions
 */

// Theme Management
function initTheme() {
  const savedTheme = localStorage.getItem('cognimap-theme') || 'dark';
  document.documentElement.setAttribute('data-theme', savedTheme);
  updateThemeIcon(savedTheme);
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  document.documentElement.setAttribute('data-theme', next);
  localStorage.setItem('cognimap-theme', next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const iconSpan = document.getElementById('theme-toggle-icon');
  if (iconSpan) {
    if (theme === 'dark') {
      iconSpan.innerHTML = '<i data-lucide="sun" style="width: 16px; height: 16px;"></i>';
    } else {
      iconSpan.innerHTML = '<i data-lucide="moon" style="width: 16px; height: 16px;"></i>';
    }
    if (typeof lucide !== 'undefined') {
      lucide.createIcons();
    }
  }
}

// Toast Notifications
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 0.6rem;
      pointer-events: none;
    `;
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const typeColors = {
    success: 'var(--status-strong)',
    danger: 'var(--status-weak)',
    warning: 'var(--status-ni)',
    info: 'var(--brand-primary)'
  };

  const typeIcons = {
    success: 'check-circle-2',
    danger: 'alert-triangle',
    warning: 'alert-circle',
    info: 'info'
  };

  toast.style.cssText = `
    background: rgba(18, 25, 41, 0.95);
    backdrop-filter: blur(16px);
    border: 1px solid var(--border-medium);
    border-left: 4px solid ${typeColors[type] || typeColors.info};
    color: var(--text-main);
    padding: 0.9rem 1.25rem;
    border-radius: 10px;
    font-size: 0.9rem;
    font-weight: 500;
    box-shadow: 0 12px 30px rgba(0, 0, 0, 0.5);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    pointer-events: auto;
    animation: toastSlideUp 0.3s cubic-bezier(0.16, 1, 0.3, 1);
    max-width: 380px;
  `;

  toast.innerHTML = `
    <i data-lucide="${typeIcons[type] || 'info'}" style="width: 18px; height: 18px; color: ${typeColors[type] || typeColors.info}; flex-shrink: 0;"></i>
    <div style="flex: 1;">${message}</div>
    <button style="background: none; border: none; color: var(--text-dim); cursor: pointer; font-size: 1rem; display: flex; align-items: center;" onclick="this.parentElement.remove()">✕</button>
  `;

  toastContainer.appendChild(toast);
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

document.addEventListener('DOMContentLoaded', () => {
  initTheme();
  if (typeof lucide !== 'undefined') {
    lucide.createIcons();
  }
});
