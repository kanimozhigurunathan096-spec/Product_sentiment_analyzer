import requests
from bs4 import BeautifulSoup

urls = [
    'https://www.amazon.in/dp/B0CHX1W1F6',
    'https://www.amazon.in/product-reviews/B0CHX1W1F6/ref=cm_cr_arp_d_viewopt_srt?ie=UTF8&reviewerType=all_reviews&sortBy=recent',
]
for url in urls:
    print('URL', url)
    r = requests.get(url, headers={'User-Agent':'Mozilla/5.0'}, timeout=30)
    print('status', r.status_code)
    soup = BeautifulSoup(r.text, 'html.parser')
    for selector in ["[data-hook='review-body']", ".review-text-content", ".review-text", "[class*='review']"]:
        elems = soup.select(selector)
        print(selector, len(elems))
    print('sample text snippets:')
    for tag in soup.find_all(['div','span','p'])[:30]:
        txt = ' '.join(tag.get_text(' ', strip=True).split())
        if 20 <= len(txt) <= 200 and any(k in txt.lower() for k in ['review','good','bad','camera','battery','quality','excellent','worth']):
            print('---', txt[:300])
            break
    print()
