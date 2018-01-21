import time
from functools import reduce


class QState:
    def __init__(self, value, basis):
        self.value = value
        self.basis = basis

    def __eq__(self, other):
        return self.value == other.value and self.basis == other.basis

    def __repr__(self):
        return 'Qubit(value={}, basis={})'.format(self.value, self.basis)


class QChannel:
    def __init__(self, connection, qubit_factory, receiver):
        self._connection = connection
        self._qubit_factory = qubit_factory
        self._receiver = receiver
        self.bases_mapping = [lambda q: None, lambda q: q.H(print_info=False)]

    def send_qubits(self, qstates):
        for qs in qstates:
            q = self._qubit_factory(self._connection)
            if qs.value == 1:
                q.X()

            self.bases_mapping[qs.basis](q)
            self._connection.sendQubit(q, self._receiver)

    def send_epr(self, bases):

        def from_created_epr_pair(idx):
            if idx % 50:
                time.sleep(0.1)
            return self._connection.createEPR(self._receiver, print_info=False)

        return self._measure_qubits_in_bases(from_created_epr_pair, bases)

    def _measure_qubits_in_bases(self, take_qubit, bases):
        qstates = []
        for i, b in enumerate(bases):
            q = take_qubit(i)
            self.bases_mapping[b](q)
            qstates.append(QState(q.measure(print_info=False), b))

        return qstates

    def receive_qubits_in(self, bases):
        def from_received_qubit(idx):
            return self._connection.recvQubit()

        return self._measure_qubits_in_bases(from_received_qubit, bases)

    def receive_epr_in(self, bases):
        def from_received_epr(idx):
            return self._connection.recvEPR(print_info=False)

        return self._measure_qubits_in_bases(from_received_epr, bases)


class CAChannel:
    def __init__(self, connection, other):
        self._connection = connection
        self._other = other

    def send(self, data):
        if not isinstance(data, list):
            data = [data]
        self._connection.sendValueList(self._other, data)

    def send_ack(self):
        self._connection.sendAck(self._other)

    def receive(self):
        data = self._connection.getValueList(self._other)
        return data

    def receive_ack(self):
        self._connection.getAck(self._other)

    def clear(self):
        self._connection.clearServer()

    def close(self):
        self._connection.closeChannel()


class ChannelFactory:
    """
    @staticmethod
    def make_q_channel(from_name, to_name):
        connection = CQCConnection(from_name)
        return QChannel(connection, qubit, to_name)

    @staticmethod
    def make_ca_channel(from_name, to_name):
        return CAChannel(ipcCacClient(from_name), to_name)
    """


START_KEY_GENERATION_TAG = "SKey"
END_KEY_GENERATION_TAG = "EKey"


class SecureChannel:
    def __init__(self, from_name, to_name):
        self.from_name = from_name
        self.to_name = to_name
        self.channel_factory = ChannelFactory()
        self.q_channel = None
        self.ca_channel = None

    def __enter__(self):
        self.q_channel = self.channel_factory.make_q_channel(self.from_name, self.to_name)
        self.ca_channel = self.channel_factory.make_ca_channel(self.from_name, self.to_name)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.ca_channel.clear()
        else:
            self.ca_channel.force_clear()

        self.q_channel.close()

    def write(self, data):
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
        node = self.channel_factory.make_sender_node(self.q_channel, self.ca_channel)
        key = []
        while len(key) < len(msg):
            self.ca_channel.send(self.to_binary_list(START_KEY_GENERATION_TAG))
            key += node.try_generate_key()

        self.ca_channel.send(self.to_binary_list(END_KEY_GENERATION_TAG))
        return key

    def read(self):
        key = self.get_key()
        enc_msg = self.ca_channel.receive()

        assert len(key) >= len(enc_msg), "Not enough key ({0}) to decode message of length {0}"\
            .format(len(key), len(enc_msg))

        msg = [(m + k) % 2 for m, k in zip(enc_msg, key)]
        return self.to_string(msg)

    def get_key(self):
        node = self.channel_factory.make_receiver_node(self.q_channel, self.ca_channel)
        key = []
        tag = self.to_string(self.ca_channel.receive())
        while tag == START_KEY_GENERATION_TAG:
            key += node.try_generate_key()
            tag = self.to_string(self.ca_channel.receive())
        assert tag == END_KEY_GENERATION_TAG, "Expected tag {}, but got {}".format(END_KEY_GENERATION_TAG, tag)
        return key

    def to_string(self, integer_array):
        msg = ''
        for i in range(0, len(integer_array), 8):
            o = int(reduce(lambda s, i: s + str(i), (integer_array[i:i+8]), ''), 2)
            msg += chr(o)

        return msg


def open_channel(from_name, to_name):
    return SecureChannel(from_name, to_name)
