let currentEmployeeId = null;
let currentEmployeeData = {};
const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

async function populatePayrollModal(employeeId) {
    try {
        const response = await fetch(`/employees/${employeeId}/api`);
        const data = await response.json();
        currentEmployeeId = employeeId;
        currentEmployeeData = data;
        currentEmployeeData.fringe_benefit_amount = parseFloat(data.fringe_benefit_amount || 0);

        const nameSpan = document.getElementById('modal-employee-name');
        if (nameSpan) {
            nameSpan.textContent = `${data.first_name} ${data.last_name}`;
        }
        document.getElementById('employee-id').value = data.id;
        document.getElementById('salary_type').value = data.salary_type.charAt(0).toUpperCase() + data.salary_type.slice(1);
        const workHours = (data.ordinary_hours_per_day || 8) * (data.work_days_per_month || 22);
        let hourlyRate;
        let baseSalary;
        if (data.salary_type === 'hourly') {
            hourlyRate = parseFloat(data.salary);
            baseSalary = hourlyRate;
        } else if (data.salary_type === 'daily') {
            hourlyRate = parseFloat(data.salary) / (data.ordinary_hours_per_day || 8);
            baseSalary = parseFloat(data.salary);
        } else {
            hourlyRate = parseFloat(data.salary) / workHours;
            baseSalary = parseFloat(data.monthly_salary);
        }
        currentEmployeeData.hourly_rate = hourlyRate;
        currentEmployeeData.work_hours = workHours;
        const ordLabel = document.getElementById('ordinary_hours_label');
        if (ordLabel) {
            if (data.salary_type === 'hourly') {
                ordLabel.textContent = 'Ordinary Hours';
            } else if (data.salary_type === 'daily') {
                ordLabel.textContent = 'Ordinary Days';
            } else if (data.salary_type === 'piece') {
                ordLabel.textContent = 'Time Worked (Optional)';
            } else {
                ordLabel.textContent = 'Ordinary Time Worked';
            }
        }
        const ordinaryInput = document.getElementById('ordinary_hours');
        const ordinaryGroup = document.getElementById('ordinary_hours_group');
        const monthlyNote = document.getElementById('monthly_hours_note');
        const pieceWorkSection = document.getElementById('piece_work_section');
        
        if (ordinaryInput) {
            ordinaryInput.value = data.salary_type === 'daily' ? '' : workHours;
            if (data.salary_type === 'monthly') {
                ordinaryInput.disabled = true;
                if (monthlyNote) monthlyNote.style.display = 'block';
            } else {
                ordinaryInput.disabled = false;
                if (monthlyNote) monthlyNote.style.display = 'none';
            }
        }
        
        // Handle piece work visibility and setup
        if (data.salary_type === 'piece') {
            if (pieceWorkSection) pieceWorkSection.style.display = 'block';
            const pieceRateDisplay = document.getElementById('piece_rate_display');
            if (pieceRateDisplay) {
                pieceRateDisplay.value = parseFloat(data.piece_rate || 0).toFixed(4);
            }
            currentEmployeeData.piece_rate = parseFloat(data.piece_rate || 0);
        } else {
            if (pieceWorkSection) pieceWorkSection.style.display = 'none';
        }
        document.getElementById('base_salary').value = baseSalary.toFixed(2);
        let baseDisplay;
        if (data.salary_type === 'hourly') {
            baseDisplay = `R ${baseSalary.toFixed(2)} / hour`;
        } else if (data.salary_type === 'daily') {
            baseDisplay = `R ${baseSalary.toFixed(2)} / day`;
        } else {
            baseDisplay = `R ${baseSalary.toFixed(2)} / month`;
        }
        document.getElementById('config-base-rate').textContent = baseDisplay;

        document.getElementById('allowances').value = data.allowances || 0;

        const bonusRow = document.getElementById('bonus-row');
        if (data.bonus_type && data.bonus_type !== 'None') {
            bonusRow.style.display = 'block';
        } else {
            bonusRow.style.display = 'none';
            document.getElementById('bonus_amount').value = 0;
        }

        // Populate configuration preview panel
        document.getElementById('config-salary-type').textContent = data.salary_type.charAt(0).toUpperCase() + data.salary_type.slice(1);
        document.getElementById('config-overtime').textContent = data.overtime_eligible ? 'Yes' : 'No';

        const card = document.getElementById('payroll-config-card');
        const otMult = parseFloat(card.dataset.ot || 1.5);
        const sunMult = parseFloat(card.dataset.sun || 2);
        const holMult = parseFloat(card.dataset.hol || 2.5);

        document.getElementById('config-hourly-rate').textContent = `R ${hourlyRate.toFixed(2)}`;
        document.getElementById('config-overtime-rate').innerHTML = `R ${(hourlyRate * otMult).toFixed(2)} <small>(× ${otMult})</small>`;
        document.getElementById('config-sunday-rate').innerHTML = `R ${(hourlyRate * sunMult).toFixed(2)} <small>(× ${sunMult})</small>`;
        document.getElementById('config-holiday-rate').innerHTML = `R ${(hourlyRate * holMult).toFixed(2)} <small>(× ${holMult})</small>`;
        document.getElementById('overtime-rates').style.display = data.overtime_eligible ? 'block' : 'none';

        const cfgUif = document.getElementById('config-uif');
        const cfgSdl = document.getElementById('config-sdl');
        const cfgPaye = document.getElementById('config-paye');
        cfgUif.checked = !!data.uif_contributing;
        cfgSdl.checked = !!data.sdl_contributing;
        cfgPaye.checked = !!data.paye_exempt;

        document.getElementById('config-med-scheme').textContent = data.medical_aid_scheme || 'N/A';
        document.getElementById('config-med-calc').textContent = data.medical_aid_use_sars ? 'SARS Table' : 'Manual';
        document.getElementById('config-med-beneficiary').textContent = data.medical_aid_linked_beneficiary || 'N/A';
        document.getElementById('config-med-employer').textContent = `R ${parseFloat(data.medical_aid_employer || 0).toFixed(2)}`;
        document.getElementById('config-med-employee').textContent = `R ${parseFloat(data.medical_aid_employee || 0).toFixed(2)}`;

        const medSection = document.getElementById('medical-aid-section');
        let medDed = null;
        if (data.recurring_deductions) {
            medDed = data.recurring_deductions.find(d => (d.deduction_type || '').toLowerCase() === 'medical aid' && (d.is_active !== false && d.enabled !== false));
        }
        if (data.medical_aid_principal_member && medDed) {
            document.getElementById('config-med-type').textContent = medDed.amount_type;
            document.getElementById('config-med-total').textContent = `R ${parseFloat(medDed.value || 0).toFixed(2)}`;
            medSection.style.display = 'block';
        } else {
            medSection.style.display = 'none';
        }

        const recList = document.getElementById('config-recurring-list');
        recList.innerHTML = '';
        if (data.recurring_deductions) {
            data.recurring_deductions.forEach(d => {
                const active = d.is_active !== undefined ? d.is_active : d.enabled;
                if (active === false) return;
                if ((d.deduction_type || '').toLowerCase() === 'medical aid') return;
                let val = 'R 0.00';
                if (d.amount_type.toLowerCase() === 'percentage') {
                    val = `${parseFloat(d.value).toFixed(2)}%`;
                } else if (d.amount_type.toLowerCase() === 'calculated') {
                    val = 'Calculated';
                } else {
                    val = `R ${parseFloat(d.value).toFixed(2)}`;
                }
                const li = document.createElement('li');
                li.textContent = `${d.beneficiary_name} – ${val}`;
                recList.appendChild(li);
            });
        }



    buildDeductionsTable();
    calculatePayroll();

    fetch(`/api/employees/${employeeId}/payroll-ytd`)
        .then(res => res.json())
        .then(data => {
            const el = document.getElementById('ytdTaxSummaryContent');
            if (!el) return;
            if (!data || data.error) {
                el.innerHTML = '<p class="text-danger">YTD tax data not available.</p>';
                return;
            }
            el.innerHTML = `
      <p><strong>Gross Pay:</strong> R ${data.gross_pay_ytd.toFixed(2)}</p>
      <p><strong>Taxable Income:</strong> R ${data.taxable_income_ytd.toFixed(2)}</p>
      <p><strong>PAYE:</strong> <span class="badge bg-danger">R ${data.paye_ytd.toFixed(2)}</span></p>
      <p><strong>UIF:</strong> R ${data.uif_ytd.toFixed(2)}</p>
      <p><strong>SDL:</strong> R ${data.sdl_ytd.toFixed(2)}</p>
      <p><strong>Bonus:</strong> R ${data.bonus_ytd.toFixed(2)}</p>
      <p><strong>Allowances:</strong> R ${data.allowances_ytd.toFixed(2)}</p>
      <hr>
      <p><strong>Net Pay:</strong> <span class="badge bg-success">R ${data.net_pay_ytd.toFixed(2)}</span></p>
    `;
        })
        .catch(err => {
            console.error(err);
            const el = document.getElementById('ytdTaxSummaryContent');
            if (el) el.innerHTML = '<p class="text-warning">Could not load YTD data.</p>';
        });

    const modal = new bootstrap.Modal(document.getElementById('payrollModal'));
    modal.show();
    } catch (err) {
        console.error(err);
        alert('Failed to load employee data');
    }
}

