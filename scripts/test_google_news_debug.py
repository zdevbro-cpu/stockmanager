
import requests
import xml.etree.ElementTree as ET
import urllib.parse

def test_google_news(query):
    print(f"Testing query: {query}")
    encoded_query = urllib.parse.quote(query)
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        response = requests.get(url, timeout=5)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            # print(response.text[:500])
            root = ET.fromstring(response.content)
            items = root.findall('.//item')
            print(f"Found {len(items)} items.")
            for i, item in enumerate(items[:3]):
                title = item.find('title').text
                print(f"{i+1}. {title}")
        else:
            print("Failed to fetch news.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_google_news("삼성전자")
