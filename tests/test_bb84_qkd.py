import unittest

from QNetwork.qkd.bb84_qkd import BB84Node, BB84SenderNode, BB84ReceiverNode
from QNetwork.q_network_channels import QState


class QChannelSpy:
    def __init__(self):
        self.qubits_sent = []

    def send_qubits(self, qubits):
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

    def receive_qubits_in(self, bases):
        self.requested_bases = bases
        return self.received


class CACStub:
    def __init__(self):
        self.received = None

    def receive(self):
        return self.received


class BB84NodeSUT(BB84Node):
    def share_q_states(self):
        pass

    def should_abort(self):
        pass

    def generate_key(self):
        pass


class TestBB84Sending(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelSpy()
        self.cac = CACSpy()
        self.node = BB84NodeSUT(self.qc, self.cac, 0)

    def test_send_bb84_states(self):
        self.node._send_q_states(42)
        self.assertSequenceEqual(self.node._qstates, self.qc.qubits_sent)

    def test_send_test_values(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0)]
        self.node._test_set = {0, 2}
        self.node._send_test_values()
        self.assertSequenceEqual([1, 0], self.cac.data_sent)


class TestBB84Operations(unittest.TestCase):
    def setUp(self):
        self.node = BB84NodeSUT(None, None, 0)

    def test_discard_invalid_states(self):
        self.node._other_bases = [1, 1, 0, 0]
        self.node._qstates = [QState(1, 0)] * 4
        self.node._discard_states()
        self.assertSequenceEqual([QState(1, 0)] * 2, self.node._qstates)

    def test_calculate_error_success(self):
        self.node._test_values = [1, 0, 0, 1]
        self.node._other_test_values = [1, 0, 0, 1]
        self.assertEqual(0.0, self.node._calculate_error())

    def test_calculate_error_failure(self):
        self.node._test_values = [1, 0, 0, 1]
        self.node._other_test_values = [1, 1, 0, 1]
        self.assertEqual(0.25, self.node._calculate_error())

    def test_privacy_amplification_even(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0), QState(1, 0)]
        self.node._test_set = {0, 2}
        self.node._seed = [1, 1, 0]
        self.assertEqual([0], self.node._privacy_amplification())

    def test_privacy_amplification_odd(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0), QState(1, 0)]
        self.node._test_set = {0, 2}
        self.node._seed = [1, 1, 1]
        self.assertEqual([1], self.node._privacy_amplification())


class TestBB84Receiving(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelStub()
        self.cac = CACStub()
        self.node = BB84NodeSUT(self.qc, self.cac, 0)

    def test_receiving_q_states(self):
        self.cac.received = [3]
        self.qc.received = [QState(1, 0), QState(1, 1), QState(0, 0)]
        self.node._receive_q_states()
        self.assertSequenceEqual(self.qc.received, self.node._qstates)
        self.assertEqual(3, len(self.qc.requested_bases))

    def test_receive_test_values(self):
        self.cac.received = [1, 1, 0, 0]
        self.node._receive_test_values()
        self.assertSequenceEqual(self.cac.received, self.node._other_test_values)


class BB84SenderNodeSpy(BB84SenderNode):
    def __init__(self):
        super().__init__(None, None, 0, 0)
        self.operations = []

    def _send_q_states(self, amount):
        self.operations.append("_send_q_states")

    def _receive_ack(self):
        self.operations.append("_receive_ack")

    def _share_bases(self):
        self.operations.append("_share_bases")

    def _discard_states(self):
        self.operations.append("_discard_states")

    def _send_test_set(self):
        self.operations.append("_send_test_set")

    def _send_test_values(self):
        self.operations.append("_send_test_values")

    def _receive_test_values(self):
        self.operations.append("_receive_test_values")

    def _calculate_error(self):
        self.operations.append("_calculate_error")

    def _is_outside_error_bound(self, matching_error):
        self.operations.append("_is_outside_error_bound")

    def _send_seed(self):
        self.operations.append("_send_seed")

    def _privacy_amplification(self):
        self.operations.append("_privacy_amplification")


class TestBB84SenderFlow(unittest.TestCase):
    def setUp(self):
        self.node = BB84SenderNodeSpy()

    def test_share_q_states(self):
        self.node.share_q_states()
        self.assertSequenceEqual(["_send_q_states", "_receive_ack", "_share_bases"], self.node.operations)

    def test_should_abort(self):
        self.node.should_abort()
        self.assertSequenceEqual(
            ["_discard_states",
             "_send_test_set",
             "_send_test_values",
             "_receive_test_values",
             "_calculate_error",
             "_is_outside_error_bound"],
            self.node.operations)

    def test_generate_key(self):
        self.node.generate_key()
        self.assertSequenceEqual(["_send_seed", "_privacy_amplification"], self.node.operations)


class BB84ReceiverNodeSpy(BB84ReceiverNode):
    def __init__(self):
        super().__init__(None, None, 0)
        self.operations = []

    def _receive_q_states(self):
        self.operations.append("_receive_q_states")

    def _send_ack(self):
        self.operations.append("_send_ack")

    def _share_bases(self):
        self.operations.append("_share_bases")

    def _discard_states(self):
        self.operations.append("_discard_states")

    def _receive_test_set(self):
        self.operations.append("_receive_test_set")

    def _send_test_values(self):
        self.operations.append("_send_test_values")

    def _receive_test_values(self):
        self.operations.append("_receive_test_values")

    def _calculate_error(self):
        self.operations.append("_calculate_error")

    def _is_outside_error_bound(self, matching_error):
        self.operations.append("_is_outside_error_bound")

    def _receive_seed(self):
        self.operations.append("_receive_seed")

    def _privacy_amplification(self):
        self.operations.append("_privacy_amplification")


class TestBB84ReceiverFlow(unittest.TestCase):
    def setUp(self):
        self.node = BB84ReceiverNodeSpy()

    def test_share_q_states(self):
        self.node.share_q_states()
        self.assertSequenceEqual(["_receive_q_states", "_send_ack", "_share_bases"], self.node.operations)

    def test_should_abort(self):
        self.node.should_abort()
        self.assertSequenceEqual(
            ["_discard_states",
             "_receive_test_set",
             "_send_test_values",
             "_receive_test_values",
             "_calculate_error",
             "_is_outside_error_bound"],
            self.node.operations)

    def test_generate_key(self):
        self.node.generate_key()
        self.assertSequenceEqual(["_receive_seed", "_privacy_amplification"], self.node.operations)
