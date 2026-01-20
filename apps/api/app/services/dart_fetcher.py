import os
import requests
import io
import zipfile
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re

# DART API Base URL
DART_BASE_URL = "https://opendart.fss.or.kr/api"

def get_dart_api_key():
    """Get DART_API_KEY from env"""
    api_key = os.environ.get("DART_API_KEY")
    if not api_key:
        print("Warning: DART_API_KEY is missing.")
        return None
    return api_key

def fetch_business_report_text(corp_code: str) -> str:
    """
    Fetch the latest 'Business Report' (사업보고서) text from DART.
    Focus on 'II. 사업의 내용' section.
    """
    api_key = get_dart_api_key()
    if not api_key:
        return ""

    # 1. Find the latest 'Business Report' (11011) rcp_no
    # Search last 3 months ~ 1 year
    # But simplified: just list recent filings and pick first 'A001' (Business Report) or 'A002' (Half), 'A003' (Quarter)
    # Actually, we can use the 'list' API.
    
    try:
        # Just simple recent search. In prod, careful date range needed.
        url_list = f"{DART_BASE_URL}/list.json"
        page_no = 1
        target_rcp_no = None
        while True:
            params = {
                "crtfc_key": api_key,
                "corp_code": corp_code,
                "bgn_de": "20230101", # Should be dynamic
                "end_de": "20251231",
                "pblntf_ty": "A", # Regular disclosure
                "page_count": 100,
                "page_no": page_no,
            }
            resp = requests.get(url_list, params=params, timeout=10)
            data = resp.json()

            if data.get('status') != '000':
                print(f"DART List Error: {data.get('message')}")
                return ""

            list_data = data.get('list') or []
            if not list_data:
                break

            for item in list_data:
                # Prioritize Annual Report (사업/분기/반기)
                rpt_name = item.get('report_nm', '')
                if '사업보고서' in rpt_name or '분기보고서' in rpt_name or '반기보고서' in rpt_name:
                    target_rcp_no = item.get('rcept_no')
                    print(f"Found Report: {rpt_name} ({target_rcp_no})")
                    break
            if target_rcp_no:
                break
            page_no += 1

        if not target_rcp_no:
            return ""

        # 2. Download Original Document (XML/HTML)
        # API: document.xml -> returns ZIP containing XMLs
        url_doc = f"{DART_BASE_URL}/document.xml"
        params_doc = {
            "crtfc_key": api_key,
            "rcept_no": target_rcp_no
        }
        
        doc_resp = requests.get(url_doc, params=params_doc, timeout=30)
        
        # Unzip
        with zipfile.ZipFile(io.BytesIO(doc_resp.content)) as z:
            # Look for huge XML or HTML file
            # Usually 'company_name.xml' or similar.
            file_names = z.namelist()
            target_file = None
            for fn in file_names:
                if fn.endswith('.xml') or fn.endswith('.htm'):
                    target_file = fn
                    break
            
            if not target_file:
                return ""
            
            with z.open(target_file) as f:
                content = f.read().decode('utf-8', errors='ignore')

        # 3. Extract 'Business Overview' (II. 사업의 내용)
        # If XML, it has sections. If HTML, it relies on text parsing.
        # Simple approach: Strip tags and find regex markers.
        
        soup = BeautifulSoup(content, 'html.parser')
        full_text = soup.get_text('\n')
        
        # Naive extraction: Find "II. 사업의 내용" ~ "III. 재무에 관한 사항"
        # Different reports might use different headers.
        
        start_markers = ["II. 사업의 내용", "2. 사업의 내용", "II.사업의내용"]
        end_markers = ["III. 재무에 관한 사항", "3. 재무에 관한 사항", "III.재무에관한사항"]
        
        start_idx = -1
        for m in start_markers:
            idx = full_text.find(m)
            if idx != -1:
                start_idx = idx
                break
        
        if start_idx == -1:
            # Fallback: Just return head of text
            return full_text[:10000]
            
        end_idx = -1
        for m in end_markers:
             idx = full_text.find(m, start_idx)
             if idx != -1:
                 end_idx = idx
                 break
        
        if end_idx == -1:
            extracted = full_text[start_idx:start_idx+15000] # Get max chars
        else:
            extracted = full_text[start_idx:end_idx]

        # Cleanup whitespace
        cleaned = re.sub(r'\n+', '\n', extracted).strip()
        return cleaned

    except Exception as e:
        print(f"DART Fetch Error: {e}")
        return ""
