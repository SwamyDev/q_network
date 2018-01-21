import unittest
from collections import deque

from QNetwork.q_network_util import QState, QChannel, CAChannel


class QConnectionSpy:
    def __init__(self, qubit_factory):
        self.qubit_factory = qubit_factory
        self.receiver = ''
        self.qubits = []
        self.epr_values = deque()

    def sendQubit(self, qubit, receiver):
        self.receiver = receiver
        self.qubits.append(qubit)

    def createEPR(self, receiver):
        self.receiver = receiver
        q = self.qubit_factory(self)
        if len(self.epr_values) != 0:
            q.value = self.epr_values.popleft()
        self.qubits.append(q)
        return q


class CACConnectionSpy:
    def __init__(self):
        self.receiver = ''
        self.sender = ''
        self.sent_data = None
        self.received_get_call = False
        self.received_clear_call = False
        self.received_close_call = False
        self.received_send_ack_call = False
        self.received_get_ack_call = False

    def sendValueList(self, receiver, data):
        self.receiver = receiver
        self.sent_data = data

    def getValueList(self, sender):
        self.sender = sender
        self.received_get_call = True

    def sendAck(self, receiver):
        self.receiver = receiver
        self.received_send_ack_call = True

    def getAck(self, sender):
        self.sender = sender
        self.received_get_ack_call = True

    def clearServer(self):
        self.received_clear_call = True

    def closeChannel(self):
        self.received_close_call = True


class QubitSpy:
    def __init__(self, value=0):
        self.operations = []
        self.value = value

    def X(self):
        self.operations.append('X')

    def Y(self):
        self.operations.append('Y')

    def Z(self):
        self.operations.append('Z')

    def H(self):
        self.operations.append('H')

    def measure(self):
        return self.value


def make_qubit_spy(connection):
    return QubitSpy()


class ConnectionStub:
    def __init__(self):
        self.qubits = None
        self.received_qubits = None
        self.idx = 0

    @property
    def received_qubits(self):
        return self.qubits

    @received_qubits.setter
    def received_qubits(self, value):
        self.qubits = value

    def recvQubit(self):
        self.idx += 1
        return self.qubits[self.idx - 1]

    def recvEPR(self):
        self.idx += 1
        return self.qubits[self.idx - 1]


class TestQChannelBase(unittest.TestCase):
    def setUp(self):
        self.con = self.make_connection_double()
        self.qc = QChannel(self.con, make_qubit_spy, 'Bob')

    def make_connection_double(self):
        raise NotImplementedError("QChannel test require a connection object")

    def assert_qubit_operations(self, *expected_operations):
        for i, e in enumerate(expected_operations):
            self.assertEqual(e, self.con.qubits[i].operations, "Unexpected operations on qubit {}".format(i))


class TestQChannelSending(TestQChannelBase):
    def make_connection_double(self):
        return QConnectionSpy(make_qubit_spy)

    def test_send_qubits_to_receiver(self):
        self.qc.send_qubits([QState(0, 0)])
        self.assertEqual('Bob', self.con.receiver)

    def test_sending_qubits_with_default_bases(self):
        self.qc.send_qubits([QState(0, 0), QState(0, 1), QState(1, 0), QState(1, 1)])
        self.assert_qubit_operations([], ['H'], ['X'], ['X', 'H'])

    def test_sending_qubits_with_specified_bases(self):
        self.qc.bases_mapping = [lambda q: q.Z(), lambda q: q.Y()]
        self.qc.send_qubits([QState(0, 0), QState(0, 1)])
        self.assert_qubit_operations(['Z'], ['Y'])

    def test_send_epr_pair_to_receiver(self):
        self.qc.send_epr([0])
        self.assertEqual('Bob', self.con.receiver)

    def test_measuring_sent_epr_pair(self):
        self.con.epr_values = deque([1, 0])
        self.assertEqual([QState(1, 0), QState(0, 1)], self.qc.send_epr([0, 1]))

    def test_measuring_sent_epr_pair_in_default_bases(self):
        self.qc.send_epr([0, 1])
        self.assert_qubit_operations([], ['H'])

    def test_measuring_sent_epr_pair_in_specified_bases(self):
        self.qc.bases_mapping = [lambda q: q.Z(), lambda q: q.Y()]
        self.qc.send_epr([0, 1])
        self.assert_qubit_operations(['Z'], ['Y'])


