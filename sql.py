import datetime
import json
import logging

import config
from config import DB, DEV, DEV_LIMIT, TOTAL_LINKS
import psycopg2
from psycopg2.extras import DictCursor
from sshtunnel import SSHTunnelForwarder


tunnel = None
sql_conn = None
sql_cur = None

log = logging.getLogger("parser")


def create_tunnel(tunneled = True):
    global tunnel
    global sql_conn
    global sql_cur
    if tunneled:
        tunnel = SSHTunnelForwarder(
            (DB.ssh_host, DB.ssh_port),
            ssh_username=DB.ssh_user,
            ssh_password=DB.ssh_password,
            remote_bind_address=(DB.db_host, DB.db_port)
        )
        tunnel.start()
        sql_conn = psycopg2.connect(
                user=DB.db_user,
                password=DB.db_password,
                host='127.0.0.1',
                port=tunnel.local_bind_port,
                database=DB.db_name,
            )
    else:
        sql_conn = psycopg2.connect(
            user=DB.db_user,
            password=DB.db_password,
            host='127.0.0.1',
            port=DB.db_port,
            database=DB.db_name,
        )

    sql_cur = sql_conn.cursor(cursor_factory=DictCursor)


def close_tunnel(tunneled = True):
    _log = logging.getLogger("parser.sql.destructor")
    global tunnel
    global sql_conn
    global sql_cur
    if sql_cur:
        sql_cur.close()
    else:
        _log.info('Create cursor before closing!')
    if sql_conn:
        sql_conn.close()
    else:
        _log.info('Create connection before closing!')
    if tunneled and tunnel:
        tunnel.close()
    else:
        _log.info('Create SSH tunnel before closing!')


def sql_push_article():
    pass


def sql_get_article():
    pass


def sql_push_articles():
    pass


def sql_get_articles():
    pass


# sql_conn = psycopg2.connect(
#     user=DB.db_user,
#     password=DB.db_password,
#     host='127.0.0.1',
#     port=DB.db_port,
#     database=DB.db_name,
# )
#
# sql_cur = sql_conn.cursor()
def sql_get_last_link_date():
    q = "select date from links order by date desc limit 1;"
    try:
        sql_cur.execute(q)
        record = sql_cur.fetchall()[0][0]
        rec_str = record.strftime("%Y-%m-%d")
        return str(rec_str)
    except:
        return None

def sql_push_links(lnks: list):
    def push_link(lnk):
        try:
            insert_query = "INSERT INTO links (name, link, date) VALUES (%s, %s, %s)"
            sql_cur.execute(insert_query,(lnk['name'],lnk['link'],lnk['date']))
            sql_conn.commit()
            return True
        except:
            return False
    _log = logging.getLogger('parser.sql.pushlinks')
    values = []
    try:
        insert_query = "INSERT INTO links (name, link, date) VALUES (%s, %s, %s)"
        for lnk in lnks:
            #print(json.dumps(lnk,ensure_ascii=False,indent=4))
            values.append((lnk['name'],lnk['link'],lnk['date']))
        sql_cur.executemany(insert_query, values)
        sql_conn.commit()
    except Exception as e:
        _log.error(e)
        sql_conn.rollback()
        for lnk in lnks:
            if push_link(lnk):
                _log.info('Ok!')
            else:
                _log.info('Not Ok =(')


def sql_get_links():
    _log = logging.getLogger('parser.sql.get_links')
    select_query = "SELECT * FROM links WHERE downloaded = False" #AND uploaded = False"
    if DEV:
        select_query = f"SELECT * FROM links WHERE downloaded = False LIMIT {DEV_LIMIT}" #AND uploaded = False LIMIT 50"
        _log.info(f'DEV mode! with DEV_LIMIT = {DEV_LIMIT}')
    sql_cur.execute(select_query)
    records = sql_cur.fetchall()
    config.TOTAL_LINKS = len(records)
    if config.TOTAL_LINKS > 0:
        return records
    else:
        return None


def sql_set_link_downloaded(link):
    _log = logging.getLogger('parser.sql.set_link_downloaded')
    try:
        q = "UPDATE links SET downloaded = %s WHERE link = %s"
        sql_cur.execute(q,(True,link))
        sql_conn.commit()
        return True
    except Exception as e:
        _log.error(e)
        sql_conn.rollback()
        return False


def sql_add_article(d: dict):
    _log = logging.getLogger('parser.sql.add_article')
    try:
        q = "INSERT INTO articles (local_id, name, origin, source, date, description) VALUES (%s, %s, %s, %s, %s, %s)"
        values = (d['local_id'],d['name'],d['origin'],d['source'],d['date'],d['description'])
        sql_cur.execute(q,values)
        sql_conn.commit()
        if sql_set_link_downloaded(d['source']):
            return True
        else:
            return False
    except Exception as e:
        _log.error(e)
        sql_conn.rollback()
        return False



def sql_version():
    _log = logging.getLogger('parser.sql')
    q = "SELECT version();"
    sql_cur.execute(q)
    _log.info(f'Version: {sql_cur.fetchone()[0]}')











# with SSHTunnelForwarder(
#     (DB.ssh_host, DB.ssh_port),
#     ssh_username=DB.ssh_user,
#     ssh_password=DB.ssh_password,
#     remote_bind_address=(DB.db_host, DB.db_port)
# ) as tunnel:
#     connection = psycopg2.connect(
#         user=DB.db_user,
#         password=DB.db_password,
#         host='127.0.0.1',
#         port=tunnel.local_bind_port,
#         database=DB.db_name,
#     )
#     # Do stuff with the database connection here
#     connection.close()