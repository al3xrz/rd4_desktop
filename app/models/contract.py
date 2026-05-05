from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id = Column(Integer, primary_key=True)
    contract_number = Column(String, unique=True, index=True, nullable=False)
    contract_date = Column(DateTime(timezone=True), nullable=False)
    birth_history_number = Column(String, nullable=True)
    category = Column(String, nullable=True)

    patient_name = Column(String, nullable=False)
    patient_birth_date = Column(DateTime(timezone=True), nullable=False)
    patient_reg_address = Column(String, nullable=False)
    patient_live_address = Column(String, nullable=False)
    patient_phone = Column(String, nullable=False)
    patient_passport_issued_by = Column(String, nullable=False)
    patient_passport_issued_code = Column(String, nullable=False)
    patient_passport_series = Column(String, nullable=False)
    patient_passport_date = Column(DateTime(timezone=True), nullable=False)

    delegate_name = Column(String, nullable=True)
    delegate_birth_date = Column(DateTime(timezone=True), nullable=True)
    delegate_reg_address = Column(String, nullable=True)
    delegate_live_address = Column(String, nullable=True)
    delegate_phone = Column(String, nullable=True)
    delegate_passport_issued_by = Column(String, nullable=True)
    delegate_passport_issued_code = Column(String, nullable=True)
    delegate_passport_series = Column(String, nullable=True)
    delegate_passport_date = Column(DateTime(timezone=True), nullable=True)

    inpatient_treatment = Column(Boolean, nullable=True)
    childbirth = Column(Boolean, nullable=True)
    prepay_inpatient_treatment = Column(Numeric(12, 2), nullable=True)
    prepay_childbirth = Column(Numeric(12, 2), nullable=True)
    service_payed = Column(Boolean, nullable=True)
    service_insurance = Column(Boolean, nullable=True)
    service_insurance_number = Column(String, nullable=True)

    discharged = Column(Boolean, nullable=True)
    discharge_date = Column(DateTime(timezone=True), nullable=True)
    deleted = Column(Boolean, nullable=False, default=False, server_default="0")
    comments = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    created_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_by_user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    payments = relationship("Payment", back_populates="contract", cascade="all, delete-orphan", lazy="selectin")
    acts = relationship("Act", back_populates="contract", cascade="all, delete-orphan", lazy="selectin")
    created_by_user = relationship(
        "User",
        foreign_keys=[created_by_user_id],
        back_populates="created_contracts",
        lazy="joined",
    )
    updated_by_user = relationship(
        "User",
        foreign_keys=[updated_by_user_id],
        back_populates="updated_contracts",
        lazy="joined",
    )
