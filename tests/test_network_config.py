import unittest

import io
import json

import os

from QNetwork.bb84_qkd import BB84SenderNode, BB84ReceiverNode
from QNetwork.diqkd import DIQKDSenderNode, DIQKDReceiverNode
from QNetwork.q_network_config import NetworkFactory


class QChannelDummy:
    pass


class CAChannelDummy:
    pass


class TestFactoryBase(unittest.TestCase):
    def setUp(self):
        self.qc = QChannelDummy()
        self.cac = CAChannelDummy()

    def assert_node(self, node, expected_type, expected_error, expected_n=None):
        self.assertIsInstance(node, expected_type)
        self.assertEqual(expected_error, node.error)
        if expected_n is not None:
            self.assertEqual(expected_n, node.n)
        self.assertEqual(self.qc, node.q_channel)
        self.assertEqual(self.cac, node.ca_channel)


class TestFactoryBB84Configuration(TestFactoryBase):
    def setUp(self):
        super().setUp()
        self.cfg_file = 'test_config.cfg'
        config = {'Protocol': 'BB84', 'Error': 0.1, 'StateSize': 1500}
        with io.open(self.cfg_file, 'w') as f:
            json.dump(config, f, ensure_ascii=False)

        self.factory = NetworkFactory(self.cfg_file)

    def tearDown(self):
        os.remove(self.cfg_file)

    def test_make_correct_sender_node(self):
        node = self.factory.make_sender_node(self.qc, self.cac)
        self.assert_node(node, BB84SenderNode, 0.1, 1500)

    def test_make_correct_receiver_node(self):
        node = self.factory.make_receiver_node(self.qc, self.cac)
        self.assert_node(node, BB84ReceiverNode, 0.1)


class TestFactoryDIQKDConfiguration(TestFactoryBase):
    def setUp(self):
        super().setUp()
        self.cfg_file = 'test_config.cfg'
        config = {'Protocol': 'DIQKD', 'Error': 0.1, 'StateSize': 1500}
        with io.open(self.cfg_file, 'w') as f:
            json.dump(config, f, ensure_ascii=False)

        self.factory = NetworkFactory(self.cfg_file)

    def tearDown(self):
        os.remove(self.cfg_file)

    def test_make_correct_sender_node(self):
        node = self.factory.make_sender_node(self.qc, self.cac)
        self.assert_node(node, DIQKDSenderNode, 0.1, 1500)

    def test_make_correct_receiver_node(self):
        node = self.factory.make_receiver_node(self.qc, self.cac)
        self.assert_node(node, DIQKDReceiverNode, 0.1)
