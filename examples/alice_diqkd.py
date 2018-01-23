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


def main_bkk():
    connection = CQCConnection('Alice')
    q_channel = QChannel(connection, qubit, 'Bob')
    ca_channel = CAChannel(ipcCacClient('Alice'), 'Bob')

    size = 1000
    for step in range(96, 256, 64):
        bases_lhs = [random.randint(0, 1) for _ in range(size)]
        ca_channel.send(bases_lhs)
        bases_rhs = ca_channel.receive()

        qs = q_channel.send_epr(bases_lhs)
        values_lhs = [q.value for q in qs]
        ca_channel.send(values_lhs)
        values_rhs = ca_channel.receive()

        and_bases = map(operator.mul, bases_lhs, bases_rhs)
        xor_values = map(operator.xor, values_lhs, values_rhs)

        t = len(values_rhs)
        w = sum(a == b for a, b in zip(and_bases, xor_values))

        print("Alice win probability {0} with step {1}".format(w / t, step))

    ca_channel.send_ack()
    connection.close()


main_bkk()