function buildDeductionsTable() {
    const tbody = document.getElementById('payrollDeductionsTableBody');
    tbody.innerHTML = '';
    if (!currentEmployeeData.recurring_deductions) return;
    currentEmployeeData.recurring_deductions.forEach(d => {
        const active = d.is_active !== undefined ? d.is_active : d.enabled;
        if (active === false) return;
        const typeLabel = d.beneficiary_type || d.deduction_type || '';
        const row = document.createElement('tr');
        row.dataset.amountType = d.amount_type;
        row.dataset.value = d.value;
        row.dataset.beneficiaryType = typeLabel;
        let displayVal = 'R 0.00';
        if (d.amount_type.toLowerCase() === 'fixed') {
            displayVal = `R ${parseFloat(d.value).toFixed(2)}`;
        } else if (d.amount_type.toLowerCase() === 'percentage') {
            displayVal = `${parseFloat(d.value).toFixed(2)}%`;
        }
        row.innerHTML = `<td>${d.beneficiary_name}</td>
                         <td>${typeLabel}</td>
                         <td>${d.amount_type}</td>
                         <td class="deduction-amount">${displayVal}</td>
                         <td></td>`;
        tbody.appendChild(row);
    });
}

function addPayrollDeductionRow() {
    const tbody = document.getElementById('payrollDeductionsTableBody');
    const row = document.createElement('tr');

    row.innerHTML = `
        <td><input type="text" class="form-control form-control-sm beneficiary-input" placeholder="Beneficiary"></td>
        <td><input type="text" class="form-control form-control-sm type-input" placeholder="Type"></td>
        <td>
            <select class="form-select form-select-sm amount-type-select">
                <option value="Fixed" selected>Fixed</option>
                <option value="Percentage">Percentage</option>
            </select>
        </td>
        <td>
            <div class="input-group input-group-sm">
                <span class="input-group-text deduction-prefix">R</span>
                <input type="number" class="form-control deduction-value" value="0" step="0.01" min="0">
            </div>
            <small class="text-muted ms-2 deduction-amount">R 0.00</small>
        </td>
        <td class="text-center"><button type="button" class="btn btn-outline-danger btn-sm delete-deduction"><i class="fas fa-trash-alt"></i></button></td>`;

    tbody.appendChild(row);

    row.querySelector('.amount-type-select').addEventListener('change', function () {
        row.querySelector('.deduction-prefix').textContent = this.value === 'Percentage' ? '%' : 'R';
        calculatePayroll();
    });
    row.querySelector('.deduction-value').addEventListener('input', calculatePayroll);
    row.querySelector('.delete-deduction').addEventListener('click', function(){
        row.remove();
        calculatePayroll();
    });
}

