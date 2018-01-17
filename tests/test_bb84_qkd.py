import unittest

from QNetwork.bb84_qkd import BB84Node
from QNetwork.q_network import QState


class QChannelDummy:
    pass


class CACDummy:
    pass


class QChannelSpy:
    def __init__(self):
        self.qubits_sent = []

    def send(self, qubits):
        self.qubits_sent = qubits


class CACSpy:
    def __init__(self):
        self.data_sent = None

    def send(self, data):
        self.data_sent = data


class QChannelStub:
    def __init__(self):
        self.requested_bases = None
        self.received = None

    def receive(self, bases):
        self.requested_bases = bases
        return self.received


class CACStub:
    def __init__(self):
        self.received = None

    def receive(self):
        return self.received


class TestBB84Sending(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelSpy()
        self.cac = CACSpy()
        self.node = BB84Node(self.qc, self.cac, 0.0)

    def test_share_n(self):
        self.node.send_q_states(42)
        self.assertEqual(42, self.cac.data_sent)

    def test_send_bb84_states(self):
        self.node.send_q_states(42)
        self.assertSequenceEqual(self.node._qstates, self.qc.qubits_sent)

    def test_send_bases(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 1), QState(1, 1)]
        self.node.send_bases()
        self.assertSequenceEqual([0, 0, 1, 1], self.cac.data_sent)

    def test_send_test_set(self):
        self.node._qstates = [QState(1, 0)] * 15
        self.node.send_test_set()
        self.assertEqual(7, len(self.cac.data_sent))

    def test_send_test_values(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0)]
        self.node._test_set = {0, 2}
        self.node.send_test_values()
        self.assertSequenceEqual([1, 0], self.cac.data_sent)

    def test_send_amplification_seed(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0), QState(0, 0)]
        self.node._test_set = {0, 2}
        self.node.send_seed()
        self.assertSequenceEqual(self.node._seed, self.cac.data_sent)


class TestBB84Operations(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelDummy()
        self.cac = CACDummy()
        self.node = BB84Node(self.qc, self.cac, 0.0)

    def test_discard_invalid_states(self):
        self.node._other_bases = [1, 1, 0, 0]
        self.node._qstates = [QState(1, 0)] * 4
        self.node.discard_states()
        self.assertSequenceEqual([QState(1, 0)] * 2, self.node._qstates)

    def test_calculate_error_success(self):
        self.node._test_values = [1, 0, 0, 1]
        self.node._other_test_values = [1, 0, 0, 1]
        self.assertEqual(0.0, self.node.calculate_error())

    def test_calculate_error_failure(self):
        self.node._test_values = [1, 0, 0, 1]
        self.node._other_test_values = [1, 1, 0, 1]
        self.assertEqual(0.25, self.node.calculate_error())

    def test_privacy_amplification_even(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0), QState(1, 0)]
        self.node._test_set = {0, 2}
        self.node._seed = [1, 1, 0]
        self.assertEqual(0, self.node.privacy_amplification())

    def test_privacy_amplification_odd(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0), QState(1, 0)]
        self.node._test_set = {0, 2}
        self.node._seed = [1, 1, 1]
        self.assertEqual(1, self.node.privacy_amplification())


class TestBB84Receiving(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelStub()
        self.cac = CACStub()
        self.node = BB84Node(self.qc, self.cac, 0.0)

    def test_receiving_q_states(self):
        self.cac.received = [3]
        self.qc.received = [QState(1, 0), QState(1, 1), QState(0, 0)]
        self.node.receive_q_states()
        self.assertSequenceEqual(self.qc.received, self.node._qstates)
        self.assertEqual(3, len(self.qc.requested_bases))

    def test_receive_basis(self):
        self.cac.received = [0, 1, 0]
        self.node.receive_bases()
        self.assertSequenceEqual(self.cac.received, self.node._other_bases)

    def test_receive_test_set(self):
        self.cac.received = [0, 1]
        self.node.receive_test_set()
        self.assertEqual({0, 1}, self.node._test_set)

    def test_receive_test_values(self):
        self.cac.received = [1, 1, 0, 0]
        self.node.receive_test_values()
        self.assertSequenceEqual(self.cac.received, self.node._other_test_values)

    def test_receive_seed(self):
        self.cac.received = [1, 0, 1, 0]
        self.node.receive_seed()
        self.assertSequenceEqual(self.cac.received, self.node._seed)

