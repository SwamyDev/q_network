import unittest

from QNetwork.q_network_impl import START_KEY_GENERATION_TAG, END_KEY_GENERATION_TAG, SecureChannel, READING


class QChannelSpy:
    def __init__(self):
        self.received_close = False

    def close(self):
        self.received_close = True


class CAChannelSpy:
    def __init__(self):
        self.data_sent = None
        self.record = []
        self.received_send_ack = False
        self.received_receive_ack = False
        self.received_clear = False

    def send(self, data):
        self.record.append(data)
        self.data_sent = data

    def send_ack(self):
        self.received_send_ack = True

    def receive_ack(self):
        self.received_receive_ack = True

    def clear(self):
        self.received_clear = True


class NetworkFactorySpy:
    def __init__(self, q_channel, ca_channel):
        self.q_channel = q_channel
        self.ca_channel = ca_channel
        self.qc_from_to_names = None
        self.cac_from_to_names = None

    def make_q_channel(self, from_name, to_name):
        self.qc_from_to_names = (from_name, to_name)
        return self.q_channel

    def make_ca_channel(self, from_name, to_name):
        self.cac_from_to_names = (from_name, to_name)
        return self.ca_channel

    def make_sender_node(self, q_channel, ca_channel):
        return NodeStub([1])

    def make_receiver_node(self, q_channel, ca_channel):
        return NodeStub([1])


class NetworkFactoryStub:
    def __init__(self, q_channel, ca_channel, node):
        self.q_channel = q_channel
        self.ca_channel = ca_channel
        self.node = node

    def make_q_channel(self, from_name, to_name):
        return self.q_channel

    def make_ca_channel(self, from_name, to_name):
        return self.ca_channel

    def make_sender_node(self, q_channel, ca_channel):
        return self.node

    def make_receiver_node(self, q_channel, ca_channel):
        return self.node


class CACStub:
    def __init__(self, *received_data):
        self.received_data = received_data
        self.idx = 0

    def receive(self):
        self.idx += 1
        return self.received_data[self.idx - 1]


class NodeStub:
    def __init__(self, key):
        self.key = key

    def try_generate_key(self):
        return self.key


class TestConnectionHandling(unittest.TestCase):
    def setUp(self):
        self.q_channel = QChannelSpy()
        self.ca_channel = CAChannelSpy()
        self.network_factory = NetworkFactorySpy(self.q_channel, self.ca_channel)
        self.sc = SecureChannel('Alice', 'Bob')
        self.sc.network_factory = self.network_factory

    def test_enter_returns_itself_as_context(self):
        self.assertEqual(self.sc, self.sc.__enter__())

    def test_open_connection(self):
        self.sc.__enter__()
        self.assertEqual(('Alice', 'Bob'), self.network_factory.qc_from_to_names)
        self.assertEqual(('Alice', 'Bob'), self.network_factory.cac_from_to_names)

    def test_normal_close_connection(self):
        self.sc.__enter__()
        self.sc.__exit__(None, None, None)
        self.assertFalse(self.ca_channel.received_receive_ack)
        self.assertFalse(self.ca_channel.received_send_ack)
        self.assertTrue(self.ca_channel.received_clear)
        self.assertTrue(self.q_channel.received_close)

    def test_after_write_wait_for_acknowledgement_before_closing(self):
        self.sc.__enter__()
        self.sc.write('H')
        self.sc.__exit__(None, None, None)
        self.assertTrue(self.ca_channel.received_receive_ack)
        self.assertTrue(self.ca_channel.received_clear)
        self.assertTrue(self.q_channel.received_close)

    def test_after_read_send_acknowledgement_before_and_do_not_close_cac(self):
        self.sc.__enter__()
        self.sc._state = READING
        self.sc.__exit__(None, None, None)
        self.assertTrue(self.ca_channel.received_send_ack)
        self.assertFalse(self.ca_channel.received_clear)
        self.assertTrue(self.q_channel.received_close)

    def test_exceptional_close_connection(self):
        self.sc.__enter__()
        self.sc.__exit__(ValueError, ValueError("Some Error"), None)
        self.assertTrue(self.ca_channel.received_clear)
        self.assertTrue(self.q_channel.received_close)


