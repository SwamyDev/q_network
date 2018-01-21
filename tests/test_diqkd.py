import random
import unittest

from QNetwork.diqkd import DIQKDNode, DIQKDSenderNode, DIQKDReceiverNode
from QNetwork.q_network_util import QState


class QChannelDummy:
    pass


class QChannelSpy:
    def __init__(self):
        self.received_bases = []

    def send_epr(self, bases):
        self.received_bases = bases

    def receive_epr_in(self, bases):
        self.received_bases = bases


class CACStub:
    def __init__(self):
        self.received = None

    def receive(self):
        return self.received

    def send(self, data):
        pass


class CACSpy:
    def __init__(self):
        self.data_sent = None

    def send(self, data):
        self.data_sent = data


class QubitSpy:
    def __init__(self):
        self.rotation_steps = 0

    def rot_Y(self, step):
        self.rotation_steps = step


class TestDIQKDEntangledSharing(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelSpy()
        self.cac = CACStub()
        self.node = DIQKDNode(self.qc, self.cac, 0)

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
        self.node = DIQKDNode(None, self.cac, 0)

    def test_send_chsh_values(self):
        self.node._qstates = [QState(1, 0), QState(0, 1), QState(0, 0), QState(1, 1)]
        self.node._chsh_test_set = {0, 1}
        self.node._send_chsh_test_values()
        self.assertSequenceEqual([1, 0], self.cac.data_sent)
        self.assertSequenceEqual([1, 0], self.node._chsh_test_values)

    def test_send_match_values(self):
        self.node._qstates = [QState(1, 0), QState(0, 1), QState(0, 0), QState(1, 1)]
        self.node._match_test_set = {0, 1}
        self.node._send_match_test_values()
        self.assertSequenceEqual([1, 0], self.cac.data_sent)
        self.assertSequenceEqual([1, 0], self.node._match_test_values)


class TestDIQKDCommonOperations(unittest.TestCase):
    def setUp(self):
        self.node = DIQKDNode(None, None, 0.1)

    def test_calculate_win_probability(self):
        self.node._qstates = [QState(1, 0), QState(0, 1), QState(1, 1), QState(0, 1), QState(0, 0)]
        self.node._chsh_test_values = [1, 0, 1, 0]
        self.node._other_chsh_test_values = [1, 1, 0, 0]
        self.node._other_bases = [1, 1, 0, 0, 0]
        self.node._chsh_test_set = {0, 1, 2, 3}
        self.assertAlmostEqual(0.75, self.node._calculate_winning_probability())

    def test_calculate_match_error(self):
        self.node._match_test_values = [1, 0, 0, 1]
        self.node._other_match_test_values = [1, 1, 0, 1]
        self.assertAlmostEqual(0.25, self.node._calculate_match_error())

    def test_pwin_outside_error_bound(self):
        self.assertTrue(self.node._is_outside_error_bound(0.75, 1.0))

    def test_pwin_inside_error_bound(self):
        self.assertFalse(self.node._is_outside_error_bound(0.85, 1.0))

    def test_match_outside_error_bound(self):
        self.assertTrue(self.node._is_outside_error_bound(0.85, 0.8))

    def test_match_inside_error_bound(self):
        self.assertFalse(self.node._is_outside_error_bound(0.85, 0.95))

    def test_privacy_amplification_even(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0), QState(1, 0)]
        self.node._raw_key_set = {1, 3, 4}
        self.node._seed = [1, 1, 0]
        self.assertEqual(0, self.node._privacy_amplification())

    def test_privacy_amplification_odd(self):
        self.node._qstates = [QState(1, 0), QState(1, 0), QState(0, 0), QState(1, 0), QState(1, 0)]
        self.node._raw_key_set = {1, 3, 4}
        self.node._seed = [1, 1, 1]
        self.assertEqual(1, self.node._privacy_amplification())


class TestDIQKDSenderOperations(unittest.TestCase):
    def setUp(self):
        self.node = DIQKDSenderNode(None, None, 0, None)

    def test_subset_separation(self):
        self.node._other_bases = [1, 0, 2, 0, 2, 2]
        self.node._test_set = {0, 1, 2}
        self.node._qstates = [QState(1, 0), QState(0, 0), QState(1, 0), QState(0, 0), QState(1, 1), QState(0, 0)]
        self.node._separate_test_subsets()
        self.assert_test_sets(expected_chsh={0, 1}, expected_match={2}, expected_raw_key={5})

    def assert_test_sets(self, expected_chsh, expected_match, expected_raw_key):
        self.assertEqual(expected_chsh, self.node._chsh_test_set)
        self.assertEqual(expected_match, self.node._match_test_set)
        self.assertEqual(expected_raw_key, self.node._raw_key_set)


