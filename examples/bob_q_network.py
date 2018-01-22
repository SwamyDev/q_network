from QNetwork.q_network import open_channel


def main():
    with open_channel('Bob', 'Alice') as channel:
        msg = channel.read()

    print("Bob received message:", msg)


main()
