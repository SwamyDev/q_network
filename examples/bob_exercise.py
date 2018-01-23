from QNetwork.qkd.bb84_qkd import BB84ReceiverNode
from QNetwork.q_network_channels import QChannel, CAChannel
from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit
from tinyIpcLib.ipcCacClient import ipcCacClient


def main():
    connection = CQCConnection('Bob')
    q_channel = QChannel(connection, qubit, 'Eve')
    ca_channel = CAChannel(ipcCacClient('Bob'), 'Alice')
    node = BB84ReceiverNode(q_channel, ca_channel, 0)

    # perform QKD protocol
    node.share_q_states()
    if not node.should_abort():
        k = node.generate_key()
        print("Bob generated key:", k)

    print("Bob calculated error:", node.matching_error)

    connection.close()

main()