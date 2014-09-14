"""
The MIT License (MIT)

Copyright (c) 2014 Jozef van Eenbergen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""
import curses


class Terminal(object):

    def __init__(self, scrn=None):
        self._screen = scrn if scrn else curses.initscr()
        self._screen = curses.initscr()
        curses.noecho()
        curses.cbreak()
#        curses.curs_set(0)
        self._screen.keypad(1)

        self._refresh_rate = 3
        self._screen.timeout(self._refresh_rate * 1000)
        self.selected_row = None
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
        self._windows = {}

    @property
    def colors(self):
        return self._colors_list

    @property
    def panels(self):
        return self._panels

    @property
    def windows(self):
        return self._windows

    def getch(self):
        return self._screen.getch()

    def refresh(self):
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
        self._windows[name] = panel
        return panel

    def create_panel(self, name, height, width):
        panel = Panel(height, width)
        self._panels[name] = panel
        return panel

    def add_line(self, text, top, left, color=None):
        self._screen.addstr(top, left, text, color)

    def up(self):
        self.selected_row -= 1

    def down(self):
        self.selected_row += 1


class Window(object):

    def __init__(self, height, width, top, left, parent):
        self._panel = parent._screen.subwin(height, width, top, left)
        self._parent = parent
        self._panel.scrollok(1)
        self._panel.idlok(1)
        self._panel.touchwin()

    def add_line(self, text, top, left, color=None):
        self._panel.addstr(top, left, text, color)

    def refresh(self):
        return self._panel.refresh()


class Panel(object):
    """ Wrapped newpad object
    """
    def __init__(self, height, width):
        self._panel = curses.newpad(height, width)
        self.selected_row = 0
        self.ptopy = 0
        self.ptopx = 0
        self.stopy = 0
        self.stopx = 0
        self.sbottomy = 0
        self.sbottomx = 0
        self.max = height

    def set_max(self, value):
        self.max = value

    def add_line(self, text, top, left, color=None):
        self._panel.addstr(top, left, text, color)

    def refresh(self, ptopy, ptopx, stopy, stopx, sbottomy, sbottomx):
        self.ptopx = ptopx
        self.ptopy = ptopy
        self.stopy = stopy
        self.stopx = stopx
        self.sbottomy = sbottomy
        self.sbottomx = sbottomx

        return self._panel.refresh(self.ptopy, self.ptopx, self.stopy, self.stopx, self.sbottomy, self.sbottomx)

    def getch(self):
        return self._panel.getch()

    def scroll_up(self):
        self.refresh(max(self.ptopy - 1, 0), self.ptopx, self.stopy, self.stopx, self.sbottomy, self.sbottomx)

    def scroll_down(self):
        self.refresh(min(self.ptopy+1, self.max), self.ptopx, self.stopy, self.stopx, self.sbottomy, self.sbottomx)