function calculateMedicalAidDeduction() {
    if (!currentEmployeeData.medical_aid_member) return 0;
    const dependants = parseInt(currentEmployeeData.medical_aid_dependants || 0);
    if (dependants === 0) {
        return 364;
    } else if (dependants === 1) {
        return 728;
    }
    return 728 + (dependants - 1) * 246;
}

function calculateRecurringDeductions(base) {
    let total = 0;
    document.querySelectorAll('#payrollDeductionsTableBody tr').forEach(row => {
        let type, value;
        if (row.dataset.amountType) {
            type = row.dataset.amountType;
            value = parseFloat(row.dataset.value);
        } else {
            const typeSelect = row.querySelector('.amount-type-select');
            const valueInput = row.querySelector('.deduction-value');
            type = typeSelect ? typeSelect.value : 'Fixed';
            value = parseFloat(valueInput ? valueInput.value : 0);
        }
        let calc;
        if (type.toLowerCase() === 'percentage') {
            calc = base * (value / 100);
        } else if (type.toLowerCase() === 'calculated' && (row.dataset.beneficiaryType || '').toLowerCase() === 'medical aid') {
            // Use pre-calculated value provided by backend
            calc = parseFloat(row.dataset.value || 0);
        } else {
            calc = value;
        }
        const cell = row.querySelector('.deduction-amount');
        if (cell) cell.textContent = `R ${calc.toFixed(2)}`;
        total += calc;
    });
    document.getElementById('preview-recurring-total').textContent = `R ${total.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    return total;
}

function calculatePayroll() {
    const ordinaryHours = parseFloat(document.getElementById('ordinary_hours').value) || 0;
    const overtimeHours = parseFloat(document.getElementById('overtime_hours').value) || 0;
    const sundayHours = parseFloat(document.getElementById('sunday_hours').value) || 0;
    const publicHolidayHours = parseFloat(document.getElementById('public_holiday_hours').value) || 0;
    const allowances = parseFloat(document.getElementById('allowances').value) || 0;
    const bonusAmount = parseFloat(document.getElementById('bonus_amount').value) || 0;


    let hourlyRate = currentEmployeeData.hourly_rate;
    if (currentEmployeeData.salary_type === 'monthly') {
        const workHours = currentEmployeeData.work_hours || ((currentEmployeeData.ordinary_hours_per_day || 8) * (currentEmployeeData.work_days_per_month || 22));
        hourlyRate = parseFloat(currentEmployeeData.salary) / workHours;

    } else if (currentEmployeeData.salary_type === 'daily') {
        hourlyRate = parseFloat(currentEmployeeData.salary) / (currentEmployeeData.ordinary_hours_per_day || 8);
        
      
    }

    let ordinaryPay;
    if (currentEmployeeData.salary_type === 'monthly') {
        ordinaryPay = parseFloat(currentEmployeeData.monthly_salary || currentEmployeeData.salary);
    } else if (currentEmployeeData.salary_type === 'daily') {
        ordinaryPay = ordinaryHours * parseFloat(currentEmployeeData.salary);
    } else if (currentEmployeeData.salary_type === 'piece') {
        // For piece work: get pieces produced and piece rate
        const piecesProduced = parseFloat(document.getElementById('pieces_produced').value) || 0;
        const pieceRate = currentEmployeeData.piece_rate || 0;
        ordinaryPay = piecesProduced * pieceRate;
    } else {
        ordinaryPay = ordinaryHours * hourlyRate;
    }
    
    let overtimePay = 0;
    let sundayPay = 0;
    let publicHolidayPay = 0;
    
    // Overtime and special pay only apply to hourly/daily employees
    if (currentEmployeeData.salary_type !== 'monthly' && currentEmployeeData.salary_type !== 'piece') {
        overtimePay = overtimeHours * hourlyRate * 1.5;
        sundayPay = sundayHours * hourlyRate * 2.0;
        publicHolidayPay = publicHolidayHours * hourlyRate * 2.0;
    }
    
    const grossPay = ordinaryPay + overtimePay + sundayPay + publicHolidayPay + allowances + bonusAmount;

    const medicalAidTaxCredit = parseFloat(currentEmployeeData.medical_aid_tax_credit || 0);
    const fringeBenefit = parseFloat(currentEmployeeData.fringe_benefit_amount || 0);

    const adjustedGrossPay = grossPay + fringeBenefit;

    let paye = 0;
    document.getElementById('paye-row').style.display = 'block';
    if (!currentEmployeeData.paye_exempt) {
        paye = Math.max((adjustedGrossPay * 0.18) - medicalAidTaxCredit, 0);
    }

    let uif = 0;
    if (currentEmployeeData.uif_contributing) {
        const uifEligibleSalary = Math.min(adjustedGrossPay, 17712.00);
        uif = uifEligibleSalary * 0.01;
    }

    let sdl = 0;
    if (currentEmployeeData.sdl_contributing) {
        sdl = adjustedGrossPay * 0.01;
    }

    const recurringTotal = calculateRecurringDeductions(grossPay);
    const totalDeductions = paye + uif + sdl + recurringTotal;
    const netPay = grossPay - totalDeductions;

    document.getElementById('preview-gross-pay').textContent = `R ${grossPay.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-medical-credit').textContent = `R ${medicalAidTaxCredit.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-fringe-benefit').textContent = `R ${fringeBenefit.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-paye').textContent = `R ${paye.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-uif').textContent = `R ${uif.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-sdl').textContent = `R ${sdl.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-total-deductions').textContent = `R ${totalDeductions.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-net-pay').textContent = `R ${netPay.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    document.getElementById('preview-net-pay-summary').textContent = `R ${netPay.toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;

    const multiplier = 1;
    const format = v => `R ${ (v*multiplier).toLocaleString('en-ZA', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    const payeCalc = adjustedGrossPay * 0.18;

    const fields = {
        'tax-gross-income': grossPay,
        'tax-allowances': allowances,
        'tax-fringe-benefit': fringeBenefit,
        'tax-taxable-income': adjustedGrossPay,
        'tax-paye-calc': payeCalc,
        'tax-uif': uif,
        'tax-sdl': sdl,
        'tax-medical-credit': medicalAidTaxCredit,
        'tax-paye-after-credit': paye,
        'tax-net-pay': netPay
    };
    Object.entries(fields).forEach(([id, val]) => {
        const el = document.getElementById(id);
        if (el) el.textContent = format(val);
    });
}

function savePayrollEntry() {
    const formData = new FormData(document.getElementById('payroll-form'));
    fetch('/payroll/save-entry', {
        method: 'POST',
        headers: { 'X-CSRFToken': csrfToken },
        body: formData
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                updateEmployeeStatus(currentEmployeeId, true);
                bootstrap.Modal.getInstance(document.getElementById('payrollModal')).hide();
                showAlert('Payroll entry saved and verified successfully!', 'success');
                updateVerificationCounts();
            } else {
                showAlert('Error saving payroll entry: ' + data.message, 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showAlert('Error saving payroll entry', 'error');
        });
}

function updateEmployeeStatus(employeeId, verified) {
    const row = document.getElementById(`employee-row-${employeeId}`);
    const statusSpan = row.querySelector('.verification-status');
    const payslipBtn = row.querySelector('.payslip-btn');
    if (verified) {
        statusSpan.innerHTML = '<i class="fas fa-check-circle text-success" title="Verified"></i>';
        statusSpan.setAttribute('data-verified', 'true');
        payslipBtn.style.display = 'inline-block';
    } else {
        statusSpan.innerHTML = '<i class="fas fa-clock text-warning" title="Pending Verification"></i>';
        statusSpan.setAttribute('data-verified', 'false');
        payslipBtn.style.display = 'none';
    }
}

function updateVerificationCounts() {
    const allStatuses = document.querySelectorAll('.verification-status');
    const verifiedCount = document.querySelectorAll('.verification-status[data-verified="true"]').length;
    const pendingCount = allStatuses.length - verifiedCount;
    document.getElementById('verified-count').textContent = `${verifiedCount} Verified`;
    document.getElementById('pending-count').textContent = `${pendingCount} Pending`;
    const processBtn = document.getElementById('process-payroll-btn');
    const statusText = document.getElementById('process-status-text');
    if (processBtn) {
        const allVerified = pendingCount === 0;
        processBtn.disabled = !allVerified;
        if (allVerified) {
            processBtn.title = `Process payroll for all verified employees`;
            processBtn.classList.remove('btn-secondary');
            processBtn.classList.add('btn-success');
            if (statusText) {
                statusText.textContent = `Ready to process payroll for ${allStatuses.length} employees`;
                statusText.classList.remove('text-muted');
                statusText.classList.add('text-success');
            }
        } else {
            processBtn.title = 'All employees must be verified before processing payroll';
            processBtn.classList.remove('btn-success');
            processBtn.classList.add('btn-secondary');
            if (statusText) {
                statusText.textContent = 'All employees must be verified first';
                statusText.classList.remove('text-success');
                statusText.classList.add('text-muted');
            }
        }
    }
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show`;
    alertDiv.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    const container = document.querySelector('.container-fluid');
    container.insertBefore(alertDiv, container.firstChild);
    setTimeout(() => { alertDiv.remove(); }, 5000);
}

document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.payroll-btn').forEach(btn => {
        btn.addEventListener('click', () => populatePayrollModal(btn.dataset.employeeId));
    });
    document.querySelectorAll('.calculation-input').forEach(inp => {
        inp.addEventListener('input', calculatePayroll);
    });
    const addBtn = document.getElementById('add-deduction-btn');
    if (addBtn) {
        addBtn.addEventListener('click', function () {
            addPayrollDeductionRow();
            calculatePayroll();
        });
    }
    updateVerificationCounts();
    document.addEventListener('click', function(e){
        if (e.target.closest('.payslip-btn')) {
            const employeeId = e.target.closest('.payslip-btn').dataset.employeeId;
            window.open(`/payroll/payslip/${employeeId}`, '_blank');
        }
    });
    document.getElementById('payroll-form').addEventListener('submit', function(e){
        e.preventDefault();
        savePayrollEntry();
    });

    const breakdownCollapse = document.getElementById('taxBreakdownCollapse');
    if (breakdownCollapse) {
        breakdownCollapse.addEventListener('shown.bs.collapse', () => {
            document.getElementById('taxBreakdownToggle').textContent = 'Hide Tax Breakdown';
        });
        breakdownCollapse.addEventListener('hidden.bs.collapse', () => {
            document.getElementById('taxBreakdownToggle').textContent = 'Show Tax Breakdown';
        });
    }


    const pdfBtn = document.getElementById('taxPdfBtn');
    if (pdfBtn) {
        pdfBtn.addEventListener('click', function(){
            const table = document.getElementById('taxBreakdownTable');
            const w = window.open('', '', 'width=800,height=600');
            w.document.write('<html><head><title>Tax Breakdown</title>');
            w.document.write('<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css">');
            w.document.write('</head><body>');
            w.document.write(table.outerHTML);
            w.document.write('</body></html>');
            w.document.close();
            w.print();
            w.close();
        });
    }

    if (window.bootstrap) {
        [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]')).map(el => new bootstrap.Tooltip(el));
    }
});
