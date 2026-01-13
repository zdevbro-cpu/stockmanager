"""
DOCX 템플릿 기반 리포트 생성 서비스
- 기존 markdown 대신 DOCX 템플릿 사용
- AI는 데이터만 생성, 포맷은 템플릿이 보장
"""
from docx import Document
from docx.shared import Pt, RGBColor, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
import os
import json
import google.generativeai as genai
from datetime import datetime

def generate_docx_report(company_name, ticker, template_path, output_path):
    """
    DOCX 템플릿을 사용하여 투자 보고서 생성
    
    Args:
        company_name: 회사명
        ticker: 종목코드
        template_path: 템플릿 DOCX 파일 경로
        output_path: 출력 DOCX 파일 경로
    """
    
    # 1. AI로부터 데이터만 받기 (JSON 형식)
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found")
    
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('models/gemini-2.0-flash')
    
    prompt = f"""
{company_name}({ticker})에 대한 투자 보고서 데이터를 JSON 형식으로 제공하십시오.

{{
  "executive_summary": "3-4문장의 투자 요약",
  "financial_analysis": {{
    "revenue_growth": "매출 성장성 분석",
    "profitability": "수익성 분석",
    "stability": "안정성 분석"
  }},
  "business_segments": [
    {{"name": "부문1", "status": "현황", "competitive_advantage": "경쟁우위", "growth_drivers": "성장동력"}},
    {{"name": "부문2", "status": "현황", "challenges": "과제", "growth_drivers": "성장동력"}},
    {{"name": "부문3", "status": "현황", "strategy": "전략"}}
  ],
  "risks": [
    {{"title": "리스크1", "content": "내용", "impact": "영향"}},
    {{"title": "리스크2", "content": "내용", "impact": "영향"}}
  ],
  "opportunities": [
    {{"title": "기회1", "content": "내용", "impact": "영향"}},
    {{"title": "기회2", "content": "내용", "impact": "영향"}}
  ],
  "investment_opinion": "Buy/Hold/Sell",
  "opinion_rationale": "투자 의견 근거",
  "monitoring_points": ["KPI1", "KPI2", "KPI3"],
  "news_insights": ["뉴스1", "뉴스2", "뉴스3"]
}}

JSON만 출력하십시오.
"""
    
    response = model.generate_content(prompt)
    raw_text = response.text.strip()
    
    # JSON 추출
    if raw_text.startswith("```json"):
        raw_text = raw_text[7:].strip()
    if raw_text.startswith("```") and raw_text.endswith("```"):
        raw_text = raw_text[3:-3].strip()
    
    data = json.loads(raw_text)
    
    # 2. 템플릿 로드
    doc = Document(template_path)
    
    # 3. 플레이스홀더 교체
    today = datetime.now().strftime("%Y년 %m월 %d일")
    
    replacements = {
        '{{COMPANY_NAME}}': company_name,
        '{{TICKER}}': ticker,
        '{{DATE}}': today,
        '{{EXECUTIVE_SUMMARY}}': data.get('executive_summary', ''),
        '{{REVENUE_GROWTH}}': data['financial_analysis'].get('revenue_growth', ''),
        '{{PROFITABILITY}}': data['financial_analysis'].get('profitability', ''),
        '{{STABILITY}}': data['financial_analysis'].get('stability', ''),
        '{{INVESTMENT_OPINION}}': data.get('investment_opinion', ''),
        '{{OPINION_RATIONALE}}': data.get('opinion_rationale', ''),
    }
    
    for para in doc.paragraphs:
        for key, value in replacements.items():
            if key in para.text:
                para.text = para.text.replace(key, value)
    
    # 4. 사업 부문 섹션 채우기 (동적)
    # TODO: 템플릿에서 마커를 찾아 동적으로 추가
    
    # 5. 저장
    doc.save(output_path)
    print(f"Report saved to: {output_path}")
    return output_path


if __name__ == "__main__":
    # 테스트
    template = r"c:\ProjectCode\stockmanager\docs\vc투자메모.docx"
    output = r"c:\ProjectCode\stockmanager\artifacts\reports\test_report.docx"
    
    generate_docx_report("삼성전자", "005930", template, output)
