from QNetwork.bb84_qkd import BB84Node
from QNetwork.q_network import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient


def main():
    connection = CQCConnection('Bob')
    q_channel = QChannel(connection, qubit, 'Alice')
    ca_channel = CAChannel(ipcCacClient('Bob'), 'Alice')
    node = BB84Node(q_channel, ca_channel, 0.0)

    node.receive_q_states()
    node.send_bases()
    node.receive_bases()
    node.discard_states()
    node.receive_test_set()
    node.send_test_values()
    node.receive_test_values()
    error = node.calculate_error()
    print("Bob calculated error:", error)
    if error == 0.0:
        k = node.privacy_amplification()
        print("Bob generated key:", k)

main()