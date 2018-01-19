from QNetwork.q_network import QState
from QNetwork.qkd import QKDNode


class BB84Node(QKDNode):
    def __init__(self, q_channel, ca_channel):
        super().__init__(ca_channel)
        self.q_channel = q_channel

        self._test_values = []
        self._other_test_values = []
        self._seed = []

    def _send_q_states(self, amount):
        super()._send_q_states(amount)
        self._qstates = [QState(value, basis) for value, basis in zip(self._gen_random_string(amount),
                                                                      self._gen_random_string(amount))]
        self.q_channel.send_qubits(self._qstates)

    def _send_test_values(self):
        self._test_values = [self._qstates[i].value for i in self._test_set]
        self.ca_channel.send(self._test_values)

    def _send_seed(self):
        m = len(self._qstates) - len(self._test_set)
        self._seed = self._gen_random_string(m)
        self.ca_channel.send(self._seed)

    def _measure_qstates(self, amount):
        self._qstates = self.q_channel.measure_qubits(self._gen_random_string(amount))

    def _receive_test_set(self):
        self._test_set = set(self.ca_channel.receive())

    def _receive_test_values(self):
        self._other_test_values = self.ca_channel.receive()

    def _receive_seed(self):
        self._seed = self.ca_channel.receive()

    def _discard_states(self):
        def has_same_basis(pair):
            q, b = pair
            return q.basis == b

        self._qstates = [q for q, _ in filter(has_same_basis, zip(self._qstates, self._other_bases))]

    def _calculate_error(self):
        t = len(self._test_values)
        w = sum(a != b for a, b in zip(self._test_values, self._other_test_values))
        return w / t

    def _privacy_amplification(self):
        indices = set(range(len(self._qstates))) - self._test_set
        x = [self._qstates[i].value for i in indices]
        return self._extract_key(x, self._seed)


class BB84SenderNode(BB84Node):
    def __init__(self, q_channel, ca_channel, n):
        super().__init__(q_channel, ca_channel)
        self.n = n

    def share_q_states(self):
        self._send_q_states(self.n)
        self._share_bases()

    def get_error(self):
        self._discard_states()
        self._send_test_set()
        self._send_test_values()
        self._receive_test_values()
        return self._calculate_error()

    def generate_key(self):
        self._send_seed()
        return self._privacy_amplification()


class BB84ReceiverNode(BB84Node):
    def __init__(self, q_channel, ca_channel):
        super().__init__(q_channel, ca_channel)

    def share_q_states(self):
        self._receive_q_states()
        self._share_bases()

    def get_error(self):
        self._discard_states()
        self._receive_test_set()
        self._send_test_values()
        self._receive_test_values()
        return self._calculate_error()

    def generate_key(self):
        self._receive_seed()
        return self._privacy_amplification()