/**
 * Shared Employee Modal JavaScript
 * Handles Edit Employee modal population and functionality
 */

// Get CSRF token from meta tag (assumed to be present in base template)
const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : null;

// Debug CSRF token
console.log('CSRF token found:', csrfToken ? 'Yes' : 'No');

// ----- Modal Utility Helpers -----


function validateAndExtractFromEditId() {
    const idInput = document.getElementById('edit_id_number');
    const dobInput = document.getElementById('edit_date_of_birth');
    const genderSelect = document.getElementById('edit_gender');

    if (!idInput || !dobInput || !genderSelect) return;

    const idNumber = idInput.value.replace(/\s/g, '');

    if (idNumber.length === 13 && /^\d{13}$/.test(idNumber)) {
        const year = parseInt(idNumber.substring(0, 2));
        const month = parseInt(idNumber.substring(2, 4));
        const day = parseInt(idNumber.substring(4, 6));

        const fullYear = year <= 24 ? 2000 + year : 1900 + year;

        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            const dobString = `${fullYear}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            dobInput.value = dobString;

            const genderDigit = parseInt(idNumber.substring(6, 10));
            if (genderDigit >= 0 && genderDigit <= 4999) {
                genderSelect.value = 'Female';
            } else if (genderDigit >= 5000 && genderDigit <= 9999) {
                genderSelect.value = 'Male';
            }

            idInput.classList.remove('is-invalid');
            idInput.classList.add('is-valid');
        } else {
            idInput.classList.remove('is-valid');
            idInput.classList.add('is-invalid');
        }
    } else {
        idInput.classList.remove('is-valid');
        if (idNumber.length > 0) {
            idInput.classList.add('is-invalid');
        }
    }
}

async function populateEditDepartmentDropdown(selectedDepartment) {
    try {
        const departmentSelect = document.getElementById('edit_department');
        const customDeptGroup = document.getElementById('edit_custom_department_group');
        const customDeptInput = document.getElementById('edit_custom_department');
        
        if (!departmentSelect) return;

        // Fetch company departments from the server
        const response = await fetch('/company/api/departments', {
            method: 'GET',
            headers: {
                'X-Requested-With': 'XMLHttpRequest'
            }
        });
        
        if (response.ok) {
            const data = await response.json();
            const departments = data.departments || [];
            
            // Clear existing options (except the default and Other option)
            departmentSelect.innerHTML = '<option value="">Choose department...</option>';
            
            // Add department options
            departments.forEach(dept => {
                const option = document.createElement('option');
                option.value = dept;
                option.textContent = dept;
                departmentSelect.appendChild(option);
            });
            
            // Add "Other" option at the end
            const otherOption = document.createElement('option');
            otherOption.value = 'Other';
            otherOption.textContent = 'Other (specify below)';
            departmentSelect.appendChild(otherOption);
            
            // Set the selected department
            if (selectedDepartment) {
                // Check if the department exists in the dropdown
                const existingOption = Array.from(departmentSelect.options).find(option => option.value === selectedDepartment);
                
                if (existingOption) {
                    departmentSelect.value = selectedDepartment;
                } else {
                    // Department is a custom one, select "Other" and populate custom field
                    departmentSelect.value = 'Other';
                    if (customDeptGroup && customDeptInput) {
                        customDeptGroup.style.display = 'block';
                        customDeptInput.value = selectedDepartment;
                        customDeptInput.required = true;
                    }
                }
            }
        } else {
            console.error('Failed to fetch departments');
            // Fallback: just set the value if the dropdown is already populated
            if (selectedDepartment) {
                departmentSelect.value = selectedDepartment;
            }
        }
    } catch (error) {
        console.error('Error populating department dropdown:', error);
        // Fallback: just set the value
        const departmentSelect = document.getElementById('edit_department');
        if (departmentSelect && selectedDepartment) {
            departmentSelect.value = selectedDepartment;
        }
    }
}

async function populateEditModal(employee) {
    console.log('Starting populateEditModal with data:', employee);
    
    try {
        // Hide loading state and show content
        document.getElementById('editModalLoading').style.display = 'none';
        document.getElementById('editModalContent').style.display = 'block';
        
        // Set employee ID on form for AJAX submission
        const editForm = document.getElementById('editEmployeeForm');
        if (editForm) {
            editForm.setAttribute('data-employee-id', employee.id);
        }
        
        // Personal Information
        console.log('Populating field: first_name', employee.first_name);
        document.getElementById('edit_first_name').value = employee.first_name || '';
        console.log('Populating field: last_name', employee.last_name);
        document.getElementById('edit_last_name').value = employee.last_name || '';
        console.log('Populating field: employee_id', employee.employee_id);
        document.getElementById('edit_employee_id').value = employee.employee_id || '';
        // Handle identification type and conditional fields
        console.log('Populating field: identification_type', employee.identification_type);
        const identificationTypeSelect = document.getElementById('edit_identification_type');
        if (identificationTypeSelect) {
            identificationTypeSelect.value = employee.identification_type || 'sa_id';
            
            // Trigger change event to show/hide appropriate fields
            const changeEvent = new Event('change');
            identificationTypeSelect.dispatchEvent(changeEvent);
        }
        
        console.log('Populating field: id_number', employee.id_number);
        document.getElementById('edit_id_number').value = employee.id_number || '';
        
        console.log('Populating field: passport_number', employee.passport_number);
        const passportField = document.getElementById('edit_passport_number');
        if (passportField) {
            passportField.value = employee.passport_number || '';
        }
        console.log('Populating field: tax_number', employee.tax_number);
        document.getElementById('edit_tax_number').value = employee.tax_number || '';
        console.log('Populating field: cell_number', employee.cell_number);
        document.getElementById('edit_cell_number').value = employee.cell_number || '';
        console.log('Populating field: email', employee.email);
        document.getElementById('edit_email').value = employee.email || '';
        console.log('Populating field: date_of_birth', employee.date_of_birth);
        document.getElementById('edit_date_of_birth').value = employee.date_of_birth || '';
        console.log('Populating field: gender', employee.gender);
        document.getElementById('edit_gender').value = employee.gender || '';
        console.log('Populating field: marital_status', employee.marital_status);
        document.getElementById('edit_marital_status').value = employee.marital_status || '';
        console.log('Populating field: physical_address', employee.physical_address);
        document.getElementById('edit_physical_address').value = employee.physical_address || '';
        
        // Employment Information
        console.log('Populating field: department', employee.department);
        await populateEditDepartmentDropdown(employee.department);
        console.log('Populating field: job_title', employee.job_title);
        document.getElementById('edit_job_title').value = employee.job_title || '';
        console.log('Populating field: start_date', employee.start_date);
        document.getElementById('edit_start_date').value = employee.start_date || '';
        console.log('Populating field: employment_type', employee.employment_type);
        document.getElementById('edit_employment_type').value = employee.employment_type || '';
        console.log('Populating field: employment_status', employee.employment_status);
        document.getElementById('edit_employment_status').value = employee.employment_status || '';
        console.log('Populating field: end_date', employee.end_date);
        document.getElementById('edit_end_date').value = employee.end_date || '';
        console.log('Populating field: reporting_manager', employee.reporting_manager);
        document.getElementById('edit_reporting_manager').value = employee.reporting_manager || '';
        
        
        // Compensation
        console.log('Populating field: salary_type', employee.salary_type);
        document.getElementById('edit_salary_type').value = employee.salary_type || '';
        console.log('Populating field: salary', employee.salary);
        document.getElementById('edit_salary').value = employee.salary || '';
        console.log('Populating field: overtime_eligible', employee.overtime_eligible);
        document.getElementById('edit_overtime_eligible').checked = employee.overtime_eligible || false;
        const methodSelect = document.getElementById('edit_overtime_calc_method');
        if (methodSelect) methodSelect.value = employee.overtime_calc_method || 'per_hour';
        console.log('Populating field: ordinary_hours_per_day', employee.ordinary_hours_per_day);
        const ohpdInput = document.getElementById('edit_ordinary_hours_per_day');
        if (ohpdInput) ohpdInput.value = employee.ordinary_hours_per_day || '';
        console.log('Populating field: work_days_per_month', employee.work_days_per_month);
        const wdpmInput = document.getElementById('edit_work_days_per_month');
        if (wdpmInput) wdpmInput.value = employee.work_days_per_month || '';
        const derivedInput = document.getElementById('edit_derived_hourly_rate');
        if (derivedInput) {
            let val = 0;
            if (employee.salary_type === 'hourly') val = employee.salary;
            else if (employee.salary_type === 'daily') val = employee.salary / (employee.ordinary_hours_per_day || 8);
            else val = employee.salary / ((employee.ordinary_hours_per_day || 8) * (employee.work_days_per_month || 22));
            derivedInput.value = val.toFixed(2);
        }

        // Ensure dynamic labels and fields reflect the loaded salary data
        if (typeof updateEditSalaryLabels === 'function') {
            updateEditSalaryLabels();
        }
        if (typeof updateEditOvertimeMethodFields === 'function') {
            updateEditOvertimeMethodFields();
        }
        if (typeof toggleEditOvertimeFields === 'function') {
            toggleEditOvertimeFields();
        }
        if (typeof updateEditDerivedHourly === 'function') {
            updateEditDerivedHourly();
        }
        console.log('Populating field: allowances', employee.allowances);
        document.getElementById('edit_allowances').value = employee.allowances || '';
        console.log('Populating field: bonus_type', employee.bonus_type);
        document.getElementById('edit_bonus_type').value = employee.bonus_type || '';
        
        // Statutory Deductions
        console.log('Populating field: uif_contributing', employee.uif_contributing);
        document.getElementById('edit_uif_contributing').checked = employee.uif_contributing || false;
        console.log('Populating field: sdl_contributing', employee.sdl_contributing);
        document.getElementById('edit_sdl_contributing').checked = employee.sdl_contributing || false;
        console.log('Populating field: paye_exempt', employee.paye_exempt);
        document.getElementById('edit_paye_exempt').checked = employee.paye_exempt || false;
        
        
        // Banking Information
        console.log('Populating field: bank_name', employee.bank_name);
        document.getElementById('edit_bank_name').value = employee.bank_name || '';
        console.log('Populating field: account_number', employee.account_number);
        document.getElementById('edit_account_number').value = employee.account_number || '';
        console.log('Populating field: account_type', employee.account_type);
        document.getElementById('edit_account_type').value = employee.account_type || '';
        console.log('Populating field: annual_leave_days', employee.annual_leave_days);
        document.getElementById('edit_annual_leave_days').value = employee.annual_leave_days || '';
        
        // Populate Recurring Deductions
        console.log('Populating recurring deductions:', employee.recurring_deductions);
        if (employee.recurring_deductions && employee.recurring_deductions.length > 0) {
            // Enable the customize deductions toggle if present
            const customizeCheckbox = document.getElementById('edit_customize_deductions');
            if (customizeCheckbox) {
                customizeCheckbox.checked = true;
            }
            
            // Show the deductions details section if present
            const deductionsDetails = document.getElementById('edit_recurring_deductions_details');
            if (deductionsDetails) {
                deductionsDetails.style.display = 'block';
            }
            
            // Clear existing table rows
            const tbody = document.getElementById('edit_deductions_tbody');
            if (tbody) {
                tbody.innerHTML = '';
            }
            
            // Populate deductions table
            employee.recurring_deductions.forEach((deduction, index) => {
                // `deduction_type` maps to beneficiary type in the backend
                const typeLabel = deduction.deduction_type || deduction.beneficiary_type || '';

                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>
                        <strong>${deduction.beneficiary_name}</strong>
                        <input type="hidden" name="deduction_beneficiary_id[]" value="${deduction.beneficiary_id}">
                    </td>
                    <td>
                        <span class="badge bg-secondary">${typeLabel}</span>
                    </td>
                    <td>
                        <select class="form-select form-select-sm" name="deduction_amount_type[]" onchange="updateEditDeductionValueField(this)">
                            <option value="fixed" ${deduction.amount_type === 'Fixed' || deduction.amount_type === 'fixed' ? 'selected' : ''}>Fixed Amount</option>
                            <option value="percent" ${deduction.amount_type === 'Percentage' || deduction.amount_type === 'percent' ? 'selected' : ''}>Percentage</option>
                            ${typeLabel === 'Medical Aid' ? `<option value="calculated" ${deduction.amount_type === 'Calculated' || deduction.amount_type === 'calculated' ? 'selected' : ''}>Calculated</option>` : ''}
                        </select>
                    </td>
                    <td>
                        <div class="d-flex align-items-center">
                            <div class="input-group input-group-sm flex-grow-1">
                                <span class="input-group-text deduction-prefix">${(deduction.amount_type === 'Percentage' || deduction.amount_type === 'percent') ? '%' : 'R'}</span>
                                <input type="number"
                                       class="form-control"
                                       name="deduction_value[]"
                                       value="${(deduction.amount_type === 'Calculated' || deduction.amount_type === 'calculated') ? '' : (deduction.value || 0.00)}"
                                       step="0.01"
                                       min="0"
                                       placeholder="${(deduction.amount_type === 'Calculated' || deduction.amount_type === 'calculated') ? 'Auto-calculated' : '0.00'}"
                                       ${deduction.amount_type === 'Calculated' || deduction.amount_type === 'calculated' ? 'disabled title="This deduction will be automatically calculated using the employee\u2019s Medical Aid information"' : ''}>
                            </div>
                            <button type="button" class="btn btn-outline-danger btn-sm ms-2" onclick="removeEditDeductionRow(this)" title="Remove this deduction">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                    </td>
                `;
                if (tbody) {
                    tbody.appendChild(row);
                    const select = row.querySelector('select[name="deduction_amount_type[]"]');
                    if (select) updateEditDeductionValueField(select);
                }
            });
        }
        
        // Store beneficiaries data for adding new deductions
        if (employee.beneficiaries) {
            window.editModalBeneficiaries = employee.beneficiaries;
        }
        
        // Update form action
        console.log('Setting form action for employee ID:', employee.id);
        const form = document.getElementById('editEmployeeForm');
        form.action = `/employees/${employee.id}/edit`;
        
        console.log('Modal populated successfully with recurring deductions');
        
        // Apply identification type toggle after all fields are populated
        toggleEditIdentificationFields();
        
    } catch (error) {
        console.error('Error populating modal:', error);
        alert('Error loading employee data into form. Please try again.');
        
        // Show error in modal
        document.getElementById('editModalLoading').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle me-2"></i>
                Error loading employee data. Please close and try again.
            </div>
        `;
    }
}

// Initialize shared modal event handlers
function initializeEmployeeModal() {
    console.log('Initializing shared employee modal system');
    
    // Delegated event listener for edit employee buttons
    document.addEventListener('click', function(event) {
        if (event.target.closest('.edit-employee-btn')) {
            console.log('Edit Employee button clicked');
            event.preventDefault();
            
            const button = event.target.closest('.edit-employee-btn');
            const employeeId = button.getAttribute('data-employee-id');
            
            console.log('Employee ID:', employeeId);
            
            if (!employeeId) {
                console.error('No employee ID found on button');
                return;
            }
            
            // Show loading spinner
            const originalContent = button.innerHTML;
            button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
            button.disabled = true;
            
            console.log('Fetching employee data from API...');
            console.log('API URL:', `/employees/${employeeId}/api`);
            
            // Fetch employee data
            fetch(`/employees/${employeeId}/api`, {
                method: 'GET',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            })
                .then(response => {
                    console.log('API Response status:', response.status);
                    console.log('API Response ok:', response.ok);
                    console.log('API Response headers:', response.headers);
                    
                    if (!response.ok) {
                        // Log response text for debugging
                        return response.text().then(text => {
                            console.error('API Response text:', text);
                            throw new Error(`HTTP error! status: ${response.status} - ${text}`);
                        });
                    }
                    return response.json();
                })
                .then(data => {
                    console.log('Employee data received:', data);
                    
                    // Check if data has error property
                    if (data.error) {
                        throw new Error(`API Error: ${data.error}`);
                    }
                    
                    // Show modal first
                    const modal = new bootstrap.Modal(document.getElementById('editEmployeeModal'));
                    modal.show();
                    
                    // Populate modal fields after modal is shown
                    setTimeout(() => {
                        populateEditModal(data);
                    }, 100);
                    
                    console.log('Modal opened successfully');
                })
                .catch(error => {
                    console.error('Error loading employee data:', error);
                    console.error('Error stack:', error.stack);
                    alert('Failed to load employee data. Please try again.');
                })
                .finally(() => {
                    // Restore button
                    button.innerHTML = originalContent;
                    button.disabled = false;
                });
        }
    });
}

// Handle Edit Employee form submission via AJAX
function handleEditEmployeeFormSubmission() {
    const editForm = document.getElementById('editEmployeeForm');
    if (!editForm) return;
    
    editForm.addEventListener('submit', function(event) {
        event.preventDefault();
        console.log('Edit Employee form submitted via AJAX');
        
        const formData = new FormData(editForm);
        const employeeId = editForm.getAttribute('data-employee-id');
        
        if (!employeeId) {
            console.error('No employee ID found on form');
            return;
        }
        
        // Show loading state
        const submitButton = editForm.querySelector('#editSaveBtn');
        const btnText = submitButton.querySelector('#editSaveBtnText');
        const btnSpinner = submitButton.querySelector('#editSaveBtnSpinner');

        btnText.classList.add('d-none');
        btnSpinner.classList.remove('d-none');
        submitButton.disabled = true;
        
        // Clear previous error messages
        const errorAlerts = editForm.querySelectorAll('.alert-danger');
        errorAlerts.forEach(alert => alert.remove());
        
        // Submit form via AJAX
        fetch(`/employees/${employeeId}/edit`, {
            method: 'POST',
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: formData
        })
        .then(response => {
            console.log('Form submission response status:', response.status);
            console.log('Response headers:', response.headers);
            console.log('Response ok:', response.ok);
            
            // Check if response is JSON
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                console.error('Response is not JSON:', contentType);
                throw new Error(`Expected JSON response, got ${contentType}`);
            }
            
            return response.json();
        })
        .then(data => {
            console.log('Form submission response:', data);
            
            if (data.success) {
                // Success - show message and handle redirect based on current page
                console.log('Employee updated successfully');
                
                // Close modal
                const modal = bootstrap.Modal.getInstance(document.getElementById('editEmployeeModal'));
                modal.hide();
                
                // Show success message
                showFlashMessage(data.message, 'success');
                
                // Determine redirect behavior based on current page
                const currentPath = window.location.pathname;
                console.log('Current path:', currentPath);
                
                if (currentPath === '/employees' || currentPath === '/employees/') {
                    // If on employees list page, refresh only the employee row instead of full page
                    console.log('Refreshing employee data in employees list');
                    refreshEmployeeRow(data.employee_id);
                } else if (currentPath.includes('/employees/') && currentPath.includes('/view')) {
                    // If on employee view page, redirect to view page to show updated data
                    console.log('Redirecting to employee view page');
                    if (data.redirect_url) {
                        window.location.href = data.redirect_url;
                    } else {
                        window.location.reload();
                    }
                } else {
                    // Default behavior - reload current page
                    console.log('Default refresh behavior');
                    window.location.reload();
                }
            } else {
                // Validation errors - display them and keep modal open
                console.log('Validation errors:', data.errors);
                displayValidationErrors(data.errors, editForm);
                
                // Restore form data if provided
                if (data.form_data) {
                    restoreFormData(data.form_data, editForm);
                }
            }
        })
        .catch(error => {
            console.error('Error submitting form:', error);
            showFlashMessage('An error occurred while updating the employee. Please try again.', 'error');
        })
        .finally(() => {
            // Restore button state
            btnText.classList.remove('d-none');
            btnSpinner.classList.add('d-none');
            submitButton.disabled = false;
        });
    });
}

// Display validation errors in the modal
function displayValidationErrors(errors, form) {
    // Create error alert container
    const errorAlert = document.createElement('div');
    errorAlert.className = 'alert alert-danger alert-dismissible fade show';
    errorAlert.innerHTML = `
        <strong>Please fix the following errors:</strong>
        <ul class="mb-0 mt-2">
            ${errors.map(error => `<li>${error}</li>`).join('')}
        </ul>
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert at the top of the modal body
    const modalBody = form.querySelector('.modal-body');
    modalBody.insertBefore(errorAlert, modalBody.firstChild);
    
    // Scroll to top of modal
    modalBody.scrollTop = 0;
}

