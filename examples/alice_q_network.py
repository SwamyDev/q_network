from QNetwork.q_network import open_channel


def main():
    with open_channel('Alice', 'Bob') as channel:
        channel.write("Hello, Bob!")

    print("=== Alice sent message ===")


main()
