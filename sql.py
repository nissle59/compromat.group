import logging

from config import DB
import psycopg2
from sshtunnel import SSHTunnelForwarder

tunnel = None
sql_conn = None
sql_cur = None

log = logging.getLogger("parser")


def create_tunnel():
    global tunnel
    global sql_conn
    global sql_cur
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
    sql_cur = sql_conn.cursor()


def close_tunnel():
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
    if tunnel:
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


def sql_push_links(lnks: list):
    _log = logging.getLogger('parser.sql.pushlinks')
    values = []
    try:
        insert_query = "INSERT INTO links (name, link, date) VALUES (%s, %s, %s)"
        for lnk in lnks:
            values.append((lnk['name'],lnk['link'],lnk['date']))
        sql_cur.executemany(insert_query, values)
        sql_conn.commit()
    except Exception as e:
        _log.error(e)


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