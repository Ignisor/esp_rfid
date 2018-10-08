import gc
import socket
import time
import ubinascii
import machine

gc.collect()

from data import conf
from utils.mfrc522 import MFRC522
from utils.pins import LED, OFF, ON
from utils.wifi import sta_if


class CardsStorage(object):
    FILENAME = conf.CARDS_STORAGE_FILE

    def __init__(self):
        self.cards_uids = set()

    def save(self):
        with open(self.FILENAME, 'w') as storage:
            for uid in self.cards_uids:
                storage.write(uid + '\n')

    def load(self):
        try:
            with open(self.FILENAME) as storage:
                self.cards_uids = set(storage.read().split())
        except OSError:
            pass

    def contains_card(self, card_uid):
        return card_uid in self.cards_uids

    def add_card(self, card_uid):
        self.cards_uids.add(card_uid)
        self.save()


def send_open_request():
    LED.value(OFF)

    # send post request to open door
    if sta_if.isconnected():
        _, _, host, path = conf.URL.split('/', 3)

        try:
            host, port = host.split(':')
            port = int(port)
        except ValueError as e:
            port = 80

        try:
            # try to get address info from domain name
            addr = socket.getaddrinfo(host, port)[0][-1]
        except OSError:
            # then just parse IP
            addr = (host, port)

        s = socket.socket()
        try:
            s.connect(addr)
            s.send(bytes('POST /%s HTTP/1.0\r\nHost: %s\r\n\r\n' % (path, host), 'utf8'))
            time.sleep(1)
        except OSError as e:
            pass

        s.close()

    LED.value(ON)


def wait_and_add_card():
    print('Waiting to store new card')
    for _ in range(10):
        time.sleep(0.1)
        LED.value(not LED.value())
    LED.value(ON)

    card = reader.read_data([])
    if not card:
        return False

    print('Storing uid:', card.str_uid)
    storage.add_card(card.str_uid)

    for _ in range(10):
        time.sleep(0.1)
        LED.value(not LED.value())
    LED.value(OFF)

    return True


storage = CardsStorage()
storage.load()
reader = MFRC522(0, 2, 4, 5, 14)

while True:
    card = reader.read_data([8])
    if not card:
        continue

    print('uid: ', card.str_uid)
    if storage.contains_card(card.str_uid):
        try:
            print('Opening the door')
            send_open_request()
        except Exception:
            pass

    if card.get_data(8) == ubinascii.hexlify(conf.ADMIN_CODE):
        wait_and_add_card()

    gc.collect()

machine.reset()
