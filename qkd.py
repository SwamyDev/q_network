class QKDNode:
    def __init__(self, ca_channel):
        self.ca_channel = ca_channel
        self._qstates = []
        self._other_bases = []

    def _share_bases(self):
        self._send_bases()
        self._receive_bases()

    def _send_bases(self):
        self.ca_channel.send([q.basis for q in self._qstates])

    def _receive_bases(self):
        self._other_bases = self.ca_channel.receive()