/**
 * Portfolio Dashboard JavaScript Module
 * Handles table sorting, calendar filtering, and interactive features
 */

class PortfolioDashboard {
    constructor() {
        this.currentMonth = new Date().getMonth();
        this.currentYear = new Date().getFullYear();
        this.sortDirection = {};
        this.originalTableData = [];
        
        this.initializeComponents();
    }

    initializeComponents() {
        this.renderMiniCalendar();
        this.initializeTooltips();
        this.cacheOriginalTableData();
        
        // Set up event listeners
        document.addEventListener('DOMContentLoaded', () => {
            this.initializeTooltips();
        });
    }

    /**
     * Mini Calendar Implementation - Clean Grid Layout
     */
    renderMiniCalendar() {
        const calendar = document.getElementById('miniCalendar');
        if (!calendar) return;

        const date = new Date(this.currentYear, this.currentMonth, 1);
        const monthNames = ["January", "February", "March", "April", "May", "June",
            "July", "August", "September", "October", "November", "December"];
        
        const firstDay = date.getDay();
        const daysInMonth = new Date(this.currentYear, this.currentMonth + 1, 0).getDate();
        const today = new Date();
        
        // Create calendar with navigation header and forced grid layout
        let html = `
            <div class="mini-calendar">
                <div class="mini-calendar-nav">
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="portfolioDashboard.previousMonth()">
                        <i class="fas fa-chevron-left"></i>
                    </button>
                    <span class="fw-bold">${monthNames[this.currentMonth]} ${this.currentYear}</span>
                    <button type="button" class="btn btn-sm btn-outline-secondary" onclick="portfolioDashboard.nextMonth()">
                        <i class="fas fa-chevron-right"></i>
                    </button>
                </div>
                <div class="mini-calendar-body" style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 1px; background: #dee2e6;">
                    <div class="mini-calendar-day-header" style="background: #6c757d; color: white; padding: 0.5rem; text-align: center; font-size: 0.75rem;">Sun</div>
                    <div class="mini-calendar-day-header" style="background: #6c757d; color: white; padding: 0.5rem; text-align: center; font-size: 0.75rem;">Mon</div>
                    <div class="mini-calendar-day-header" style="background: #6c757d; color: white; padding: 0.5rem; text-align: center; font-size: 0.75rem;">Tue</div>
                    <div class="mini-calendar-day-header" style="background: #6c757d; color: white; padding: 0.5rem; text-align: center; font-size: 0.75rem;">Wed</div>
                    <div class="mini-calendar-day-header" style="background: #6c757d; color: white; padding: 0.5rem; text-align: center; font-size: 0.75rem;">Thu</div>
                    <div class="mini-calendar-day-header" style="background: #6c757d; color: white; padding: 0.5rem; text-align: center; font-size: 0.75rem;">Fri</div>
                    <div class="mini-calendar-day-header" style="background: #6c757d; color: white; padding: 0.5rem; text-align: center; font-size: 0.75rem;">Sat</div>
        `;
        
        // Empty cells for days before month starts
        for (let i = 0; i < firstDay; i++) {
            html += '<div class="mini-calendar-day" style="background: white; padding: 0.75rem 0.5rem; min-height: 40px;"></div>';
        }
        
        // Days of the month
        for (let day = 1; day <= daysInMonth; day++) {
            const cellDate = new Date(this.currentYear, this.currentMonth, day);
            const isToday = cellDate.toDateString() === today.toDateString();
            const dateString = cellDate.toISOString().split('T')[0];
            
            const dayStyle = isToday ? 
                'background: #0d6efd; color: white; font-weight: bold; padding: 0.75rem 0.5rem; text-align: center; cursor: pointer; min-height: 40px; display: flex; align-items: center; justify-content: center;' :
                'background: white; padding: 0.75rem 0.5rem; text-align: center; cursor: pointer; min-height: 40px; display: flex; align-items: center; justify-content: center;';
            
            html += `<div class="mini-calendar-day ${isToday ? 'today' : ''}" style="${dayStyle}" onclick="portfolioDashboard.filterByDate('${dateString}')">${day}</div>`;
        }
        
        html += '</div></div>';
        calendar.innerHTML = html;
    }

