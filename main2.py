import curses
from threading import Thread

# Global out and inp for universal access
out = None
inp = None


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


def main(_):
    global out, inp

    # Invisible cursor
    curses.curs_set(0)

    # Defines output and input
    out = Output()
    inp = Input()

    # Outputs input.
    while True:
        out.send(inp.input())


curses.wrapper(main)
