import random

from ftw import to_alpha


class Word(object):
    """word in puzzle"""

    def __init__(self, puzzle, word, clue = None):
        """
            puzzle is the puzzle to which the word is belongs
            word is the word text displayed to the user
            clue is optionally the word as it appears in the word list
        """
        self.puzzle = puzzle
        self.word_alpha = to_alpha(word)
        self.word = word
        self.length = len(self.word_alpha)
        if clue:
            self.clue = clue
        else:
            self.clue = word
        self.clear()

    def clear(self):
        """clear the word's location"""
        self.set_coordinates()
        self.set_direction()

    def draw(self):
        """draws the word in the puzzle's grid.  This method does not update
        the puzzle's hidden message"""
        x, y = self.get_coordinates()
        x_dir, y_dir = self.get_direction()
        if x_dir is not None and y_dir is not None:
            for letter in self.get_word_alpha():
                self.puzzle.grid.set_cell(x, y, letter)
                x += x_dir
                y += y_dir

    def test_draw(self):
        """checks whether the word will fit in the puzzle's grid"""
        x, y = self.get_coordinates()
        x_dir, y_dir = self.get_direction()
        if x_dir is not None and y_dir is not None:
            fits = True
            for letter in self.get_word_alpha():
                if self.puzzle.grid.get_cell(x, y) not in (' ', letter):
                    fits = False
                x += x_dir
                y += y_dir
        else:
            fits = False
        return fits

    def place(self):
        """find a free location in the grid and draw the word
        Returns True if successful"""
        untried_locations = self.get_possible_locations()

        #Try each location in turn until the word fits
        placed = False
        while untried_locations <> [] and not placed:
            current_location = untried_locations.pop()
            x, y = current_location['coordinates']
            self.set_coordinates(x, y)
            x_dir, y_dir = current_location['direction']
            self.set_direction(x_dir, y_dir)
            if self.test_draw():
                placed = True
                self.draw()
                #if a hidden message is to be displayed, re-draw it
                if not self.puzzle.grid.random_padding:
                    self.puzzle.grid.add_padding()

        #Return the result of the attempted placement
        return placed

    def get_possible_locations(self):
        """return a list of possible locations and directions where the word would
        fit if the grid were empty"""
        all_directions = ([-1, -1], [-1, 0], [-1, 1], [0, -1], [0, 1], [1, -1], [1, 0], [1, 1])
        untried_locations = []
        grid_x_size, grid_y_size = self.puzzle.grid.get_grid_size()
        word_length = self.get_length()
        for direction in all_directions:
            #Find the cells in the grid where the word could fit
            x_start = max(0, -direction[0] * word_length - 1)
            y_start = max(0, -direction[1] * word_length - 1)
            x_end = min(grid_x_size - 1, grid_x_size - direction[0] * word_length)
            y_end = min(grid_y_size - 1, grid_y_size - direction[1] * word_length)

            #Build up the list of untried locations
            for x in range(x_start, x_end + 1):
                for y in range(y_start, y_end + 1):
                    untried_locations.append({'coordinates': [x, y], 'direction': direction})
        random.shuffle(untried_locations)
        return untried_locations

    def update(self, new_word, new_clue):
        """Change the word and / or description"""
        sucess = True
        if new_clue:
            self.clue = new_clue
        if new_word <> self.get_word():
            #The word has changed.  Rebuild everything
            self.word_alpha = to_alpha(new_word)
            self.word = new_word
            self.length = len(self.word_alpha)
            if not new_clue:
                self.clue = new_word
            self.clear()
            success = self.puzzle.resize_and_rebuild()
        return success

    def get_word_alpha(self):
        return self.word_alpha

    def get_word(self):
        return self.word

    def get_clue(self):
        return self.clue

    def get_coordinates(self):
        return self.coordinates

    def set_coordinates(self, x = None, y = None):
        self.coordinates = [x, y]

    def get_direction(self):
        return self.direction

    def set_direction(self, x = None, y = None):
        self.direction = [x, y]

    def get_length(self):
        return self.length