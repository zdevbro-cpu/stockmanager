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
        else:
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
        token = self._get_token()
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        headers = {
            "content-type": "application/json",
            "authorization": f"Bearer {token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": "FHKST01010100" # Using stock price query as index query is similar or same in some contexts, but KIS has dedicated index tr_id. 
            # Actually for Index, it is FHKUP03500100. Let's try to use the same logic if possible or dedicated one.
            # Warning: Getting Real-time Index via KIS REST API is tricky. 
            # Let's use FHKUP03500100 (Index Chart Price) to get latest value.
        }
        # Correct approach for Index: FHKUP03500100
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-index-chartprice"
        headers["tr_id"] = "FHKUP03500100"
        
        params = {
            "fid_cond_mrkt_div_code": "U", # U: Upjong (Index)
            "fid_input_iscd": index_code,
            "fid_input_date_1": "",
            "fid_input_date_2": "",
            "fid_period_div_code": "D",
            "fid_org_adj_prc": "0"
        }
        
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code == 200:
            data = resp.json()
            # output1: Current Snapshot
            if data.get("output1"):
                return data.get("output1")
            # Fallback: output2 (History, latest day)
            if data.get("output2") and len(data.get("output2")) > 0:
                return data.get("output2")[0]
        print(f"KIS Index Error for {index_code}: {resp.text}")
        return None

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
