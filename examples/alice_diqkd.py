import operator
import random

from QNetwork.qkd.diqkd import DIQKDSenderNode
from QNetwork.q_network_channels import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient


def main():
    connection = CQCConnection('Alice')
    q_channel = QChannel(connection, qubit, 'Bob')
    ca_channel = CAChannel(ipcCacClient('Alice'), 'Bob')
    node = DIQKDSenderNode(q_channel, ca_channel, 0.01, 1000)

    node.share_q_states()
    if node.should_abort():
        print(
            "Alice aborted with win probability {0} and matching error {1}".format(node.win_prob, node.matching_error))
    else:
        k = node.generate_key()
        print("Alice generated key:", k)

    ca_channel.send_ack()
    connection.close()


main()
