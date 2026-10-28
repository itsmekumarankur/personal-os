"""
I - Interface Segregation Principle
Clients should not be forced to depend on methods they do not use.
Prefer several small, focused interfaces over one fat interface.

Example: different kinds of investment products.
"""

from abc import ABC, abstractmethod


# ---------- BAD: one fat interface ----------
class BadInvestment(ABC):
    @abstractmethod
    def buy(self): ...

    @abstractmethod
    def sell(self): ...

    @abstractmethod
    def pay_dividend(self): ...

    @abstractmethod
    def apply_for_ipo(self): ...


class BadMutualFund(BadInvestment):
    def buy(self):
        print("Buying fund units")

    def sell(self):
        print("Redeeming fund units")

    def pay_dividend(self):
        print("Paying dividend")

    def apply_for_ipo(self):
        # Forced to implement something that makes no sense for a mutual fund
        raise NotImplementedError("Mutual funds have no IPO")


# ---------- GOOD: small, focused interfaces ----------
class Tradable(ABC):
    @abstractmethod
    def buy(self): ...

    @abstractmethod
    def sell(self): ...


class DividendPaying(ABC):
    @abstractmethod
    def pay_dividend(self): ...


class IPOApplicable(ABC):
    @abstractmethod
    def apply_for_ipo(self): ...


class MutualFund(Tradable, DividendPaying):
    def buy(self):
        print("Buying fund units")

    def sell(self):
        print("Redeeming fund units")

    def pay_dividend(self):
        print("Paying dividend")


class NewCompanyShare(Tradable, IPOApplicable):
    def buy(self):
        print("Buying shares")

    def sell(self):
        print("Selling shares")

    def apply_for_ipo(self):
        print("Applying for IPO")


if __name__ == "__main__":
    try:
        BadMutualFund().apply_for_ipo()
    except NotImplementedError as e:
        print("BAD  :", e)

    fund = MutualFund()
    fund.buy()
    fund.pay_dividend()  # no unused apply_for_ipo() in sight

    share = NewCompanyShare()
    share.apply_for_ipo()
    share.sell()
