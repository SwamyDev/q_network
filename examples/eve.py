import random

from SimulaQron.cqc.pythonLib.cqc import CQCConnection, qubit


def main():
    eve = CQCConnection('Eve')
    qvalues = []
    for i in range(1000):
        q = eve.recvQubit()
        b = random.randint(0, 1)
        if b == 1:
            qvalues.append(q.measure(True))

        #value = q.measure()
        #qvalues.append(value)
        #
        #q_new = qubit(eve)
        #if value == 1:
        #    q_new.X()
        #if b == 1:
        #    q_new.H()

        eve.sendQubit(q, 'Bob')

    print("Eve received qbits: {}".format(qvalues))
    eve.close()

main()