import random
import unittest

from QNetwork.diqkd import DIQKDNode
from QNetwork.q_network import QState


class QChannelSpy:
    def __init__(self):
        self.received_bases = []

    def measure_entangled(self, bases):
        self.received_bases = bases


class CACStub:
    def __init__(self):
        self.received = None

    def receive(self):
        return self.received


class CACSpy:
    def __init__(self):
        self.data_sent = None

    def send(self, data):
        self.data_sent = data


class TestDIQKDEntangledSharing(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelSpy()
        self.cac = CACStub()
        self.node = DIQKDNode(self.qc, self.cac)

    def test_send_entangled_states(self):
        random.seed(42)
        self.node._send_q_states(4)
        self.assertSequenceEqual([0, 0, 1, 0], self.qc.received_bases)

    def test_receive_entangled_states(self):
        random.seed(7)
        self.cac.received = [4]
        self.node._receive_q_states()
        self.assertSequenceEqual([1, 0, 1, 2], self.qc.received_bases)


class TestDIQKDSending(unittest.TestCase):
    def setUp(self):
        self.cac = CACSpy()
        self.node = DIQKDNode(None, self.cac)

