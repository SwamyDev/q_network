import operator
import random

from QNetwork.q_network import QState


class BB84Node:
    def __init__(self, q_channel, ca_channel, max_error):
        self.q_channel = q_channel
        self.ca_channel = ca_channel
        self.max_error = max_error

        self._qstates = []
        self._other_bases = []
        self._test_set = set()
        self._test_values = []
        self._other_test_values = []
        self._seed = []

    def send_q_states(self, amount):
        self.ca_channel.send(amount)
        self._qstates = [QState(value, basis) for value, basis in zip(self._gen_random_string(amount),
                                                                      self._gen_random_string(amount))]
        self.q_channel.send(self._qstates)

    @staticmethod
    def _gen_random_string(size):
        return [random.randint(0, 1) for _ in range(size)]

    def send_test_set(self):
        s = len(self._qstates)
        t = s // 2
        self._test_set = set()
        while len(self._test_set) < t:
            self._test_set.add(random.randint(0, s - 1))

        self.ca_channel.send(list(self._test_set))

    def send_test_values(self):
        self._test_values = [self._qstates[i].value for i in self._test_set]
        self.ca_channel.send(self._test_values)

    def send_seed(self):
        m = len(self._qstates) - len(self._test_set)
        self._seed = self._gen_random_string(m)
        self.ca_channel.send(self._seed)

    def send_bases(self):
        self.ca_channel.send([q.basis for q in self._qstates])

    def receive_q_states(self):
        n = self.ca_channel.receive()[0]
        self._qstates = self.q_channel.receive(self._gen_random_string(n))

    def receive_bases(self):
        self._other_bases = self.ca_channel.receive()

    def receive_test_set(self):
        self._test_set = set(self.ca_channel.receive())

    def receive_test_values(self):
        self._other_test_values = self.ca_channel.receive()

    def discard_states(self):
        def has_same_basis(pair):
            q, b = pair
            return q.basis == b

        self._qstates = [q for q, _ in filter(has_same_basis, zip(self._qstates, self._other_bases))]

    def calculate_error(self):
        t = len(self._test_values)
        w = sum(a != b for a, b in zip(self._test_values, self._other_test_values))
        return w / t

    def privacy_amplification(self):
        indices = set(range(len(self._qstates))) - self._test_set
        x = [self._qstates[i].value for i in indices]
        k = sum(map(operator.mul, x, self._seed)) % 2
        return k