// Restore form data after validation errors
function restoreFormData(formData, form) {
    Object.keys(formData).forEach(key => {
        const field = form.querySelector(`[name="${key}"]`);
        if (field) {
            if (field.type === 'checkbox') {
                field.checked = formData[key] === '1' || formData[key] === 'on';
            } else {
                field.value = formData[key];
            }
        }
    });
    
    // Trigger change events to update dependent fields
    const changeEvents = ['salary_type'];
    changeEvents.forEach(fieldName => {
        const field = form.querySelector(`[name="${fieldName}"]`);
        if (field) {
            field.dispatchEvent(new Event('change'));
        }
    });

    // Ensure deduction value fields reflect selected amount type
    form.querySelectorAll('#edit_deductions_tbody select[name="deduction_amount_type[]"]').forEach(sel => {
        if (sel.value === 'calculated' && !Array.from(sel.options).some(o => o.value === 'calculated')) {
            sel.insertAdjacentHTML('beforeend', '<option value="calculated">Calculated</option>');
            sel.value = 'calculated';
        }
        if (typeof updateEditDeductionValueField === 'function') {
            updateEditDeductionValueField(sel);
        }
    });
}

// Refresh a specific employee row in the employees table
function refreshEmployeeRow(employeeId) {
    console.log('Refreshing employee row for ID:', employeeId);
    
    // Fetch updated employee data
    fetch(`/employees/${employeeId}/api`)
        .then(response => response.json())
        .then(employee => {
            console.log('Updated employee data:', employee);
            
            // Find the employee row in the table
            const employeeRow = document.querySelector(`tr[data-employee-id="${employeeId}"]`);
            if (!employeeRow) {
                console.log('Employee row not found, falling back to page reload');
                window.location.reload();
                return;
            }
            
            // Update the row data
            updateEmployeeRowData(employeeRow, employee);
            
            // Add a brief highlight effect to show the update
            employeeRow.classList.add('table-success');
            setTimeout(() => {
                employeeRow.classList.remove('table-success');
            }, 2000);
        })
        .catch(error => {
            console.error('Error refreshing employee row:', error);
            // Fall back to page reload if refresh fails
            window.location.reload();
        });
}

