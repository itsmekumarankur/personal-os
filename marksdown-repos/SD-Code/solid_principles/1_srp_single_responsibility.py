"""
S - Single Responsibility Principle
A class should have only ONE reason to change.

Example: generating and delivering an account statement.
"""


# ---------- BAD: one class does everything ----------
class BadStatementService:
    def __init__(self, account_id, transactions):
        self.account_id = account_id
        self.transactions = transactions

    def generate_and_send(self, email):
        # 1) business logic (calculation)
        total = sum(self.transactions)
        # 2) formatting
        text = f"Statement for {self.account_id}: total = {total}"
        # 3) delivery
        print(f"[BAD] Sending email to {email}: {text}")
        # Changes to calculation, format OR delivery all force edits here.


# ---------- GOOD: each class has one job ----------
class StatementCalculator:
    """Only knows how to calculate."""

    def total(self, transactions):
        return sum(transactions)


class StatementFormatter:
    """Only knows how to format."""

    def format(self, account_id, total):
        return f"Statement for {account_id}: total = {total}"


class EmailSender:
    """Only knows how to deliver."""

    def send(self, email, message):
        print(f"[GOOD] Sending email to {email}: {message}")


class StatementService:
    """Coordinates the three collaborators."""

    def __init__(self, calculator, formatter, sender):
        self.calculator = calculator
        self.formatter = formatter
        self.sender = sender

    def run(self, account_id, transactions, email):
        total = self.calculator.total(transactions)
        message = self.formatter.format(account_id, total)
        self.sender.send(email, message)


if __name__ == "__main__":
    txns = [100, 250, -50]

    BadStatementService("ACC-1", txns).generate_and_send("user@example.com")

    service = StatementService(StatementCalculator(), StatementFormatter(), EmailSender())
    service.run("ACC-1", txns, "user@example.com")
