import time


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
