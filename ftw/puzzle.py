
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

import copy
import math
import pango
import pangocairo
from ftw.grid import Grid
from ftw.word import Word


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
