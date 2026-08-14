from typing import Dict, Any

class FinancialAnalytics:
    """Parses raw Account Aggregator bank statement data and computes underwriting metrics."""

    @staticmethod
    def analyze_statement(statement_data: Dict[str, Any]) -> Dict[str, Any]:
        account = statement_data.get("account", {})
        transactions = statement_data.get("transactions", [])
        
        total_credits = sum(t["amount"] for t in transactions if t["type"] == "CREDIT")
        total_debits = sum(t["amount"] for t in transactions if t["type"] == "DEBIT")
        
        # Monthly averages (assuming 6 months data)
        months_count = 6
        avg_monthly_income = round(total_credits / months_count, 2)
        avg_monthly_expense = round(total_debits / months_count, 2)
        net_monthly_savings = round(avg_monthly_income - avg_monthly_expense, 2)
        
        # Savings Rate (%)
        savings_rate = round((net_monthly_savings / avg_monthly_income * 100), 1) if avg_monthly_income > 0 else 0
        
        # Category Breakdown
        categories = {}
        for t in transactions:
            cat = t.get("category", "OTHER")
            amt = t.get("amount", 0.0)
            if t["type"] == "DEBIT":
                categories[cat] = round(categories.get(cat, 0.0) + amt, 2)
                
        # Existing EMI obligation
        total_emi = categories.get("EMI", 0.0)
        monthly_emi = round(total_emi / months_count, 2)
        dti_ratio = round((monthly_emi / avg_monthly_income * 100), 1) if avg_monthly_income > 0 else 0
        
        # Risk Flags Evaluation
        cheque_bounces = statement_data.get("summary", {}).get("chequeBounces", 0)
        min_balance = min((t["currentBalance"] for t in transactions), default=0.0)
        
        risk_level = "LOW"
        risk_flags = []
        
        if cheque_bounces > 0:
            risk_flags.append(f"{cheque_bounces} Bounced Transactions Detected")
            risk_level = "HIGH"
            
        if dti_ratio > 45:
            risk_flags.append(f"High Debt-to-Income Ratio ({dti_ratio}%)")
            if risk_level != "HIGH":
                risk_level = "MEDIUM"
                
        if min_balance < 5000:
            risk_flags.append(f"Low Balance Dip Detected (₹{min_balance:,.2f})")
            
        if not risk_flags:
            risk_flags.append("No Negative Red Flags Found")
            
        # Automated Loan Eligibility Engine
        max_disposable = max(0, net_monthly_savings * 0.6)
        # Max tenure 36 months, interest 11% p.a. approx multiplier ~28x disposable monthly
        max_eligible_loan = round(max_disposable * 28, -3) # Round to nearest 1000
        
        decision = "APPROVED" if risk_level != "HIGH" and max_eligible_loan >= 100000 else "REJECTED"
        suggested_rate = 10.5 if risk_level == "LOW" else 13.5
        
        return {
            "accountHolder": account.get("holder", "Customer"),
            "bankName": account.get("bank", "Bank"),
            "accountNumber": account.get("number", "N/A"),
            "currentBalance": account.get("currentBalance", 0.0),
            "metrics": {
                "avgMonthlyIncome": avg_monthly_income,
                "avgMonthlyExpense": avg_monthly_expense,
                "netMonthlySavings": net_monthly_savings,
                "savingsRatePct": savings_rate,
                "monthlyExistingEmi": monthly_emi,
                "debtToIncomePct": dti_ratio,
                "total6MIncome": round(total_credits, 2),
                "total6MExpense": round(total_debits, 2)
            },
            "categoryExpenses": categories,
            "underwriting": {
                "riskLevel": risk_level,
                "riskFlags": risk_flags,
                "decision": decision,
                "eligibleLoanAmount": max_eligible_loan,
                "interestRatePct": suggested_rate,
                "recommendedTenureMonths": 36
            }
        }
