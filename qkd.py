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

    def _receive_q_states(self):
        amount = self.ca_channel.receive()[0]
        self._measure_qstates(amount)

    @abstractmethod
    def _measure_qstates(self, amount):
        pass

    def _receive_bases(self):
        self._other_bases = self.ca_channel.receive()

    @staticmethod
    def _extract_key(x, seed):
        return sum(map(operator.mul, x, seed)) % 2

    @staticmethod
    def _gen_random_string(size, up_to=1):
        return [random.randint(0, up_to) for _ in range(size)]