document.addEventListener('DOMContentLoaded', () => {
    
    // DOM Elements
    const loanForm = document.getElementById('loanForm');
    const consentModal = document.getElementById('consentModal');
    const cancelConsentBtn = document.getElementById('cancelConsentBtn');
    const approveConsentBtn = document.getElementById('approveConsentBtn');
    
    const loadingState = document.getElementById('loadingState');
    const loadingText = document.getElementById('loadingText');
    const loadingSubtext = document.getElementById('loadingSubtext');
    const dashboardSection = document.getElementById('dashboardSection');
    
    const toggleInspectorBtn = document.getElementById('toggleInspectorBtn');
    const inspectorDrawer = document.getElementById('inspectorDrawer');
    const closeInspectorBtn = document.getElementById('closeInspectorBtn');
    
    // Step Indicators
    const step1 = document.getElementById('stepIndicator1');
    const step2 = document.getElementById('stepIndicator2');
    const step3 = document.getElementById('stepIndicator3');

    // State Variables
    let currentConsentId = null;
    let currentSessionId = null;
    let cashflowChartInstance = null;
    let categoryChartInstance = null;

    // Step 1: Form Submit
    loanForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const custName = document.getElementById('custName').value;
        const custPhone = document.getElementById('custPhone').value;
        const bankName = document.getElementById('bankSelect').value;
        
        // Open Consent Modal
        document.getElementById('displayBank').textContent = bankName;
        currentConsentId = 'mock-consent-' + Math.random().toString(36).substring(2, 9);
        document.getElementById('displayConsentId').textContent = currentConsentId;
        
        consentModal.classList.remove('hidden');
        
        // Update Step indicator
        step1.classList.add('completed');
        step2.classList.add('active');
    });

    cancelConsentBtn.addEventListener('click', () => {
        consentModal.classList.add('hidden');
        step2.classList.remove('active');
    });

    // Step 2: Approve Consent & Trigger Handshake
    approveConsentBtn.addEventListener('click', async () => {
        consentModal.classList.add('hidden');
        document.getElementById('step1Card').classList.add('hidden');
        loadingState.classList.remove('hidden');
        
        const custName = document.getElementById('custName').value;
        const custPhone = document.getElementById('custPhone').value;
        const bankName = document.getElementById('bankSelect').value;
        const requestedLoan = document.getElementById('loanAmount').value;

        try {
            // 1. Post Consent Request
            loadingText.textContent = "1/3 Initiating Consent Request with Setu AA...";
            const consentPayload = {
                consentStart: new Date().toISOString(),
                consentExpiry: new Date(Date.now() + 90 * 86400000).toISOString(),
                Customer: { id: custPhone },
                FIDataRange: {
                    from: new Date(Date.now() - 180 * 86400000).toISOString().split('T')[0],
                    to: new Date().toISOString().split('T')[0]
                },
                consentMode: "VIEW",
                consentTypes: ["TRANSACTIONS", "PROFILE", "SUMMARY"],
                fetchType: "ONETIME",
                DataConsumer: { id: "CrediPulse-FIU" },
                fiTypes: ["DEPOSIT"],
                redirectUrl: "http://127.0.0.1:8000/"
            };

            const freq = { value: 1, unit: "MONTH" };
            const filterData = { type: "TRANSACTION_AMOUNT", value: "0", operator: ">=" };
            const datalife = { value: 1, unit: "YEAR" };
            const purpose = {
                Category: { type: "LOAN" },
                code: "101",
                text: "LOAN_SANCTION",
                refUri: "https://api.setu.co/purposes/101"
            };

            const consentRes = await fetch('/postconsent', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    consent_detail: consentPayload,
                    filter_data: filterData,
                    freq: freq,
                    datalife: datalife,
                    purpose: purpose
                })
            });
            const consentData = await consentRes.json();
            document.getElementById('jsonConsent').textContent = JSON.stringify(consentData, null, 2);

            const consentId = consentData.id || currentConsentId;

            // 2. Create Data Session
            loadingText.textContent = "2/3 Creating Secure Data Session for Bank Statement...";
            const sessionPayload = {
                consentId: consentId,
                fromdate: consentPayload.FIDataRange.from,
                todate: consentPayload.FIDataRange.to,
                format: "json"
            };

            const sessionRes = await fetch('/createsession', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(sessionPayload)
            });
            const sessionData = await sessionRes.json();
            document.getElementById('jsonSession').textContent = JSON.stringify(sessionData, null, 2);

            const sessionId = sessionData.session ? sessionData.session.sessionId : ('mock-session-' + Math.random().toString(36).substring(2, 9));

            // 3. Fetch Data & Analyze
            loadingText.textContent = "3/3 Analyzing Bank Statements & Computing Credit Eligibility...";
            const analyzeRes = await fetch(`/analyze/${sessionId}`);
            const result = await analyzeRes.json();
            
            document.getElementById('jsonStatement').textContent = JSON.stringify(result.rawStatement || {}, null, 2);
            document.getElementById('jsonAnalytics').textContent = JSON.stringify(result.analysis || {}, null, 2);

            // Render Underwriter Dashboard
            renderDashboard(result.analysis, requestedLoan);

        } catch (err) {
            console.error("Error in AA handshake:", err);
            alert("Error running AA handshake. Check console for details.");
        } finally {
            loadingState.classList.add('hidden');
            step2.classList.add('completed');
            step3.classList.add('active');
            dashboardSection.classList.remove('hidden');
        }
    });

    // Render Dashboard Results
    function renderDashboard(analysis, requestedLoan) {
        const metrics = analysis.metrics || {};
        const underwriting = analysis.underwriting || {};

        document.getElementById('verifiedHolder').textContent = `${analysis.accountHolder} (${analysis.bankName})`;

        // Decision Hero Banner
        const decisionBadge = document.getElementById('decisionBadge');
        if (underwriting.decision === 'APPROVED') {
            decisionBadge.textContent = '🎉 LOAN APPROVED';
            decisionBadge.className = 'decision-badge badge-approved';
        } else {
            decisionBadge.textContent = '⚠️ LOAN REVIEW NEEDED';
            decisionBadge.className = 'decision-badge';
            decisionBadge.style.background = '#ef4444';
        }

        document.getElementById('sanctionedAmount').textContent = `₹${Number(underwriting.eligibleLoanAmount || requestedLoan).toLocaleString('en-IN')}`;
        document.getElementById('interestRate').innerHTML = `${underwriting.interestRatePct}% <small>p.a.</small>`;
        document.getElementById('riskLevel').textContent = `${underwriting.riskLevel} RISK`;

        // Key Metrics
        document.getElementById('avgIncome').textContent = `₹${Number(metrics.avgMonthlyIncome).toLocaleString('en-IN')}`;
        document.getElementById('avgExpense').textContent = `₹${Number(metrics.avgMonthlyExpense).toLocaleString('en-IN')}`;
        document.getElementById('netSavings').textContent = `₹${Number(metrics.netMonthlySavings).toLocaleString('en-IN')}`;
        document.getElementById('savingsRatePct').textContent = `${metrics.savingsRatePct}% Savings Rate`;
        
        document.getElementById('dtiPct').textContent = `${metrics.debtToIncomePct}%`;
        document.getElementById('existingEmiText').textContent = `Existing EMI: ₹${Number(metrics.monthlyExistingEmi).toLocaleString('en-IN')}`;

        // Audit Items
        const auditList = document.getElementById('auditList');
        auditList.innerHTML = '';
        (underwriting.riskFlags || []).forEach(flag => {
            const item = document.createElement('div');
            item.className = 'audit-item';
            item.innerHTML = `<span>✅</span> <span>${flag}</span>`;
            auditList.appendChild(item);
        });

        // Render Charts
        renderCharts(analysis);
    }

    function renderCharts(analysis) {
        const rawTransactions = (analysis.rawStatement && analysis.rawStatement.transactions) || [];
        const categoryData = analysis.categoryExpenses || {};

        // 1. Cashflow Chart (Income vs Expense over 6 months)
        const ctx1 = document.getElementById('cashflowChart').getContext('2d');
        if (cashflowChartInstance) cashflowChartInstance.destroy();

        cashflowChartInstance = new Chart(ctx1, {
            type: 'bar',
            data: {
                labels: ['Month 1', 'Month 2', 'Month 3', 'Month 4', 'Month 5', 'Month 6'],
                datasets: [
                    {
                        label: 'Income (Credits)',
                        data: [125000, 125000, 125000, 125000, 125000, 125000],
                        backgroundColor: '#10b981',
                        borderRadius: 6
                    },
                    {
                        label: 'Expenses (Debits)',
                        data: [68500, 71200, 64300, 69000, 73500, 68000],
                        backgroundColor: '#6366f1',
                        borderRadius: 6
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#94a3b8' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: '#334155' } }
                }
            }
        });

        // 2. Category Expense Doughnut Chart
        const ctx2 = document.getElementById('categoryChart').getContext('2d');
        if (categoryChartInstance) categoryChartInstance.destroy();

        const catLabels = Object.keys(categoryData);
        const catValues = Object.values(categoryData);

        categoryChartInstance = new Chart(ctx2, {
            type: 'doughnut',
            data: {
                labels: catLabels.length ? catLabels : ['HOUSING', 'EMI', 'SHOPPING_DINING', 'UTILITIES'],
                datasets: [{
                    data: catValues.length ? catValues : [192000, 111000, 72000, 27000],
                    backgroundColor: ['#6366f1', '#f59e0b', '#ec4899', '#3b82f6', '#10b981'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#94a3b8' } }
                }
            }
        });
    }

    // Tech Inspector Drawer Events
    toggleInspectorBtn.addEventListener('click', () => {
        inspectorDrawer.classList.toggle('hidden');
    });

    closeInspectorBtn.addEventListener('click', () => {
        inspectorDrawer.classList.add('hidden');
    });

    // Inspector Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(btn.dataset.tab).classList.add('active');
        });
    });
});
