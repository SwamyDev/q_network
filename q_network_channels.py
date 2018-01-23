import time


class QState:
    """
    POD class to hold value and measurement basis of a quantum state
    """
    def __init__(self, value, basis):
        self.value = value
        self.basis = basis

    def __eq__(self, other):
        return self.value == other.value and self.basis == other.basis

    def __repr__(self):
        return 'Qubit(value={}, basis={})'.format(self.value, self.basis)


class QChannel:
    """
    Object that handles quantum communication via the a quantum device interface.
    """
    def __init__(self, connection, qubit_factory, receiver):
        self._connection = connection
        self._qubit_factory = qubit_factory
        self._receiver = receiver
        self.bases_mapping = [lambda q: None, lambda q: q.H(print_info=False)]

    def send_qubits(self, qstates):
        """
        Takes a list of QStates and prepares qubits dependent on value and basis specified in the QStates. It then
        sends them via the quantum connection to the specified receiver
        :param qstates: List of QStates
        """
        for qs in qstates:
            q = self._qubit_factory(self._connection)
            if qs.value == 1:
                q.X()

            self.bases_mapping[qs.basis](q)
            self._connection.sendQubit(q, self._receiver)

    def send_epr(self, bases):
        """
        Takes a list of bases and prepare an EPR-pair. One qubit is sent to the specified receiver and the other is
        measured specified by the basis in the provided list.
        :param bases: Integer list representing measurement bases
        :return: List of QStates containing the measurement outcome as value and the basis used for measurement
        """
        def from_created_epr_pair(idx):
            # The recipient needs some time to catch up otherwise the sender runs out of available qubits
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
        """
        Takes a list of bases and measures the retrieved qubits in those bases. Returns a list of QStates containing
        measurement outcomes and the used bases.
        :param bases: Integer list representing bases
        :return: QState list containing the measurement outcome as value and the used basis
        """
        def from_received_qubit(idx):
            return self._connection.recvQubit()

        return self._measure_qubits_in_bases(from_received_qubit, bases)

    def receive_epr_in(self, bases):
        """
        Takes a list of bases and measures the retrieved entangled qubits in those bases. Returns a list of QStates
        containing measurement outcomes and the used bases.
        :param bases: Integer list representing bases
        :return: QState list containing the measurement outcome as value and the used basis
        """
        def from_received_epr(idx):
            return self._connection.recvEPR(print_info=False)

        return self._measure_qubits_in_bases(from_received_epr, bases)

    def close(self):
        """
        Closes the quantum connection.
        """
        self._connection.close()


class CAChannel:
    """
    An object that handled classical authenticated communication used in quantum key distribution.
    """
    def __init__(self, connection, other):
        self._connection = connection
        self._other = other

    def send(self, data):
        """
        Sends data via the classical authenticated channel.
        :param data: Integer list containing binary representation of the data to be sent
        """
        if not isinstance(data, list):
            data = [data]
        self._connection.sendValueList(self._other, data)

    def send_ack(self):
        """
        Sends an acknowledgment signal
        """
        self._connection.sendAck(self._other)

    def receive(self):
        """
        Receives data sent via the classical authenticated channel as integer list.
        :return: Integer list containing binary representation of the data received
        """
        data = self._connection.getValueList(self._other)
        return data

    def receive_ack(self):
        """
        Receives an acknowledgement signal.
        """
        self._connection.getAck(self._other)

    def clear(self):
        """
        Clears the classical server.
        """
        self._connection.clearServer()

    def close(self):
        """
        Closes the classical server.
        """
        self._connection.closeChannel()
