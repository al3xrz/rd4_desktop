from __future__ import annotations


class DomainError(Exception):
    """Base class for application-level errors."""


class ValidationError(DomainError):
    pass


class NotFoundError(DomainError):
    pass


class PermissionDeniedError(DomainError):
    pass


class BusinessRuleError(DomainError):
    pass


class DuplicateError(DomainError):
    pass