// Update employee row data in the table
function updateEmployeeRowData(row, employee) {
    // Update cells based on actual table structure
    const cells = row.querySelectorAll('td');
    
    if (cells.length >= 8) {
        // Table structure: Employee ID, First Name, Last Name, ID Number, Department, Start Date, Salary, Actions
        cells[0].innerHTML = `<strong>${employee.employee_id}</strong>`; // Employee ID
        cells[1].textContent = employee.first_name; // First Name
        cells[2].textContent = employee.last_name; // Last Name
        cells[3].textContent = employee.id_number; // ID Number
        cells[4].innerHTML = `<span class="badge bg-secondary">${employee.department}</span>`; // Department
        
        // Start Date
        if (employee.start_date) {
            const startDate = new Date(employee.start_date);
            cells[5].textContent = startDate.toLocaleDateString('en-US');
        } else {
            cells[5].textContent = 'N/A';
        }
        
        // Salary
        if (employee.salary_type === 'monthly') {
            cells[6].textContent = `R${parseFloat(employee.salary).toFixed(2)}/mo`;
        } else if (employee.salary_type === 'hourly') {
            cells[6].textContent = `R${parseFloat(employee.salary).toFixed(2)}/hr`;
        } else if (employee.salary_type === 'daily') {
            cells[6].textContent = `R${parseFloat(employee.salary).toFixed(2)}/day`;
        } else {
            cells[6].textContent = 'N/A';
        }
        
        // Actions column (cells[7]) remains unchanged
    }
    
    console.log('Employee row updated successfully');
}

