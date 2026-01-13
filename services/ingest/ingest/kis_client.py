import requests
import json
from ingest.config import settings

class KisClient:
    def __init__(self):
        self.base_url = settings.KIS_BASE_URL
        self.app_key = settings.KIS_API_KEY
        self.app_secret = settings.KIS_API_SECRET_KEY
        self.access_token = None
        
        if not self.app_key or not self.app_secret:
            print("WARNING: KIS Credentials missing.")

    def _get_token(self):
        if self.access_token:
            return self.access_token
            
        url = f"{self.base_url}/oauth2/tokenP"
        headers = {"content-type": "application/json"}
        body = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret
        }
        
        resp = requests.post(url, headers=headers, data=json.dumps(body))
        if resp.status_code == 200:
            self.access_token = resp.json().get("access_token")
            return self.access_token
        if "EGW00133" in resp.text:
            print(f"KIS Token Error (rate limit): {resp.text}")
            import time
            time.sleep(65)
            resp = requests.post(url, headers=headers, data=json.dumps(body))
            if resp.status_code == 200:
                self.access_token = resp.json().get("access_token")
                return self.access_token
        print(f"KIS Token Error: {resp.text}")
        raise Exception("Failed to get KIS token")

    def get_current_price(self, ticker: str):
        token = self._get_token()
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100"
        }
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_input_iscd": ticker
        }
        
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json().get("output")
        else:
            print(f"KIS Price Error for {ticker}: {resp.text}")
            return None

    def get_market_index(self, index_code: str):
        # 0001: KOSPI, 1001: KOSDAQ
        from datetime import datetime, timedelta

        end_date = datetime.now()
        start_date = end_date - timedelta(days=10)

        rows = self.get_market_index_history(
            index_code,
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d"),
        )
        if rows:
            return rows[-1]
        return None

    def get_market_index_history(self, index_code: str, start_date: str | None = None, end_date: str | None = None):
        """
        Fetch daily index chart data (history) for the given index.
        Dates should be YYYYMMDD. If omitted, KIS decides the range.
        """
        try:
            token = self._get_token()
        except Exception as exc:
            print(f"KIS Index Intraday Token Error: {exc}")
            return []
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-index-chartprice"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKUP03500100",
            "custtype": "P",
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code,
            "FID_INPUT_DATE_1": start_date or "",
            "FID_INPUT_DATE_2": end_date or "",
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
        }

        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            rows = data.get("output2") or []
            return list(reversed(rows))
        print(f"KIS Index History Error for {index_code}: status={resp.status_code} body={resp.text[:200]}")
        return []

    def get_market_index_intraday(self, index_code: str, date: str | None = None):
        """
        Fetch intraday (minute) index chart data for the given index.
        Date should be YYYYMMDD; defaults to today.
        """
        from datetime import datetime

        token = self._get_token()
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-time-index-chartprice"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKUP03500200",
            "custtype": "P",
        }
        target_date = date or datetime.now().strftime("%Y%m%d")
        params_base = {
            "FID_COND_MRKT_DIV_CODE": "U",
            "FID_INPUT_ISCD": index_code,
            "FID_INPUT_DATE_1": target_date,
        }

        for hour, include_prev in (("000000", "N"), ("090000", "N"), ("000000", "Y")):
            params = {
                **params_base,
                "FID_INPUT_HOUR_1": hour,
                "FID_PW_DATA_INCU_YN": include_prev,
            }
            resp = requests.get(url, headers=headers, params=params)
            if resp.status_code == 200:
                data = resp.json()
                rows = data.get("output2") or data.get("output") or []
                print(f"KIS Index Intraday {index_code} date={target_date} hour={hour} include_prev={include_prev} rows={len(rows)}")
                if rows:
                    return list(reversed(rows))
                continue
            print(f"KIS Index Intraday Error for {index_code}: status={resp.status_code} body={resp.text[:200]}")
            return []
        return []

    def get_volume_rank(self):
        # Volume Rank (FHPST01710000)
        token = self._get_token()
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/volume-rank"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHPST01710000",
            "custtype": "P"
        }
        params = {
            "fid_cond_mrkt_div_code": "J",
            "fid_cond_scr_div_code": "20171",
            "fid_input_iscd": "0000", # All
            "fid_div_cls_code": "0",
            "fid_blng_cls_code": "0",
            "fid_trgt_cls_code": "111111111",
            "fid_trgt_exls_cls_code": "000000",
            "fid_input_price_1": "",
            "fid_input_price_2": "",
            "fid_vol_cnt": "",
            "fid_input_date_1": ""
        }
        
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json().get("output")
        print(f"KIS Volume Rank Error: {resp.text}")
        return None

    def get_investor_trend(self, market_code="0001"):
        """
        Fetch Daily Investor Trading Trend (FHKUP03500300)
        Returns daily trading summaries for Investor categories.
        """
        try:
            token = self._get_token()
        except Exception:
            return None

        # API URL for Inquire Daily Investor Trading Trend
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-investor-daily-trade-trend"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKUP03500300",
            "custtype": "P"
        }
        
        from datetime import datetime, timedelta
        today = datetime.now().strftime("%Y%m%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y%m%d")
        
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": market_code,
            "FID_INPUT_DATE_1": week_ago,
            "FID_INPUT_DATE_2": today,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0"
        }
        
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            return resp.json().get("output")
        print(f"KIS Investor Trend Error: {resp.text}")
        return None

    def get_stock_price(self, stock_code):
        """
        Fetch Current Stock Price (FHKST01010100)
        """
        if not self._get_token():
            return None

        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100",
            "custtype": "P"
        }
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": stock_code
        }
        
        resp = requests.get(url, headers=headers, params=params, timeout=5)
        if resp.status_code == 200:
            return resp.json().get("output")
        print(f"KIS Price Error for {stock_code}: {resp.text}")
        return None
