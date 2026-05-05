from __future__ import annotations

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class MedService(Base):
    __tablename__ = "med_services"

    id = Column(Integer, primary_key=True)
    code = Column(String, nullable=True, index=True)
    parent_id = Column(Integer, ForeignKey("med_services.id", ondelete="CASCADE"), nullable=True)
    is_folder = Column(Boolean, nullable=False)
    name = Column(String, nullable=False, index=True)
    unit = Column(String, nullable=False, default="", server_default="")
    price = Column(Numeric(12, 2), nullable=False, default=0, server_default="0")
    vat = Column(Float, nullable=False, default=0, server_default="0")
    deleted = Column(Boolean, nullable=False, default=False, server_default="0")
    comments = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=True, onupdate=func.now())

    parent = relationship("MedService", remote_side=[id], back_populates="children", lazy="joined")
    children = relationship("MedService", back_populates="parent", cascade="all, delete-orphan", lazy="selectin")
    act_rows = relationship("ActMedService", back_populates="med_service", lazy="noload")
