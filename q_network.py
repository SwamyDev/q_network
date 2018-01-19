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

    def send_qubits(self, qstates):
        for qs in qstates:
            q = self._qubit_factory(self._connection)
            if qs.value == 1:
                q.X()
            if qs.basis == 1:
                q.H()

            self._connection.sendQubit(q, self._receiver)

    def measure_qubits(self, bases):
        qstates = []
        for b in bases:
            q = self._connection.recvQubit()
            if b == 1:
                q.H()
            qstates.append(QState(q.measure(), b))

        return qstates


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
