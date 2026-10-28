"""
O - Open/Closed Principle
Software should be OPEN for extension but CLOSED for modification.

Example: calculating fees for different account types.
"""


# ---------- BAD: every new account type edits this function ----------
def bad_fee(account_type, amount):
    if account_type == "savings":
        return amount * 0.01
    elif account_type == "current":
        return amount * 0.02
    # Adding "premium" means modifying this function (risk of breaking old code).
    raise ValueError("Unknown account type")


# ---------- GOOD: add new behaviour by adding a new class ----------
class FeeStrategy:
    def fee(self, amount):
        raise NotImplementedError


class SavingsFee(FeeStrategy):
    def fee(self, amount):
        return amount * 0.01


class CurrentFee(FeeStrategy):
    def fee(self, amount):
        return amount * 0.02


class PremiumFee(FeeStrategy):  # NEW type: no existing code touched
    def fee(self, amount):
        return 0.0


def calculate_fee(strategy: FeeStrategy, amount):
    return strategy.fee(amount)  # never changes


if __name__ == "__main__":
    print("BAD  savings:", bad_fee("savings", 1000))
    for strategy in (SavingsFee(), CurrentFee(), PremiumFee()):
        print(f"GOOD {type(strategy).__name__}:", calculate_fee(strategy, 1000))
