import uuid
from datetime import datetime, timedelta
import random

class MockDataEngine:
    """Generates realistic Account Aggregator mock bank statement data for demo purposes."""
    
    @staticmethod
    def generate_consent_response(customer_phone: str = "9999999999"):
        consent_id = f"mock-consent-{uuid.uuid4().hex[:8]}"
        redirect_url = f"http://127.0.0.1:8000/?action=consent_approve&consent_id={consent_id}"
        return {
            "status_code": 201,
            "id": consent_id,
            "consent_status": "PENDING",
            "consent_details": {
                "id": consent_id,
                "status": "PENDING",
                "redirectUrl": redirect_url,
                "Customer": {"id": customer_phone},
                "consentStart": datetime.now().isoformat(),
                "consentExpiry": (datetime.now() + timedelta(days=90)).isoformat()
            }
        }

    @staticmethod
    def generate_session_response(consent_id: str):
        session_id = f"mock-session-{uuid.uuid4().hex[:8]}"
        return {
            "status_code": 201,
            "session": {
                "sessionId": session_id,
                "consentId": consent_id,
                "status": "COMPLETED",
                "format": "json"
            }
        }

    @staticmethod
    def generate_bank_statement(customer_name: str = "Rahul Sharma", bank_name: str = "HDFC Bank"):
        now = datetime.now()
        months = 6
        
        account_number = f"501002{random.randint(100000, 999999)}"
        monthly_salary = 125000
        
        transactions = []
        balance = 45000.0
        
        # Generate 6 months of historical transactions
        for m in range(months, 0, -1):
            month_date = now - timedelta(days=m * 30)
            
            # 1. Salary Credit (1st of every month)
            salary_date = month_date.replace(day=1)
            balance += monthly_salary
            transactions.append({
                "txnId": f"TXN-SAL-{salary_date.strftime('%Y%m%d')}",
                "timestamp": salary_date.strftime("%Y-%m-%dT09:30:00Z"),
                "type": "CREDIT",
                "amount": float(monthly_salary),
                "currentBalance": float(balance),
                "narration": "ACH CREDIT - TECH CORP INFOTECH SALARY",
                "mode": "ACH",
                "category": "SALARY"
            })
            
            # 2. Rent Expense (5th of every month)
            rent_date = month_date.replace(day=5)
            rent_amount = 32000.0
            balance -= rent_amount
            transactions.append({
                "txnId": f"TXN-RENT-{rent_date.strftime('%Y%m%d')}",
                "timestamp": rent_date.strftime("%Y-%m-%dT11:00:00Z"),
                "type": "DEBIT",
                "amount": rent_amount,
                "currentBalance": float(balance),
                "narration": "UPI/HOUSE RENT TRANSFER TO LANDLORD",
                "mode": "UPI",
                "category": "HOUSING"
            })
            
            # 3. Existing Loan EMI (10th of every month)
            emi_date = month_date.replace(day=10)
            emi_amount = 18500.0
            balance -= emi_amount
            transactions.append({
                "txnId": f"TXN-EMI-{emi_date.strftime('%Y%m%d')}",
                "timestamp": emi_date.strftime("%Y-%m-%dT04:00:00Z"),
                "type": "DEBIT",
                "amount": emi_amount,
                "currentBalance": float(balance),
                "narration": "AUTO DEBIT - HDFC AUTO LOAN EMI",
                "mode": "NACH",
                "category": "EMI"
            })

            # 4. Utility Bills & Subscriptions (15th)
            bill_date = month_date.replace(day=15)
            bill_amount = 4500.0
            balance -= bill_amount
            transactions.append({
                "txnId": f"TXN-UTIL-{bill_date.strftime('%Y%m%d')}",
                "timestamp": bill_date.strftime("%Y-%m-%dT14:20:00Z"),
                "type": "DEBIT",
                "amount": bill_amount,
                "currentBalance": float(balance),
                "narration": "BILLPAY - ELECTRICITY & BROADBAND",
                "mode": "BILLPAY",
                "category": "UTILITIES"
            })
            
            # 5. Food, Shopping & Swiggy/Uber (Random transactions throughout month)
            for day in [8, 12, 18, 22, 27]:
                tx_date = month_date.replace(day=day)
                spend = float(random.randint(600, 3500))
                balance -= spend
                vendor = random.choice(["SWIGGY", "AMAZON", "UBER", "DMART", "ZOMATO", "BIGBASKET"])
                transactions.append({
                    "txnId": f"TXN-SHOP-{tx_date.strftime('%Y%m%d')}-{day}",
                    "timestamp": tx_date.strftime("%Y-%m-%dT19:15:00Z"),
                    "type": "DEBIT",
                    "amount": spend,
                    "currentBalance": float(balance),
                    "narration": f"UPI/{vendor}/PAYMENT",
                    "mode": "UPI",
                    "category": "SHOPPING_DINING"
                })

        # Sort transactions by timestamp ascending
        transactions.sort(key=lambda x: x["timestamp"])

        return {
            "account": {
                "type": "SAVINGS",
                "number": account_number,
                "bank": bank_name,
                "holder": customer_name,
                "currentBalance": round(balance, 2),
                "currency": "INR",
                "openingDate": "2019-04-12"
            },
            "summary": {
                "monthlySalary": monthly_salary,
                "averageMonthlyBalance": round(balance + 25000, 2),
                "totalCredits6M": monthly_salary * months,
                "totalDebits6M": round(sum(t["amount"] for t in transactions if t["type"] == "DEBIT"), 2),
                "chequeBounces": 0
            },
            "transactions": transactions
        }
