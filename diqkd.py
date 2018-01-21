import operator

import math

from QNetwork.qkd import QKDNode


class DIQKDNode(QKDNode):
    def __init__(self, q_channel, ca_channel, error):
        super().__init__(ca_channel, error)
        self.q_channel = q_channel
        self._chsh_test_set = set()
        self._match_test_set = set()
        self._raw_key_set = set()
        self._chsh_test_values = []
        self._other_chsh_test_values = []
        self._match_test_values = []
        self._other_match_test_values = []

    def _send_q_states(self, amount):
        super()._send_q_states(amount)
        self._qstates = self.q_channel.send_epr(self._gen_random_string(amount))

    def _send_chsh_test_values(self):
        self._chsh_test_values = self._get_and_send_values_from_test_set(self._chsh_test_set)

    def _get_and_send_values_from_test_set(self, test_set):
        values = [self._qstates[i].value for i in test_set]
        self.ca_channel.send(values)
        return values

    def _send_match_test_values(self):
        self._match_test_values = self._get_and_send_values_from_test_set(self._match_test_set)

    def _measure_qstates(self, amount):
        print('Bob amount', amount)
        self._qstates = self.q_channel.receive_epr_in(self._gen_random_string(amount, up_to=2))

    def _receive_chsh_test_values(self):
        self._other_chsh_test_values = self.ca_channel.receive()

    def _receive_match_test_values(self):
        self._other_match_test_values = self.ca_channel.receive()

    def _separate_test_subsets(self):
        self._chsh_test_set = set(filter(self._is_chsh_test, self._test_set))

        self._match_test_set = set(filter(self._is_matching_basis, self._test_set))

        remaining = set(range(len(self._qstates))) - self._test_set
        self._raw_key_set = set(filter(self._is_matching_basis, remaining))

    def _is_chsh_test(self, index):
        pass

    def _is_matching_basis(self, index):
        pass

    def _calculate_winning_probability(self):
        test_bases = [self._qstates[i].basis for i in self._chsh_test_set]
        other_test_bases = [self._other_bases[i] for i in self._chsh_test_set]
        and_bases = map(operator.mul, test_bases, other_test_bases)
        xor_values = map(operator.xor, self._chsh_test_values, self._other_chsh_test_values)

        t = len(self._chsh_test_values)
        w = sum(a == b for a, b in zip(and_bases, xor_values))
        return w / t

    def _calculate_match_error(self):
        return self._calculate_matching_error_of_values(self._match_test_values, self._other_match_test_values)

    def _privacy_amplification(self):
        return self._calc_privacy_amplification_of(self._raw_key_set)

    def _perform_abort_test(self):
        self._separate_test_subsets()
        self._send_chsh_test_values()
        self._receive_chsh_test_values()
        self._send_match_test_values()
        self._receive_match_test_values()
        self.win_prob = self._calculate_winning_probability()
        self.matching_error = self._calculate_match_error()
        return self._is_outside_error_bound(self.win_prob, self.matching_error)

    def _is_outside_error_bound(self, win_prob, matching_error):
        return (win_prob < (0.5 + (1 / (2 * math.sqrt(2)))) - self.error) or (matching_error < 1.0 - self.error)


class DIQKDSenderNode(DIQKDNode):
    def __init__(self, q_channel, ca_channel, error, n):
        super().__init__(q_channel, ca_channel, error)
        self.n = n

    def _is_chsh_test(self, index):
        return self._other_bases[index] < 2

    def _is_matching_basis(self, index):
        return self._other_bases[index] == 2 and self._qstates[index].basis == 0

    def share_q_states(self):
        self._send_q_states(self.n)
        self._receive_ack()
        self._share_bases()

    def should_abort(self):
        self._send_test_set()
        return self._perform_abort_test()

    def generate_key(self):
        self._send_seed()
        return self._privacy_amplification()


class DIQKDReceiverNode(DIQKDNode):
    def __init__(self, q_channel, ca_channel, error, step):
        q_channel.bases_mapping = [lambda q: q.rot_Y(128+step, print_info=False), lambda q: q.rot_Y(step, print_info=False), lambda q: None]
        super().__init__(q_channel, ca_channel, error)

    def _is_chsh_test(self, index):
        return self._qstates[index].basis < 2

    def _is_matching_basis(self, index):
        return self._other_bases[index] == 0 and self._qstates[index].basis == 2

    def share_q_states(self):
        self._receive_q_states()
        self._send_ack()
        self._share_bases()

    def should_abort(self):
        self._receive_test_set()
        return self._perform_abort_test()

    def generate_key(self):
        self._receive_seed()
        return self._privacy_amplification()