class TestQChannelReceiving(TestQChannelBase):
    def make_connection_double(self):
        return ConnectionStub()

    def test_receiving_qubits(self):
        self.con.received_qubits = [QubitSpy(0), QubitSpy(0), QubitSpy(1), QubitSpy(1)]
        self.assertSequenceEqual([QState(0, 0), QState(0, 1), QState(1, 0), QState(1, 1)]
                                 , self.qc.receive_qubits_in([0, 1, 0, 1]))

    def test_measure_qubits_in_default_bases(self):
        self.con.received_qubits = [QubitSpy(), QubitSpy()]
        self.qc.receive_qubits_in([0, 1])
        self.assert_qubit_operations([], ['H'])

    def test_measure_qubits_in_specified_bases(self):
        self.con.received_qubits = [QubitSpy(), QubitSpy(), QubitSpy()]
        self.qc.bases_mapping = [lambda q: q.Y(), lambda q: q.Z(), lambda q: q.H()]
        self.qc.receive_qubits_in([0, 1, 2])
        self.assert_qubit_operations(['Y'], ['Z'], ['H'])

    def test_receiving_epr_pair(self):
        self.con.received_qubits = [QubitSpy(0), QubitSpy(0), QubitSpy(1), QubitSpy(1)]
        self.assertSequenceEqual([QState(0, 0), QState(0, 1), QState(1, 0), QState(1, 1)]
                                 , self.qc.receive_epr_in([0, 1, 0, 1]))

    def test_measure_epr_in_default_bases(self):
        self.con.received_qubits = [QubitSpy(), QubitSpy()]
        self.qc.receive_epr_in([0, 1])
        self.assert_qubit_operations([], ['H'])

    def test_measure_epr_in_specified_bases(self):
        self.con.received_qubits = [QubitSpy(), QubitSpy(), QubitSpy()]
        self.qc.bases_mapping = [lambda q: q.Y(), lambda q: q.Z(), lambda q: q.H()]
        self.qc.receive_epr_in([0, 1, 2])
        self.assert_qubit_operations(['Y'], ['Z'], ['H'])


class TestCAC(unittest.TestCase):
    def test_sending_list_data(self):
        connection = CACConnectionSpy()
        ca = CAChannel(connection, 'Bob')
        ca.send([1, 2])
        self.assertSequenceEqual([1, 2], connection.sent_data)
        self.assertEqual('Bob', connection.receiver)

    def test_sending_single_int(self):
        connection = CACConnectionSpy()
        ca = CAChannel(connection, 'Bob')
        ca.send(42)
        self.assertSequenceEqual([42], connection.sent_data)
        self.assertEqual('Bob', connection.receiver)

    def test_receiving_data(self):
        connection = CACConnectionSpy()
        ca = CAChannel(connection, 'Alice')
        ca.receive()
        self.assertTrue(connection.received_get_call)
        self.assertEqual('Alice', connection.sender)

    def test_send_acknowledgement(self):
        connection = CACConnectionSpy()
        ca = CAChannel(connection, 'Alice')
        ca.send_ack()
        self.assertTrue(connection.received_send_ack_call)
        self.assertEqual('Alice', connection.receiver)

    def test_receive_acknowledgement(self):
        connection = CACConnectionSpy()
        ca = CAChannel(connection, 'Bob')
        ca.receive_ack()
        self.assertTrue(connection.received_get_ack_call)
        self.assertEqual('Bob', connection.sender)

    def test_clear(self):
        connection = CACConnectionSpy()
        ca = CAChannel(connection, 'Alice')
        ca.clear()
        self.assertTrue(connection.received_clear_call)

    def test_close(self):
        connection = CACConnectionSpy()
        ca = CAChannel(connection, 'Alice')
        ca.close()
        self.assertTrue(connection.received_close_call)
