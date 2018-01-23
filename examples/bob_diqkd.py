import operator
import random

from QNetwork.qkd.diqkd import DIQKDReceiverNode
from QNetwork.q_network_channels import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient


def main():
    connection = CQCConnection('Bob')
    q_channel = QChannel(connection, qubit, 'Alice')
    ca_channel = CAChannel(ipcCacClient('Bob'), 'Alice')
    node = DIQKDReceiverNode(q_channel, ca_channel, 0.01)

    node.share_q_states()
    if node.should_abort():
        print("Bob aborted with win probability {0} and matching error {1}".format(node.win_prob, node.matching_error))
    else:
        k = node.generate_key()
        print("Bob generated key:", k)

    ca_channel.receive_ack()
    ca_channel.clear()
    connection.close()

main()
