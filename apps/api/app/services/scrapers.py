import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import time

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

_INDUSTRY_LINK_CACHE: dict[str, str] = {}
_THEME_LINK_CACHE: dict[str, str] = {}
_THEME_CACHE: list[dict] | None = None
_THEME_CACHE_AT: float | None = None
_THEME_REFRESHING: bool = False
_INDUSTRY_CACHE: list[dict] | None = None
_INDUSTRY_CACHE_AT: float | None = None
_INDUSTRY_REFRESHING: bool = False
_INDUSTRY_LEADING_CACHE: list[dict] | None = None
_INDUSTRY_LEADING_CACHE_AT: float | None = None
_INDUSTRY_LEADING_REFRESHING: bool = False
_INDUSTRY_LEADING_NAME_CACHE: dict[str, str] = {}
_INDUSTRY_LEADING_CACHE_LIMITED: bool = False

def _get_cached_industry_leading(name: str | None) -> str:
    if not name:
        return "-"
    return _INDUSTRY_LEADING_NAME_CACHE.get(name, "-")

def _set_cached_industry_leading(name: str | None, value: str) -> None:
    if not name or not value or value == "-":
        return
    _INDUSTRY_LEADING_NAME_CACHE[name] = value

def fetch_leading_stock(sub_url_suffix):
    """
    Fetch the leading stock (highest change rate) from the theme detail page.
    """
    try:
        url = f"https://finance.naver.com{sub_url_suffix}"
        resp = requests.get(url, headers=HEADERS, timeout=10)
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
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.type_1")
        if not table: return []
        
        themes = []
        rows = table.select("tr")
        for row in rows:
            cols = row.select("td")
            if len(cols) < 4:
                continue
            
            name_link = cols[0].select_one("a")
            if not name_link: continue
            
            name = name_link.get_text(strip=True)
            link = name_link.get("href") or ""
            if name and link:
                _THEME_LINK_CACHE[name] = link
            leading_stock = "-"
            if len(cols) >= 7:
                primary = cols[6].get_text(strip=True)
                secondary = cols[7].get_text(strip=True) if len(cols) >= 8 else ""
                leading_stock = primary or secondary or "-"

            themes.append({
                "name": name_link.get_text(strip=True),
                "link": link,
                "change": cols[1].get_text(strip=True),
                "avg3d": cols[2].get_text(strip=True),
                "leadingStock": leading_stock,
            })
        return themes
    except:
        return []

def get_naver_themes(
    include_leading_stock: bool = True,
    cache_ttl_sec: int = 900,
    time_budget_sec: int = 8,
    pages: int = 5,
):
    """
    Scrape Theme rankings from Naver Finance (Multi-page)
    URL: https://finance.naver.com/sise/theme.nhn
    Columns: 테마명 | 전일대비 | 최근3일등락률(평균) | 상승/보합/하락 (종목수)
    Includes deep scraping for 'Leading Stock'.
    """
    global _THEME_CACHE, _THEME_CACHE_AT, _THEME_REFRESHING
    try:
        now = time.time()
        if _THEME_CACHE and _THEME_CACHE_AT and (now - _THEME_CACHE_AT) < cache_ttl_sec:
            return _THEME_CACHE
        if _THEME_CACHE and not _THEME_REFRESHING:
            def _refresh():
                global _THEME_REFRESHING
                _THEME_REFRESHING = True
                try:
                    get_naver_themes(
                        include_leading_stock=include_leading_stock,
                        cache_ttl_sec=cache_ttl_sec,
                        time_budget_sec=time_budget_sec,
                        pages=pages,
                    )
                finally:
                    _THEME_REFRESHING = False
            ThreadPoolExecutor(max_workers=1).submit(_refresh)
            return _THEME_CACHE

        start_time = time.time()
        pages = max(1, min(pages, 10))
        # Fetch pages 1..N concurrently
        all_rows = []
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_theme_page, page) for page in range(1, pages + 1)]
            for future in futures:
                all_rows.extend(future.result())
        
        # Deduplicate if needed (though pages shouldn't overlap)
        results_map = {}
        if include_leading_stock and all_rows:
            # Skip deep scrape if time budget already exceeded.
            if time.time() - start_time < time_budget_sec:
                targets = [i for i, item in enumerate(all_rows) if not item.get("leadingStock") or item.get("leadingStock") == "-"]
                if targets:
                    with ThreadPoolExecutor(max_workers=5) as executor:
                        futures = {executor.submit(fetch_leading_stock, all_rows[i]['link']): i for i in targets}
                        for future in futures:
                            idx = futures[future]
                            try:
                                results_map[idx] = future.result()
                            except Exception:
                                results_map[idx] = "-"

        # Assemble result
        themes = []
        for i, item in enumerate(all_rows):
            leading = item.get("leadingStock") or results_map.get(i, "-")
            themes.append({
                "rank": i + 1,
                "name": item['name'],
                "changePercent": item['change'],
                "change3d": item['avg3d'],
                "leadingStock": leading,
            })
        
        _THEME_CACHE = themes
        _THEME_CACHE_AT = time.time()
        return themes
        
    except Exception as e:
        print(f"Error scraping themes: {str(e)}")
        return _THEME_CACHE or []

