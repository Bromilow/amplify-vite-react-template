document.addEventListener('DOMContentLoaded', () => {
  const rows = document.querySelectorAll('[data-index]');
  const importAllBtn = document.getElementById('importAllBtn');
  const editModalEl = document.getElementById('importEditModal');
  const editForm = document.getElementById('importEditForm');
  let currentIndex = null;

  function updateImportButton() {
    const allReviewed = Array.from(rows).every(r => r.querySelector('input[name^="status_"]').value !== 'pending');
    importAllBtn.disabled = !allReviewed;
  }

  rows.forEach(card => {
    const index = card.getAttribute('data-index');
    card.querySelector('.confirm-row').addEventListener('click', () => {
      card.querySelector('#status-' + index).textContent = '✅ Confirmed';
      card.querySelector('#status-' + index).className = 'status-badge badge bg-success';
      document.getElementById('input-status-' + index).value = 'confirmed';
      updateImportButton();
    });
    card.querySelector('.skip-row').addEventListener('click', () => {
      card.querySelector('#status-' + index).textContent = '❌ Skipped';
      card.querySelector('#status-' + index).className = 'status-badge badge bg-warning';
      document.getElementById('input-status-' + index).value = 'skipped';
      updateImportButton();
    });
    card.querySelector('.delete-row').addEventListener('click', () => {
      card.remove();
      updateImportButton();
    });
    card.querySelector('.edit-row').addEventListener('click', () => {
      currentIndex = index;
      loadRowData(index);
      const modal = new bootstrap.Modal(editModalEl);
      modal.show();
    });
  });

  function loadRowData(index) {
    document.getElementById('editRowIndex').value = index;
    const getVal = f => document.getElementById(`row-${index}-${f}`).value;
    document.getElementById('edit_first_name').value = getVal('first_name');
    document.getElementById('edit_last_name').value = getVal('last_name');
    document.getElementById('edit_id_number').value = getVal('id_number');
    document.getElementById('edit_cell_number').value = getVal('cell_number');
    document.getElementById('edit_department').value = getVal('department');
    document.getElementById('edit_job_title').value = getVal('job_title');
    document.getElementById('edit_start_date').value = getVal('start_date');
    document.getElementById('edit_salary_type').value = getVal('salary_type');
    document.getElementById('edit_monthly_salary').value = getVal('monthly_salary');
    document.getElementById('edit_hourly_rate').value = getVal('hourly_rate');
    document.getElementById('edit_bank_name').value = getVal('bank_name');
    document.getElementById('edit_account_number').value = getVal('account_number');
    document.getElementById('edit_account_type').value = getVal('account_type');
    document.getElementById('edit_annual_leave_days').value = getVal('annual_leave_days');
    toggleSalaryFields();
  }

  function toggleSalaryFields() {
    const type = document.getElementById('edit_salary_type').value;
    document.getElementById('monthlyField').style.display = type === 'monthly' ? 'block' : 'none';
    document.getElementById('hourlyField').style.display = type === 'hourly' ? 'block' : 'none';
  }

  document.getElementById('edit_salary_type').addEventListener('change', toggleSalaryFields);

  editForm.addEventListener('submit', e => {
    e.preventDefault();
    const idx = document.getElementById('editRowIndex').value;
    const setVal = (f, val) => document.getElementById(`row-${idx}-${f}`).value = val;
    setVal('first_name', document.getElementById('edit_first_name').value);
    setVal('last_name', document.getElementById('edit_last_name').value);
    setVal('id_number', document.getElementById('edit_id_number').value);
    setVal('cell_number', document.getElementById('edit_cell_number').value);
    setVal('department', document.getElementById('edit_department').value);
    setVal('job_title', document.getElementById('edit_job_title').value);
    setVal('start_date', document.getElementById('edit_start_date').value);
    setVal('salary_type', document.getElementById('edit_salary_type').value);
    setVal('monthly_salary', document.getElementById('edit_monthly_salary').value);
    setVal('hourly_rate', document.getElementById('edit_hourly_rate').value);
    setVal('bank_name', document.getElementById('edit_bank_name').value);
    setVal('account_number', document.getElementById('edit_account_number').value);
    setVal('account_type', document.getElementById('edit_account_type').value);
    setVal('annual_leave_days', document.getElementById('edit_annual_leave_days').value);
    const modal = bootstrap.Modal.getInstance(editModalEl);
    modal.hide();
  });
});
