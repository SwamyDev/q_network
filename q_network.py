from QNetwork.q_network_config import NetworkFactory
from QNetwork.q_network_impl import SecureChannel

CONFIG_FILE = "q_network.cfg"


def open_channel(from_name, to_name):
    sc = SecureChannel(from_name, to_name)
    sc.network_factory = NetworkFactory(CONFIG_FILE)
    return sc
