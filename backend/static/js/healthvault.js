// =============================================================================
// healthvault.js — Client-side JavaScript v2.0
// Premium UI: Apple-style animations, scroll-reveal, counters, ripple
// =============================================================================

// --- SIDEBAR TOGGLE ---
const sidebarToggle = document.getElementById('sidebarToggle');
const sidebar = document.getElementById('sidebar');

if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
        document.body.classList.toggle('sidebar-mobile-open');
    });
    document.addEventListener('click', function (e) {
        if (window.innerWidth < 992 && document.body.classList.contains('sidebar-mobile-open')) {
            if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                document.body.classList.remove('sidebar-mobile-open');
            }
        }
    });
}

// --- AUTO-DISMISS FLASH ALERTS ---
document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000);
    });
});

// --- CONFIRM DANGEROUS ACTIONS ---
document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('[data-confirm]').forEach(function (el) {
        el.addEventListener('click', function (e) {
            const message = el.getAttribute('data-confirm');
            if (!confirm(message)) { e.preventDefault(); }
        });
    });
});

// --- LAB RESULT TREND CHART ---
function loadLabTrendChart(testName, canvasId) {
    fetch(`/api/charts/lab-trend/${encodeURIComponent(testName)}`)
        .then(response => response.json())
        .then(data => {
            if (data.data && data.data.length > 1) {
                const canvas = document.getElementById(canvasId);
                if (!canvas) return;
                const ctx = canvas.getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.data.map(d => d.date),
                        datasets: [{
                            label: testName,
                            data: data.data.map(d => d.value),
                            borderColor: '#0d9488',
                            backgroundColor: 'rgba(13,148,136,0.08)',
                            borderWidth: 2,
                            pointRadius: 5,
                            pointBackgroundColor: data.data.map(d => d.is_abnormal ? '#ef4444' : '#10b981'),
                            pointBorderColor: 'white',
                            pointBorderWidth: 2,
                            tension: 0.4,
                            fill: true
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { display: false },
                            tooltip: {
                                backgroundColor: 'rgba(15,23,42,0.9)',
                                cornerRadius: 10,
                                padding: 10,
                                callbacks: {
                                    label: function (ctx) {
                                        const point = data.data[ctx.dataIndex];
                                        return `${ctx.parsed.y} ${point.unit}`;
                                    }
                                }
                            }
                        },
                        scales: {
                            y: {
                                beginAtZero: false,
                                grid: { color: 'rgba(0,0,0,0.04)' },
                                ticks: { color: '#64748b', font: { size: 11 } }
                            },
                            x: {
                                grid: { display: false },
                                ticks: { color: '#64748b', font: { size: 11 } }
                            }
                        },
                        animation: { duration: 600, easing: 'easeInOutQuart' }
                    }
                });
            }
        })
        .catch(err => console.log('Chart data not available:', err));
}

// --- ADD TEST ROW (Lab report form) ---
let testRowCount = 0;
function addTestRow() {
    testRowCount++;
    const container = document.getElementById('testRowsContainer');
    if (!container) return;
    const row = document.createElement('div');
    row.className = 'row g-2 mb-2 test-row align-items-center';
    row.style.opacity = '0';
    row.style.transform = 'translateY(10px)';
    row.innerHTML = `
        <div class="col-md-3">
            <input type="text" name="test_name[]" class="form-control form-control-sm" placeholder="Test name (e.g. Hemoglobin)" required>
        </div>
        <div class="col-md-2">
            <input type="text" name="test_value[]" class="form-control form-control-sm" placeholder="Value (e.g. 13.8)">
        </div>
        <div class="col-md-2">
            <input type="text" name="test_unit[]" class="form-control form-control-sm" placeholder="Unit (e.g. g/dL)">
        </div>
        <div class="col-md-3">
            <input type="text" name="test_range[]" class="form-control form-control-sm" placeholder="Range (e.g. 13.0 - 17.0)">
        </div>
        <div class="col-md-1 text-center">
            <input type="checkbox" name="test_abnormal[]" value="${testRowCount - 1}" class="form-check-input" title="Abnormal?">
            <small class="d-block text-muted" style="font-size:0.65rem;">Abnormal</small>
        </div>
        <div class="col-md-1">
            <button type="button" class="btn btn-sm btn-outline-danger" onclick="this.closest('.test-row').remove()">
                <i class="bi bi-trash"></i>
            </button>
        </div>
    `;
    container.appendChild(row);
    // Animate in
    requestAnimationFrame(() => {
        row.style.transition = 'opacity 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94), transform 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94)';
        row.style.opacity = '1';
        row.style.transform = 'translateY(0)';
    });
}

// --- PRINT PAGE ---
function printPage() { window.print(); }

// --- QR CODE DOWNLOAD ---
function downloadQR(imgId, filename) {
    const img = document.getElementById(imgId);
    if (!img) return;
    const link = document.createElement('a');
    link.download = filename || 'healthvault-qr.png';
    link.href = img.src;
    link.click();
}

// --- NOTIFICATION BADGE UPDATE ---
function updateNotificationBadge() {
    fetch('/api/notifications/count')
        .then(r => r.json())
        .then(data => {
            const badges = document.querySelectorAll('.notification-badge');
            badges.forEach(b => {
                if (data.count > 0) { b.textContent = data.count; b.style.display = 'inline'; }
                else { b.style.display = 'none'; }
            });
        })
        .catch(() => {});
}
setInterval(updateNotificationBadge, 60000);

