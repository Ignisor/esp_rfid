SSID = '[ssid]'
PASSWORD = '[pass]'
CONNECT_RETRIES = 10
CONNECTION_TIME = 6.0

CARDS_STORAGE_FILE = 'cards.txt'

URL = 'http://door.gowombat.team/open/'

try:
    from .local_conf import *
except ImportError:
    pass
