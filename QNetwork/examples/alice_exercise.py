from QNetwork.qkd.bb84_qkd import BB84SenderNode
from QNetwork.q_network_channels import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient


def main():
    connection = CQCConnection('Alice')
    q_channel = QChannel(connection, qubit, 'Eve')
    ca_channel = CAChannel(ipcCacClient('Alice'), 'Bob')
    node = BB84SenderNode(q_channel, ca_channel, 0, 1000)

    # perform QKD protocol
    node.share_q_states()
    if not node.should_abort():
        k = node.generate_key()
        print("Alice generated key:", k)

    print("Alice calculated error:", node.matching_error)

    connection.close()

main()
