import operator
import random
from abc import ABC, abstractmethod

import math


class QKDNode(ABC):
    def __init__(self, ca_channel, error):
        self.ca_channel = ca_channel
        self.error = error
        self.maximize_key_bits = False
        self._qstates = []
        self._other_bases = []
        self._test_set = set()
        self._mismatching_states = 0

    def try_generate_key(self):
        self.share_q_states()
        if self.should_abort():
            return []

        return self.generate_key()

    @abstractmethod
    def share_q_states(self):
        pass

    @abstractmethod
    def should_abort(self):
        pass

    @abstractmethod
    def generate_key(self):
        pass

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

    def _calculate_matching_error_of_values(self, lhs, rhs):
        t = len(lhs)
        self._mismatching_states = sum(a != b for a, b in zip(lhs, rhs))
        return self._mismatching_states / t

    def _calc_privacy_amplification_of(self, indices):
        x = [self._qstates[i].value for i in indices]
        k = len(x) - self._mismatching_states if self.maximize_key_bits else 1
        return self._extract_key(x, self._seed, k)

    @staticmethod
    def _extract_key(x, seed, k):
        chunk_size = math.floor(len(x) / k)
        if chunk_size == 0:
            raise ValueError("The requested key ({}) is too long for the raw key ({}).".format(k, len(x)))

        return [sum(map(operator.mul, xp, sp)) % 2 for xp, sp in zip(QKDNode._split_list(x, chunk_size),
                                                                     QKDNode._split_list(seed, chunk_size))]

    @staticmethod
    def _split_list(list, size):
        for i in range(0, len(list), size):
            yield list[i:i+size]