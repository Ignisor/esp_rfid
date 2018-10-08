class CardData(object):
    def __init__(self, uid, tag_type):
        self.uid = uid
        self.tag_type = tag_type
        self.__data = {}

    @property
    def str_uid(self):
        return '0x' + ''.join('{:02x}'.format(i) for i in self.uid)

    def get_data(self, address=None):
        data = []
        if address is None:
            for addr in range(64):
                data.append(self.__data.get(address, None))
        else:
            data = self.__data.get(address, None)

        return data

    def set_data(self, address, value):
        self.__data[address] = value
