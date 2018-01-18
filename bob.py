from QNetwork.bb84_qkd import BB84ReceiverNode
from QNetwork.q_network import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient


def main():
    connection = CQCConnection('Bob')
    q_channel = QChannel(connection, qubit, 'Eve')
    ca_channel = CAChannel(ipcCacClient('Bob'), 'Alice')
    node = BB84ReceiverNode(q_channel, ca_channel)

    node.share_q_states()
    error = node.get_error()
    print("Bob calculated error:", error)
    if error == 0.0:
        k = node.generate_key()
        print("Bob generated key:", k)

    connection.close()

main()