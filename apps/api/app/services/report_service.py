import os
import datetime
import re
import google.generativeai as genai
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List
import xml.etree.ElementTree as ET
import urllib.parse
import requests
from docx import Document
from docx.shared import Pt, RGBColor, Inches

# Import settings to get API key
from ..config import settings

def fetch_google_news(query: str, limit: int | None = None) -> str:
    """Fetch recent news from Google News RSS"""
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
        response = requests.get(url, timeout=5)
        
        if response.status_code != 200:
            return "뉴스 데이터를 불러오지 못했습니다."
            
        root = ET.fromstring(response.content)
        items = root.findall('.//item')
        
        news_list = []
        if limit is None:
            target_items = items
        else:
            target_items = items[:limit]

        for item in target_items:
            title = item.find('title').text if item.find('title') is not None else "No Title"
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            news_list.append(f"- {title} ({pub_date})")
            
        return "\n".join(news_list)
    except Exception as e:
        print(f"News fetch error: {e}")
        return "뉴스 데이터를 가져오는 중 오류가 발생했습니다."

def generate_ai_report(company_id: int, report_id: int):
    """
    Generate VC investment report (Long Form - Modular Approach):
    Calls AI multiple times to ensure length and stability.
    """
    from ..db import SessionLocal
    import time
    
    db = SessionLocal()
    
    try:
        # 1. Fetch Company Info
        company = db.execute(text("SELECT name_ko, corp_code, stock_code, sector_name FROM company WHERE company_id = :cid"), 
                             {"cid": company_id}).fetchone()
        
        if not company:
            db.execute(text("UPDATE report_request SET status = 'FAILED' WHERE report_id = :rid"),
                      {"rid": report_id})
            db.commit()
            return
        
        name = company[0]
        ticker = company[2] or "N/A"
        sector = company[3] or "Technology"
        
        # Update status to RUNNING
        db.execute(text("UPDATE report_request SET status = 'RUNNING' WHERE report_id = :rid"), {"rid": report_id})
        db.commit()
        
        print(f"Starting MODULAR report generation for {name}...")
        
        # 2. Fetch News (Increase limit)
        news_summary = fetch_google_news(name, limit=None) 
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        
        # 3. Setup AI
        api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        model_id = 'models/gemini-2.0-flash'
        model = genai.GenerativeModel(model_id)
        fin_summary_rows = db.execute(text("""
            SELECT fiscal_year, revenue, op_income, net_income, assets, equity
            FROM fs_mart_annual
            WHERE company_id = :cid
            ORDER BY fiscal_year DESC
            LIMIT 3
        """), {"cid": company_id}).fetchall()

        fin_ratio_rows = db.execute(text("""
            SELECT fiscal_year, op_margin, roe, debt_ratio
            FROM fs_ratio_mart
            WHERE company_id = :cid AND period_type = 'ANNUAL'
            ORDER BY fiscal_year DESC
            LIMIT 3
        """), {"cid": company_id}).fetchall()

        def _to_float(value):
            try:
                return float(value) if value is not None else None
            except (TypeError, ValueError):
                return None

        def _fmt_krw_100m(value):
            if value is None:
                return '-'
            return f"{value / 100000000:,.1f}억"

        def _fmt_pct(value):
            if value is None:
                return '-'
            return f"{value:.1f}%"

        summary_by_year = {}
        for row in fin_summary_rows:
            summary_by_year[row.fiscal_year] = {
                'revenue': _to_float(row.revenue),
                'op_income': _to_float(row.op_income),
                'net_income': _to_float(row.net_income),
                'assets': _to_float(row.assets),
                'equity': _to_float(row.equity),
            }

        ratio_by_year = {}
        for row in fin_ratio_rows:
            ratio_by_year[row.fiscal_year] = {
                'op_margin': _to_float(row.op_margin),
                'roe': _to_float(row.roe),
                'debt_ratio': _to_float(row.debt_ratio),
            }

        years = sorted(set(summary_by_year.keys()) | set(ratio_by_year.keys()), reverse=True)[:3]
        if not years:
            current_year = datetime.date.today().year
            years = [current_year - 1, current_year - 2, current_year - 3]

        def _build_table(headers, rows):
            header = '| ' + ' | '.join(headers) + ' |'
            separator = '| ' + ' | '.join([':---'] + [':---:' for _ in headers[1:]]) + ' |'
            body = ['| ' + ' | '.join(row) + ' |' for row in rows]
            return '\n'.join([header, separator] + body)

        financial_rows = [
            ['매출액'] + [_fmt_krw_100m(summary_by_year.get(y, {}).get('revenue')) for y in years],
            ['영업이익'] + [_fmt_krw_100m(summary_by_year.get(y, {}).get('op_income')) for y in years],
            ['순이익'] + [_fmt_krw_100m(summary_by_year.get(y, {}).get('net_income')) for y in years],
            ['자산총계'] + [_fmt_krw_100m(summary_by_year.get(y, {}).get('assets')) for y in years],
            ['자본총계'] + [_fmt_krw_100m(summary_by_year.get(y, {}).get('equity')) for y in years],
        ]
        financial_table = _build_table(['구분'] + [f'{y}년' for y in years], financial_rows)

        ratio_rows = [
            ['영업이익률'] + [_fmt_pct(ratio_by_year.get(y, {}).get('op_margin')) for y in years],
            ['ROE'] + [_fmt_pct(ratio_by_year.get(y, {}).get('roe')) for y in years],
            ['부채비율'] + [_fmt_pct(ratio_by_year.get(y, {}).get('debt_ratio')) for y in years],
        ]
        ratio_table = _build_table(['지표'] + [f'{y}년' for y in years], ratio_rows)

        has_fin_data = bool(summary_by_year or ratio_by_year)
        data_note = '' if has_fin_data else '재무 데이터가 부족하여 일부 항목은 - 로 표시됩니다.'
        

        # --- PART 1: Intro & Financials ---
        print("Generating Part 1 (Summary & Financials)...")
        prompt1 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제1부(요약 및 재무)**를 작성하십시오.
