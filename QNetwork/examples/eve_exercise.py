import random

from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit


def main():
    eve = CQCConnection('Eve')
    qvalues = []
    for i in range(1000):
        # Simple attack where eve just measures the qubit it receives and just sends it on to Bob
        q = eve.recvQubit()
        b = random.randint(0, 1)
        if b == 1:
            qvalues.append(q.measure(True))

        eve.sendQubit(q, 'Bob')

    print("Eve received qbits: {}".format(qvalues))
    eve.close()

main()