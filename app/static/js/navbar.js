document.addEventListener('DOMContentLoaded', function () {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  function loadNotifications() {
    fetch('/notifications/unread')
      .then(res => res.json())
      .then(data => {
        renderNotificationDropdown(data.notifications);
        updateUnreadBadge(data.count);
      });
  }

  function updateUnreadBadge(count) {
    const badge = document.getElementById('notification-count');
    if (!badge) return;
    if (count > 0) {
      badge.style.display = 'inline-block';
      badge.textContent = count;
    } else {
      badge.style.display = 'none';
    }
  }

  function getIconClass(category) {
    switch (category) {
      case 'tax':
        return 'fas fa-file-invoice-dollar text-danger';
      case 'payroll':
        return 'fas fa-money-bill-wave text-success';
      case 'employment':
        return 'fas fa-user text-primary';
      default:
        return 'fas fa-info-circle text-secondary';
    }
  }

  function renderNotificationDropdown(notifications) {
    const list = document.getElementById('notifications-list');
    if (!list) return;
    list.innerHTML = '';
    if (notifications.length === 0) {
      list.innerHTML = '<li class="dropdown-item-text text-center text-muted py-3"><i class="fas fa-bell-slash fa-2x mb-2 d-block"></i>No notifications</li>';
      return;
    }
    notifications.forEach(n => {
      const li = document.createElement('li');
      li.className = 'dropdown-item d-flex justify-content-between align-items-start';
      li.innerHTML = `<div><i class="me-2 ${getIconClass(n.category)}"></i>${n.title}<div class="small text-muted">${n.time_ago}</div></div>` +
        `<button class="btn btn-sm btn-link" data-id="${n.id}"><i class="fas fa-check"></i></button>`;
      list.appendChild(li);
    });
    list.querySelectorAll('button').forEach(btn => {
      btn.addEventListener('click', function () {
        const id = this.getAttribute('data-id');
        fetch(`/notifications/api/${id}/mark-read`, {
          method: 'POST',
          headers: { 'X-CSRFToken': csrfToken }
        }).then(loadNotifications);
      });
    });
  }

  window.markAllNotificationsRead = function () {
    fetch('/notifications/api/mark-all-read', {
      method: 'POST',
      headers: { 'X-CSRFToken': csrfToken }
    }).then(loadNotifications);
  };

  loadNotifications();
});