// Show flash message
function showFlashMessage(message, type) {
    // Create flash message element
    const flashMessage = document.createElement('div');
    flashMessage.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    flashMessage.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Insert into flash messages container or create one
    let flashContainer = document.querySelector('.flash-messages');
    if (!flashContainer) {
        flashContainer = document.createElement('div');
        flashContainer.className = 'flash-messages container mt-3';
        document.querySelector('main').prepend(flashContainer);
    }
    
    flashContainer.appendChild(flashMessage);
    
    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        flashMessage.remove();
    }, 5000);
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeEmployeeModal();
    handleEditEmployeeFormSubmission();

    // Salary label updates are handled inside the modal's inline script.
    // Removing the duplicate logic here prevents conflicts that occurred when
    // this script overwrote the label's inner HTML before the modal was
    // populated, which caused the salary label to remain "Monthly Salary".

    const idInput = document.getElementById('edit_id_number');
    if (idInput) {
        idInput.addEventListener('input', validateAndExtractFromEditId);
    }

    // Setup department change handler for edit modal
    const editDepartmentSelect = document.getElementById('edit_department');
    if (editDepartmentSelect) {
        editDepartmentSelect.addEventListener('change', function() {
            handleEditDepartmentChange();
        });
    }

    document.querySelectorAll('input[type="number"]').forEach(input => {
        input.addEventListener('wheel', e => e.preventDefault());
    });

    if (window.location.hash === '#editEmployeeModal') {
        const editButton = document.querySelector('.edit-employee-btn');
        if (editButton) {
            editButton.click();
        }
    }

});