// --- FORMAT FILE SIZE ---
function formatBytes(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// --- DARK MODE TOGGLE ---
function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    const icon = document.getElementById('darkModeIcon');
    const label = document.getElementById('darkModeLabel');
    if (isDark) {
        localStorage.setItem('theme', 'dark');
        if (icon) icon.className = 'bi bi-sun-fill me-2';
        if (label) label.innerText = 'Light Mode';
    } else {
        localStorage.setItem('theme', 'light');
        if (icon) icon.className = 'bi bi-moon-stars-fill me-2';
        if (label) label.innerText = 'Dark Mode';
    }
}
document.addEventListener('DOMContentLoaded', function () {
    if (document.body.classList.contains('dark-mode')) {
        const icon = document.getElementById('darkModeIcon');
        const label = document.getElementById('darkModeLabel');
        if (icon) icon.className = 'bi bi-sun-fill me-2';
        if (label) label.innerText = 'Light Mode';
    }
});

// =============================================================================
// PREMIUM UI — Animation Engine v2.0
// =============================================================================

// --- SCROLL-REVEAL ENGINE ---
// Uses IntersectionObserver to reveal elements as they enter the viewport
(function initScrollReveal() {
    const APPLE_EASE = 'cubic-bezier(0.25, 0.46, 0.45, 0.94)';

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                // Don't unobserve — let it stay visible
            }
        });
    }, {
        threshold: 0.08,
        rootMargin: '0px 0px -30px 0px'
    });

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('.reveal, .reveal-stagger').forEach(el => {
            observer.observe(el);
        });
    });
})();

// --- ANIMATED NUMBER COUNTERS ---
// Elements with data-counter attribute animate from 0 to their value
(function initCounters() {
    function animateCounter(el, target, duration) {
        if (isNaN(target) || target === 0) return;
        const start = performance.now();
        function step(now) {
            const elapsed = now - start;
            const progress = Math.min(elapsed / duration, 1);
            // Apple-style ease-out
            const eased = 1 - Math.pow(1 - progress, 3);
            el.textContent = Math.round(eased * target);
            if (progress < 1) requestAnimationFrame(step);
        }
        requestAnimationFrame(step);
    }

    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting && !entry.target.dataset.counted) {
                entry.target.dataset.counted = 'true';
                const target = parseInt(entry.target.dataset.counter, 10);
                animateCounter(entry.target, target, 900);
            }
        });
    }, { threshold: 0.5 });

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-counter]').forEach(el => {
            counterObserver.observe(el);
        });
    });
})();

// --- BUTTON RIPPLE EFFECT ---
(function initRipple() {
    document.addEventListener('click', function (e) {
        const btn = e.target.closest('.btn');
        if (!btn) return;
        const ripple = document.createElement('span');
        ripple.className = 'btn-ripple';
        const rect = btn.getBoundingClientRect();
        ripple.style.left = (e.clientX - rect.left - 2) + 'px';
        ripple.style.top  = (e.clientY - rect.top - 2) + 'px';
        btn.appendChild(ripple);
        ripple.addEventListener('animationend', () => ripple.remove());
    });
})();

// --- STAGGER INIT ---
// Auto-mark stagger groups and add reveal to cards/stat-cards on DOMContentLoaded
(function initStagger() {
    document.addEventListener('DOMContentLoaded', () => {
        // Auto-add reveal to stat cards
        document.querySelectorAll('.stat-card:not(.no-reveal)').forEach(el => {
            el.classList.add('reveal');
        });
        // Auto-add reveal to cards that are inside reveal-stagger
        // (reveal-stagger itself handles children via CSS)
    });
})();

// --- THEME TOGGLE (topbar version) ---
function toggleTheme() {
    const isDark = document.body.classList.toggle('dark-mode');
    document.documentElement.classList.toggle('dark-mode', isDark);
    localStorage.setItem('hv-theme', isDark ? 'dark' : 'light');
    updateThemeBtn(isDark);
}

function updateThemeBtn(isDark) {
    const icon  = document.getElementById('themeIcon');
    const label = document.getElementById('themeLabel');
    const pill  = document.getElementById('themeStatusPill');
    if (icon)  icon.className  = isDark ? 'bi bi-sun-fill' : 'bi bi-moon-stars-fill';
    if (label) label.textContent = isDark ? 'Light Mode' : 'Dark Mode';
    if (pill)  pill.textContent  = isDark ? 'On' : 'Off';
    if (icon)  icon.style.color  = 'var(--primary)';
}

// --- SIDEBAR MINIMIZE ---
function toggleSidebarMinimize() {
    const isMin = document.body.classList.toggle('sidebar-minimized');
    localStorage.setItem('hv-sidebar', isMin ? 'minimized' : 'expanded');
    const icon = document.getElementById('minimizeIcon');
    if (icon) icon.className = isMin ? 'bi bi-layout-sidebar' : 'bi bi-layout-sidebar-reverse';
}

// Initialise button state on load
document.addEventListener('DOMContentLoaded', () => {
    const isDark = document.body.classList.contains('dark-mode');
    updateThemeBtn(isDark);
    if (localStorage.getItem('hv-sidebar') === 'minimized') {
        document.body.classList.add('sidebar-minimized');
        const icon = document.getElementById('minimizeIcon');
        if (icon) icon.className = 'bi bi-layout-sidebar';
    }
    // Auto-populate title attributes on nav links for minimized-mode tooltips
    document.querySelectorAll('.sidebar-nav .nav-link').forEach(link => {
        const text = link.textContent.trim();
        if (text && !link.hasAttribute('title')) link.setAttribute('title', text);
    });
});