정량/정성 분석을 포함한 전문적인 톤으로 작성하십시오.

[목차]
# 투자 검토 보고서: {name}

## 1. 투자 요약 (Executive Summary)
(A4 1페이지 분량으로 핵심 요약: 시장 기회, 리스크, 투자 포인트, 결론)

## 2. 재무 실적 및 지표 심층 분석

### 2.1 재무상태표 및 손익계산서 요약
{financial_table}

### 2.2 주요 재무 지표
{ratio_table}
{data_note}

### 2.3 재무 분석
(재무제표 수치 변화의 원인과 질적 변화를 5문단 이상으로 분석)

### 2.4 매출 및 이익 성장
(사업/제품별 성장 동력과 구조적 요인을 분석)

### 2.5 수익성/효율성 분석
(마진 변화, 비용 구조, 운영 효율 개선 가능성)

### 2.6 재무 건전성
(부채비율, 현금흐름, 유동성 관점에서 위험 요인 평가)

마크다운으로 작성하십시오.
"""
        resp1 = model.generate_content(prompt1)
        part1 = clean_markdown(resp1.text)
        
        # --- PART 2: Business Model ---
        print("Generating Part 2 (Business Model)...")
        time.sleep(1)
        prompt2 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제2부(사업 모델)**를 작성하십시오.
정량/정성 근거를 포함해 서술하십시오.

[목차]
## 3. 사업 모델 및 경쟁 우위

### 3.1 핵심 사업 구조와 수익원
(주요 제품/서비스, 매출 구성, 수익 구조를 설명)

### 3.2 시장 포지션 및 경쟁 환경
(시장 규모, 성장률, 경쟁사 대비 차별점)

### 3.3 성장 전략 및 제품 로드맵
(신규 시장/제품 확장 전략과 실행 가능성)

### 3.4 운영 역량 및 ESG
(생산/공급망/인재/ESG 관점에서 평가)

### 3.5 결론: 사업 모델의 지속 가능성
(향후 3~5년 관점에서 지속성 평가)

**뉴스 참고:**
{news_summary}

마크다운으로 작성하십시오.
"""
        resp2 = model.generate_content(prompt2)
        part2 = clean_markdown(resp2.text)

        # --- PART 3: Risks, Opps, Ops ---
        print("Generating Part 3 (Risks & Conclusion)...")
        time.sleep(1)
        prompt3 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제3부(리스크/기회/결론)**를 작성하십시오.
