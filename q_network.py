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

    def send(self, qstates):
        for qs in qstates:
            q = self._qubit_factory(self._connection)
            if qs.value == 1:
                q.X()
            if qs.basis == 1:
                q.H()

            self._connection.sendQubit(q, self._receiver)

    def receive(self, bases):
        qstates = []
        for b in bases:
            q = self._connection.recvQubit()
            if b == 1:
                q.H()
            qstates.append(QState(q.measure(), b))

        return qstates


class CAChannel:
    def __init__(self, connection, receiver):
        self._connection = connection
        self._receiver = receiver

    def send(self, data):
        if not isinstance(data, list):
            data = [data]
        self._connection.sendValueList(self._receiver, data)

    def receive(self):
        data = self._connection.getValueList(self._receiver)
        return data

    def clear(self):
        self._connection.clearServer()

    def close(self):
        self._connection.closeChannel()