function handleEditDepartmentChange() {
    const departmentSelect = document.getElementById('edit_department');
    const customDeptGroup = document.getElementById('edit_custom_department_group');
    const customDeptInput = document.getElementById('edit_custom_department');
    
    if (!departmentSelect || !customDeptGroup || !customDeptInput) return;
    
    if (departmentSelect.value === 'Other') {
        customDeptGroup.style.display = 'block';
        customDeptInput.required = true;
        customDeptInput.focus();
    } else {
        customDeptGroup.style.display = 'none';
        customDeptInput.required = false;
        customDeptInput.value = '';
    }
}

// Toggle identification fields in edit modal
function toggleEditIdentificationFields() {
    const identificationType = document.getElementById('edit_identification_type');
    const saIdField = document.getElementById('edit_sa_id_field');
    const passportField = document.getElementById('edit_passport_field');
    const dobField = document.getElementById('edit_date_of_birth');
    const genderField = document.getElementById('edit_gender');
    const dobHelpText = document.getElementById('edit_dob_help_text');
    const genderHelpText = document.getElementById('edit_gender_help_text');

    if (!identificationType || !saIdField || !passportField) return;

    const isPassport = identificationType.value === 'passport';

    if (isPassport) {
        // Show passport field, hide SA ID field
        saIdField.style.display = 'none';
        passportField.style.display = 'block';
        
        // Make DOB and Gender editable for passport holders
        if (dobField) {
            dobField.removeAttribute('readonly');
            dobField.style.backgroundColor = '';
        }
        if (genderField) {
            genderField.removeAttribute('disabled');
            genderField.style.backgroundColor = '';
        }
        
        // Update help text
        if (dobHelpText) dobHelpText.textContent = 'Enter date of birth';
        if (genderHelpText) genderHelpText.textContent = 'Select gender';
        
        // Clear SA ID validation messages
        const validationMsg = document.getElementById('edit_id_validation_message');
        const successMsg = document.getElementById('edit_id_success_message');
        if (validationMsg) validationMsg.style.display = 'none';
        if (successMsg) successMsg.style.display = 'none';
        
    } else {
        // Show SA ID field, hide passport field
        saIdField.style.display = 'block';
        passportField.style.display = 'none';
        
        // Make DOB and Gender readonly/disabled for SA ID holders
        if (dobField) {
            dobField.setAttribute('readonly', true);
            dobField.style.backgroundColor = 'var(--bs-secondary-bg)';
        }
        if (genderField) {
            genderField.setAttribute('disabled', true);
            genderField.style.backgroundColor = 'var(--bs-secondary-bg)';
        }
        
        // Update help text
        if (dobHelpText) dobHelpText.textContent = 'Auto-filled from ID number';
        if (genderHelpText) genderHelpText.textContent = 'Auto-filled from ID number';
    }
}

