"""
D - Dependency Inversion Principle
High-level modules should not depend on low-level modules.
Both should depend on ABSTRACTIONS.

Example: a payment service that can use different payment gateways.
"""

from abc import ABC, abstractmethod


# ---------- BAD: high-level class hard-wires a concrete low-level class ----------
class BadUpiGateway:
    def pay(self, amount):
        print(f"[BAD] Paid {amount} via UPI")


class BadPaymentService:
    def __init__(self):
        self.gateway = BadUpiGateway()  # tightly coupled, hard to swap or test

    def checkout(self, amount):
        self.gateway.pay(amount)


# ---------- GOOD: depend on an abstraction, inject the implementation ----------
class PaymentGateway(ABC):
    @abstractmethod
    def pay(self, amount): ...


class UpiGateway(PaymentGateway):
    def pay(self, amount):
        print(f"[GOOD] Paid {amount} via UPI")


class CardGateway(PaymentGateway):
    def pay(self, amount):
        print(f"[GOOD] Paid {amount} via Card")


class FakeGateway(PaymentGateway):
    """Test double: no real money moves."""

    def __init__(self):
        self.payments = []

    def pay(self, amount):
        self.payments.append(amount)


class PaymentService:
    def __init__(self, gateway: PaymentGateway):  # injected dependency
        self.gateway = gateway

    def checkout(self, amount):
        self.gateway.pay(amount)


if __name__ == "__main__":
    BadPaymentService().checkout(500)

    PaymentService(UpiGateway()).checkout(500)
    PaymentService(CardGateway()).checkout(500)

    # Easy unit testing thanks to the abstraction
    fake = FakeGateway()
    PaymentService(fake).checkout(500)
    assert fake.payments == [500]
    print("Test with FakeGateway passed:", fake.payments)
