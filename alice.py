from QNetwork.bb84_qkd import BB84Node
from QNetwork.q_network import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient


def main():
    connection = CQCConnection('Alice')
    q_channel = QChannel(connection, qubit, 'Bob')
    ca_channel = CAChannel(ipcCacClient('Alice'), 'Bob')
    node = BB84Node(q_channel, ca_channel, 0.0)

    node.send_q_states(1000)
    node.receive_bases()
    node.send_bases()
    node.discard_states()
    node.send_test_set()
    node.receive_test_values()
    node.send_test_values()
    error = node.calculate_error()
    print("Alice calculated error:", error)
    if error == 0.0:
        k = node.privacy_amplification()
        print("Alice generated key:", k)

main()