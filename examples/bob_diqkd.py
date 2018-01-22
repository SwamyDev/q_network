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
    node = DIQKDReceiverNode(q_channel, ca_channel, 0.01, 60)

    node.share_q_states()
    if node.should_abort():
        print("Bob aborted with win probability {0} and matching error {1}".format(node.win_prob, node.matching_error))
    else:
        k = node.generate_key()
        print("Bob generated key:", k)

    ca_channel.receive_ack()
    ca_channel.clear()
    connection.close()


def main_bkk():
    connection = CQCConnection('Bob')
    q_channel = QChannel(connection, qubit, 'Alice')
    ca_channel = CAChannel(ipcCacClient('Bob'), 'Alice')

    size = 1000
    for step in range(24, 64, 8):

        def trans(q):
            q.rot_Y(step, print_info=False)

        def trans2(q):
            #q.H(print_info=False)
            q.rot_Y(step, print_info=False)
            q.X(print_info=False)

        q_channel.bases_mapping = [trans, trans2]
        bases_lhs = [random.randint(0, 1) for _ in range(size)]
        ca_channel.send(bases_lhs)
        bases_rhs = ca_channel.receive()

        qs = q_channel.receive_epr_in(bases_lhs)
        values_lhs = [q.value for q in qs]
        ca_channel.send(values_lhs)
        values_rhs = ca_channel.receive()

        and_bases = map(operator.mul, bases_lhs, bases_rhs)
        xor_values = map(operator.xor, values_lhs, values_rhs)

        t = len(values_rhs)
        w = sum(a == b for a, b in zip(and_bases, xor_values))

        print("Bob win probability {0} with step {1}".format(w / t, step))

    ca_channel.receive_ack()
    ca_channel.clear()
    connection.close()


main_bkk()