// Validate and extract from SA ID in edit modal
function validateAndExtractFromEditId() {
    const idInput = document.getElementById('edit_id_number');
    const dobInput = document.getElementById('edit_date_of_birth');
    const genderSelect = document.getElementById('edit_gender');

    if (!idInput || !dobInput || !genderSelect) return;

    const idNumber = idInput.value.replace(/\s/g, '');

    if (idNumber.length === 13 && /^\d{13}$/.test(idNumber)) {
        const year = parseInt(idNumber.substring(0, 2));
        const month = parseInt(idNumber.substring(2, 4));
        const day = parseInt(idNumber.substring(4, 6));

        const fullYear = year <= 24 ? 2000 + year : 1900 + year;

        if (month >= 1 && month <= 12 && day >= 1 && day <= 31) {
            const dobString = `${fullYear}-${month.toString().padStart(2, '0')}-${day.toString().padStart(2, '0')}`;
            dobInput.value = dobString;

            const genderDigit = parseInt(idNumber.substring(6, 10));
            if (genderDigit >= 0 && genderDigit <= 4999) {
                genderSelect.value = 'Female';
            } else if (genderDigit >= 5000 && genderDigit <= 9999) {
                genderSelect.value = 'Male';
            }

            // Show success message
            const validationMsg = document.getElementById('edit_id_validation_message');
            const successMsg = document.getElementById('edit_id_success_message');
            if (validationMsg) validationMsg.style.display = 'none';
            if (successMsg) successMsg.style.display = 'block';
        } else {
            // Show validation error
            const validationMsg = document.getElementById('edit_id_validation_message');
            const successMsg = document.getElementById('edit_id_success_message');
            if (validationMsg) {
                validationMsg.textContent = 'Invalid date in ID number';
                validationMsg.style.display = 'block';
            }
            if (successMsg) successMsg.style.display = 'none';
        }
    } else if (idNumber.length > 0) {
        // Show validation error for incomplete ID
        const validationMsg = document.getElementById('edit_id_validation_message');
        const successMsg = document.getElementById('edit_id_success_message');
        if (validationMsg) {
            validationMsg.textContent = 'ID number must be exactly 13 digits';
            validationMsg.style.display = 'block';
        }
        if (successMsg) successMsg.style.display = 'none';
    } else {
        // Clear messages when field is empty
        const validationMsg = document.getElementById('edit_id_validation_message');
        const successMsg = document.getElementById('edit_id_success_message');
        if (validationMsg) validationMsg.style.display = 'none';
        if (successMsg) successMsg.style.display = 'none';
    }
}