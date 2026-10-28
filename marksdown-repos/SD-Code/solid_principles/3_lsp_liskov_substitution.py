"""
L - Liskov Substitution Principle
Subclasses must be usable anywhere the parent is expected,
without breaking the program's correctness.

Example: withdrawing money from accounts.
"""


# ---------- BAD: subclass breaks the parent's contract ----------
class BadAccount:
    def __init__(self, balance):
        self.balance = balance

    def withdraw(self, amount):
        self.balance -= amount


class BadFixedDeposit(BadAccount):
    def withdraw(self, amount):
        # Parent promises withdraw() works; this subclass blows up.
        raise Exception("Cannot withdraw from a fixed deposit!")


def bad_pay_bill(account: BadAccount, amount):
    account.withdraw(amount)  # crashes if given a BadFixedDeposit


# ---------- GOOD: model what each type can really do ----------
class Account:
    def __init__(self, balance):
        self.balance = balance


class WithdrawableAccount(Account):
    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        self.balance -= amount


class SavingsAccount(WithdrawableAccount):
    pass


class CurrentAccount(WithdrawableAccount):
    pass


class FixedDeposit(Account):
    """Not withdrawable, so it does not claim to be."""

    def mature(self):
        return self.balance * 1.07


def pay_bill(account: WithdrawableAccount, amount):
    account.withdraw(amount)  # works for ANY WithdrawableAccount subtype
    return account.balance


if __name__ == "__main__":
    try:
        bad_pay_bill(BadFixedDeposit(1000), 100)
    except Exception as e:
        print("BAD  :", e)

    for acct in (SavingsAccount(1000), CurrentAccount(500)):
        print(f"GOOD {type(acct).__name__}: balance after bill =", pay_bill(acct, 100))
    print("GOOD FixedDeposit maturity value =", FixedDeposit(1000).mature())
