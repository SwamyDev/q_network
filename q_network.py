from QNetwork.q_network_config import NetworkFactory
from QNetwork.q_network_impl import SecureChannel

CONFIG_FILE = "q_network.cfg"


def open_channel(from_name, to_name):
    """
    Opens a secure channel between the two nodes provided via their respective identifiers.

    Uses the quantum key distribution protocol specified in q_network.cfg to distribute key between the nodes. This key
    is used to encrypt messages sent through the classical channel using the one-time pad.

    The function returns a context manager to be used in a with statement.
        - write(data) generates the necessary key end sends data encrypted to the recipient.
            Currently only ASCII strings are supported
        - read() receives an encrypted message from a sender and decrypts it using the shared key

    >>> def example_write()
    >>>     with open_channel('Alice', 'Bob') as channel:
    >>>         channel.write("Hello, Bob!")

    >>> def example_read()
    >>>     with open_channel('Alice', 'Bob') as channel:
    >>>         msg = channel.read()
    >>>         print("Bob received message:", msg)


    :param from_name: Unique identifier of sender node
    :param to_name: Unique identifier of receiver node
    :return: SecureChannel object
    """
    sc = SecureChannel(from_name, to_name)
    sc.network_factory = NetworkFactory(CONFIG_FILE)
    return sc