class TestDIQKDReceiverOperations(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelDummy()
        self.node = DIQKDReceiverNode(self.qc, None, 0)

    def test_has_correct_bases_mapping(self):
        q1 = QubitSpy()
        self.node.q_channel.bases_mapping[0](q1)
        self.assertEqual(128+32, q1.rotation_steps)

        q2 = QubitSpy()
        self.node.q_channel.bases_mapping[1](q2)
        self.assertEqual(32, q2.rotation_steps)

        q3 = QubitSpy()
        self.node.q_channel.bases_mapping[2](q3)
        self.assertEqual(0, q3.rotation_steps)

    def test_subset_separation(self):
        self.node._other_bases = [1, 0, 0, 0, 1, 0]
        self.node._test_set = {0, 1, 2}
        self.node._qstates = [QState(1, 1), QState(0, 0), QState(1, 2), QState(0, 0), QState(1, 1), QState(0, 2)]
        self.node._separate_test_subsets()
        self.assert_test_sets(expected_chsh={0, 1}, expected_match={2}, expected_raw_key={5})

    def assert_test_sets(self, expected_chsh, expected_match, expected_raw_key):
        self.assertEqual(expected_chsh, self.node._chsh_test_set)
        self.assertEqual(expected_match, self.node._match_test_set)
        self.assertEqual(expected_raw_key, self.node._raw_key_set)


class TestDIQKDReceiving(unittest.TestCase):
    def setUp(self):
        self.cac = CACStub()
        self.node = DIQKDNode(None, self.cac, 0)

    def test_receive_chsh_values(self):
        self.cac.received = [1, 1, 0, 0]
        self.node._receive_chsh_test_values()
        self.assertSequenceEqual(self.cac.received, self.node._other_chsh_test_values)

    def test_receive_match_values(self):
        self.cac.received = [1, 1, 0, 0]
        self.node._receive_match_test_values()
        self.assertSequenceEqual(self.cac.received, self.node._other_match_test_values)


class DIQKDSenderNodeSpy(DIQKDSenderNode):
    def __init__(self):
        super().__init__(None, None, None, 0)
        self.operations = []

    def _send_q_states(self, amount):
        self.operations.append("_send_q_states")

    def _receive_ack(self):
        self.operations.append("_receive_ack")

    def _share_bases(self):
        self.operations.append("_share_bases")

    def _send_test_set(self):
        self.operations.append("_send_test_set")

    def _separate_test_subsets(self):
        self.operations.append("_separate_test_subsets")

    def _send_chsh_test_values(self):
        self.operations.append("_send_chsh_test_values")

    def _receive_chsh_test_values(self):
        self.operations.append("_receive_chsh_test_values")

    def _send_match_test_values(self):
        self.operations.append("_send_match_test_values")

    def _receive_match_test_values(self):
        self.operations.append("_receive_match_test_values")

    def _calculate_winning_probability(self):
        self.operations.append("_calculate_winning_probability")

    def _calculate_match_error(self):
        self.operations.append("_calculate_match_error")

    def _is_outside_error_bound(self, win_prob, matching_error):
        self.operations.append("_is_outside_error_bound")

    def _send_seed(self):
        self.operations.append("_send_seed")

    def _privacy_amplification(self):
        self.operations.append("_privacy_amplification")


class TestDIQKDSenderFlow(unittest.TestCase):
    def setUp(self):
        self.node = DIQKDSenderNodeSpy()

    def test_share_q_states(self):
        self.node.share_q_states()
        self.assertSequenceEqual(["_send_q_states", "_receive_ack", "_share_bases"], self.node.operations)

    def test_should_abort(self):
        self.node.should_abort()
        self.assertSequenceEqual(
            ["_send_test_set",
             "_separate_test_subsets",
             "_send_chsh_test_values",
             "_receive_chsh_test_values",
             "_send_match_test_values",
             "_receive_match_test_values",
             "_calculate_winning_probability",
             "_calculate_match_error",
             "_is_outside_error_bound"],
            self.node.operations)

    def test_generate_key(self):
        self.node.generate_key()
        self.assertSequenceEqual(["_send_seed", "_privacy_amplification"], self.node.operations)


class DIQKDReceiverNodeSpy(DIQKDReceiverNode):
    def __init__(self):
        super().__init__(QChannelDummy(), None, 0)
        self.operations = []

    def _receive_q_states(self):
        self.operations.append("_receive_q_states")

    def _send_ack(self):
        self.operations.append("_send_ack")

    def _share_bases(self):
        self.operations.append("_share_bases")

    def _receive_test_set(self):
        self.operations.append("_receive_test_set")

    def _separate_test_subsets(self):
        self.operations.append("_separate_test_subsets")

    def _send_chsh_test_values(self):
        self.operations.append("_send_chsh_test_values")

    def _receive_chsh_test_values(self):
        self.operations.append("_receive_chsh_test_values")

    def _send_match_test_values(self):
        self.operations.append("_send_match_test_values")

    def _receive_match_test_values(self):
        self.operations.append("_receive_match_test_values")

    def _calculate_winning_probability(self):
        self.operations.append("_calculate_winning_probability")

    def _calculate_match_error(self):
        self.operations.append("_calculate_match_error")

    def _is_outside_error_bound(self, win_prob, matching_error):
        self.operations.append("_is_outside_error_bound")

    def _receive_seed(self):
        self.operations.append("_receive_seed")

    def _privacy_amplification(self):
        self.operations.append("_privacy_amplification")


class TestDIQKDReceiverFlow(unittest.TestCase):
    def setUp(self):
        self.node = DIQKDReceiverNodeSpy()

    def test_share_q_states(self):
        self.node.share_q_states()
        self.assertSequenceEqual(["_receive_q_states", "_send_ack", "_share_bases"], self.node.operations)

    def test_should_abort(self):
        self.node.should_abort()
        self.assertSequenceEqual(
            ["_receive_test_set",
             "_separate_test_subsets",
             "_send_chsh_test_values",
             "_receive_chsh_test_values",
             "_send_match_test_values",
             "_receive_match_test_values",
             "_calculate_winning_probability",
             "_calculate_match_error",
             "_is_outside_error_bound"],
            self.node.operations)

    def test_generate_key(self):
        self.node.generate_key()
        self.assertSequenceEqual(["_receive_seed", "_privacy_amplification"], self.node.operations)
