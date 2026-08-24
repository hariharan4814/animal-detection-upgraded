/**
 * FarmSync Application Controller (Step 14)
 * Orchestrates views, state management, modal dialogs, API data bindings, and role-based UX adjustments.
 */

document.addEventListener('DOMContentLoaded', () => {
  // UI Elements
  const navLinks = document.querySelectorAll('.sidebar-nav li a');
  const viewSections = document.querySelectorAll('.view-section');
  const pageTitle = document.getElementById('page-title');
  const pageSubtitle = document.getElementById('page-subtitle');
  const userNameDisplay = document.getElementById('user-name-display');
  const userRoleDisplay = document.getElementById('user-role-display');
  const loginModal = document.getElementById('login-modal');
  const loginForm = document.getElementById('login-form');
  const logoutBtn = document.getElementById('logout-btn');

  let currentView = 'dashboard';
  let cachedFarmers = [];

  // =========================================================================
  // TOAST NOTIFICATIONS
  // =========================================================================
  window.showToast = function(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type === 'error' ? 'toast-error' : type === 'warning' ? 'toast-warning' : ''}`;
    toast.innerText = message;
    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transform = 'translateX(100%)';
      setTimeout(() => toast.remove(), 300);
    }, 4000);
  };

  // =========================================================================
  // MODAL UTILITIES
  // =========================================================================
  window.openModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('active');
  };

  window.closeModal = function(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
  };

  // Close modals when clicking outside card or clicking close button
  document.querySelectorAll('.modal-backdrop').forEach(modal => {
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        modal.classList.remove('active');
      }
    });
  });

  document.querySelectorAll('.modal-close').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const modal = btn.closest('.modal-backdrop');
      if (modal && modal.id !== 'login-modal') {
        modal.classList.remove('active');
      }
    });
  });

  // =========================================================================
  // AUTHENTICATION & INITIALIZATION
  // =========================================================================
  async function checkAuthAndInit() {
    if (!api.isAuthenticated()) {
      showLoginModal();
      return;
    }

    try {
      const user = await api.getMe();
      updateUserUI(user);
      hideLoginModal();
      switchView(currentView);
    } catch (e) {
      showLoginModal();
    }
  }

  function showLoginModal() {
    loginModal.classList.add('active');
  }

  function hideLoginModal() {
    loginModal.classList.remove('active');
  }

  function updateUserUI(user) {
    if (!user) return;
    if (userNameDisplay) userNameDisplay.innerText = user.username || 'User';
    if (userRoleDisplay) {
      const role = user.is_staff || user.is_superuser ? 'Admin / Staff' : 'Worker';
      userRoleDisplay.innerText = role;
    }

    // Role-based visibility adjustments
    const isStaff = api.isStaffOrAdmin();
    document.querySelectorAll('.staff-only').forEach(el => {
      el.style.display = isStaff ? '' : 'none';
    });
  }

  // Handle Login submission
  if (loginForm) {
    loginForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const username = document.getElementById('login-username').value.trim();
      const password = document.getElementById('login-password').value;
      const errorBanner = document.getElementById('login-error');

      if (!username || !password) {
        if (errorBanner) {
          errorBanner.innerText = 'Please enter both username and password.';
          errorBanner.style.display = 'block';
        }
        return;
      }

      try {
        if (errorBanner) errorBanner.style.display = 'none';
        const data = await api.login(username, password);
        updateUserUI(data.user);
        hideLoginModal();
        showToast('Login successful! Welcome to FarmSync.');
        switchView(currentView);
      } catch (err) {
        if (errorBanner) {
          errorBanner.innerText = err.message || 'Invalid credentials.';
          errorBanner.style.display = 'block';
        }
      }
    });
  }

  if (logoutBtn) {
    logoutBtn.addEventListener('click', async () => {
      await api.logout();
      showToast('Logged out successfully.');
    });
  }

  window.addEventListener('farmsync:unauthorized', () => {
    showLoginModal();
  });

  // =========================================================================
  // VIEW ROUTING
  // =========================================================================
  function switchView(viewName) {
    currentView = viewName;

    navLinks.forEach(link => {
      const parent = link.closest('li');
      if (link.dataset.view === viewName) {
        parent.classList.add('active');
      } else {
        parent.classList.remove('active');
      }
    });

    viewSections.forEach(section => {
      if (section.id === `${viewName}-view`) {
        section.classList.add('active');
      } else {
        section.classList.remove('active');
      }
    });

    // Update Header
    const titles = {
      dashboard: { title: 'Farm Dashboard', sub: 'Real-time farm metrics and operations summary' },
      farmers: { title: 'Workforce Roster', sub: 'Registered farmers and field assignments' },
      attendance: { title: 'Attendance Logging', sub: 'Daily check-in/out and shift duration tracking' },
      tasks: { title: 'Agricultural Tasks', sub: 'Field task assignments and status updates' },
      camera: { title: 'Live Camera & AI Detection', sub: 'Real-time hazard monitoring feed' },
      detection_logs: { title: 'Detection Logs', sub: 'Historical animal intrusion events and snapshots' },
      alerts: { title: 'Dispatched Hazard Alerts', sub: 'Read-only audit history of hazard notifications' },
      settings: { title: 'System Settings', sub: 'Dynamic parameters, detection thresholds, and email dispatch' }
    };

    if (titles[viewName]) {
      if (pageTitle) pageTitle.innerText = titles[viewName].title;
      if (pageSubtitle) pageSubtitle.innerText = titles[viewName].sub;
    }

    // Trigger view-specific data loader
    loadViewData(viewName);
  }

  navLinks.forEach(link => {
    link.addEventListener('click', (e) => {
      e.preventDefault();
      const view = link.dataset.view;
      if (view) switchView(view);
    });
  });

  function loadViewData(viewName) {
    if (!api.isAuthenticated()) return;

    switch (viewName) {
      case 'dashboard':
        loadDashboardData();
        break;
      case 'farmers':
        loadFarmersData();
        break;
      case 'attendance':
        loadAttendanceData();
        break;
      case 'tasks':
        loadTasksData();
        break;
      case 'camera':
        loadCameraData();
        break;
      case 'detection_logs':
        loadDetectionLogsData();
        break;
      case 'alerts':
        loadAlertsData();
        break;
      case 'settings':
        loadSettingsData();
        break;
    }
  }

  // =========================================================================
  // 1. DASHBOARD VIEW
  // =========================================================================
  async function loadDashboardData() {
    try {
      const summary = await api.getDashboardSummary();
      if (summary) {
        document.getElementById('stat-total-farmers').innerText = summary.total_farmers ?? 0;
        document.getElementById('stat-present-today').innerText = summary.present_today ?? 0;
        document.getElementById('stat-pending-tasks').innerText = summary.pending_tasks ?? 0;
        document.getElementById('stat-total-alerts').innerText = summary.total_alerts ?? 0;
      }

      const activity = await api.getDashboardActivity();
      const activityContainer = document.getElementById('dashboard-recent-activity');
      if (activityContainer) {
        if (!activity || (!activity.recent_detections?.length && !activity.recent_attendance?.length && !activity.recent_tasks?.length)) {
          activityContainer.innerHTML = '<div class="empty-state"><p>No recent activity recorded.</p></div>';
        } else {
          let html = '';
          (activity.recent_detections || []).slice(0, 5).forEach(det => {
            html += `
              <tr>
                <td><strong>Detection:</strong> ${escapeHtml(det.animal_type)} (${Math.round(det.confidence * 100)}%)</td>
                <td>${escapeHtml(det.field || 'Main Field')}</td>
                <td>${formatDate(det.timestamp)}</td>
              </tr>
            `;
          });
          activityContainer.innerHTML = html;
        }
      }
    } catch (e) {
      showToast(e.message, 'error');
    }
  }

  // =========================================================================
  // 2. FARMERS VIEW
  // =========================================================================
  async function loadFarmersData() {
    const tableBody = document.getElementById('farmers-table-body');
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Loading workforce...</td></tr>';

    try {
      const farmers = await api.getFarmers();
      cachedFarmers = farmers || [];
      renderFarmersTable(cachedFarmers);
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="5" class="empty-state" style="color:var(--danger);">Error loading farmers: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  function renderFarmersTable(farmers) {
    const tableBody = document.getElementById('farmers-table-body');
    if (!tableBody) return;

    if (!farmers || !farmers.length) {
      tableBody.innerHTML = '<tr><td colspan="5" class="empty-state"><p>No farmers registered yet.</p></td></tr>';
      return;
    }

    const isStaff = api.isStaffOrAdmin();
    tableBody.innerHTML = farmers.map(farmer => `
      <tr>
        <td>#${farmer.id}</td>
        <td><strong>${escapeHtml(farmer.name)}</strong></td>
        <td>${escapeHtml(farmer.field || 'General Field')}</td>
        <td>${escapeHtml(farmer.phone || 'N/A')}</td>
        <td>
          ${isStaff ? `
            <button class="btn btn-sm btn-outline" onclick="window.editFarmerPrompt(${farmer.id})">Edit</button>
            <button class="btn btn-sm btn-danger" onclick="window.deleteFarmerPrompt(${farmer.id})">Delete</button>
          ` : '<span class="badge badge-muted">View Only</span>'}
        </td>
      </tr>
    `).join('');
  }

  // Add Farmer Form
  const addFarmerForm = document.getElementById('add-farmer-form');
  if (addFarmerForm) {
    addFarmerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById('farmer-name').value.trim(),
        field: document.getElementById('farmer-field').value.trim(),
        phone: document.getElementById('farmer-phone').value.trim()
      };

      try {
        await api.createFarmer(payload);
        closeModal('add-farmer-modal');
        addFarmerForm.reset();
        showToast(`Farmer "${payload.name}" created successfully.`);
        loadFarmersData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  window.deleteFarmerPrompt = async function(id) {
    if (confirm(`Are you sure you want to remove farmer #${id}?`)) {
      try {
        await api.deleteFarmer(id);
        showToast('Farmer deleted successfully.');
        loadFarmersData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    }
  };

  window.editFarmerPrompt = function(id) {
    const farmer = cachedFarmers.find(f => f.id === id);
    if (!farmer) return;
    document.getElementById('edit-farmer-id').value = farmer.id;
    document.getElementById('edit-farmer-name').value = farmer.name;
    document.getElementById('edit-farmer-field').value = farmer.field || '';
    document.getElementById('edit-farmer-phone').value = farmer.phone || '';
    openModal('edit-farmer-modal');
  };

  const editFarmerForm = document.getElementById('edit-farmer-form');
  if (editFarmerForm) {
    editFarmerForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const id = document.getElementById('edit-farmer-id').value;
      const payload = {
        name: document.getElementById('edit-farmer-name').value.trim(),
        field: document.getElementById('edit-farmer-field').value.trim(),
        phone: document.getElementById('edit-farmer-phone').value.trim()
      };

      try {
        await api.updateFarmer(id, payload);
        closeModal('edit-farmer-modal');
        showToast('Farmer details updated successfully.');
        loadFarmersData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // =========================================================================
  // 3. ATTENDANCE VIEW
  // =========================================================================
  async function loadAttendanceData() {
    const tableBody = document.getElementById('attendance-table-body');
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Loading attendance records...</td></tr>';

    try {
      const records = await api.getAttendance();
      if (!records || !records.length) {
        tableBody.innerHTML = '<tr><td colspan="6" class="empty-state"><p>No attendance entries found.</p></td></tr>';
        return;
      }

      tableBody.innerHTML = records.map(rec => `
        <tr>
          <td><strong>${escapeHtml(rec.farmer_name || `Farmer #${rec.farmer}`)}</strong></td>
          <td>${formatDate(rec.date)}</td>
          <td>${formatTime(rec.check_in)}</td>
          <td>${rec.check_out ? formatTime(rec.check_out) : '<span class="badge badge-warning">Active Shift</span>'}</td>
          <td>${rec.total_hours !== null && rec.total_hours !== undefined ? `${rec.total_hours} hrs` : 'In Progress'}</td>
          <td>${escapeHtml(rec.device_location || 'Main Field')}</td>
        </tr>
      `).join('');
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="6" class="empty-state" style="color:var(--danger);">Error loading attendance: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  // Populate Farmers Dropdown in Check-In / Check-Out Modals
  window.openCheckInModal = async function() {
    const select = document.getElementById('checkin-farmer-select');
    if (!select) return;
    select.innerHTML = '<option value="">Loading farmers...</option>';
    try {
      const farmers = await api.getFarmers();
      select.innerHTML = farmers.map(f => `<option value="${f.id}">${escapeHtml(f.name)} (${escapeHtml(f.field || 'General')})</option>`).join('');
      openModal('checkin-modal');
    } catch (e) {
      showToast('Unable to load farmers list', 'error');
    }
  };

  window.openCheckOutModal = async function() {
    const select = document.getElementById('checkout-farmer-select');
    if (!select) return;
    select.innerHTML = '<option value="">Loading active shifts...</option>';
    try {
      const farmers = await api.getFarmers();
      select.innerHTML = farmers.map(f => `<option value="${f.id}">${escapeHtml(f.name)}</option>`).join('');
      openModal('checkout-modal');
    } catch (e) {
      showToast('Unable to load farmers list', 'error');
    }
  };

  const checkinForm = document.getElementById('checkin-form');
  if (checkinForm) {
    checkinForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const farmerId = document.getElementById('checkin-farmer-select').value;
      const location = document.getElementById('checkin-location').value.trim();

      try {
        await api.checkIn(farmerId, location);
        closeModal('checkin-modal');
        showToast('Farmer check-in recorded successfully.');
        loadAttendanceData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  const checkoutForm = document.getElementById('checkout-form');
  if (checkoutForm) {
    checkoutForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const farmerId = document.getElementById('checkout-farmer-select').value;
      const location = document.getElementById('checkout-location').value.trim();

      try {
        await api.checkOut(farmerId, location);
        closeModal('checkout-modal');
        showToast('Farmer check-out recorded successfully.');
        loadAttendanceData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Attendance Report Modal
  window.openAttendanceReportModal = async function() {
    const content = document.getElementById('attendance-report-content');
    if (!content) return;
    content.innerHTML = '<p>Generating attendance report...</p>';
    openModal('attendance-report-modal');

    try {
      const report = await api.getAttendanceReport();
      if (!report || !report.length) {
        content.innerHTML = '<p class="empty-state">No attendance records available for reporting.</p>';
        return;
      }

      content.innerHTML = `
        <table style="margin-top:10px;">
          <thead>
            <tr>
              <th>Farmer</th>
              <th>Total Days</th>
              <th>Total Hours</th>
            </tr>
          </thead>
          <tbody>
            ${report.map(r => `
              <tr>
                <td><strong>${escapeHtml(r.farmer_name)}</strong></td>
                <td>${r.total_days}</td>
                <td>${r.total_hours} hrs</td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      `;
    } catch (e) {
      content.innerHTML = `<p style="color:var(--danger);">${escapeHtml(e.message)}</p>`;
    }
  };

  // =========================================================================
  // 4. TASKS VIEW
  // =========================================================================
  async function loadTasksData() {
    const tableBody = document.getElementById('tasks-table-body');
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Loading tasks...</td></tr>';

    try {
      const tasks = await api.getTasks();
      if (!tasks || !tasks.length) {
        tableBody.innerHTML = '<tr><td colspan="5" class="empty-state"><p>No tasks currently scheduled.</p></td></tr>';
        return;
      }

      const isStaff = api.isStaffOrAdmin();
      tableBody.innerHTML = tasks.map(task => `
        <tr>
          <td><strong>${escapeHtml(task.task_name)}</strong></td>
          <td>${escapeHtml(task.farmer_name || `Farmer #${task.assigned_to}`)}</td>
          <td>
            <span class="badge ${task.status === 'Completed' ? 'badge-success' : 'badge-warning'}">
              ${escapeHtml(task.status)}
            </span>
          </td>
          <td>${formatDate(task.created_at)}</td>
          <td>
            ${isStaff ? `
              <button class="btn btn-sm btn-outline" onclick="window.toggleTaskStatus(${task.id}, '${task.status}')">
                Mark ${task.status === 'Completed' ? 'Pending' : 'Completed'}
              </button>
              <button class="btn btn-sm btn-danger" onclick="window.deleteTaskPrompt(${task.id})">Delete</button>
            ` : '<span class="badge badge-muted">View Only</span>'}
          </td>
        </tr>
      `).join('');
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="5" class="empty-state" style="color:var(--danger);">Error loading tasks: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  window.openCreateTaskModal = async function() {
    const select = document.getElementById('task-assigned-farmer');
    if (select) {
      const farmers = await api.getFarmers();
      select.innerHTML = farmers.map(f => `<option value="${f.id}">${escapeHtml(f.name)}</option>`).join('');
    }
    openModal('create-task-modal');
  };

  const createTaskForm = document.getElementById('create-task-form');
  if (createTaskForm) {
    createTaskForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        task_name: document.getElementById('task-name-input').value.trim(),
        assigned_to: document.getElementById('task-assigned-farmer').value,
        status: document.getElementById('task-status-input').value
      };

      try {
        await api.createTask(payload);
        closeModal('create-task-modal');
        createTaskForm.reset();
        showToast('Task created successfully.');
        loadTasksData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  window.toggleTaskStatus = async function(id, currentStatus) {
    const newStatus = currentStatus === 'Completed' ? 'Pending' : 'Completed';
    try {
      await api.updateTask(id, { status: newStatus });
      showToast(`Task status updated to ${newStatus}.`);
      loadTasksData();
    } catch (err) {
      showToast(err.message, 'error');
    }
  };

  window.deleteTaskPrompt = async function(id) {
    if (confirm(`Are you sure you want to delete task #${id}?`)) {
      try {
        await api.deleteTask(id);
        showToast('Task deleted successfully.');
        loadTasksData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    }
  };

  // =========================================================================
  // 5. CAMERA & LIVE MONITORING VIEW
  // =========================================================================
  async function loadCameraData() {
    const streamImg = document.getElementById('camera-stream-img');
    const statusPill = document.getElementById('detection-status-pill');
    const toggleBtn = document.getElementById('detection-toggle-btn');

    if (streamImg) {
      streamImg.src = api.getStreamUrl();
    }

    try {
      const statusData = await api.getDetectionStatus();
      if (statusData) {
        updateDetectionUI(statusData);
      }
    } catch (e) {
      // Non-blocking
    }
  }

  function updateDetectionUI(statusData) {
    const statusPill = document.getElementById('detection-status-pill');
    const toggleBtn = document.getElementById('detection-toggle-btn');

    if (statusPill) {
      if (statusData.detection_enabled) {
        statusPill.className = 'badge badge-success';
        statusPill.innerText = 'AI Detection: ACTIVE';
      } else {
        statusPill.className = 'badge badge-danger';
        statusPill.innerText = 'AI Detection: DISABLED';
      }
    }

    if (toggleBtn) {
      toggleBtn.innerText = statusData.detection_enabled ? 'Disable AI Detection' : 'Enable AI Detection';
      toggleBtn.className = `btn ${statusData.detection_enabled ? 'btn-danger' : 'btn-primary'}`;
      toggleBtn.onclick = async () => {
        try {
          const updated = await api.toggleDetection(!statusData.detection_enabled);
          updateDetectionUI(updated);
          showToast(`AI Detection ${updated.detection_enabled ? 'enabled' : 'disabled'}.`);
        } catch (err) {
          showToast(err.message, 'error');
        }
      };
    }
  }

  // Manual Snapshot Image Analysis
  const analyzeForm = document.getElementById('snapshot-analyze-form');
  if (analyzeForm) {
    analyzeForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const fileInput = document.getElementById('snapshot-file');
      const fieldInput = document.getElementById('snapshot-field');
      const resultCard = document.getElementById('snapshot-analysis-result');

      if (!fileInput.files || !fileInput.files[0]) {
        showToast('Please select an image file to analyze.', 'warning');
        return;
      }

      try {
        resultCard.innerHTML = '<p>Analyzing image with YOLOv8...</p>';
        resultCard.style.display = 'block';

        const result = await api.analyzeImage(fileInput.files[0], fieldInput.value.trim());
        resultCard.innerHTML = `
          <div class="glass-panel" style="padding:18px; margin-top:15px;">
            <h4>Analysis Result:</h4>
            <p><strong>Detections Count:</strong> ${result.detections_count}</p>
            <p><strong>Highest Threat:</strong> ${result.highest_threat_animal || 'None'} (${result.highest_threat_level || 'low'})</p>
            <p><strong>Confidence:</strong> ${result.highest_confidence ? Math.round(result.highest_confidence * 100) + '%' : 'N/A'}</p>
            <p><strong>Alert Triggered:</strong> ${result.alert_triggered ? `<span class="badge badge-danger">${result.alert_type}</span>` : '<span class="badge badge-muted">No</span>'}</p>
          </div>
        `;
        showToast('Image analysis complete!');
      } catch (err) {
        resultCard.innerHTML = `<p style="color:var(--danger);">${escapeHtml(err.message)}</p>`;
        showToast(err.message, 'error');
      }
    });
  }

  // =========================================================================
  // 6. DETECTION LOGS VIEW
  // =========================================================================
  async function loadDetectionLogsData() {
    const tableBody = document.getElementById('detection-logs-table-body');
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">Loading detection history...</td></tr>';

    try {
      const logs = await api.getDetectionLogs();
      if (!logs || !logs.length) {
        tableBody.innerHTML = '<tr><td colspan="5" class="empty-state"><p>No animal intrusions logged.</p></td></tr>';
        return;
      }

      tableBody.innerHTML = logs.map(log => `
        <tr>
          <td><strong>${escapeHtml(capitalize(log.animal_type))}</strong></td>
          <td>${Math.round(log.confidence * 100)}%</td>
          <td>${escapeHtml(log.field || 'Main Field')}</td>
          <td>${formatDate(log.timestamp)}</td>
          <td>
            ${log.image_path ? `<a href="/${log.image_path}" target="_blank" class="btn btn-sm btn-outline">View Snapshot</a>` : '<span class="badge badge-muted">No Image</span>'}
          </td>
        </tr>
      `).join('');
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="5" class="empty-state" style="color:var(--danger);">Error loading logs: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  // =========================================================================
  // 7. ALERTS VIEW (READ-ONLY AUDIT)
  // =========================================================================
  async function loadAlertsData() {
    const tableBody = document.getElementById('alerts-table-body');
    if (!tableBody) return;
    tableBody.innerHTML = '<tr><td colspan="6" style="text-align:center;">Loading alert history...</td></tr>';

    try {
      const alerts = await api.getAlerts();
      if (!alerts || !alerts.length) {
        tableBody.innerHTML = '<tr><td colspan="6" class="empty-state"><p>No hazard alerts recorded.</p></td></tr>';
        return;
      }

      tableBody.innerHTML = alerts.map(alert => `
        <tr>
          <td>#${alert.id}</td>
          <td>
            <span class="badge ${alert.alert_type === 'Email + Buzzer' ? 'badge-danger' : alert.alert_type === 'Email' ? 'badge-warning' : 'badge-info'}">
              ${escapeHtml(alert.alert_type)}
            </span>
          </td>
          <td><span class="badge badge-success">${escapeHtml(alert.status)}</span></td>
          <td>${escapeHtml(alert.animal_type ? `${capitalize(alert.animal_type)} (${Math.round((alert.confidence || 0) * 100)}%)` : 'N/A')}</td>
          <td>${escapeHtml(alert.field || 'Main Field')}</td>
          <td>${formatDate(alert.created_at)}</td>
        </tr>
      `).join('');
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="6" class="empty-state" style="color:var(--danger);">Error loading alerts: ${escapeHtml(e.message)}</td></tr>`;
    }
  }

  // =========================================================================
  // 8. SETTINGS VIEW
  // =========================================================================
  async function loadSettingsData() {
    try {
      // 1. Project Settings
      const settings = await api.getSettings();
      if (settings) {
        document.getElementById('settings-system-name').value = settings.system_name || '';
        document.getElementById('settings-confidence-threshold').value = settings.detection_confidence_threshold || 0.50;
        document.getElementById('settings-cooldown-seconds').value = settings.alert_cooldown_seconds || 60;
        document.getElementById('settings-camera-device-index').value = settings.camera_device_index || 0;
        document.getElementById('settings-wage-per-hour').value = settings.wage_per_hour || 15.0;
        document.getElementById('settings-detection-enabled').checked = !!settings.detection_enabled;
        document.getElementById('settings-buzzer-enabled').checked = !!settings.audio_buzzer_enabled;
        document.getElementById('settings-email-alerts-enabled').checked = !!settings.email_alerts_enabled;
      }

      // 2. Email Sender Status
      if (api.isStaffOrAdmin()) {
        const sender = await api.getEmailSender();
        if (sender) {
          document.getElementById('sender-name-input').value = sender.sender_name || '';
          document.getElementById('sender-email-input').value = sender.sender_email || '';
          document.getElementById('smtp-host-input').value = sender.smtp_host || '';
          document.getElementById('smtp-port-input').value = sender.smtp_port || 587;
          document.getElementById('smtp-username-input').value = sender.smtp_username || '';
          document.getElementById('smtp-password-configured-badge').innerText = sender.smtp_password_configured ? 'Password Configured' : 'No Password Stored';
        }
      }

      // 3. Receivers List
      loadReceiversTable();
    } catch (e) {
      showToast(e.message, 'error');
    }
  }

  // Update Project Settings Form
  const projectSettingsForm = document.getElementById('project-settings-form');
  if (projectSettingsForm) {
    projectSettingsForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        system_name: document.getElementById('settings-system-name').value.trim(),
        detection_confidence_threshold: parseFloat(document.getElementById('settings-confidence-threshold').value),
        alert_cooldown_seconds: parseInt(document.getElementById('settings-cooldown-seconds').value, 10),
        camera_device_index: parseInt(document.getElementById('settings-camera-device-index').value, 10),
        wage_per_hour: parseFloat(document.getElementById('settings-wage-per-hour').value),
        detection_enabled: document.getElementById('settings-detection-enabled').checked,
        audio_buzzer_enabled: document.getElementById('settings-buzzer-enabled').checked,
        email_alerts_enabled: document.getElementById('settings-email-alerts-enabled').checked
      };

      try {
        await api.updateSettings(payload);
        showToast('Project settings updated successfully.');
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  // Update Email Sender Form
  const emailSenderForm = document.getElementById('email-sender-form');
  if (emailSenderForm) {
    emailSenderForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const password = document.getElementById('smtp-password-input').value;
      const payload = {
        sender_name: document.getElementById('sender-name-input').value.trim(),
        sender_email: document.getElementById('sender-email-input').value.trim(),
        smtp_host: document.getElementById('smtp-host-input').value.trim(),
        smtp_port: parseInt(document.getElementById('smtp-port-input').value, 10),
        smtp_username: document.getElementById('smtp-username-input').value.trim()
      };
      if (password && password.trim()) {
        payload.smtp_password = password.trim();
      }

      try {
        await api.updateEmailSender(payload);
        document.getElementById('smtp-password-input').value = '';
        showToast('Email sender configuration updated.');
        loadSettingsData();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  async function loadReceiversTable() {
    const tableBody = document.getElementById('receivers-table-body');
    if (!tableBody) return;

    try {
      const receivers = await api.getReceivers();
      if (!receivers || !receivers.length) {
        tableBody.innerHTML = '<tr><td colspan="4" class="empty-state"><p>No alert recipients registered.</p></td></tr>';
        return;
      }

      const isStaff = api.isStaffOrAdmin();
      tableBody.innerHTML = receivers.map(rec => `
        <tr>
          <td><strong>${escapeHtml(rec.name)}</strong></td>
          <td>${escapeHtml(rec.email)}</td>
          <td><span class="badge ${rec.is_active ? 'badge-success' : 'badge-danger'}">${rec.is_active ? 'Active' : 'Disabled'}</span></td>
          <td>
            ${isStaff ? `<button class="btn btn-sm btn-danger" onclick="window.deleteReceiverPrompt(${rec.id})">Delete</button>` : '<span class="badge badge-muted">View Only</span>'}
          </td>
        </tr>
      `).join('');
    } catch (e) {
      tableBody.innerHTML = `<tr><td colspan="4" class="empty-state" style="color:var(--danger);">${escapeHtml(e.message)}</td></tr>`;
    }
  }

  window.openAddReceiverModal = function() {
    openModal('add-receiver-modal');
  };

  const addReceiverForm = document.getElementById('add-receiver-form');
  if (addReceiverForm) {
    addReceiverForm.addEventListener('submit', async (e) => {
      e.preventDefault();
      const payload = {
        name: document.getElementById('receiver-name').value.trim(),
        email: document.getElementById('receiver-email').value.trim(),
        is_active: document.getElementById('receiver-active').checked
      };

      try {
        await api.createReceiver(payload);
        closeModal('add-receiver-modal');
        addReceiverForm.reset();
        showToast('Alert recipient registered.');
        loadReceiversTable();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }

  window.deleteReceiverPrompt = async function(id) {
    if (confirm(`Remove alert recipient #${id}?`)) {
      try {
        await api.deleteReceiver(id);
        showToast('Alert recipient removed.');
        loadReceiversTable();
      } catch (err) {
        showToast(err.message, 'error');
      }
    }
  };

  // =========================================================================
  // HELPER UTILITIES
  // =========================================================================
  function escapeHtml(str) {
    if (!str) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }

  function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
  }

  function formatDate(dateStr) {
    if (!dateStr) return 'N/A';
    const d = new Date(dateStr);
    return isNaN(d.getTime()) ? dateStr : d.toLocaleDateString() + ' ' + d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  function formatTime(timeStr) {
    if (!timeStr) return 'N/A';
    const d = new Date(timeStr);
    return isNaN(d.getTime()) ? timeStr : d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }

  // Initialize App
  checkAuthAndInit();
});
