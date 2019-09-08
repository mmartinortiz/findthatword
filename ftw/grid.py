import copy
import random
import string

from ftw import to_alpha

BG_COLOUR = (1, 1, 1)
GRID_COLOUR = (0.5, 0.5, 0.5)
WORD_COLOUR = (0.75, 0.0, 0.0, 0.3)
SELECTED_COLOUR = (0.5, 0.0, 0.75, 0.6)
PADDING_COLOUR = (0, 0, 0)


class Grid(object):
    """letter grid in worsdearch puzzle"""

    def __init__(self, puzzle):
        """ x, y are the dimensions of the grid.  If y isn't supplied, a square grid is assumed"""

        #Assume a 2x2 grid initially
        self.set_grid_size(4, 4)
        self.padding = ''
        self.random_padding = True
        self.puzzle = puzzle
        self.clear()

    def clear(self):
        """Clear the grid"""
        x_size, y_size = self.get_grid_size()
        self.array = []
        for i in range(0, x_size):
            self.array.append([' '] * y_size)
        self.array_padding = copy.deepcopy(self.array)
        self.add_padding()

    def get_cell(self, x, y, result_type = "words"):
        """Return the content of reference (x,y).
            result_type indicates the type of content to return:
                words = words placed in the grid
                padding = padding letters
                both = both types of content"""

        if result_type == "words":
            return self.array[x][y]
        elif result_type == "padding":
            return self.array_padding[x][y]
        elif self.array[x][y] == ' ':
            return self.array_padding[x][y]
        else:
            return self.array[x][y]

    def set_cell(self, x, y, letter):
        self.array[x][y] = letter

    def add_padding(self):
        """populate the empty cells in the grid with a hidden message"""

        x_size, y_size = self.get_grid_size()
        padding = self.get_padding_text()
        for row in range(0, y_size):
            self.array.append([])
            for column in range(0, x_size):
                if self.array[column][row] == ' ' or self.random_padding:
                    self.array_padding[column][row] = padding[0]
                    padding = padding[1:]
                    if len(padding) == 0 and self.random_padding:
                        padding = self.get_padding_text()
                    elif len(padding) == 0:
                        padding = [' '] * 20
                else:
                    self.array_padding[column][row] = ' '

    def get_grid_size(self):
        return self.grid_size

    def set_grid_size(self, x, y):
        self.grid_size = [x, y]

    def get_padding_text(self):
        """Return the hidden message to be used for blank cells"""

        if self.random_padding:
            padding = list(string.ascii_lowercase)
            random.shuffle(padding)
        else:
            padding = to_alpha(self.padding)
            if padding == '':
                padding = ' '
        return padding

    def draw_as_cairo(self, surface, start_x, start_y, size_x, size_y, show_solution, selected_word, max_cell_size):
        """Renders the grid onto a cairo surface.
            Returns the font size used and the actual grid height"""

        #The size of the font relative to the size of the grid
        FONT_SIZE = 0.75

        #Calculate the optimum size of each cell
        cells_x, cells_y = self.get_grid_size()
        cell_size = min(max_cell_size, size_x / cells_x, size_y / cells_y)
        cell_size = int(cell_size)
        grid_x_size = cell_size * cells_x
        grid_y_size = cell_size * cells_y
        x_offset = 0.5 + int(start_x) + int((size_x - grid_x_size) / 2)
        y_offset = 0.5 + int(start_y)

        #Draw the grid
        surface.set_source_rgb(BG_COLOUR[0], BG_COLOUR[1], BG_COLOUR[2])
        surface.set_line_width(1)
        surface.set_source_rgb(GRID_COLOUR[0], GRID_COLOUR[1], GRID_COLOUR[2])

        for x in range(0, cells_x + 1):
            surface.move_to(x_offset + x * cell_size, y_offset)
            surface.rel_line_to(0, grid_y_size)
            surface.stroke()

        for y in range(0, cells_y + 1):
            surface.move_to(x_offset, y_offset + y * cell_size)
            surface.rel_line_to(grid_x_size, 0)
            surface.stroke()

        #Draw the letters in the grid
        surface.set_font_size(cell_size * FONT_SIZE)
        fascent, fdescent, fheight, fxadvance, fyadvance = surface.font_extents()
        font_y_offset = float( cell_size + fheight ) / 2 - fdescent

        for x in range(0, cells_x):
            for y in range(0, cells_y):
                letter = self.get_cell(x, y)

                #Decide what colour to display
                if show_solution and letter != " ":
                    r, g, b, a = WORD_COLOUR
                else:
                    r, g, b = PADDING_COLOUR
                surface.set_source_rgb(r, g, b)

                #Fetch padding if not part of a word
                if letter == " ":
                    letter = self.get_cell(x, y, "padding")

                #Display the letter
                xbearing, ybearing, width, height, xadvance, yadvance = surface.text_extents(letter)
                font_x_offset = float(cell_size - width) / 2 - xbearing
                surface.move_to(x_offset + x * cell_size + font_x_offset
                                    , y_offset + y * cell_size + font_y_offset)
                surface.show_text(letter)

       #Draw the solution lines
        if show_solution:
            surface.set_line_width(cell_size * 0.3)
            for word in self.puzzle.get_wordlist():
                x, y = word.get_coordinates()
                if x is not None:
                    if word == selected_word:
                        r, g, b, a = SELECTED_COLOUR
                    else:
                        r, g, b, a = WORD_COLOUR
                    surface.set_source_rgba(r, g, b, a)
                    x_dir, y_dir = word.get_direction()
                    word_length = word.get_length() - 1
                    surface.move_to(x_offset + (x + 0.5) * cell_size
                                        , y_offset + (y + 0.5) * cell_size)
                    surface.rel_line_to(x_dir * word_length * cell_size
                                            , y_dir * word_length * cell_size)
                    surface.stroke()

        #Return the font size that we used
        return grid_y_size