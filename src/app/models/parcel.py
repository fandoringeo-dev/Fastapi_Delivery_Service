import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import ParcelStatus
from app.db.base import Base


class Parcel(Base):
    __tablename__ = "parcels"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    client_session_id: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[ParcelStatus] = mapped_column(
        Enum(ParcelStatus), nullable=False, default=ParcelStatus.PENDING.value
    )
    weight_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    type_id: Mapped[int] = mapped_column(
        ForeignKey("parcel_types.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    declared_value_usd: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    delivery_cost_rub: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2), nullable=True
    )
    company_id: Mapped[int | None] = mapped_column(nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    parcel_type: Mapped["ParcelType"] = relationship(back_populates="parcels")
