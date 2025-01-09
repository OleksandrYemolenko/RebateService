from abc import ABC, abstractmethod


class Specification(ABC):
    @abstractmethod
    def is_satisfied_by(self, transaction):
        pass


class MinAmountSpecification(Specification):
    def __init__(self, min_amount):
        self.min_amount = min_amount

    def is_satisfied_by(self, transaction):
        return transaction.amount >= self.min_amount


class TransactionDateRangeSpecification(Specification):
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date

    def is_satisfied_by(self, transaction):
        return self.start_date <= transaction.transaction_date <= self.end_date


class AndSpecification(Specification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def is_satisfied_by(self, transaction):
        return all(spec.is_satisfied_by(transaction) for spec in self.specifications)


class OrSpecification(Specification):
    def __init__(self, *specifications):
        self.specifications = specifications

    def is_satisfied_by(self, transaction):
        return any(spec.is_satisfied_by(transaction) for spec in self.specifications)


class NotSpecification(Specification):
    def __init__(self, specification):
        self.specification = specification

    def is_satisfied_by(self, transaction):
        return not self.specification.is_satisfied_by(transaction)
