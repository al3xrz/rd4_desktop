from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class ActMedService(Base):
    __tablename__ = "act_med_services"

    id = Column(Integer, primary_key=True)
    act_id = Column(Integer, ForeignKey("acts.id", ondelete="CASCADE"), nullable=False)
    med_service_id = Column(Integer, ForeignKey("med_services.id", ondelete="RESTRICT"), nullable=False)
    current_code = Column(String, nullable=True, index=True)
    current_name = Column(String, nullable=False, index=True)
    unit = Column(String, nullable=False, default="шт", server_default="шт")
    price = Column(Numeric(12, 2), nullable=False)
    discount = Column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    count = Column(Integer, nullable=False, default=1, server_default="1")
    deleted = Column(Boolean, nullable=False, default=False, server_default="0")
    comments = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    act = relationship("Act", back_populates="services", lazy="select")
    med_service = relationship("MedService", back_populates="act_rows", lazy="joined")
