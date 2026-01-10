from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
import json

# Add ingest path for DB access
import sys
import os
INGEST_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../services/ingest"))
if INGEST_PATH not in sys.path:
    sys.path.append(INGEST_PATH)

from ingest.db import SessionLocal
from sqlalchemy import text

router = APIRouter(prefix="/financials", tags=["Financials"])

class FinRatio(BaseModel):
    fiscal_year: int
    op_margin: float
    roe: float
    debt_ratio: float

class FinSummary(BaseModel):
    fiscal_year: int
    revenue: float
    op_income: float
    net_income: float
    assets: float
    equity: float

class MarketAction(BaseModel):
    action_type: str
    reason: str
    start_date: str
    severity: str

class FinancialsResponse(BaseModel):
    company_id: int
    summary_3y: List[FinSummary]
    ratios_3y: List[FinRatio]
    market_actions: List[MarketAction]

@router.get("/{company_id}", response_model=FinancialsResponse)
def get_company_financials(company_id: int):
    with SessionLocal() as db:
        # 1. Fetch 3Y Summary (Mart)
        summary_query = text("""
            SELECT fiscal_year, revenue, op_income, net_income, assets, equity
            FROM fs_mart_annual
            WHERE company_id = :cid
            ORDER BY fiscal_year DESC
            LIMIT 3
        """)
        summary_rows = db.execute(summary_query, {"cid": company_id}).fetchall()
        summary_3y = [
            FinSummary(
                fiscal_year=row.fiscal_year,
                revenue=float(row.revenue or 0),
                op_income=float(row.op_income or 0),
                net_income=float(row.net_income or 0),
                assets=float(row.assets or 0),
                equity=float(row.equity or 0)
            ) for row in summary_rows
        ]
        # Sort ASC for chart/display
        summary_3y.sort(key=lambda x: x.fiscal_year)

        # 2. Fetch Ratios (Mart)
        ratio_query = text("""
            SELECT fiscal_year, op_margin, roe, debt_ratio
            FROM fs_ratio_mart
            WHERE company_id = :cid AND period_type = 'ANNUAL'
            ORDER BY fiscal_year DESC
            LIMIT 3
        """)
        ratio_rows = db.execute(ratio_query, {"cid": company_id}).fetchall()
        ratios_3y = [
            FinRatio(
                fiscal_year=row.fiscal_year,
                op_margin=float(row.op_margin or 0),
                roe=float(row.roe or 0),
                debt_ratio=float(row.debt_ratio or 0)
            ) for row in ratio_rows
        ]
        ratios_3y.sort(key=lambda x: x.fiscal_year)

        # 3. Fetch Risks (KIND) - using stock_code join or direct security_id if available
        # Currently standard implementation assumes company -> security link.
        # Fallback: find stock_code by company_id, then query kind
        
        # Simple Join
        risk_query = text("""
            SELECT k.action_type, k.reason, k.start_date, k.severity
            FROM kind_market_action k
            JOIN security_master s ON k.stock_code = s.stock_code
            WHERE s.company_id = :cid
            AND (k.end_date IS NULL OR k.end_date >= CURRENT_DATE)
        """)
        # If security_master is not populated, we might miss this.
        # Minimal viable query assuming loose coupling (by stock_code if company has it)
        
        # Try direct or via security
        # For Demo/MVP, let's use a simpler query if tables aren't fully linked
        # "SELECT * FROM kind_market_action WHERE stock_code IN (SELECT stock_code FROM company WHERE id = :cid)" (Conceptual)
        
        # Since we use stub data and mapped codes.
        # Let's assume passed company_id maps to a stock code in 'company' table
        
        risk_rows = db.execute(risk_query, {"cid": company_id}).fetchall()
        market_actions = [
            MarketAction(
                action_type=row.action_type,
                reason=row.reason or "-",
                start_date=str(row.start_date),
                severity=row.severity
            ) for row in risk_rows
        ]

        return FinancialsResponse(
            company_id=company_id,
            summary_3y=summary_3y,
            ratios_3y=ratios_3y,
            market_actions=market_actions
        )

@router.get("/{company_id}/chart/{chart_key}")
def get_financial_chart(company_id: int, chart_key: str):
    """
    Returns cached chart data for Recharts
    """
    with SessionLocal() as db:
        # Check cache first
        cache = db.execute(
            text("SELECT payload FROM chart_cache WHERE company_id = :cid AND chart_key = :key"),
            {"cid": company_id, "key": chart_key}
        ).scalar()
        
        if cache:
            return cache
            
        # If no cache (Cold Start), generate on-the-fly (Stub logic for MVP)
        # In real spec, this should trigger a generation job or calc logic.
        # Here we return a standardized structure based on marts.
        
        if chart_key == "FIN_IS_ANNUAL_3Y":
            # Generate from Mart
            rows = db.execute(text("""
                SELECT fiscal_year, revenue, op_income, net_income
                FROM fs_mart_annual
                WHERE company_id = :cid
                ORDER BY fiscal_year ASC
                LIMIT 5
            """), {"cid": company_id}).fetchall()
            
            data = [
                {
                    "name": str(row.fiscal_year),
                    "매출액": float(row.revenue or 0),
                    "영업이익": float(row.op_income or 0),
                    "순이익": float(row.net_income or 0)
                } for row in rows
            ]
            return data
            
        elif chart_key == "FIN_RATIO_TREND":
             rows = db.execute(text("""
                SELECT fiscal_year, op_margin, roe
                FROM fs_ratio_mart
                WHERE company_id = :cid AND period_type = 'ANNUAL'
                ORDER BY fiscal_year ASC
                LIMIT 5
            """), {"cid": company_id}).fetchall()
             
             data = [
                {
                    "name": str(row.fiscal_year),
                    "영업이익률": float(row.op_margin or 0),
                    "ROE": float(row.roe or 0)
                } for row in rows
            ]
             return data
        
        raise HTTPException(status_code=404, detail="Chart not found")
