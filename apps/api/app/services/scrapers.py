import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

def fetch_leading_stock(sub_url_suffix):
    """
    Fetch the leading stock (highest change rate) from the theme detail page.
    """
    try:
        url = f"https://finance.naver.com{sub_url_suffix}"
        resp = requests.get(url, timeout=3)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # The detail page lists stocks. Usually sorted by change rate desc?
        # We need to find the first stock in the list.
        # Table class 'type_5' usually contains stock list in detail page.
        table = soup.select_one("table.type_5")
        if not table:
            return "-"
            
        # Find first stock row
        rows = table.select("tr")
        for row in rows:
            name_td = row.select_one("td.name")
            if name_td:
                # Found the first stock!
                stock_name = name_td.get_text(strip=True)
                return stock_name
        return "-"
    except Exception:
        return "-"

def fetch_theme_page(page):
    """
    Fetch a single page of themes.
    """
    url = f"https://finance.naver.com/sise/theme.nhn?&page={page}"
    try:
        resp = requests.get(url, timeout=3)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.type_1")
        if not table: return []
        
        themes = []
        rows = table.select("tr")
        for row in rows:
            cols = row.select("td")
            if len(cols) < 4: continue
            
            name_link = cols[0].select_one("a")
            if not name_link: continue
            
            themes.append({
                "name": name_link.get_text(strip=True),
                "link": name_link['href'],
                "change": cols[1].get_text(strip=True),
                "avg3d": cols[2].get_text(strip=True)
            })
        return themes
    except:
        return []

def get_naver_themes():
    """
    Scrape Theme rankings from Naver Finance (Multi-page)
    URL: https://finance.naver.com/sise/theme.nhn
    Columns: 테마명 | 전일대비 | 최근3일등락률(평균) | 상승/보합/하락 (종목수)
    Includes deep scraping for 'Leading Stock'.
    """
    try:
        # Fetch pages 1 to 5 concurrently (approx 200 themes)
        all_rows = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_theme_page, page) for page in range(1, 6)]
            for future in futures:
                all_rows.extend(future.result())
        
        # Deduplicate if needed (though pages shouldn't overlap)
        # Deep scrape leading stocks for Top 20 only
        top_n = 20
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_leading_stock, item['link']): i for i, item in enumerate(all_rows[:top_n])}
            
            results_map = {}
            for future in futures:
                idx = futures[future]
                try:
                    results_map[idx] = future.result()
                except:
                    results_map[idx] = "-"

        # Assemble result
        themes = []
        for i, item in enumerate(all_rows):
            themes.append({
                "rank": i + 1,
                "name": item['name'],
                "changePercent": item['change'],
                "change3d": item['avg3d'],
                "leadingStock": results_map.get(i, "-")
            })
            
        return themes
        
    except Exception as e:
        print(f"Error scraping themes: {str(e)}")
        return []

def get_naver_industries():
    """
    Scrape Industry rankings from Naver Finance
    URL: https://finance.naver.com/sise/sise_group.nhn?type=upjong
    Columns: 업종명 | 전일대비 | 전체/상승/보합/하락 (Graph/Text) | 등락그래프
    """
    url = "https://finance.naver.com/sise/sise_group.nhn?type=upjong"
    try:
        resp = requests.get(url, timeout=5)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")
        
        table = soup.select_one("table.type_1")
        if not table:
            return []
            
        industries = []
        rows = table.select("tr")
        rank = 1
        
        for row in rows:
            cols = row.select("td")
            if len(cols) < 3:
                continue
            
            link = cols[0].select_one("a")
            if not link:
                continue
                
            name = link.get_text(strip=True)
            change = cols[1].get_text(strip=True)
            
            # Scrape detailed counts if possible?
            # For now return 0s to prevent broken UI
            
            industries.append({
                "rank": rank,
                "name": name,
                "change": change,
                "up": 0, "flat": 0, "down": 0
            })
            rank += 1
            
        return industries
        
    except Exception as e:
        print(f"Error scraping industries: {str(e)}")
        return []
