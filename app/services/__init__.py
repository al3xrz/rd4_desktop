"""Application services for RD4 desktop."""

from app.services.act import ActService
from app.services.auth import AuthService
from app.services.contract import ContractService
from app.services.docx import DocxService
from app.services.med_service import MedServiceService
from app.services.payment import PaymentService
from app.services.report import ReportService

__all__ = [
    "ActService",
    "AuthService",
    "ContractService",
    "DocxService",
    "MedServiceService",
    "PaymentService",
    "ReportService",
]
