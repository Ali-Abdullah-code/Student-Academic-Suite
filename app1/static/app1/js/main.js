document.addEventListener('DOMContentLoaded', function () {
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');

    if (sidebarToggle) {
        sidebarToggle.addEventListener('click', function () {
            if (sidebar) sidebar.classList.toggle('active');
        });

        document.addEventListener('click', function (e) {
            if (sidebar && sidebar.classList.contains('active')) {
                if (!sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
                    sidebar.classList.remove('active');
                }
            }
        });
    }

    // Auto-close alerts after 5 seconds
    document.querySelectorAll('.alert').forEach(function (a) {
        setTimeout(function () {
            a.style.opacity = '0';
            setTimeout(function () { a.remove(); }, 300);
        }, 5000);
    });

    // Form validation feedback
    document.querySelectorAll('form').forEach(function (form) {
        form.addEventListener('submit', function (e) {
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;

            requiredFields.forEach(function (field) {
                if (!field.value.trim()) {
                    field.classList.add('is-invalid');
                    isValid = false;
                } else {
                    field.classList.remove('is-invalid');
                }
            });

            if (!isValid) {
                e.preventDefault();
                showNotification('Please fill in all required fields', 'warning');
            }
        });
    });

    // Input change handler
    document.querySelectorAll('[required]').forEach(function (input) {
        input.addEventListener('change', function () {
            if (this.value.trim()) this.classList.remove('is-invalid');
        });
    });
});

function showNotification(message, type) {
    type = type || 'info';
    const container = document.querySelector('.messages-container') || document.body;
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible`;
    alert.innerHTML = `${message}<button type="button" class="alert-close" onclick="this.parentElement.style.display='none';">×</button>`;

    if (container === document.body) {
        container.insertBefore(alert, container.firstChild);
    } else {
        container.appendChild(alert);
    }

    setTimeout(function () {
        alert.style.opacity = '0';
        setTimeout(function () { alert.remove(); }, 300);
    }, 5000);
}

function confirmAction(message) {
    return confirm(message || 'Are you sure?');
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
}

function formatPercentage(value) {
    return `${parseFloat(value).toFixed(2)}%`;
}

function getAttendanceColor(percentage) {
    if (percentage >= 75) return '#22C55E';
    if (percentage >= 60) return '#F59E0B';
    return '#EF4444';
}

function setTodayDate(inputId) {
    const input = document.getElementById(inputId);
    if (input && input.type === 'date') {
        input.value = new Date().toISOString().split('T')[0];
    }
}

function calculateAttendanceTotal() {
    const presentCount = document.querySelectorAll('input[value="present"]:checked').length;
    const absentCount = document.querySelectorAll('input[value="absent"]:checked').length;
    const totalCount = presentCount + absentCount;
    const percentage = totalCount > 0 ? ((presentCount / totalCount) * 100).toFixed(2) : 0;

    return { present: presentCount, absent: absentCount, total: totalCount, percentage: percentage };
}

function exportTableToCSV(tableId, fileName) {
    fileName = fileName || 'export.csv';
    const table = document.getElementById(tableId);
    if (!table) return;

    const csv = [];
    const rows = table.querySelectorAll('tr');

    rows.forEach(function (row) {
        const cols = row.querySelectorAll('td, th');
        const csvRow = [];
        cols.forEach(function (col) {
            csvRow.push('"' + col.innerText.replace(/"/g, '""') + '"');
        });
        csv.push(csvRow.join(','));
    });

    downloadCSV(csv.join('\n'), fileName);
}

function downloadCSV(csv, fileName) {
    const link = document.createElement('a');
    link.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(csv);
    link.download = fileName;
    link.click();
}

function printPage() { window.print(); }

function isValidEmail(email) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email); }

function isValidPhone(phone) { return /^[\d\s\-\+\(\)]{10,}$/.test(phone.trim()); }

function isStrongPassword(password) {
    return (
        password.length >= 8 && /[A-Z]/.test(password) && /[a-z]/.test(password) && /[0-9]/.test(password)
    );
}

function showLoading() {
    const loader = document.createElement('div');
    loader.className = 'loader';
    loader.innerHTML = '<div class="spinner"></div>';
    document.body.appendChild(loader);
}

function hideLoading() { const loader = document.querySelector('.loader'); if (loader) loader.remove(); }

function debounce(func, wait) {
    let timeout;
    return function executedFunction() {
        const args = arguments;
        const later = function () {
            clearTimeout(timeout);
            func.apply(null, args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Export functions for use in other scripts
window.StudentAcademicSuite = {
    showNotification: showNotification,
    confirmAction: confirmAction,
    formatDate: formatDate,
    formatPercentage: formatPercentage,
    getAttendanceColor: getAttendanceColor,
    setTodayDate: setTodayDate,
    calculateAttendanceTotal: calculateAttendanceTotal,
    exportTableToCSV: exportTableToCSV,
    downloadCSV: downloadCSV,
    printPage: printPage,
    isValidEmail: isValidEmail,
    isValidPhone: isValidPhone,
    isStrongPassword: isStrongPassword,
    showLoading: showLoading,
    hideLoading: hideLoading,
    debounce: debounce
};