class TestMessageSending(unittest.TestCase):
    def setUp(self):
        self.sc = SecureChannel('Alice', 'Bob')
        self.cac = CAChannelSpy()

    def test_send_encrypted_message(self):
        self.sc.network_factory = NetworkFactoryStub(None, self.cac, NodeStub([1, 1, 1, 1, 1, 1, 1, 1]))
        self.sc.__enter__()
        self.sc.write("H")
        self.assertEqual([1, 0, 1, 1, 0, 1, 1, 1], self.cac.data_sent)

    def test_fill_up_key(self):
        self.sc.network_factory = NetworkFactoryStub(None, self.cac, NodeStub([1, 1, 1]))
        self.sc.__enter__()
        self.sc.write("H")
        self.assertEqual([1, 0, 1, 1, 0, 1, 1, 1], self.cac.data_sent)

    def test_inform_receiver_about_key_generation(self):
        self.sc.network_factory = NetworkFactoryStub(None, self.cac, NodeStub([1, 1, 1]))
        self.sc.__enter__()
        self.sc.write("H")
        self.assertEqual(self.sc.to_binary_list(START_KEY_GENERATION_TAG), self.cac.record[0])
        self.assertEqual(self.sc.to_binary_list(START_KEY_GENERATION_TAG), self.cac.record[1])
        self.assertEqual(self.sc.to_binary_list(START_KEY_GENERATION_TAG), self.cac.record[2])
        self.assertEqual(self.sc.to_binary_list(END_KEY_GENERATION_TAG), self.cac.record[3])


class TestMessageReceiving(unittest.TestCase):
    def setUp(self):
        self.sc = SecureChannel('Alice', 'Bob')
        self.start_tag = self.sc.to_binary_list(START_KEY_GENERATION_TAG)
        self.end_tag = self.sc.to_binary_list(END_KEY_GENERATION_TAG)

    def test_receive_encrypted_message(self):
        self.sc.network_factory = NetworkFactoryStub(None, CACStub(self.start_tag, self.end_tag,
                                                                   [1, 0, 1, 1, 0, 1, 1, 1]),
                                                     NodeStub([1, 1, 1, 1, 1, 1, 1, 1]))
        self.sc.__enter__()
        msg = self.sc.read()
        self.assertEqual('H', msg)
        self.assertEqual(READING, self.sc._state)

    def test_receive_multiple_key_generations(self):
        self.sc.network_factory = NetworkFactoryStub(None, CACStub(self.start_tag, self.start_tag, self.start_tag,
                                                                   self.end_tag,
                                                                   [1, 0, 1, 1, 0, 1, 1, 1]), NodeStub([1, 1, 1]))
        self.sc.__enter__()
        msg = self.sc.read()
        self.assertEqual('H', msg)

    def test_assert_key_generation_is_ended_properly(self):
        self.sc.network_factory = NetworkFactoryStub(None, CACStub(self.start_tag,
                                                                   [1, 0, 1, 1, 0, 1, 1, 1]),
                                                     NodeStub([1, 1, 1, 1, 1, 1, 1, 1]))
        self.sc.__enter__()
        with self.assertRaises(AssertionError):
            msg = self.sc.read()

    def test_assert_that_there_is_enough_key(self):
        self.sc.network_factory = NetworkFactoryStub(None, CACStub(self.start_tag, self.end_tag,
                                                                   [1, 0, 1, 1, 0, 1, 1, 1]), NodeStub([1, 1, 1]))
        self.sc.__enter__()
        with self.assertRaises(AssertionError):
            msg = self.sc.read()
