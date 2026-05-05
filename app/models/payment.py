from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    amount = Column(Numeric(12, 2), nullable=False)
    posted = Column(Boolean, nullable=False, default=True, server_default="1")
    unposted_at = Column(DateTime(timezone=True), nullable=True)
    unposted_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    unpost_reason = Column(String, nullable=True)
    deleted = Column(Boolean, nullable=False, default=False, server_default="0")
    comments = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)

    contract = relationship("Contract", back_populates="payments", lazy="joined")
    user = relationship("User", foreign_keys=[user_id], back_populates="payments", lazy="joined")
    unposted_by = relationship(
        "User",
        foreign_keys=[unposted_by_id],
        back_populates="unposted_payments",
        lazy="joined",
    )
