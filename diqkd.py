from QNetwork.qkd import QKDNode


class DIQKDNode(QKDNode):
    def __init__(self, q_channel, ca_channel):
        super().__init__(ca_channel)
        self.q_channel = q_channel

    def _send_q_states(self, amount):
        super().__init__(amount)
        self._qstates = self.q_channel.measure_entangled(self._gen_random_string(amount))

    def _measure_qstates(self, amount):
        self._qstates = self.q_channel.measure_entangled(self._gen_random_string(amount, up_to=2))
