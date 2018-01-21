import operator
import random
from abc import ABC, abstractmethod


class QKDNode(ABC):
    def __init__(self, ca_channel):
        self.ca_channel = ca_channel
        self._qstates = []
        self._other_bases = []
        self._test_set = set()

    def _send_q_states(self, amount):
        self.ca_channel.send(amount)

    def _share_bases(self):
        self._send_bases()
        self._receive_bases()

    def _send_bases(self):
        self.ca_channel.send([q.basis for q in self._qstates])

    def _send_test_set(self):
        s = len(self._qstates)
        t = s // 2
        self._test_set = set()
        while len(self._test_set) < t:
            self._test_set.add(random.randint(0, s - 1))

        self.ca_channel.send(list(self._test_set))

    def _send_seed(self):
        m = len(self._qstates) - len(self._test_set)
        self._seed = self._gen_random_string(m)
        self.ca_channel.send(self._seed)

    def _send_ack(self):
        self.ca_channel.send_ack()

    def _receive_q_states(self):
        amount = self.ca_channel.receive()[0]
        self._measure_qstates(amount)

    @abstractmethod
    def _measure_qstates(self, amount):
        pass

    def _receive_bases(self):
        self._other_bases = self.ca_channel.receive()

    def _receive_seed(self):
        self._seed = self.ca_channel.receive()

    def _receive_test_set(self):
        self._test_set = set(self.ca_channel.receive())

    def _receive_ack(self):
        self.ca_channel.receive_ack()

    @staticmethod
    def _gen_random_string(size, up_to=1):
        return [random.randint(0, up_to) for _ in range(size)]

    @staticmethod
    def _calculate_matching_error_of_values(lhs, rhs):
        t = len(lhs)
        w = sum(a != b for a, b in zip(lhs, rhs))
        return w / t

    def _calc_privacy_amplification_of(self, indices):
        x = [self._qstates[i].value for i in indices]
        return self._extract_key(x, self._seed)

    @staticmethod
    def _extract_key(x, seed):
        return sum(map(operator.mul, x, seed)) % 2