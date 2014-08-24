import curses


class Terminal(object):

    def __init__(self):
        self._screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
#        curses.curs_set(0)
        self._screen.keypad(1)

        self._refresh_rate = 3
        self._screen.timeout(self._refresh_rate * 1000)
        self.selected_row = 0
        self.start_row = 0

        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_RED)
        curses.init_pair(3, curses.COLOR_WHITE, curses.COLOR_GREEN)
        curses.init_pair(4, curses.COLOR_WHITE, curses.COLOR_BLUE)
        curses.init_pair(5, curses.COLOR_WHITE, curses.COLOR_MAGENTA)
        curses.init_pair(6, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(7, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(8, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(9, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(10, curses.COLOR_BLACK, curses.COLOR_YELLOW)
        curses.init_pair(11, curses.COLOR_BLACK, curses.COLOR_WHITE)

        self._colors_list = {
            'DEFAULT': curses.color_pair(1),
            'UNDERLINE': curses.A_UNDERLINE,
            'BOLD': curses.A_BOLD,
            'SORT': curses.A_BOLD,
            'OK': curses.color_pair(7),
            'TITLE': curses.A_BOLD,
            'PROCESS': curses.color_pair(7),
            'STATUS': curses.color_pair(7),
            'NICE': curses.color_pair(9),
            'CAREFUL': curses.color_pair(8),
            'WARNING': curses.color_pair(9),
            'CRITICAL': curses.color_pair(6),
            'OK_LOG': curses.color_pair(3),
            'CAREFUL_LOG': curses.color_pair(4),
            'WARNING_LOG': curses.color_pair(5),
            'CRITICAL_LOG': curses.color_pair(2),
            'SEPARATOR': curses.color_pair(10),
            'REVERSE': curses.color_pair(11),
        }

        self._panels = {}

    @property
    def colors(self):
        return self._colors_list

    @property
    def panels(self):
        return self._panels

    def getch(self):
        return self._screen.getch()

    def refresh(self):
        for panel in self._panels.itervalues():
            panel.refresh()
        return self._screen.refresh()

    def get_size(self):
        return self._screen.getmaxyx()

    def stop(self):
        curses.nocbreak()
        self._screen.keypad(0)
        curses.echo()
        curses.endwin()

    def create_window(self, name, height, width, top, left):
        panel = Window(height, width, top, left, self)
        self._panels[name] = panel
        return panel

    def create_panel(self, name, height, width):
        panel = Panel(height, width)
        self._panels[name] = panel
        return panel

    def addLine(self, text, top, left, color=None):
        self._screen.addstr(top, left, text, color)

    def up(self):
        self.selected_row -= 1

    def down(self):
        self.selected_row += 1

class Window(object):

    def __init__(self, height, width, top, left, parent):
        self._panel = curses.newwin(height, width, top, left)
        self._parent = parent

    def addLine(self, text, top, left, color=None):
        self._panel.addstr(top, left, text, color)

    def refresh(self):
        return self._panel.refresh()

class Panel(object):
    def __init__(self, height, width):
        self._panel = curses.newpad(height, width)

    def addLine(self, text, top, left, color=None):
        self._panel.addstr(top, left, text, color)

    def refresh(self, top_corner, left, top, top2, bottom, bottom2):
        return self._panel.refresh(top_corner, left, top, top2, bottom, bottom2)

    def getch(self):
        return self._panel.getch()