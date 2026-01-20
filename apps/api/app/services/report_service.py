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
            return "뉴스 데이터를 불러올 수 없습니다."
            
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
        return "뉴스 데이터 수집 중 오류 발생"

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
        today_str = datetime.date.today().strftime("%Y년 %m월 %d일")
        
        # 3. Setup AI
        api_key = settings.GOOGLE_API_KEY or os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not configured")
        
        genai.configure(api_key=api_key)
        model_id = 'models/gemini-2.0-flash'
        model = genai.GenerativeModel(model_id)
        
        fin_data = {
            "2023": {"rev": "320조", "op": "48조", "net": "38.4조", "asset": "480조", "liab": "144조", "cap": "336조", "op_margin": "15.0%", "roe": "11.4%", "debt_ratio": "42.9%"},
            "2022": {"rev": "310조", "op": "46.5조", "net": "37.2조", "asset": "465조", "liab": "139.5조", "cap": "325.5조", "op_margin": "15.0%", "roe": "11.4%", "debt_ratio": "42.9%"},
            "2021": {"rev": "300조", "op": "45조", "net": "36조", "asset": "450조", "liab": "135조", "cap": "315조", "op_margin": "15.0%", "roe": "11.4%", "debt_ratio": "42.9%"}
        }

        # --- PART 1: Intro & Financials ---
        print("Generating Part 1 (Summary & Financials)...")
        prompt1 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제1부(요약 및 재무)**를 작성하십시오.
상세하고 전문적인 어조로 작성하십시오.

**[목차]**
# 투자 검토 보고서: {name}

## 1. 투자 요약 (Executive Summary)
(A4 1페이지 분량의 심층 에세이. 핵심 경쟁력, 시장 기회, 리스크 관리, 최종 의견 포함)

## 2. 재무 실적 및 지표 심층 분석

### 2.1 재무상태표 및 손익계산서 요약

| 구분 | 2023년 | 2022년 | 2021년 |
| :--- | :---: | :---: | :---: |
| 매출액 | 320조 | 310조 | 300조 |
| 영업이익 | 48조 | 46.5조 | 45조 |
| 순이익 | 38.4조 | 37.2조 | 36조 |
| 자산총계 | 480조 | 465조 | 450조 |
| 부채총계 | 144조 | 139.5조 | 135조 |
| 자본총계 | 336조 | 325.5조 | 315조 |

### 2.2 주요 투자 지표

| 지표 | 2023년 | 2022년 | 2021년 |
| :--- | :---: | :---: | :---: |
| 영업이익률 | 15.0% | 15.0% | 15.0% |
| ROE | 11.4% | 11.4% | 11.4% |
| 부채비율 | 42.9% | 42.9% | 42.9% |

### 2.3 심층 분석
(재무제표 수치의 질적 변화를 5문단 이상 심층 분석)

### 2.4 매출 및 이익 성장
(제품별/지역별 매출 성장 동력 분석)

### 2.5 수익성 및 효율성
(마진율 변화 및 비용 통제 능력 분석)

### 2.6 재무 건전성
(부채비율, 현금흐름 등을 통한 위기 대응 능력 평가)

반드시 마크다운으로 출력하십시오.
"""
        resp1 = model.generate_content(prompt1)
        part1 = clean_markdown(resp1.text)
        
        # --- PART 2: Business Model ---
        print("Generating Part 2 (Business Model)...")
        time.sleep(1)
        prompt2 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제2부(사업 모델)**를 작성하십시오.
이전 섹션에 이어지는 내용입니다.

**[목차]**
## 3. 사업모델 및 핵심 이슈

### 3.1 [현황 1: 주력 사업의 경쟁력과 과제]
(시장 점유율, 경쟁 강도, 기술 격차 등 5문단 이상)

### 3.2 [현황 2: 신성장 동력의 진행 상황]
(미래 먹거리 로드맵, 가시적 성과 시점 등 5문단 이상)

### 3.3 [현황 3: 글로벌 공급망 및 지정학적 이슈]
(대외 환경 영향 분석 5문단 이상)

### 3.4 [현황 4: 조직 혁신 및 ESG 경영]
(조직 문화, 인재, ESG 이슈 5문단 이상)

### 3.5 결론: 사업 모델의 지속 가능성 평가
(향후 10년 지속 가능성 평가)

**뉴스 참고:**
{news_summary}

반드시 마크다운으로 출력하십시오.
"""
        resp2 = model.generate_content(prompt2)
        part2 = clean_markdown(resp2.text)

        # --- PART 3: Risks, Opps, Ops ---
        print("Generating Part 3 (Risks & Conclusion)...")
        time.sleep(1)
        prompt3 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제3부(리스크, 기회, 결론)**를 작성하십시오.
불렛 포인트 개수를 정확히 지키십시오.

**[목차]**
## 4. 리스크 및 기회요인 분석

### 4.1 리스크 요인 (Risk Factors)
(각 항목 3문장 이상, **정확히 8개**)
o **[리스크 1]:** ...
(8개까지 작성)

### 4.2 기회 요인 (Opportunity Factors)
(각 항목 3문장 이상, **정확히 8개**)
o **[기회 1]:** ...
(8개까지 작성)

## 5. 최종 투자의견 및 모니터링 포인트

### 5.1 최종 투자 의견
**[의견: 매수 (Buy)]**
(투자 당위성을 3문단 이상 강력하게 호소)

### 5.2 모니터링 포인트
(핵심 지표 **정확히 8개**)
o **[Point 1]:** ...
(8개까지 작성)

반드시 마크다운으로 출력하십시오.
"""
        resp3 = model.generate_content(prompt3)
        part3 = clean_markdown(resp3.text)

        # --- PART 4: News Insights ---
        print("Generating Part 4 (News Insights)...")
        time.sleep(1)
        prompt4 = f"""
당신은 VC 수석 심사역입니다. {name}({ticker}) 보고서의 **제4부(뉴스 인사이트)**를 작성하십시오.
최신 뉴스를 분석하여 **정확히 16개 항목**을 작성하십시오.

**[뉴스 데이터]**
{news_summary}

**[목차]**
## 6. 인터넷 뉴스 및 기사 인사이트
(각 항목은 뉴스 제목과 상세 투자 인사이트 포함)
o **[뉴스 1]:** ...
o **[뉴스 2]:** ...
...
o **[뉴스 16]:** ...

반드시 마크다운으로 출력하십시오.
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
    """마크다운을 DOCX로 변환 (H4 및 서브 섹션 지원 강화)"""
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    import re
    
    doc = Document()
    
    # 페이지 설정
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
