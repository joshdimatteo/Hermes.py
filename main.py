import socket
import curses
from threading import Thread

# Public room data
PUBLIC_RANGE = (50000, 50009)
public_rooms = []

# Address to broadcast to. Mainly used for debugging.
BROADCAST = '255.255.255.255'

# Keeps out and inp global in order to allow global access (go figure)
out = None
inp = None


# Joins a room and begins messaging.
def join(port):
    global out, inp

    # Sockets to broadcast data and receive data.
    b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    b.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    r.bind(('0.0.0.0', port))

    # Broadcasts data
    def broadcast(message):
        b.sendto(message.encode(), (BROADCAST, port))

    # Constantly receives and outputs data.
    def receiver():
        while True:
            data = r.recvfrom(1024)

            if data[0].decode == 'ping':
                broadcast('pong')
            elif data[0].decode != 'pong':
                out.send(data[0].decode())

    # Grabs nickname from user.
    out.send('Enter your nickname.\n')
    nickname = inp.input()

    # Starts receiving messages
    Thread(target=receiver).start()

    broadcast(f'{nickname} joined the room.')
    while True:
        broadcast(f'{nickname}: {inp.input()}')


# Check rooms for a specific range.
def ping_range(low, high):
    open_rooms = []

    def ping(port):
        nonlocal open_rooms

        # Sockets for pinging
        b = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        b.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        r = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        r.bind(('0.0.0.0', port))

        # Sends ping and receives it, so it doesn't create interference when it receives from other pings.
        b.sendto('ping'.encode(), (BROADCAST, port))

        r.settimeout(2)
        r.recvfrom(1024)

        # Waits for ping with timeout of 2 seconds.
        r.settimeout(2)

        try:
            if r.recvfrom(1024)[0].decode() == 'pong':
                open_rooms.append(port)
        except socket.timeout:
            pass

        b.close()
        r.close()

    threads = []
    for n in range(low, high + 1):
        t = Thread(target=ping, args=(n,))
        t.start()
        threads.append(t)

    for thread in threads:
        thread.join()

    return open_rooms


# Output screen
class Output:
    def __init__(self, rows=24, columns=118, x=0, y=1):

        # Makes text border for output (doesn't need to be saved to class)
        border = curses.newwin(rows, columns, x, y)
        border.box()
        border.refresh()

        # Makes output screen
        self.output_screen = curses.newwin(rows - 2, columns - 4, x + 1, y + 2)

        # Buffer for messages to be displayed
        self.buffer = []
        self.rows = rows
        self.columns = columns

        # Begins continuous refreshing
        Thread(target=self.refresh_loop).start()

    # Adds data to be outputted.
    def send(self, text):
        self.buffer.append(text)

    def clear(self):
        self.output_screen.clear()
        self.output_screen.refresh()

    # Refresh screen
    def refresh(self):

        # Creates array to be outputted
        output = []
        count = 0

        dupe = self.buffer.copy()
        dupe.reverse()

        for message in dupe:
            for string in message.split('\n'):
                count += len(string) // (self.columns - 4) + 1

            if count > self.rows - 2:
                break
            else:
                output.append(message)
        output.reverse()

        # Sends messages
        self.clear()
        try:
            self.output_screen.addstr('\n'.join(output))
        except curses.error:
            pass
        self.output_screen.refresh()

    # Refreshes upon buffer change
    def refresh_loop(self):

        # Checks for changes in buffer
        length = len(self.buffer)

        while True:
            if len(self.buffer) != length:
                length = len(self.buffer)

                self.refresh()


# Input screen
class Input:
    def __init__(self, rows=5, columns=118, x=24, y=1):

        # Makes text border for input
        border = curses.newwin(rows, columns, x, y)
        border.box()
        border.refresh()

        # Makes input screen
        self.input_screen = curses.newwin(rows - 2, columns - 4, x + 1, y + 2)

    def input(self):
        data = ''

        while True:

            # Gets key
            key = self.input_screen.getkey()

            # Processes key
            if key == '\n':
                self.input_screen.clear()
                self.input_screen.refresh()
                break
            elif key == '\b':
                data = data[:-1]
            else:
                data += key

            # Prints data.
            try:
                self.input_screen.clear()
                self.input_screen.addstr(data)
            except curses.error:
                pass

        return data


def main(_):
    global out, inp

    # Invisible cursor
    curses.curs_set(0)

    # Global out and inp variables
    out = Output()
    inp = Input()

    # Notification
    out.send('Hermes Chatroom by Josh DiMatteo')
    out.send('Enter "help" for a list of commands.\n')

    # Begins running console loop.
    while True:
        command = inp.input()
        out.send(f'> {command}')

        if command == 'help':
            out.send('''Help Commands

rooms                  Lists all public occupied rooms
join <room number>     Joins a specific room

help                   Prints this table
''')
        elif command == 'rooms':
            rooms = ping_range(PUBLIC_RANGE[0], PUBLIC_RANGE[1])
            out.send('\n'.join(rooms) + '\n' if len(rooms) > 0 else 'No occupied rooms.\n')

        elif command.startswith('join'):
            if len(command.split(' ')) == 1:
                out.send('No room supplied.\n')
            elif len(command.split(' ')) >= 3:
                out.send('Too many parameters.\n')
            elif int(command.split(' ')[1]) < PUBLIC_RANGE[0] or int(command.split(' ')[1]) > PUBLIC_RANGE[1]:
                out.send(f'Invalid room entered. Rooms range from {PUBLIC_RANGE[0]} to {PUBLIC_RANGE[1]}\n')
            else:
                join(int(command.split(' ')[1]))

        else:
            out.send('Unknown command. Enter "help" for a list of commands.\n')


if __name__ == '__main__':
    curses.wrapper(main)
