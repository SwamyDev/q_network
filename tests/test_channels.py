import unittest

from QNetwork.q_network import QState, QChannel, CAChannel


class QConnectionSpy:
    def __init__(self):
        self.receiver = ''
        self.sent_qubits = []

    def sendQubit(self, qubit, receiver):
        self.receiver = receiver
        self.sent_qubits.append(qubit)


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
    def __init__(self):
        self.operations = []

    def X(self):
        self.operations.append('X')

    def H(self):
        self.operations.append('H')


def make_qubit_spy(connection):
    return QubitSpy()


class ConnectionStub:
    def __init__(self, received_data):
        self.received_qubits = received_data
        self.idx = 0

    def recvQubit(self):
        self.idx += 1
        return self.received_qubits[self.idx - 1]



class QubitMock:
    def __init__(self, value):
        self.value = value
        self.is_hadamard = False

    def H(self):
        self.is_hadamard = True

    def measure(self):
        return self.value


class TestQChannel(unittest.TestCase):
    def test_sending_qubits(self):
        connection = QConnectionSpy()
        qc = QChannel(connection, make_qubit_spy, 'Bob')
        qc.send_qubits([QState(0, 0), QState(0, 1), QState(1, 0), QState(1, 1)])
        self.assertEqual('Bob', connection.receiver)
        self.assertEqual([], connection.sent_qubits[0].operations)
        self.assertEqual(['H'], connection.sent_qubits[1].operations)
        self.assertEqual(['X'], connection.sent_qubits[2].operations)
        self.assertEqual(['X', 'H'], connection.sent_qubits[3].operations)

    def test_receiving_qubits(self):
        connection = ConnectionStub([QubitMock(0), QubitMock(0), QubitMock(1), QubitMock(1)])
        qc = QChannel(connection, make_qubit_spy, 'Alice')
        self.assertSequenceEqual([QState(0, 0), QState(0, 1), QState(1, 0), QState(1, 1)]
                                 , qc.measure_qubits([0, 1, 0, 1]))

    def test_received_qubits_are_measured_in_correct_basis(self):
        connection = ConnectionStub([QubitMock(0), QubitMock(0)])
        qc = QChannel(connection, make_qubit_spy, 'Alice')
        qc.measure_qubits([0, 1])
        self.assertEqual(False, connection.received_qubits[0].is_hadamard)
        self.assertEqual(True, connection.received_qubits[1].is_hadamard)


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