def fetch_industry_leading_stock(industry_link: str, industry_name: str | None = None) -> str:
    """
    Fetch the leading stock from an industry detail page.
    """
    cached = _get_cached_industry_leading(industry_name)
    if not industry_link:
        return cached if cached != "-" else "-"
    url = industry_link
    if industry_link.startswith("/"):
        url = f"https://finance.naver.com{industry_link}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.type_5")
        if not table:
            return cached if cached != "-" else "-"
        rows = table.select("tr")
        for row in rows:
            name_td = row.select_one("td.name")
            if name_td:
                stock_name = name_td.get_text(strip=True)
                _set_cached_industry_leading(industry_name, stock_name)
                return stock_name
        return cached if cached != "-" else "-"
    except Exception:
        return cached if cached != "-" else "-"


def get_naver_industries(
    include_leading_stock: bool = False,
    cache_ttl_sec: int = 300,
    time_budget_sec: int = 8,
    limit_leading: int = 0,
):
    """
    Scrape Industry rankings from Naver Finance
    URL: https://finance.naver.com/sise/sise_group.nhn?type=upjong
    """
    global _INDUSTRY_CACHE, _INDUSTRY_CACHE_AT, _INDUSTRY_REFRESHING
    global _INDUSTRY_LEADING_CACHE, _INDUSTRY_LEADING_CACHE_AT, _INDUSTRY_LEADING_REFRESHING
    global _INDUSTRY_LEADING_CACHE_LIMITED
    url = "https://finance.naver.com/sise/sise_group.nhn?type=upjong"
    try:
        now = time.time()
        if include_leading_stock:
            if (
                _INDUSTRY_LEADING_CACHE
                and _INDUSTRY_LEADING_CACHE_AT
                and (now - _INDUSTRY_LEADING_CACHE_AT) < cache_ttl_sec
                and not (_INDUSTRY_LEADING_CACHE_LIMITED and not limit_leading)
            ):
                return _INDUSTRY_LEADING_CACHE
            if (
                _INDUSTRY_LEADING_CACHE
                and not _INDUSTRY_LEADING_REFRESHING
                and not (_INDUSTRY_LEADING_CACHE_LIMITED and not limit_leading)
            ):
                def _refresh():
                    global _INDUSTRY_LEADING_REFRESHING
                    _INDUSTRY_LEADING_REFRESHING = True
                    try:
                        get_naver_industries(
                            include_leading_stock=True,
                            cache_ttl_sec=cache_ttl_sec,
                            time_budget_sec=time_budget_sec,
                            limit_leading=limit_leading,
                        )
                    finally:
                        _INDUSTRY_LEADING_REFRESHING = False
                ThreadPoolExecutor(max_workers=1).submit(_refresh)
                return _INDUSTRY_LEADING_CACHE
        else:
            if _INDUSTRY_CACHE and _INDUSTRY_CACHE_AT and (now - _INDUSTRY_CACHE_AT) < cache_ttl_sec:
                return _INDUSTRY_CACHE
            if _INDUSTRY_CACHE and not _INDUSTRY_REFRESHING:
                def _refresh():
                    global _INDUSTRY_REFRESHING
                    _INDUSTRY_REFRESHING = True
                    try:
                        get_naver_industries(
                            include_leading_stock=False,
                            cache_ttl_sec=cache_ttl_sec,
                            time_budget_sec=time_budget_sec,
                            limit_leading=limit_leading,
                        )
                    finally:
                        _INDUSTRY_REFRESHING = False
                ThreadPoolExecutor(max_workers=1).submit(_refresh)
                return _INDUSTRY_CACHE

        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")

        table = soup.select_one("table.type_1")
        if not table:
            return []

        industries = []
        rows = table.select("tr")
        rank = 1

        def parse_int(value: str):
            try:
                return int(value.replace(",", ""))
            except Exception:
                return 0

        for row in rows:
            cols = row.select("td")
            if len(cols) < 6:
                continue

            link = cols[0].select_one("a")
            if not link:
                continue

            name = link.get_text(strip=True)
            change = cols[1].get_text(strip=True)
            href = link.get("href") or ""
            if name and href:
                _INDUSTRY_LINK_CACHE[name] = href

            total = parse_int(cols[2].get_text(strip=True))
            up = parse_int(cols[3].get_text(strip=True))
            flat = parse_int(cols[4].get_text(strip=True))
            down = parse_int(cols[5].get_text(strip=True))

            cached_leading = _get_cached_industry_leading(name)
            industries.append({
                "rank": rank,
                "name": name,
                "link": href,
                "change": change,
                "total": total,
                "up": up,
                "flat": flat,
                "down": down,
                "leadingStock": cached_leading if cached_leading != "-" else "-",
            })
            rank += 1

        if include_leading_stock and industries:
            start_time = time.time()
            targets = industries[:limit_leading] if limit_leading else industries
            if time.time() - start_time < time_budget_sec and targets:
                with ThreadPoolExecutor(max_workers=5) as executor:
                    futures = {
                        executor.submit(fetch_industry_leading_stock, item["link"], item["name"]): i
                        for i, item in enumerate(targets)
                        if item.get("leadingStock") in ("", "-", None)
                    }
                    for future in futures:
                        idx = futures[future]
                        try:
                            industries[idx]["leadingStock"] = future.result()
                        except Exception:
                            industries[idx]["leadingStock"] = "-"

        if include_leading_stock:
            if not limit_leading:
                _INDUSTRY_LEADING_CACHE = industries
                _INDUSTRY_LEADING_CACHE_AT = time.time()
                _INDUSTRY_LEADING_CACHE_LIMITED = False
        else:
            _INDUSTRY_CACHE = industries
            _INDUSTRY_CACHE_AT = time.time()
        return industries

    except Exception as e:
        print(f"Error scraping industries: {str(e)}")
        return _INDUSTRY_LEADING_CACHE or _INDUSTRY_CACHE or []

