"""Payroll-related service functions."""

from datetime import date
from decimal import Decimal
from app.models import Employee, PayrollEntry


def calculate_medical_aid_deduction(employee):
    """Calculate the monthly medical aid deduction for an employee.

    This implements the SARS 2025/26 medical tax credit rules. If the
    employee does not have an active recurring deduction linked to a
    medical aid beneficiary, ``0`` is returned.

    Parameters
    ----------
    employee : :class:`~app.models.employee.Employee`
        Employee instance containing ``recurring_deductions`` and the
        ``medical_aid_dependants`` attribute.

    Returns
    -------
    int
        The monthly medical aid deduction amount in Rand.
    """
    # Check if the employee has an active medical aid deduction
    has_medical_aid = any(
        d.is_active and d.beneficiary and d.beneficiary.type == "Medical Aid"
        for d in employee.recurring_deductions
    )
    if not has_medical_aid:
        return 0

    info = getattr(employee, "medical_aid_info", None)

    if info and not info.use_sars_calculation:
        total = 0
        if info.employer_contribution_override:
            total += float(info.employer_contribution_override)
        if info.employee_contribution_override:
            total += float(info.employee_contribution_override)
        return total

    dependants = 0
    if info:
        dependants = (info.number_of_dependants or 0) + (
            info.additional_dependants or 0
        )
    else:
        # Check if Employee has medical_aid_dependants field, fallback to 0
        dependants = getattr(employee, 'medical_aid_dependants', 0) or 0

    from app.services.sars_service import SARSService
    sars_config = SARSService.get_global_sars_config()
    
    primary_credit = float(sars_config.medical_primary_credit)
    dependant_credit = float(sars_config.medical_dependant_credit)
    
    if dependants == 0:
        return primary_credit
    elif dependants == 1:
        return primary_credit * 2  # Main member + 1 dependant (primary x 2)
    else:
        return (primary_credit * 2) + (dependants - 1) * dependant_credit


def calculate_medical_aid_fringe_benefit(info):
    """Calculate the taxable fringe benefit for an employee's medical aid.

    Parameters
    ----------
    info : :class:`~app.models.employee_medical_aid_info.EmployeeMedicalAidInfo` or ``None``
        Medical aid configuration for the employee.

    Returns
    -------
    float
        The fringe benefit amount in Rand.
    """

    if not info:
        return 0.0

    if info.use_sars_calculation:
        dependants = (info.number_of_dependants or 0) + (
            info.additional_dependants or 0
        )
        from app.services.sars_service import SARSService
        sars_config = SARSService.get_global_sars_config()
        
        primary_credit = float(sars_config.medical_primary_credit)
        dependant_credit = float(sars_config.medical_dependant_credit)
        
        if dependants == 0:
            return primary_credit
        elif dependants == 1:
            return primary_credit * 2  # Main member + 1 dependant (primary x 2)
        else:
            return (primary_credit * 2) + (dependants - 1) * dependant_credit

    if info.employer_contribution_override is not None:
        return float(info.employer_contribution_override)

    return 0.0

def calculate_ytd_totals(employee_id, tax_year_start):
    """Calculate year-to-date payroll totals for an employee.

    Parameters
    ----------
    employee_id : int
        The employee ID to calculate totals for.
    tax_year_start : date
        Start date of the SARS tax year.

    Returns
    -------
    dict
        Dictionary of YTD totals rounded to 2 decimal places. Missing employees
        result in all zero values.
    """
    # Fetch employee and handle missing records gracefully
    employee = Employee.query.get(employee_id)
    if not employee:
        return {
            "gross_pay_ytd": 0.0,
            "paye_ytd": 0.0,
            "uif_ytd": 0.0,
            "sdl_ytd": 0.0,
            "net_pay_ytd": 0.0,
            "fringe_benefit_ytd": 0.0,
            "taxable_income_ytd": 0.0,
            "bonus_ytd": 0.0,
            "allowances_ytd": 0.0,
        }

    effective_start = max(employee.start_date, tax_year_start)
    today = date.today()

    entries = (
        PayrollEntry.query.filter(
            PayrollEntry.employee_id == employee.id,
            PayrollEntry.is_finalized.is_(True),
            PayrollEntry.pay_period_start >= effective_start,
            PayrollEntry.pay_period_start <= today,
        ).all()
    )

    gross_pay = Decimal("0")
    paye = Decimal("0")
    uif = Decimal("0")
    sdl = Decimal("0")
    net_pay = Decimal("0")
    fringe = Decimal("0")
    bonus = Decimal("0")
    allowances = Decimal("0")

    for entry in entries:
        gross_pay += Decimal(str(entry.gross_pay or 0))
        paye += Decimal(str(entry.paye or 0))
        uif += Decimal(str(entry.uif or 0))
        sdl += Decimal(str(entry.sdl or 0))
        net_pay += Decimal(str(entry.net_pay or 0))
        fringe += Decimal(str(entry.fringe_benefit_medical or 0))
        bonus += Decimal(str(entry.bonus_amount or 0))
        allowances += Decimal(str(entry.allowances or 0))

    taxable_income = gross_pay + fringe

    def r(value):
        return round(float(value), 2)

    return {
        "gross_pay_ytd": r(gross_pay),
        "paye_ytd": r(paye),
        "uif_ytd": r(uif),
        "sdl_ytd": r(sdl),
        "net_pay_ytd": r(net_pay),
        "fringe_benefit_ytd": r(fringe),
        "taxable_income_ytd": r(taxable_income),
        "bonus_ytd": r(bonus),
        "allowances_ytd": r(allowances),
    }
