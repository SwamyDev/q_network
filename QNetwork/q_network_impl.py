from functools import reduce

START_KEY_GENERATION_TAG = "SKey"
END_KEY_GENERATION_TAG = "EKey"

IDLE = 0
WRITING = 1
READING = 2


class SecureChannel:
    def __init__(self, from_name, to_name):
        self.from_name = from_name
        self.to_name = to_name
        self.network_factory = None
        self.q_channel = None
        self.ca_channel = None

        self._state = IDLE

    def __enter__(self):
        self.q_channel = self.network_factory.make_q_channel(self.from_name, self.to_name)
        self.ca_channel = self.network_factory.make_ca_channel(self.from_name, self.to_name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            if self._state is WRITING:
                self.ca_channel.receive_ack()
                self.ca_channel.clear()
            elif self._state is READING:
                self.ca_channel.send_ack()
            else:
                self.ca_channel.clear()

        else:
            self.ca_channel.clear()

        self.q_channel.close()

    def write(self, data):
        self._state = WRITING
        msg = self.to_binary_list(data)
        key = self.create_key(msg)
        enc_msg = [(m + k) % 2 for m, k in zip(msg, key)]
        self.ca_channel.send(enc_msg)

    @staticmethod
    def to_binary_list(data):
        msg = []
        for c in data:
            binary_str = format(ord(c), 'b').rjust(8, '0')
            for b in binary_str:
                msg.append(int(b))
        return msg

    def create_key(self, msg):
        node = self.network_factory.make_sender_node(self.q_channel, self.ca_channel)
        key = []
        while len(key) < len(msg):
            self.ca_channel.send(self.to_binary_list(START_KEY_GENERATION_TAG))
            key += node.try_generate_key()

        self.ca_channel.send(self.to_binary_list(END_KEY_GENERATION_TAG))
        return key

    def read(self):
        self._state = READING
        key = self.get_key()
        enc_msg = self.ca_channel.receive()

        assert len(key) >= len(enc_msg), "Not enough key ({0}) to decode message of length {1}"\
            .format(len(key), len(enc_msg))

        msg = [(m + k) % 2 for m, k in zip(enc_msg, key)]
        return self.to_string(msg)

    def get_key(self):
        node = self.network_factory.make_receiver_node(self.q_channel, self.ca_channel)
        key = []
        tag = self.to_string(self.ca_channel.receive())
        while tag == START_KEY_GENERATION_TAG:
            key += node.try_generate_key()
            tag = self.to_string(self.ca_channel.receive())
        assert tag == END_KEY_GENERATION_TAG, "Expected tag {}, but got {}".format(END_KEY_GENERATION_TAG, tag)
        return key

    @staticmethod
    def to_string(integer_array):
        msg = ''
        for i in range(0, len(integer_array), 8):
            o = int(reduce(lambda s, i: s + str(i), (integer_array[i:i+8]), ''), 2)
            msg += chr(o)

        return msg