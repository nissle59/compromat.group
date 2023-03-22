import requests
import locale
import json
import datetime
from bs4 import BeautifulSoup
from tqdm.auto import trange
from config import *
import logging
from sql import *

locale.setlocale(locale.LC_TIME, "ru_RU")

log = logging.getLogger("parser")
# log_level = logging.INFO

rs = requests.session()
rs.headers = headers
rs.proxies = proxies[iter_proxy]

rs.verify = False


def GET(url):
    _log = logging.getLogger('parser.GET')

    def with_proxy(url, proxy):
        px = {
            'http': 'http://' + proxy,
            'htts': 'http://' + proxy
        }
        try:
            _log.info(f'Try to {url} with proxy {proxy}')
            resp = rs.get(url, proxies=px)
            if resp.status_code in [200, 201]:
                return resp
        except:
            return None

    try:
        resp = rs.get(url)
        if resp.status_code in [200, 201]:
            return resp
        else:
            for p in proxies:
                try:
                    resp = with_proxy(url, p)
                    if resp.status_code in [200, 201]:
                        return resp
                except Exception as e:
                    pass
    except Exception as e:
        for p in proxies:
            try:
                resp = with_proxy(url, p)
                if resp.status_code in [200, 201]:
                    return resp
            except Exception as e:
                pass
        _log.info(f'{url} failed')
        return None


def get_articles_links():
    links = []
    _log = logging.getLogger('parser.getlinks')
    init_url = base_url + 'news/'
    resp = GET(init_url)
    html = resp.text
    soup = BeautifulSoup(html, features='html.parser')
    nav = soup.find('div', {'class': 'navigation'})
    a_s = nav.find_all('a', recursive=False)
    total_pages = int(a_s[-1:][0].text.strip())
    _log.info(f'Total pages: {total_pages}')
    for current_page in trange(1, total_pages, desc='Loading links...'):
        d = {}
        page_url = init_url + f'page/{current_page}/'
        resp = GET(page_url)
        if resp:
            arr = []
            html = resp.text
            soup = BeautifulSoup(html, features='html.parser')
            art_list = soup.find('div', {'id': 'dle-content'}).find_all('article', recursive=False)
            _log.info(f'[{round(current_page/total_pages*100,2)}%] Processing {current_page} of {total_pages} -=-=- URL: {page_url}...')
            for article in art_list:
                try:
                    a = article.find('a')
                    h2 = a.find('h2').text.strip()
                    date = a.find('div', {'class': 'stories_date'}).text.strip().title()
                    dt = datetime.datetime.strptime(date, '%d %b %Y')
                    date = dt.strftime('%Y-%m-%d')
                    link = a['href']
                    d = {}
                    d = {
                        'name': h2,
                        'date': date,
                        'link': link
                    }
                    #print((d['name'],d['link'],d['date']))
                    arr.append(d)
                    links.append(d)
                except Exception as e:
                    _log.error(e)
            sql_push_links(arr)
            arr.clear()
            # with open('links.json', 'w', encoding='utf-8') as f:
            #     f.write(json.dumps(links, ensure_ascii=False, indent=4))
        else:
            _log.error(f'[{page_url}] FAILED!')


if __name__ == "__main__":
    pass
