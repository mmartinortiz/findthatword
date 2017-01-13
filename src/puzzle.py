
"""
Copyright 2009 Jonny Jones and Ieuan Jones

    This file is part of FindThatWord.

    FindThatWord is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""

import random
import copy
import math
import cairo
import pango
import pangocairo
import gobject
import gtk
import string

BG_COLOUR = (1, 1, 1)
GRID_COLOUR = (0.5, 0.5, 0.5)
WORD_COLOUR = (0.75, 0.0, 0.0, 0.3)
SELECTED_COLOUR = (0.5, 0.0, 0.75, 0.6)
PADDING_COLOUR = (0, 0, 0)

def to_alpha(text):
    """Remove non-aphabetic characters and switch to lower case""" 
    result = ''
    for letter in text.lower():
        if letter.isalpha():
            result += letter
    return result

class Puzzle(object):
    """ wordsearch puzzle """
    
    def __init__(self):
        self.grid = Grid(self)
        self.wordlist = []
        self.title = ""
        self.narrative = ""
        self.set_is_forced_size(False)
        self.force_x = 10
        self.force_y = 10
        self.longest_word = 0
        self.total_letters = 0
        self.resize_grid()
        
    def add_word(self, name, description = None):
        """add an individual word to the puzzle"""
        
        success = True
        new_word = Word(self, name, description)
        
        #Is the grid still the right size?  Resize it if necessary
        word_length = new_word.get_length()
        if word_length > self.longest_word:
            self.longest_word = word_length
        self.total_letters += word_length
        self.resize_grid()

        #Add the word
        self.wordlist.append(new_word)
        placed = new_word.place()
        if not placed:
            success = self.populate_grid()
        return success
            
    def get_word(self, word_id):
        """Returns the word object with position in list given by word_id"""
        return self.wordlist[word_id]
            
    def delete_word(self, word_id):
        """Removes the word with an index of word_id"""
        self.wordlist = self.wordlist[ : word_id ] + self.wordlist[ word_id + 1 : ]
        self.resize_and_rebuild()
        
    def resize_and_rebuild(self):
        """A word has changed.  Recalculate everything.  Returns false if all words not placed"""
        self.longest_word = 0
        self.total_letters = 0
        for word in self.get_wordlist():
            self.longest_word = max( self.longest_word, word.get_length() )
            self.total_letters += word.get_length()
        self.resize_grid()
        return self.populate_grid()        

    def move_word_up(self, word_id):
        """Moves the word with an index of word_id up one place"""
        
        if word_id > 0 and word_id <= self.get_word_count():
            self.wordlist = self.wordlist[ : word_id - 1 ] + self.wordlist[ word_id : word_id + 1 ] + self.wordlist[ word_id - 1 : word_id ] + self.wordlist[ word_id + 1 : ]
        
    def sort_wordlist(self):
        """Sorts the word list alphabetically"""
        self.wordlist.sort(cmp = lambda x, y: cmp(x.get_word_alpha(), y.get_word_alpha()))
        
    def clear_wordlist(self):
        """Clear the location of all words from the puzzle"""
        self.grid.clear()
        for word in self.get_wordlist():
            word.clear()
            
    def get_wordlist(self):
        """Returns the puzzle's wordlist"""
        return self.wordlist
        
    def get_word_count(self):
        return len(self.wordlist)
    
    def resize_grid(self):
        """Resize the grid and place all the words in it"""
        current_x_size, current_y_size = self.grid.get_grid_size()
        result = True
        if not self.get_is_forced_size():
            #Automatic grid size
            new_size = self.get_optimum_size()
            if current_x_size <> new_size or current_y_size <> new_size:
                #The grid size needs to change
                self.grid.set_grid_size(new_size, new_size)
                self.force_x = new_size
                self.force_y = new_size
                result = self.populate_grid()
        else:
            #Manual grid size
            if current_x_size <> self.force_x or current_y_size <> self.force_y:
                #The grid size needs to change
                self.grid.set_grid_size(self.force_x, self.force_y)
                result = self.populate_grid()
        return result
    
    def populate_grid(self):
        """Place all words on the puzzle grid.  Returns True if ssuccessful"""
        
        placed = False     #all words have been placed successfully
        finished = False   #stop attempting to place words and return
        
        while not finished:
            #if not forced size, keep trying different grid sizes until successful
            wordlist = copy.copy(self.wordlist)
            wordlist.sort(cmp = lambda x, y: cmp(-x.get_length(), -y.get_length()))
            i = 0
            while i < 20 and not placed:
                #Repeatedly attempt to fit the words into the grid before giving up
                self.clear_wordlist()
                i += 1
                for word in wordlist:
                    placed = word.place()
                    if not placed:
                        word.clear()
                        break
                else:
                    placed = True
            
            if placed or self.get_is_forced_size():
                #Success or give up
                finished = True
            else:
                #Try a larger grid
                current_x_size, current_y_size = self.grid.get_grid_size()
                self.grid.set_grid_size(current_x_size + 1, current_y_size + 1)
                self.grid.clear
        
        return placed
    
    def get_is_forced_size(self):
        return self.is_forced_size
    
    def set_is_forced_size(self, is_forced_size):
        self.is_forced_size = is_forced_size
            
    def get_optimum_size(self):
        """Returns the ideal grid size for the words in the puzzle"""
        
        if math.pow(self.longest_word + 2, 2) > self.total_letters * 1.2:
            return self.longest_word + 2
        else:
            return int(math.sqrt(self.total_letters * 1.2)) + 1

    def get_title(self):
        return self.title
    
    def set_title(self, title):
        self.title = title
        
    def get_narrative(self):
        return self.narrative
    
    def set_narrative(self, narrative):
        self.narrative = narrative
    
    def draw_as_text(self, show_solution, show_title, show_grid, show_words):
        """Returns puzzle as a string for subsequent export"""
        
        #Add the puzle title and narrative if required
        exported_text = ""
        if self.get_title() and show_title:
            exported_text = self.get_title()
            exported_text += "\n"
            exported_text += "=" * len(self.get_title())
            exported_text += "\n\n"

        if self.get_narrative() and show_title:
            exported_text += self.get_narrative()
            exported_text += "\n\n"
            
        #Export the puzzle grid if required
        if show_grid:
            cells_x, cells_y = self.grid.get_grid_size()
            for y in range(0, cells_y):
                for x in range(0, cells_x):
                    exported_text += self.grid.get_cell(x, y, "both") + " "
                exported_text = exported_text.strip()
                exported_text += "\n"
            exported_text += "\n"
        
        #Export the wordlist if required
        if show_words:
            for word in self.get_wordlist():
                exported_text += word.get_clue()
                if show_solution:
                    exported_text += '('
                    if word.get_clue() != word.get_word():
                        exported_text += word.get_word()
                    word_location_x, word_location_y = word.get_coordinates()
                    if word_location_x is not None and word_location_y is not None:
                        exported_text += str(word_location_x + 1) + "," + str(word_location_y + 1)
                    else:
                        exported_text += "unplaced"
                    exported_text += ")"
                exported_text += "\n"
        return exported_text
    
    def draw_as_cairo(self, surface, start_x, start_y, size_x, size_y, dpi,
                      show_solution = True, selected_word = None, 
                      show_title = True, show_grid = True, show_words = True):
        """Draws the entire puzzle onto the Cairo surface.  dpi specifies the number of pixels per inch"""
        
        #Cairo assumes that a pixel is a point, but that's not true for all all of our surfaces.  We calculate
        #a scale to allow us to convert points to pixels.  72 points = 1 inch
        scale = dpi / 72
        surface.set_source_rgb(0, 0, 0)
        y_position = start_y
        drawn_grid = False
        surface.move_to(start_x, start_y)
        
        #Relative size of displayed components compared with grid letters and word list
        BASE_FONT_POINTS = 16
        TITLE_SCALE = 1.4
        NARRATIVE_SCALE = 0.8
        GRID_CELL_SCALE = 2.0
        SPACING_SCALE = 0.3
        
        #Estimate the total number of lines in the output to determine whether the bas font is too large
        estimated_lines = 0
        if self.get_title() and show_title:
            #Assume the title will fit on one line
            estimated_lines += TITLE_SCALE + SPACING_SCALE
        if self.get_narrative() and show_title:
            #crudely assume that we fit 100 characters of narrative per line
            estimated_lines += NARRATIVE_SCALE * len(self.get_narrative()) / 100 + SPACING_SCALE
        if show_grid:
            estimated_lines += self.grid.get_grid_size()[1] * GRID_CELL_SCALE + SPACING_SCALE
        if show_words:
            #if we're tight for spce, we'l always use two columns for the word list
            estimated_lines += self.get_word_count() / 2
        estimated_lines = max(estimated_lines, 1)
        #size in points of grid letters and word list.  The 1.2 is a fudge to allow for the font's
        #ascenders and descenders
        base_font_size = min(BASE_FONT_POINTS * scale, size_y / estimated_lines / 1.2)
        
        #Draw the title if required
        if self.get_title() and show_title:
            font_description = pango.FontDescription()
            font_description.set_family("Sans,Arial,Helvetica")
            font_description.set_size(int(base_font_size * TITLE_SCALE * pango.SCALE))
            font_description.set_weight(pango.WEIGHT_BOLD)
            
            #Create cairo context and create text layout
            title_context = pangocairo.CairoContext( surface )
            title_layout = title_context.create_layout()
            title_layout.set_width(size_x * pango.SCALE)
            title_layout.set_justify(False)
            title_layout.set_alignment(pango.ALIGN_CENTER)
            title_layout.set_wrap(pango.WRAP_WORD_CHAR)
            title_layout.set_font_description(font_description)
            title_layout.set_text( self.get_title() )
            title_context.show_layout( title_layout )
            y_position += title_layout.get_pixel_extents()[1][3]
            y_position += base_font_size * SPACING_SCALE
        
        #Draw the narrative if required
        if self.get_narrative() and show_title:
            #Set up the narrrative font
            font_description = pango.FontDescription()
            font_description.set_family("Sans,Arial,Helvetica")
            font_description.set_size(int(base_font_size * NARRATIVE_SCALE * pango.SCALE))
            font_description.set_weight(pango.WEIGHT_NORMAL)
            
            #Create cairo context and create text layout
            narrative_context = pangocairo.CairoContext( surface )
            narrative_layout = narrative_context.create_layout()
            narrative_layout.set_width(size_x * pango.SCALE)
            narrative_layout.set_justify(False)
            narrative_layout.set_alignment(pango.ALIGN_LEFT)
            narrative_layout.set_wrap(pango.WRAP_WORD_CHAR)
            narrative_layout.set_font_description(font_description)
            narrative_layout.set_text( self.get_narrative() )
            
            #Display the narrative
            narrative_context.move_to(start_x, y_position)
            narrative_context.show_layout( narrative_layout )
            y_position += narrative_layout.get_pixel_extents()[1][3]
            y_position += base_font_size * SPACING_SCALE
                
        #Draw the puzzle grid
        if show_grid:
            grid_letters_x, grid_letters_y = self.grid.get_grid_size()
            if show_words:
                word_count = self.get_word_count()
            else:
                word_count = 0
            #Decide how much space to allocate to the grid
            grid_ratio = float(grid_letters_y * GRID_CELL_SCALE / (grid_letters_y * GRID_CELL_SCALE + word_count / 2.0))
            grid_size_y = int((size_y + start_y - y_position) * grid_ratio)
            grid_size_y = self.grid.draw_as_cairo(surface
                                        , start_x, y_position
                                        , size_x, grid_size_y
                                        , show_solution
                                        , selected_word
                                        , base_font_size * GRID_CELL_SCALE)
            y_position += grid_size_y + base_font_size * SPACING_SCALE
        word_list_start_y = y_position
        word_list_start_x = start_x
        
        #Draw the list of words if required
        if show_words:
            #Set the wordlist font up
            wordlist_font_size = base_font_size
            font_description = pango.FontDescription()
            font_description.set_family("Sans,Arial,Helvetica")
            font_description.set_size(int(pango.SCALE * wordlist_font_size))
            font_description.set_weight(pango.WEIGHT_NORMAL)
            surface.set_source_rgb(0, 0, 0)
            wordlist_font_size = base_font_size
            
            #Create cairo context and create text layout
            column_width = int(size_x / 2)
            wordlist_margin = base_font_size * SPACING_SCALE
            wordlist_context = pangocairo.CairoContext( surface )
            wordlist_layout = wordlist_context.create_layout()
            wordlist_layout.set_width(int((column_width - wordlist_margin) * pango.SCALE))
            wordlist_layout.set_justify(False)
            wordlist_layout.set_alignment(pango.ALIGN_LEFT)
            wordlist_layout.set_wrap(pango.WRAP_WORD_CHAR)
            wordlist_layout.set_font_description(font_description)
            
            #Establish whether we need to shrink the font.  We add 1px to the font height because that's sometimes used by Pango
            #when it lays out the font
            font_metrics = wordlist_layout.get_context().get_metrics(font_description)
            font_height = 1 + (font_metrics.get_ascent() + font_metrics.get_descent()) / pango.SCALE
            available_space = size_y + start_y - y_position
            words_per_column = int((self.get_word_count() + 1) / 2)
            if words_per_column * font_height > available_space:
                wordlist_font_size = available_space * 2 / self.get_word_count() * base_font_size / font_height
                font_description.set_size(int(pango.SCALE * wordlist_font_size))
                wordlist_layout.set_font_description(font_description)
                font_metrics = wordlist_layout.get_context().get_metrics(font_description)
                font_height = 1 + (font_metrics.get_ascent() + font_metrics.get_descent()) / pango.SCALE
                
            #Due to rounding (displayed fonts are always an exact number of pixels), further shrinkage might be necessary:
            while words_per_column * font_height > available_space:
                wordlist_font_size += -(100.0 / pango.SCALE)
                font_description.set_size(int(pango.SCALE * wordlist_font_size))
                wordlist_layout.set_font_description(font_description)
                font_metrics = wordlist_layout.get_context().get_metrics(font_description)
                font_height = 1 + (font_metrics.get_ascent() + font_metrics.get_descent()) / pango.SCALE
                            
            #Display the wordlist
            i = 0
            for word in self.get_wordlist():
                display_text = word.get_clue()
                if show_solution and word.get_clue() != word.get_word():
                    display_text += " (" + word.get_word() + ")"
                wordlist_layout.set_text( display_text )
                wordlist_context.move_to(word_list_start_x, y_position)
                wordlist_context.show_layout( wordlist_layout )
                y_position += wordlist_layout.get_pixel_extents()[1][3]
                i += 1
                if i == words_per_column:
                    #Start a new column
                    word_list_start_x += column_width
                    y_position = word_list_start_y


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