def get_naver_industry_members(industry_link: str):
    """
    Scrape member tickers from a Naver industry detail page.
    """
    if not industry_link:
        return []

    url = industry_link
    if industry_link.startswith("/"):
        url = f"https://finance.naver.com{industry_link}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.type_5")
        if not table:
            return []

        tickers = []
        for a in table.select("a[href*='code=']"):
            href = a.get("href") or ""
            if "code=" not in href:
                continue
            code = href.split("code=")[-1].split("&")[0]
            if code and code.isdigit() and len(code) == 6:
                tickers.append(code)

        return sorted(set(tickers))
    except Exception:
        return []

def get_industry_link_by_name(name: str) -> str | None:
    if not _INDUSTRY_LINK_CACHE:
        get_naver_industries()
    return _INDUSTRY_LINK_CACHE.get(name)

def get_naver_theme_members(theme_link: str):
    """
    Scrape member tickers from a Naver theme detail page.
    """
    if not theme_link:
        return []

    url = theme_link
    if theme_link.startswith("/"):
        url = f"https://finance.naver.com{theme_link}"

    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.encoding = 'euc-kr'
        soup = BeautifulSoup(resp.text, "html.parser")
        table = soup.select_one("table.type_5")
        if not table:
            return []

        tickers = []
        for a in table.select("a[href*='code=']"):
            href = a.get("href") or ""
            if "code=" not in href:
                continue
            code = href.split("code=")[-1].split("&")[0]
            if code and code.isdigit() and len(code) == 6:
                tickers.append(code)

        return sorted(set(tickers))
    except Exception:
        return []

def get_theme_link_by_name(name: str) -> str | None:
    if not _THEME_LINK_CACHE:
        get_naver_themes()
    return _THEME_LINK_CACHE.get(name)
