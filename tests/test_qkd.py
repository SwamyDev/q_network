import random
import unittest

from QNetwork.q_network import QState
from QNetwork.qkd import QKDNode


class CACMock:
    def __init__(self, expected_sent=None, received_data=None):
        self.expected_sent = expected_sent
        self.received_data = received_data
        self.send_was_called = False

    def send(self, data):
        self.send_was_called = True
        if not data == self.expected_sent:
            raise Exception("This mock was given an unexpected argument. Expected {0} got {1}"
                            .format(self.expected_sent, data))

    def receive(self):
        return self.received_data


class QKDNodeSUT(QKDNode):
    def _measure_qstates(self, amount):
        pass


class TestQKDCommonFunctions(unittest.TestCase):
    def test_share_bases(self):
        cac = CACMock(expected_sent=[0, 0, 1, 1], received_data=[0, 1, 0, 1])
        node = QKDNodeSUT(cac)
        node._qstates = [QState(1, 0), QState(1, 0), QState(0, 1), QState(1, 1)]
        node._share_bases()
        self.assertSequenceEqual([0, 1, 0, 1], node._other_bases)
        self.assertTrue(cac.send_was_called)

    def test_share_n(self):
        cac = CACMock(expected_sent=42)
        node = QKDNodeSUT(cac)
        node._send_q_states(42)
        self.assertTrue(cac.send_was_called)

    def test_send_test_set(self):
        random.seed(7)
        cac = CACMock(expected_sent=[0, 1, 2, 5, 6, 10, 13])
        node = QKDNodeSUT(cac)
        node._qstates = [QState(1, 0)] * 15
        node._send_test_set()
        self.assertTrue(cac.send_was_called)

    def test_simple_extractor_returns_zero_bit(self):
        self.assert_extract_bit(0, [1, 1, 1], [1, 1, 0])

    def assert_extract_bit(self, expected, x, seed):
        node = QKDNodeSUT(None)
        self.assertEqual(expected, node._extract_key(x, seed))

    def test_privacy_amplification_odd(self):
        self.assert_extract_bit(1, [1, 1, 1], [1, 1, 1])