    previousMonth() {
        this.currentMonth--;
        if (this.currentMonth < 0) {
            this.currentMonth = 11;
            this.currentYear--;
        }
        this.renderMiniCalendar();
    }

    nextMonth() {
        this.currentMonth++;
        if (this.currentMonth > 11) {
            this.currentMonth = 0;
            this.currentYear++;
        }
        this.renderMiniCalendar();
    }

    /**
     * Date-based Filtering
     */
    filterByDate(dateString) {
        fetch(`/accountant/calendar-data?start=${dateString}&end=${dateString}`)
            .then(response => response.json())
            .then(events => {
                const companyIds = [...new Set(events.map(event => event.extendedProps.company_id))];
                this.filterTableByCompanies(companyIds);
            })
            .catch(error => {
                console.error('Error filtering by date:', error);
            });
    }

    filterTableByCompanies(companyIds) {
        const table = document.getElementById('portfolioTable');
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const companyId = parseInt(row.dataset.companyId);
            if (companyIds.length === 0 || companyIds.includes(companyId)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });

        // Update mobile accordion view
        const mobileCards = document.querySelectorAll('.mobile-company-card');
        mobileCards.forEach(card => {
            const companyId = parseInt(card.dataset.companyId);
            if (companyIds.length === 0 || companyIds.includes(companyId)) {
                card.style.display = '';
            } else {
                card.style.display = 'none';
            }
        });
    }

    /**
     * Table Sorting Implementation
     */
    cacheOriginalTableData() {
        const table = document.getElementById('portfolioTable');
        if (!table) return;

        const rows = Array.from(table.querySelectorAll('tbody tr'));
        this.originalTableData = rows.map(row => ({
            element: row.cloneNode(true),
            data: {
                name: row.cells[0].textContent.trim(),
                sector: row.cells[1].textContent.trim(),
                payrollStatus: row.cells[2].textContent.trim(),
                lastRun: row.cells[3].textContent.trim(),
                employees: parseInt(row.cells[4].textContent.trim()) || 0,
                compliance: row.cells[5].textContent.trim()
            }
        }));
    }

    sortTable(column) {
        const table = document.getElementById('portfolioTable');
        if (!table) return;

        const tbody = table.querySelector('tbody');
        const rows = Array.from(tbody.querySelectorAll('tr'));
        
        // Toggle sort direction
        this.sortDirection[column] = this.sortDirection[column] === 'asc' ? 'desc' : 'asc';
        const direction = this.sortDirection[column];
        
        // Sort rows based on column
        rows.sort((a, b) => {
            let aVal, bVal;
            
            switch(column) {
                case 'name':
                    aVal = a.cells[0].textContent.trim().toLowerCase();
                    bVal = b.cells[0].textContent.trim().toLowerCase();
                    break;
                case 'sector':
                    aVal = a.cells[1].textContent.trim().toLowerCase();
                    bVal = b.cells[1].textContent.trim().toLowerCase();
                    break;
                case 'status':
                    aVal = a.cells[2].textContent.trim().toLowerCase();
                    bVal = b.cells[2].textContent.trim().toLowerCase();
                    break;
                case 'lastrun':
                    aVal = new Date(a.cells[3].textContent.trim() || '1900-01-01');
                    bVal = new Date(b.cells[3].textContent.trim() || '1900-01-01');
                    break;
                case 'employees':
                    aVal = parseInt(a.cells[4].textContent.trim()) || 0;
                    bVal = parseInt(b.cells[4].textContent.trim()) || 0;
                    break;
                case 'compliance':
                    // Sort by compliance status (compliant first, then by issue count)
                    const aCompliant = a.cells[5].textContent.includes('Compliant');
                    const bCompliant = b.cells[5].textContent.includes('Compliant');
                    if (aCompliant && !bCompliant) return direction === 'asc' ? -1 : 1;
                    if (!aCompliant && bCompliant) return direction === 'asc' ? 1 : -1;
                    aVal = a.cells[5].textContent.trim().toLowerCase();
                    bVal = b.cells[5].textContent.trim().toLowerCase();
                    break;
                default:
                    return 0;
            }
            
            if (aVal < bVal) return direction === 'asc' ? -1 : 1;
            if (aVal > bVal) return direction === 'asc' ? 1 : -1;
            return 0;
        });
        
        // Reorder table rows
        rows.forEach(row => tbody.appendChild(row));
        
        // Update sort indicators
        this.updateSortIndicators(column, direction);
        
        // Reinitialize tooltips after sorting
        this.initializeTooltips();
    }

    updateSortIndicators(activeColumn, direction) {
        // Remove existing sort indicators
        document.querySelectorAll('.sort-indicator').forEach(indicator => {
            indicator.remove();
        });
        
        // Add new sort indicator
        const buttons = document.querySelectorAll('[onclick*="sortTable"]');
        buttons.forEach(button => {
            const onclick = button.getAttribute('onclick');
            if (onclick && onclick.includes(`'${activeColumn}'`)) {
                const indicator = document.createElement('i');
                indicator.className = `fas fa-sort-${direction === 'asc' ? 'up' : 'down'} ms-1 sort-indicator`;
                button.appendChild(indicator);
            }
        });
    }

    /**
     * Tooltip Management
     */
    initializeTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    /**
     * Compliance Card Interactions
     */
    showOverdueReminders() {
        // Filter table to show only companies with overdue compliance
        const table = document.getElementById('portfolioTable');
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const complianceCell = row.cells[5];
            const hasIssues = complianceCell.textContent.includes('Issues');
            row.style.display = hasIssues ? '' : 'none';
        });
    }

    showDueThisWeek() {
        // This would integrate with calendar data to show companies with items due this week
        console.log('Filtering companies with compliance due this week');
    }

    showCompliantCompanies() {
        // Filter table to show only compliant companies
        const table = document.getElementById('portfolioTable');
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const complianceCell = row.cells[5];
            const isCompliant = complianceCell.textContent.includes('Compliant');
            row.style.display = isCompliant ? '' : 'none';
        });
    }

    filterComplianceCalendar(filter) {
        // Calendar filtering logic would go here
        console.log(`Filtering calendar by: ${filter}`);
    }

    /**
     * Export Functions
     */
    exportCompliance(format) {
        // Export functionality placeholder
        console.log(`Exporting compliance data as ${format}`);
        // Implementation would create download for PDF/CSV
    }
}

// Initialize dashboard when DOM is ready
let portfolioDashboard;
document.addEventListener('DOMContentLoaded', function() {
    portfolioDashboard = new PortfolioDashboard();
});

// Global functions for template onclick handlers
function sortTable(column) {
    if (portfolioDashboard) {
        portfolioDashboard.sortTable(column);
    }
}

function previousMonth() {
    if (portfolioDashboard) {
        portfolioDashboard.previousMonth();
    }
}

function nextMonth() {
    if (portfolioDashboard) {
        portfolioDashboard.nextMonth();
    }
}

function showOverdueReminders() {
    if (portfolioDashboard) {
        portfolioDashboard.showOverdueReminders();
    }
}

function showDueThisWeek() {
    if (portfolioDashboard) {
        portfolioDashboard.showDueThisWeek();
    }
}

function showCompliantCompanies() {
    if (portfolioDashboard) {
        portfolioDashboard.showCompliantCompanies();
    }
}

function filterComplianceCalendar(filter) {
    if (portfolioDashboard) {
        portfolioDashboard.filterComplianceCalendar(filter);
    }
}

function exportCompliance(format) {
    if (portfolioDashboard) {
        portfolioDashboard.exportCompliance(format);
    }
}