정확하고 구체적인 항목으로 작성하십시오.

[목차]
## 4. 리스크 및 기회 요인

### 4.1 리스크 요인 (Risk Factors)
(각 항목 3문장 이상, 정확히 8개)
- [리스크 1]
- [리스크 2]
- [리스크 3]
- [리스크 4]
- [리스크 5]
- [리스크 6]
- [리스크 7]
- [리스크 8]

### 4.2 기회 요인 (Opportunity Factors)
(각 항목 3문장 이상, 정확히 8개)
- [기회 1]
- [기회 2]
- [기회 3]
- [기회 4]
- [기회 5]
- [기회 6]
- [기회 7]
- [기회 8]

## 5. 최종 투자 결론 및 모니터링 포인트

### 5.1 최종 투자 결론
(투자 의견과 근거를 3문단 이상)

### 5.2 모니터링 포인트
(정확히 8개 항목)
- [포인트 1]
- [포인트 2]
- [포인트 3]
- [포인트 4]
- [포인트 5]
- [포인트 6]
- [포인트 7]
- [포인트 8]

마크다운으로 작성하십시오.
"""
        resp3 = model.generate_content(prompt3)
        part3 = clean_markdown(resp3.text)

        # --- PART 4: News Insights ---
        print("Generating Part 4 (News Insights)...")
        time.sleep(1)
        prompt4 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제4부(뉴스 인사이트)**를 작성하십시오.
최근 뉴스 기준으로 16개 항목을 정리하십시오.

**뉴스 참고:**
{news_summary}

[목차]
## 6. 최근 뉴스 및 인사이트
(각 항목에 뉴스 제목과 의미를 요약)
- [뉴스 1]
- [뉴스 2]
- [뉴스 3]
- [뉴스 4]
- [뉴스 5]
- [뉴스 6]
- [뉴스 7]
- [뉴스 8]
- [뉴스 9]
- [뉴스 10]
- [뉴스 11]
- [뉴스 12]
- [뉴스 13]
- [뉴스 14]
- [뉴스 15]
- [뉴스 16]

마크다운으로 작성하십시오.
"""
        resp4 = model.generate_content(prompt4)
        part4 = clean_markdown(resp4.text)

        # Combine all parts
        full_report = f"{part1}\n\n{part2}\n\n{part3}\n\n{part4}"
        
        # 4. Save as Markdown
        root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
        artifacts_dir = os.path.join(root_dir, "artifacts", "reports")
        os.makedirs(artifacts_dir, exist_ok=True)
        
        md_path = os.path.join(artifacts_dir, f"report_{report_id}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(full_report)
        print(f"Markdown saved: {md_path}")
        
        # 5. Convert to DOCX
        docx_path = os.path.join(artifacts_dir, f"report_{report_id}.docx")
        markdown_to_docx_converter(full_report, docx_path, name, ticker)
        print(f"DOCX saved: {docx_path}")
        
        # 6. Update DB status to DONE
        db.execute(text("UPDATE report_request SET status = 'DONE' WHERE report_id = :rid"),
                  {"rid": report_id})
        db.commit()
        
        print(f"Report {report_id} generated successfully!")
        
    except Exception as e:
        print(f"Report generation failed: {e}")
        db.rollback()
        db.execute(text("UPDATE report_request SET status = 'FAILED' WHERE report_id = :rid"),
                  {"rid": report_id})
        db.commit()
    
    finally:
        db.close()

def clean_markdown(text):
    """Clean up markdown code blocks"""
    text = text.strip()
    if text.startswith("```markdown"):
        text = text[11:]
    elif text.startswith("```"):
        text = text[3:]
    
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()

def markdown_to_docx_converter(markdown_text, output_path, company_name, ticker):
    """留덊겕?ㅼ슫??DOCX濡?蹂??(H4 諛??쒕툕 ?뱀뀡 吏??媛뺥솕)"""
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    import re
    
    doc = Document()
    
    # ?섏씠吏 ?ㅼ젙
    sections = doc.sections
    for section in sections:
        section.page_height = Inches(11.69)
        section.page_width = Inches(8.27)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
    
    lines = markdown_text.split('\n')
    in_table = False
    table_rows = []
    
    for line in lines:
        line_stripped = line.strip()
        
        # H1 (Title)
        if line_stripped.startswith('# ') and not line_stripped.startswith('## '):
            text = line_stripped[2:].strip()
            p = doc.add_paragraph(text)
            p.style = 'Heading 1'
            for run in p.runs:
                run.font.size = Pt(20)
                run.font.bold = True
                run.font.color.rgb = RGBColor(14, 165, 233) # Blue
                
        # H2 (Main Section)
        elif line_stripped.startswith('## '):
            text = line_stripped[3:].strip()
            p = doc.add_paragraph(text)
            p.style = 'Heading 2'
            for run in p.runs:
                run.font.size = Pt(16)
                run.font.bold = True
                run.font.color.rgb = RGBColor(0, 0, 0) # Black
                
        # H3 (Sub Section 2.1, 2.2 etc)
        elif line_stripped.startswith('### '):
            text = line_stripped[4:].strip()
            p = doc.add_paragraph(text)
            p.style = 'Heading 3'
            for run in p.runs:
                run.font.size = Pt(13)
                run.font.bold = True
                run.font.color.rgb = RGBColor(60, 60, 60) # Dark Gray
                
        # H4 (Deep Detail if needed)
        elif line_stripped.startswith('#### '):
            text = line_stripped[5:].strip()
            p = doc.add_paragraph(text)
            p.style = 'Heading 4'
            for run in p.runs:
                run.font.size = Pt(11)
                run.font.bold = True
        
        # Table
        elif line_stripped.startswith('|'):
            if not in_table:
                in_table = True
                table_rows = [line_stripped]
            else:
                table_rows.append(line_stripped)
        
        # Table End check
        elif not line_stripped.startswith('|') and in_table:
            _create_table(doc, table_rows)
            in_table = False
            table_rows = []
            
            # Process current line after table
            _process_line(doc, line_stripped)
            
        else:
            _process_line(doc, line_stripped)
    
    if in_table and table_rows:
        _create_table(doc, table_rows)
    
    doc.save(output_path)

def _process_line(doc, line):
    """Helper to process normal lines, bullets, etc."""
    import re
    if not line:
        return
        
    # Bullet point
    if line.startswith('o ') or line.startswith('- '):
        text = line[2:].strip()
        p = doc.add_paragraph(text, style='List Bullet')
        
    # Numbered list
    elif re.match(r'^\d+[\.\)]\s', line):
        text = re.sub(r'^\d+[\.\)]\s', '', line)
        p = doc.add_paragraph(text, style='List Number')
        
    # Bold text processing
    elif '**' in line:
        p = doc.add_paragraph()
        parts = line.split('**')
        for i, part in enumerate(parts):
            run = p.add_run(part)
            if i % 2 == 1:
                run.bold = True
    else:
        doc.add_paragraph(line)

def _create_table(doc, table_rows):
    """Create DOCX table from markdown table rows"""
    if len(table_rows) < 2:
        return
    
    header = [c.strip() for c in table_rows[0].split('|')[1:-1]]
    data_rows = []
    
    # Skip header(0) and separator(1)
    for row in table_rows[2:]:
        if row.strip():
            cells = [c.strip() for c in row.split('|')[1:-1]]
            data_rows.append(cells)
    
    if not data_rows:
        return
    
    table = doc.add_table(rows=1 + len(data_rows), cols=len(header))
    table.style = 'Light Grid Accent 1'
    
    # Header
    for i, h in enumerate(header):
        cell = table.rows[0].cells[i]
        cell.text = h
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.font.bold = True
    
    # Data
    for r_idx, row_data in enumerate(data_rows):
        for c_idx, cell_text in enumerate(row_data):
            if c_idx < len(table.rows[r_idx + 1].cells):
                table.rows[r_idx + 1].cells[c_idx].text = cell_text
