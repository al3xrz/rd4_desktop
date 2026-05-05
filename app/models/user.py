from __future__ import annotations

import enum

from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Role(str, enum.Enum):
    OPERATOR = "operator"
    CASHIER = "cashier"
    ADMIN = "admin"


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    role = Column(
        Enum(Role, values_callable=lambda roles: [role.value for role in roles]),
        nullable=False,
        default=Role.OPERATOR,
        server_default=Role.OPERATOR.value,
    )
    comments = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    acts = relationship("Act", back_populates="user", lazy="noload")
    created_contracts = relationship(
        "Contract",
        foreign_keys="Contract.created_by_user_id",
        back_populates="created_by_user",
        lazy="noload",
    )
    updated_contracts = relationship(
        "Contract",
        foreign_keys="Contract.updated_by_user_id",
        back_populates="updated_by_user",
        lazy="noload",
    )
    payments = relationship(
        "Payment",
        foreign_keys="Payment.user_id",
        back_populates="user",
        lazy="noload",
    )
    unposted_payments = relationship(
        "Payment",
        foreign_keys="Payment.unposted_by_id",
        back_populates="unposted_by",
        lazy="noload",
    )
