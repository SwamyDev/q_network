import io
import json

from QNetwork.qkd.bb84_qkd import BB84ReceiverNode, BB84SenderNode
from QNetwork.qkd.diqkd import DIQKDSenderNode, DIQKDReceiverNode
from QNetwork.q_network_channels import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient

SENDER_CLASSES = {'BB84': BB84SenderNode, 'DIQKD': DIQKDSenderNode}
RECEIVER_CLASSES = {'BB84': BB84ReceiverNode, 'DIQKD': DIQKDReceiverNode}


class NetworkFactory:
    def __init__(self, config_file):
        with io.open(config_file, 'r') as f:
            config = json.load(f)
            self.protocol = config['Protocol']
            self.error = config['Error']
            self.n = config['StateSize']
            self.maximize_key_bits = config['MaximizeKeyBits']

    @staticmethod
    def make_q_channel(from_name, to_name):
        connection = CQCConnection(from_name)
        return QChannel(connection, qubit, to_name)

    @staticmethod
    def make_ca_channel(from_name, to_name):
        return CAChannel(ipcCacClient(from_name), to_name)
        pass

    def make_sender_node(self, q_channel, ca_channel):
        node = SENDER_CLASSES[self.protocol](q_channel, ca_channel, self.error, self.n)
        node.maximize_key_bits = self.maximize_key_bits
        return node

    def make_receiver_node(self, q_channel, ca_channel):
        node = RECEIVER_CLASSES[self.protocol](q_channel, ca_channel, self.error)
        node.maximize_key_bits = self.maximize_key_bits
        return node
