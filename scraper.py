import requests
import locale
import json
import datetime
from bs4 import BeautifulSoup, Comment, Tag
from tqdm.auto import trange
import concurrent.futures as pool
import threading, time

import config
from config import *
import logging
from sql import *
from urllib.parse import urlparse

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
        _log.debug(f'{resp.status_code}')
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
    last_date = sql_get_last_link_date()
    if last_date:
        last_dt = datetime.datetime.strptime(last_date,"%Y-%m-%d")
    _log = logging.getLogger('parser.getlinks')
    init_url = base_url + 'news/'
    resp = GET(init_url)
    html = resp.text
    soup = BeautifulSoup(html, features='html.parser')
    nav = soup.find('div', {'class': 'navigation'})
    a_s = nav.find_all('a', recursive=False)
    total_pages = int(a_s[-1:][0].text.strip())
    _log.info(f'Total pages: {total_pages}')
    _log.info(f'Found last date in DB: {last_date}')
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
                    if last_date:
                        days_diff = (dt - last_dt).days
                        if days_diff <= -1:
                            _log.info(f'Links get ended with last_date = {last_date} and current date = {date}')
                            return True
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
        else:
            _log.error(f'[{page_url}] FAILED!')


def parse_article(url):
    _log = logging.getLogger('parser.parsearticle')
    resp = GET(url)
    d = None
    img = None
    if resp:
        local_id = int(urlparse(url).path.split('/')[-1:][0].split('-')[0])
        origin = f'{urlparse(url).scheme}://{urlparse(url).netloc}/'
        html = resp.text
        soup = BeautifulSoup(html, features='html.parser')
        full = soup.find('div',{'class':'full-story'})
        date = full.find('meta',{'itemprop':'datePublished'})['content'].strip()
        title = full.find('span',{'id':'news-title'}).text.strip()
        post = soup.find('div',{'class':'post_content','itemprop':'description'})
        try:
            img_src = full.find('div',{'class':'article_img'}).find('img')['src']
            if img_src[0]=='/':
                img_src = base_url[:-1]+img_src
            b_data = GET(img_src).content
            try:
                ext = urlparse(img_src).path.split('/')[-1:][0].split('.')[-1:][0]
            except:
                ext = 'jpg'
            img = {
                'source':url,
                'ext':ext,
                'b_data':b_data
            }
        except:
            img = None
        try:
            for noindex in post.find_all('noindex'):
                noindex.extract()
        except:
            pass
        try:
            for span in post.find_all('span'):
                span.extract()
        except:
            pass
        try:
            for br in post.find_all('br'):
                br.extract()
        except:
            pass
        try:
            for p in post.find_all('p'):
                try:
                    del p['class']
                except:
                    pass
                for element in p(text=lambda text: isinstance(text, Comment)):
                    element.extract()
        except:
            pass
        try:
            for a in post.find_all('a'):
                a.unwrap()
        except:
            pass
        try:
            del post['itemprop']
            del post['class']
            #post.unwrap()
        except:
            pass

        d = {
            'local_id':local_id,
            'name': title,
            'origin': origin,
            'source': url,
            'date': date,
            'description': post.prettify().replace('<div>','').replace('</div>','').strip(' \n'),
        }
        #return d
    #else:
        #return None
    if d:
        if sql_add_article(d):
            config.CURRENT_LINK += 1
            if img:
                sql_add_image(img)
            _log.info(
                f'[{round(config.CURRENT_LINK / config.TOTAL_LINKS * 100, 2)}%] {config.CURRENT_LINK} of {config.TOTAL_LINKS} -=- {url} parsed and added')
        else:
            _log.info(f'{url} parsed, NOT added')
    else:
        _log.info(f'{url} FAILED')


def parse_articles(links: dict):
    _log = logging.getLogger('parser.parse_articles')
    urls = [link['link'] for link in links]
    for url in urls:
        d = parse_article(url)
        # if d:
        #     if sql_add_article(d):
        #         config.CURRENT_LINK += 1
        #         _log.info(f'[{round(config.CURRENT_LINK / config.TOTAL_LINKS * 100, 2)}%] {config.CURRENT_LINK} of {config.TOTAL_LINKS} -=- {url} parsed and added')
        #     else:
        #         _log.info(f'{url} parsed, NOT added')
        # else:
        #     _log.info(f'{url} FAILED')


def multithreaded_parse_articles(links: dict):
    _log = logging.getLogger('parser.multiparse')
    t_s = []
    tc = THREADS

    l_count, l_mod = divmod(len(links), tc)

    l_mod = len(links) % tc

    if l_mod != 0:

        l_mod = len(links) % THREADS
        if l_mod == 0:
            tc = THREADS
            l_count = len(links) // tc

        else:
            tc = THREADS - 1
            l_count = len(links) // tc

    l_c = []
    for i in range(0, THREADS):
        _log.info(f'{i + 1} of {THREADS}')

        l_c.append(links[l_count * i:l_count * i + l_count])

    for i in range(0, THREADS):
        t_s.append(
            threading.Thread(target=parse_articles, args=(l_c[i],), daemon=True))
    for t in t_s:
        t.start()

        _log.info(f'Started thread #{t_s.index(t) + 1} of {len(t_s)} with {len(l_c[t_s.index(t)])} links')

    for t in t_s:
        t.join()
        _log.info(f'Joined thread #{t_s.index(t) + 1} of {len(t_s)} with {len(l_c[t_s.index(t)])} links')


if __name__ == "__main__":
    pass
