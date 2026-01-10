from .base import SessionLocal, text

def crawl_kind_market_actions():
    """
    Crawls KRX KIND for Inspection/Market Actions.
    For MVP/Spec, this creates STUB data for demonstration.
    """
    print("Fetching KIND Market Actions (Stub Mode)...", flush=True)
    
    stub_data = [
        {"code": "005930", "type": "INVESTMENT_CAUTION", "reason": "Short-term Overheating", "severity": "LOW"},
        {"code": "000660", "type": "NONE", "reason": "", "severity": "TRIVIAL"},
        {"code": "051910", "type": "MANAGEMENT_ITEM", "reason": "Insufficient Activity", "severity": "HIGH"} # hypothetical
    ]
    
    with SessionLocal() as db:
        try:
            for item in stub_data:
                # Find security
                # Security Master might not be populated or linked yet, so we just use stock_code for now
                
                # Check duplication?
                # Simplified UPSERT
                stmt = text("""
                    INSERT INTO kind_market_action (stock_code, security_id, action_type, reason, severity, start_date)
                    VALUES (:c, 0, :t, :r, :s, CURRENT_DATE)
                """)
                # Note: security_id 0 is placeholder
                
                db.execute(stmt, {
                    "c": item["code"],
                    "t": item["type"],
                    "r": item["reason"],
                    "s": item["severity"]
                })
                
            db.commit()
            print("KIND Stub Data Loaded.")
            
        except Exception as e:
            print(f"KIND Load Failed: {e}")
            db.rollback()
        finally:
            db.close()

if __name__ == "__main__":
    crawl_kind_market_actions()
