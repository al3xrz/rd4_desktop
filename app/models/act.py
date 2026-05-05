from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Act(Base):
    __tablename__ = "acts"

    id = Column(Integer, primary_key=True)
    number = Column(String, unique=True, index=True, nullable=False)
    contract_id = Column(Integer, ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    deleted = Column(Boolean, nullable=False, default=False, server_default="0")
    comments = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    contract = relationship("Contract", back_populates="acts", lazy="joined")
    user = relationship("User", back_populates="acts", lazy="joined")
    services = relationship("ActMedService", back_populates="act", cascade="all, delete-orphan", lazy="selectin")
