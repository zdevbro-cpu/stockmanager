from __future__ import annotations

from datetime import date, datetime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import (
    String, Integer, Float, Date, DateTime, Boolean, ForeignKey, UniqueConstraint, Index, JSON, Enum
)


class Base(DeclarativeBase):
    pass


class Security(Base):
    __tablename__ = "security"
    security_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticker: Mapped[str] = mapped_column(String(12), unique=True, index=True)
    isin: Mapped[str | None] = mapped_column(String(20), nullable=True)
    market: Mapped[str | None] = mapped_column(String(20), nullable=True)
    currency: Mapped[str | None] = mapped_column(String(10), nullable=True)
    lot_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    tick_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    company_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("company.company_id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ClassificationTaxonomy(Base):
    __tablename__ = "classification_taxonomy"
    taxonomy_id: Mapped[str] = mapped_column(String(50), primary_key=True)  # KIS_INDUSTRY, THEME
    kind: Mapped[str] = mapped_column(String(20))  # INDUSTRY, THEME
    name: Mapped[str] = mapped_column(String(200))
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class ClassificationNode(Base):
    __tablename__ = "classification_node"
    taxonomy_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("classification_taxonomy.taxonomy_id", ondelete="CASCADE"),
        primary_key=True,
    )
    code: Mapped[str] = mapped_column(String(80), primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parent_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_class_node_tax_parent", "taxonomy_id", "parent_code"),
        Index("idx_class_node_tax_level", "taxonomy_id", "level"),
    )


class SecurityClassification(Base):
    __tablename__ = "security_classification"
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("security.ticker", ondelete="CASCADE"), primary_key=True
    )
    taxonomy_id: Mapped[str] = mapped_column(String(50), primary_key=True)
    code: Mapped[str] = mapped_column(String(80), primary_key=True)
    effective_from: Mapped[date | None] = mapped_column(Date, primary_key=True, nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    effective_to: Mapped[date | None] = mapped_column(Date, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_sec_class_ticker", "ticker"),
        Index("idx_sec_class_tax_code", "taxonomy_id", "code"),
    )


class PriceDaily(Base):
    __tablename__ = "price_daily"
    ticker: Mapped[str] = mapped_column(
        String(12), ForeignKey("security.ticker", ondelete="CASCADE"), primary_key=True
    )
    trade_date: Mapped[date] = mapped_column(Date, primary_key=True)
    close: Mapped[float] = mapped_column(Float)
    volume: Mapped[float | None] = mapped_column(Float, nullable=True)
    turnover_krw: Mapped[float | None] = mapped_column(Float, nullable=True)

    __table_args__ = (Index("idx_price_daily_date", "trade_date"),)


class RecommendationRow(Base):
    __tablename__ = "recommendation"
    as_of_date: Mapped[date] = mapped_column(Date, primary_key=True, index=True)
    strategy_id: Mapped[str] = mapped_column(String(80), primary_key=True, index=True)
    strategy_version: Mapped[str] = mapped_column(String(20), primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(12), ForeignKey("security.ticker", ondelete="CASCADE"), primary_key=True, index=True)
    rank: Mapped[int] = mapped_column(Integer)
    score: Mapped[float | None] = mapped_column(Float, nullable=True)
    target_weight: Mapped[float] = mapped_column(Float)
    rationale: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    __table_args__ = (
        Index("idx_reco_lookup", "as_of_date", "strategy_id", "strategy_version"),
    )


class TimingSignalRow(Base):
    __tablename__ = "timing_signal"
    ts: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True, index=True)
    ticker: Mapped[str] = mapped_column(String(12), ForeignKey("security.ticker", ondelete="CASCADE"), primary_key=True, index=True)
    horizon: Mapped[str] = mapped_column(String(10), primary_key=True)
    signal: Mapped[str] = mapped_column(Enum("BUY", "WAIT", "REDUCE", "SELL", name="signal_type"))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    triggers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    risk_flags: Mapped[list | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    __table_args__ = (Index("idx_signal_lookup", "ticker", "horizon", "ts"),)


class SignalConfigRow(Base):
    __tablename__ = "signal_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    engine: Mapped[str] = mapped_column(String(50), nullable=False)
    horizons: Mapped[dict] = mapped_column(JSON, nullable=False)
    weights: Mapped[dict] = mapped_column(JSON, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)
