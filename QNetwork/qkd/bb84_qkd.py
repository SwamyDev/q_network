from QNetwork.q_network_channels import QState
from QNetwork.qkd.qkd import QKDNode


class BB84Node(QKDNode):
    def __init__(self, q_channel, ca_channel, error):
        super().__init__(ca_channel, error)
        self.q_channel = q_channel

        self._test_values = []
        self._other_test_values = []
        self._seed = []
        self.matching_error = 0

    def _send_q_states(self, amount):
        super()._send_q_states(amount)
        self._qstates = [QState(value, basis) for value, basis in zip(self._gen_random_string(amount),
                                                                      self._gen_random_string(amount))]
        self.q_channel.send_qubits(self._qstates)

    def _send_test_values(self):
        self._test_values = [self._qstates[i].value for i in self._test_set]
        self.ca_channel.send(self._test_values)

    def _measure_qstates(self, amount):
        self._qstates = self.q_channel.receive_qubits_in(self._gen_random_string(amount))

    def _receive_test_values(self):
        self._other_test_values = self.ca_channel.receive()

    def _discard_states(self):
        def has_same_basis(pair):
            q, b = pair
            return q.basis == b

        self._qstates = [q for q, _ in filter(has_same_basis, zip(self._qstates, self._other_bases))]

    def _calculate_error(self):
        return self._calculate_matching_error_of_values(self._test_values, self._other_test_values)

    def _is_outside_error_bound(self, matching_error):
        return matching_error > self.error

    def _privacy_amplification(self):
        indices = set(range(len(self._qstates))) - self._test_set
        return self._calc_privacy_amplification_of(indices)


class BB84SenderNode(BB84Node):
    """
    Node object that handles sending of the BB84 quantum key distribution protocol.
    """
    def __init__(self, q_channel, ca_channel, error, n):
        super().__init__(q_channel, ca_channel, error)
        self.n = n

    def share_q_states(self):
        """
        The sender implementation of BB84 state sharing.
            1. It prepares and sends the BB84 states to the receiver.
            2. Waits for acknowledgement of the receiver that it has received and measured the states
            3. Shares the bases used for preparation with the receiver
        """
        self._send_q_states(self.n)
        self._receive_ack()
        self._share_bases()

    def should_abort(self):
        """
        Calculates the matching error in the channel and decides whether to abort or not, dependent on the configured
        self.error parameter
        :return: True if the error exceeds specified bounds, False otherwise
        """
        self._discard_states()
        self._send_test_set()
        self._send_test_values()
        self._receive_test_values()
        self.matching_error = self._calculate_error()
        return self._is_outside_error_bound(self.matching_error)

    def generate_key(self):
        """
        Generates key bits based on the produced raw key of QKD.
        Generates a seed and sends it to the receiver. It then performs privacy amplification.
        :return: integer list of extracted key bits ([0, 1, 1])
        """
        self._send_seed()
        return self._privacy_amplification()


class BB84ReceiverNode(BB84Node):
    """
    Node object that handles receiving of the BB84 quantum key distribution protocol.
    """
    def __init__(self, q_channel, ca_channel, error):
        super().__init__(q_channel, ca_channel, error)

    def share_q_states(self):
        """
        The receiver implementation of BB84 state sharing.
            1. It retrieves the BB84 states from the sender and measures it.
            2. Sends an acknowledgement to the sender that it received and measured the states.
            3. Shares the bases used for measurement with the sender.
        """
        self._receive_q_states()
        self._send_ack()
        self._share_bases()

    def should_abort(self):
        """
        Calculates the matching error in the channel and decides whether to abort or not, dependent on the configured
        self.error parameter.
        :return: True if the error exceeds specified bounds, False otherwise
        """
        self._discard_states()
        self._receive_test_set()
        self._send_test_values()
        self._receive_test_values()
        self.matching_error = self._calculate_error()
        return self._is_outside_error_bound(self.matching_error)

    def generate_key(self):
        """
        Generates key bits based on the produced raw key of QKD.
        Retrieves seed from the sender and then performs privacy amplification.
        :return: integer list of extracted key bits ([0, 1, 1])
        """
        self._receive_seed()
        return self._privacy_amplification()
