import json
with open('config.json','r') as f:
    c = json.loads(f.read())

DEV = c['DEV']['DEV']
if DEV:
    DEV_LIMIT = c['DEV']['DEV_LIMIT']
else:
    DEV_LIMIT = 1

SSH_TUNNELED = c['SSH_TUNNELED']
MULTITHREADED = c['MULTITHREADED']
THREADS = c['THREADS']

proxies = c['proxies']
headers = c['headers']

base_url = c['base_url']


class DB:
    db_user : str
    db_password : str
    db_host : str
    db_port : int
    db_name : str
    ssh_host : str
    ssh_port : int
    ssh_user : str
    ssh_password : str

    def __init__(self):
        db = c['db']
        ssh = c['ssh']
        self.db_host = db['host']
        self.db_port = db['port']
        self.db_user = db['user']
        self.db_password = db['pass']
        self.db_name = db['name']

        self.ssh_host = ssh['host']
        self.ssh_port = ssh['port']
        self.ssh_user = ssh['user']
        self.ssh_password = ssh['pass']


TOTAL_LINKS = 0
CURRENT_LINK = 0

iter_proxy = 0

REMOVE_ATTRIBUTES = ['lang','language','onmouseover','onmouseout','script','style','font',
                        'dir','face','size','color','style','class','width','height','hspace',
                        'border','valign','align','background','bgcolor','text','link','vlink',
                        'alink','cellpadding','cellspacing']
