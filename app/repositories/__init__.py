"""Data access repositories for RD4 desktop."""

from app.repositories.act import ActRepository
from app.repositories.act_med_service import ActMedServiceRepository
from app.repositories.base import BaseRepository
from app.repositories.contract import ContractRepository
from app.repositories.med_service import MedServiceRepository
from app.repositories.payment import PaymentRepository
from app.repositories.user import UserRepository

__all__ = [
    "ActRepository",
    "ActMedServiceRepository",
    "BaseRepository",
    "ContractRepository",
    "MedServiceRepository",
    "PaymentRepository",
    "UserRepository",
]
