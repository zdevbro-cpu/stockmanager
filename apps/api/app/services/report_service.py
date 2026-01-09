import os
from sqlalchemy.orm import Session
from sqlalchemy import text
import google.generativeai as genai

import xml.etree.ElementTree as ET
import urllib.parse
import requests

def fetch_google_news(query: str, limit: int = 7) -> str:
    """Fetch recent news from Google News RSS"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return "뉴스 데이터를 불러올 수 없습니다."
            
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        news_list = []
        for i, item in enumerate(items[:limit]):
            title = item.find('title').text if item.find('title') is not None else "No Title"
            pubDate = item.find('pubDate').text if item.find('pubDate') is not None else ""
            # Simple cleanup of date
            news_list.append(f"- {title} ({pubDate})")
            
        return "\n".join(news_list)
    except Exception as e:
        print(f"News fetch error: {e}")
        return "뉴스 데이터 수집 중 오류 발생"

def generate_ai_report(db: Session, company_id: int, report_id: int):
    """
    Generate a VC-level investment report using financial data and DART filings.
    """
    # 1. Fetch Company Info
    company = db.execute(text("SELECT name_ko, corp_code, stock_code, sector_name FROM company WHERE company_id = :cid"), 
                         {"cid": company_id}).fetchone()
    if not company:
        return
    
    name, corp_code, ticker, sector = company
    
    # 2. Fetch Financial Data (Numerical)
    financials = db.execute(text("""
        SELECT item_name, value, unit, period_end 
        FROM financial_statement 
        WHERE corp_code = :cc 
        ORDER BY period_end DESC, item_name
    """), {"cc": corp_code}).fetchall()
    
    fin_summary = ""
    if financials:
        fin_summary = "\n".join([f"- {row[0]}: {row[1]:,.0f} {row[2]} (Period: {row[3]})" for row in financials])
    else:
        fin_summary = "재무 데이터 없음"

    # 3. Fetch Recent Filings
    filings = db.execute(text("""
        SELECT title, filing_date 
        FROM dart_filing 
        WHERE corp_code = :cc 
        ORDER BY filing_date DESC LIMIT 5
    """), {"cc": corp_code}).fetchall()
    filing_summary = "최근 3개월 내 주요 공시(DART)가 있다면 이를 최우선으로 분석에 반영하세요."

    # 4. Fetch News (Google News RSS)
    news_summary = fetch_google_news(name)
    print(f"Fetched news for {name}: {len(news_summary)} chars")

    # 5. Build AI Prompt
    prompt = f"""
당신은 대한민국 최고의 벤처캐피탈(VC) 심사역입니다. 
다음 기업에 대한 심도 있는 투자 검토 보고서(Investment Memo)를 작성해야 합니다.

[대상 기업]: {name} ({ticker})

[기본 재무 정보]
{fin_summary}

[최근 주요 공시]
{filing_summary}

[최근 뉴스/기사 데이터]
{news_summary}

위 데이터를 바탕으로 다음 항목을 포함하여 전문적인 보고서를 작성해 주세요 (Markdown 형식):
# INVESTMENT MEMO
## {name} ({ticker})

1. 개요 및 요약: 기업의 핵심 가치와 현재 위치
2. 재무 건전성 분석: 자산, 부채, 자본 구조를 바탕으로 한 안정성 평가
3. 최근 이슈 분석: 공시 내용을 바탕으로 한 리스크 및 기회 요인 (주요 공시 내용 포함)
4. VC 관점의 투자 의견: 매수/관망/매도 의견과 구체적인 근거
5. 향후 모니터링 포인트: 투자 후 관리 항목 및 주요 마일스톤
6. 인터넷 뉴스 및 기타 기사 요약 (구조화 필수):
   - 단순 나열이 아닌, [실적], [신사업], [리스크], [시장반응] 등의 키워드로 그룹화하여 정리하세요.
   - 각 기사 내용이 기업 가치에 미치는 영향을 한 줄 코멘트로 덧붙이세요.

데이터 표와 항목별 불렛 포인트를 적절히 사용하여 가독성 있게 작성해 주세요. 회사명은 제목 외의 본문에서는 적절히 생략하거나 약칭을 사용하세요.
"""

    # 5. Call LLM (Gemini)
    import os
    from dotenv import load_dotenv
    # Use absolute path to project root to find .env reliably
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    env_path = os.path.join(root_dir, ".env")
    load_dotenv(env_path, override=True) # Force override
    
    # Directly read from environment to avoid cached settings
    api_key = os.environ.get("GOOGLE_API_KEY")
    if api_key:
        print(f"DEBUG: report_service loaded key length {len(api_key)}, starts with {api_key[:2]}, ends with {api_key[-2:]}")
    else:
        print("DEBUG: report_service failed to load GOOGLE_API_KEY from environment")
        
    if not api_key:
        # Fallback to a mock report if key is missing, for demonstration
        report_content = f"# [VC Report] {name} 투자 검토\n\n(API KEY 누락으로 인한 샘플 리포트)\n\n## 1. 재무 분석\n{fin_summary}\n\n## 2. 공시 분석\n{filing_summary}\n\n## 3. 최종 의견\n데이터를 고려할 때 긍정적 검토 필요."
    else:
        import time
        # Use ONLY verified existing models found in debug output
        models_to_try = [
            'gemini-2.0-flash',        # Priority 1: Proven available
            'gemini-2.5-flash',        # Priority 2: Newer version verified
        ]
        
        report_content = ""
        last_error = None
        
        try:
            genai.configure(api_key=api_key)
            
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]

            for model_name in models_to_try:
                try:
                    print(f"Attempting report generation with {model_name}...")
                    model = genai.GenerativeModel(model_name)
                    response = model.generate_content(prompt, safety_settings=safety_settings)
                    
                    if response and response.text:
                        report_content = response.text
                        print(f"Success with {model_name}")
                        last_error = None
                        break # Success!
                    else:
                        raise Exception("Empty response from AI")
                        
                except Exception as e:
                    error_str = str(e)
                    print(f"Failed with {model_name}: {error_str}")
                    last_error = error_str
                    
                    # If 429 (Quota) or similar resource exhaustion, wait briefly and try next
                    if "429" in error_str or "Quota" in error_str or "ResourceExhausted" in error_str:
                        print("Quota limit hit, pausing before next model...")
                        time.sleep(2)
                        continue
                    # If 404 (Model not found), just continue to next
                    elif "404" in error_str:
                        continue
                    else:
                        # For other unknown errors, let's try the next model anyway to be safe
                        time.sleep(1)
                        continue

            # If all models failed
            if not report_content:
                if last_error and ("429" in last_error or "Quota" in last_error):
                    report_content = "현재 AI 사용량이 많아 쿼터가 초과되었습니다(429). 잠시 후(약 1분 뒤) 다시 시도해 주세요."
                elif last_error:
                    report_content = f"리포트 생성 실패 (모든 모델 시도): {last_error}"
                else:
                    report_content = "리포트 생성 중 알 수 없는 오류가 발생했습니다."

        except Exception as e:
            # Config level errors
            report_content = f"AI 설정 오류: {str(e)}"

    # 6. Save to Artifact
    # Use absolute path from project root to be safe
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
    save_dir = os.path.join(root_dir, "artifacts", "reports")
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, f"report_{report_id}.md")
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    # Update report status
    db.execute(text("UPDATE report_request SET status = 'DONE', updated_at = NOW() WHERE report_id = :rid"), 
               {"rid": report_id})
    db.commit()

    return report_content
