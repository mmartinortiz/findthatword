#!/usr/bin/env python

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

APP_NAME = "FindThatWord"
APP_VERSION = '0.1'
FILE_EXT = "ftw"
COPYRIGHT = 'Copyright Jonny Jones and Ieuan Jones 2009'
AUTHORS = ['Jonny Jones','Ieuan Jones']

import sys
try:
    import pygtk
    import gtk
    a = gtk.check_version(2, 10, 0)
    if a:
        print a
        sys.exit(1)
except:
    print "Please install pyGTK version 2.10 or later"
    sys.exit(1)
try:
    import time
    import datetime
    import gtk.glade
    import cairo
    import pango
    import pangocairo
    import gobject
    import os
    import cPickle
    from ftw.puzzle import *
except ImportError, error_message:
    error_dialog = gtk.MessageDialog(None
                      , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                      , gtk.MESSAGE_ERROR
                      , gtk.BUTTONS_CLOSE,
                      "Cannot start FindThatWord")
    error_dialog.format_secondary_text(str(error_message) + "\nPlease install the missing modules")
    error_dialog.run()
    error_dialog.destroy()
    sys.exit(1)
#We silently drop support for the recent file manager if gnomevfs isn't installed, as
#it's hard to work wih URIs without it
try:
    import gnomevfs
    RECENT_CHOOSER = True
except:
    RECENT_CHOOSER = False


class FindThatWord():
    """GTK-based wordsearch puzzle"""
    
    def __init__(self):
        """initialise a new puzzle"""
        
        #Set the environment variables and default display settings
        self.local_path = os.path.realpath(os.path.dirname(sys.argv[0]))
        self.gladefile = os.path.join(self.local_path, 'assets', "findthatword.glade")
        self.show_title = True
        self.show_grid = True
        self.show_words = True
        self.show_solution = True
        
        #Initialise the Glade GUI environment
        self.widget_tree = gtk.glade.XML(self.gladefile, "MainWindow")
        self.widget_tree.signal_autoconnect(self)
        self.main_window = self.widget_tree.get_widget("MainWindow")
        
        #Draw the icon.  Unofortunately, not all operating systems can accept SVGs
        if os.name == 'posix':
            icon_file = os.path.join(self.local_path, 'assets', "ftw_small.svg")
            self.main_window.set_icon_from_file(icon_file)
        else:
            icon_file = os.path.join(self.local_path, 'assets' "ftw_small.ico")
            self.main_window.set_icon_from_file(icon_file)
            
        #Disable printing support on Windows - the GTK page setup dialogue doesn't
        #work so the printed puzzle is incorrectly scaled to the page
        if os.name == 'nt' or os.name == 'ce':
            self.widget_tree.get_widget("PrintIcon").hide()
            self.widget_tree.get_widget("FilePageSetupMenuItem").hide()
            self.widget_tree.get_widget("FilePrintMenuItem").hide()
            self.widget_tree.get_widget("separatormenuitem2").hide()
        
        #Setup the Recent Files menu if the modules are available
        recent_widget = self.widget_tree.get_widget("FileRecentMenuItem")
        if RECENT_CHOOSER:
            recent_manager = gtk.recent_manager_get_default()
            recent_chooser = gtk.RecentChooserMenu(recent_manager)
            recent_filter = gtk.RecentFilter()
            recent_filter.add_pattern("*.ftw")
            recent_chooser.add_filter(recent_filter)
            recent_chooser.set_show_not_found(False)
            recent_chooser.connect("item-activated", self.on_RecentChooser_activate)
            recent_widget.set_submenu(recent_chooser)
        else:
            recent_widget.hide()

        #Create a permanent reference to frequently used widgets
        self.new_word_entry_widget = self.widget_tree.get_widget("NewWordEntry")
        self.new_description_entry_widget = self.widget_tree.get_widget("NewDescriptionEntry")
        self.words_view_widget = self.widget_tree.get_widget("WordsView")
                
        #Initialise the WordsView widget
        for i in range(0, 2):
            column = gtk.TreeViewColumn("Word", gtk.CellRendererText(), text = i)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_FIXED)
            self.words_view_widget.append_column(column)
            column.set_sizing(gtk.TREE_VIEW_COLUMN_AUTOSIZE)
        self.words_list = gtk.ListStore(gobject.TYPE_STRING, gobject.TYPE_STRING)
        self.words_view_widget.set_model(self.words_list)
        self.words_view_widget_selection = self.words_view_widget.get_selection()
        
        #Manually connect signals where Glade provides no options
        self.widget_tree.get_widget("NarrativeEntry").get_buffer().connect("changed", self.on_NarrativeWidget_changed)
        self.words_view_widget_selection.connect('changed', self.on_WordsListWidgetSelection_changed)
        
        #Initialise print settings
        self.print_settings = None
        self.print_settings = gtk.PrintSettings()
        self.page_setup = gtk.PageSetup()
        
        #Create and display a new puzzle
        self.dirty = False
        
        #Let's celelebrate being Welsh
        if datetime.date.today().month == 3 and datetime.date.today().day == 1:
            self.st_davids_day = True
        else:
            self.st_davids_day = False
        self.new_puzzle()

        #Find the name of a file passed on the command line
        if len(sys.argv) >= 2:
            self.load_file(sys.argv[len(sys.argv) - 1], "Filename")
                
    def new_puzzle(self):
        """Start a new puzzle"""
        #Instantiate a new puzzle object
        self.puzzle = Puzzle()
        self.filename = None
        self.uri = None
        self.set_dirty(False)
        self.set_edit_mode(False)
        #Clean up the remnants of any previous puzzles still displayed on screen
        self.words_view_widget_selection.unselect_all()
        self.new_word_entry_widget.set_text("")
        self.new_description_entry_widget.set_text("")
        self.update_all_widgets()
        self.set_dirty(False)
        
        #Let's celebrate being Welsh
        if self.st_davids_day:
            stdavids_filename = os.path.join(self.local_path, 'assets', "stdavids.ftw")
            self.load_file(stdavids_filename, "File")
            self.st_davids_day = False
           
    
    """
    ***********************************************************
    *                                                         *
    * Functions to redraw screen widgets                      *
    *                                                         *
    ***********************************************************
    """
    
    def update_all_widgets(self):
        """Redraw all widgets on screen.  This has the effect of making
        the puzzle dirty"""
        #Look up widgets
        puzzle_title_entry_widget = self.widget_tree.get_widget("PuzzleTitleEntry")
        narrative_entry_widget = self.widget_tree.get_widget("NarrativeEntry")
        hidden_message_check_button_widget = self.widget_tree.get_widget("HiddenMessageCheckButton")
        hidden_message_entry_widget = self.widget_tree.get_widget("HiddenMessageEntry")
        force_size_check_button_widget = self.widget_tree.get_widget("ForceSizeCheckButton")
        x_spin_widget = self.widget_tree.get_widget("xSpin")
        y_spin_widget = self.widget_tree.get_widget("ySpin")
        results_area_widget = self.widget_tree.get_widget("ResultsAreaCairo")
        #Update all widgets in turn
        self.update_window_title()
        self.update_save_icons()
        self.update_results_area_aspect_frame()
        puzzle_title_entry_widget.set_text(self.puzzle.get_title())
        narrative_entry_widget.get_buffer().set_text(self.puzzle.get_narrative())
        self.update_add_button()
        hidden_message_entry_widget.set_sensitive(True)
        hidden_message_entry_widget.set_text(self.puzzle.grid.padding)
        hidden_message_check_button_widget.set_active(not self.puzzle.grid.random_padding)
        self.update_hidden_message_widget()
        x_spin_widget.set_sensitive(True)
        y_spin_widget.set_sensitive(True)
        x_spin_widget.set_text(str(self.puzzle.force_x))
        y_spin_widget.set_text(str(self.puzzle.force_y))
        force_size_check_button_widget.set_active(self.puzzle.get_is_forced_size())
        self.update_grid_size_widget()
        self.update_ascending_button()
        self.on_WordsListWidgetSelection_changed(None)
        self.update_words_list()
        results_area_widget.queue_draw()
        
    def update_window_title(self):
        """Set the window title based on the filename and whether the file is dirty"""
        if self.dirty:
            displayed_title = "*"
        else:
            displayed_title = ""
        displayed_title += "Find That Word - "
        if self.filename:
            displayed_title += (os.path.basename(self.filename))
        else:
            displayed_title += "Untitled"
        self.main_window.set_title(displayed_title)

    def update_add_button(self):
        """Enable or disable the Add and Cancel buttons according to the contents of the
        new_word_entry_widget"""
        #Look up widgets
        add_button_widget = self.widget_tree.get_widget("AddButton")
        apply_button_widget = self.widget_tree.get_widget("ApplyButton")
        cancel_button_widget = self.widget_tree.get_widget("CancelButton")
        #Update the widgets by reference to the contents of the word entry widgets
        if self.edit_mode:
            relevant_button = apply_button_widget
        else:
            relevant_button = add_button_widget
        new_word = self.new_word_entry_widget.get_text()
        usable_characters = 0
        for letter in new_word:
            if letter.isalpha():
                usable_characters += 1
        if usable_characters >=1:
            relevant_button.set_sensitive(True)
            relevant_button.grab_default()
        else:
            relevant_button.set_sensitive(False)
        if new_word or self.new_description_entry_widget.get_text():
            cancel_button_widget.set_sensitive(True)
        else:
            cancel_button_widget.set_sensitive(False)
    
    def update_words_list(self):
        """Redraw the Words_list widget by recreating the associated data model"""
        self.words_list.clear()
        for word in self.puzzle.get_wordlist():
            if word.get_word() == word.get_clue():
                self.words_list.append( [word.get_word(), ""] )
            else:
                self.words_list.append( [word.get_word(), word.get_clue()] )
                
    def update_ascending_button(self):
        """Enables or disables the sort button based on the number of words in the puzzle"""
        ascending_button_widget = self.widget_tree.get_widget("AscendingButton")
        if len(self.puzzle.get_wordlist()) >= 2:
            ascending_button_widget.set_sensitive(True)
        else:
            ascending_button_widget.set_sensitive(False)
            
    def update_results_widget(self):
        """Redraw the puzzle output"""          
        self.draw_as_widget()
       
    def update_hidden_message_widget(self):
        """Enable / disable the hidden message widget"""
        hidden_message_check_button_widget = self.widget_tree.get_widget("HiddenMessageCheckButton")
        hidden_message_entry_widget = self.widget_tree.get_widget("HiddenMessageEntry")
        if hidden_message_check_button_widget.get_active():
            hidden_message_entry_widget.set_sensitive(True)
        else:
            hidden_message_entry_widget.set_sensitive(False)

    def update_grid_size_widget(self):
        """Enable / disable the grid size spinners"""
        x_spin_widget = self.widget_tree.get_widget("xSpin")
        y_spin_widget = self.widget_tree.get_widget("ySpin")
        if self.puzzle.get_is_forced_size():
            x_spin_widget.set_sensitive(True)
            y_spin_widget.set_sensitive(True)
        else:
            x_spin_widget.set_sensitive(False)
            y_spin_widget.set_sensitive(False)
            
    def update_save_icons(self):
        """Disable the Save icons if the puzzle isn't dirty"""
        #Look up the widget references
        file_save_menu_item_widget = self.widget_tree.get_widget("FileSaveMenuItem")
        save_icon_widget = self.widget_tree.get_widget("SaveIcon")
        #Enable / disable as required
        if self.dirty:
            save_icon_widget.set_sensitive(True)
            file_save_menu_item_widget.set_sensitive(True)
        else:
            save_icon_widget.set_sensitive(False)
            file_save_menu_item_widget.set_sensitive(False)
        
    def update_results_area_aspect_frame(self):
        """Updates the aspect ratio of the results area"""
        paper_height = self.page_setup.get_page_height(gtk.UNIT_MM)
        paper_width = self.page_setup.get_page_width(gtk.UNIT_MM)
        ratio = paper_width / paper_height
        self.widget_tree.get_widget("ResultsAreaAspectFrame").set(0.5, 0.5, ratio, False)
            
    def display_failure(self):
        """Display warning that puzzle could not be completed"""
        msg_dialog = gtk.MessageDialog(self.main_window
                          , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                          , gtk.MESSAGE_WARNING
                          , gtk.BUTTONS_CLOSE,
                          "Error creating puzzle")
        msg_dialog.format_secondary_text("It was not possible to fit all the words in the puzzle grid.  Try a larger grid size.")
        response = msg_dialog.run()
        msg_dialog.destroy()
        return response == gtk.RESPONSE_YES
         
    def set_edit_mode(self, edit_mode):
        """Edit mode indicates that a word in the wordlist is being edited"""
        #Look up widgets
        add_button_widget = self.widget_tree.get_widget("AddButton")
        apply_button_widget = self.widget_tree.get_widget("ApplyButton")
        self.edit_mode = edit_mode
        if edit_mode:
            add_button_widget.hide()
            apply_button_widget.show()
        else:
            add_button_widget.show()
            apply_button_widget.hide()
        
    """
    ***********************************************************
    *                                                         *
    * File handling functions                                 *
    *                                                         *
    ***********************************************************
    """
    def set_dirty(self, dirty):
        """Make the puzzle dirty or clean and update the title bar and
        save icons accordingly"""
        if not self.dirty and dirty:
            self.dirty_time = time.time()
        self.dirty = dirty
        self.update_window_title()
        self.update_save_icons()
        
    def set_filename(self, filename, uri, auto_extension = True):
        """Change the puzzle's filename and optionally correct the
        file extension"""
        self.filename = filename
        self.uri = uri
        if auto_extension and not filename[ -len(FILE_EXT) - 1 : ] == '.' + FILE_EXT:
            self.filename += "." + FILE_EXT
            if self.uri:
                self.uri += "." + FILE_EXT            
        #Add the file to the recently used file list
        if self.uri and RECENT_CHOOSER:
            gtk.recent_manager_get_default().add_item( self.uri )
        #Update the display
        self.update_window_title()

    def confirm_lose_changes(self):
        """Ask the user whether they really want to lose their changes.
        Returns True or False"""
        if self.dirty:
            msg_dialog = gtk.MessageDialog(self.main_window
                              , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                              , gtk.MESSAGE_WARNING
                              , gtk.BUTTONS_CANCEL,
                              "You have unsaved changes")
            elapsed_time = time.time() - self.dirty_time
            if elapsed_time < 120:
                time_message = str(int(elapsed_time)) + " seconds"
            elif elapsed_time < 120 * 60:
                time_message = str(int(elapsed_time / 60)) + " minutes"
            else:
                time_message = str(int(elapsed_time / 60 / 60)) + " hours"
            msg_dialog.format_secondary_text("If you continue, changes from the last " + time_message + " will be lost")
            msg_dialog.add_button("Discard Unsaved Work", gtk.RESPONSE_CLOSE)
            response = msg_dialog.run()
            msg_dialog.destroy()
            return response == gtk.RESPONSE_CLOSE
        else:
            return True
    
    def save_file_as(self):
        """Open a Save As dialogue and save the file"""
        #Initialise the dialog
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        chooser = gtk.FileChooserDialog("Save WordSearch", self.main_window, 
                                        gtk.FILE_CHOOSER_ACTION_SAVE, buttons)
        chooser.set_do_overwrite_confirmation(True)
        filter = gtk.FileFilter()
        filter.set_name("FindThatWord files")
        filter.add_pattern("*." + FILE_EXT)
        chooser.add_filter(filter)
        chooser.set_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        chooser.add_filter(filter)
        #Run the dialog
        if chooser.run() == gtk.RESPONSE_OK:
            #It's easier to create a new file using a filename than a URI, so we set the URI after it's been saved
            self.set_filename(chooser.get_filename(), None, True)
            self.save_file()
            self.set_filename(chooser.get_filename(), chooser.get_uri().strip(), True)
        chooser.destroy()
            
    def save_file(self):
        """Save the file.  The filename must already have been set"""
        try:
            file = cPickle.dumps(self.puzzle, cPickle.HIGHEST_PROTOCOL)
            if self.uri and RECENT_CHOOSER:
                #We know the file by its URI
                handler = gnomevfs.Handle(self.uri, gnomevfs.OPEN_WRITE)
            elif self.filename:
                #We know the file by its filename
                handler = open(self.filename, 'wb')
            handler.write(file)
            handler.close()
            self.set_dirty(False)
        except IOError, (error_number, error_message):
            error_dialog = gtk.MessageDialog(self.main_window
                              , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                              , gtk.MESSAGE_ERROR
                              , gtk.BUTTONS_CLOSE,
                              "Error saving file")
            error_dialog.format_secondary_text(error_message)
            error_dialog.run()
            error_dialog.destroy()
        except:
            error_dialog = gtk.MessageDialog(self.main_window
                              , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                              , gtk.MESSAGE_ERROR
                              , gtk.BUTTONS_CLOSE,
                              "Error saving file")
            error_dialog.format_secondary_text(self.filename)
            error_dialog.run()
            error_dialog.destroy()
            
    def export_file(self):
        """Open a Export dialogue and export the file in the format specified by the user"""
        #Initialise the dialog
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
                   gtk.STOCK_SAVE, gtk.RESPONSE_OK)
        chooser = gtk.FileChooserDialog("Export WordSearch", self.main_window, 
                                        gtk.FILE_CHOOSER_ACTION_SAVE, buttons)
        chooser.set_do_overwrite_confirmation(True)
        #Create the file filters
        filters = [["Adobe Acrobat", 'pdf'],
                   ["Portable network graphic", 'png'],
                   ["Scalable vector graphic", 'svg'],
                   ["Text", 'txt']]
        
        for filter in filters:
            new_filter = gtk.FileFilter()
            new_filter.set_name( filter[0] + ' (' + filter[1] + ')' )
            new_filter.add_pattern( filter[1] )
            new_filter.add_pattern( filter[1].upper() )
            chooser.add_filter( new_filter )
            if filter[1] == 'pdf':
                chooser.set_filter( new_filter )
        
        #Run the dialog
        if chooser.run() == gtk.RESPONSE_OK:
            #Export to the chosen format
            filename = chooser.get_filename()
            selected_filter = chooser.get_filter().get_name()
            if selected_filter == 'Adobe Acrobat (pdf)':
                if filename[-4:] != '.pdf':
                    filename += ".pdf"
                self.draw_as_pdf(filename)
            elif selected_filter == 'Portable network graphic (png)':
                if filename[-4:] != '.png':
                    filename += ".png"
                self.draw_as_png(filename)
            elif selected_filter == 'Scalable vector graphic (svg)':
                if filename[-4:] != '.svg':
                    filename += ".svg"
                self.draw_as_svg(filename)
            elif selected_filter == 'Text (txt)':
                if filename[-4:] != '.txt':
                    filename += ".txt"
                self.draw_as_text(filename)
        chooser.destroy()

    def load_file(self, filename, type = "URI"):
        """Opens the FTW file with a the supplied URI or filename and returns True if successful.  We
        prefer to work with URIs than files, as they're easier to add to the recent file list.  In the
        interests of simplicity, we only add URIs to the recent file list"""
        self.set_dirty("clean")
        try:
            if type == "URI" and RECENT_CHOOSER:
                handler = gnomevfs.Handle( filename )
                file_size = handler.get_file_info().size
                new_file = handler.read(file_size)
                self.puzzle = cPickle.loads(new_file)
                handler.close()
                #make a crude guess at a sensible filename from the URI
                uri = filename
                filename = uri[ uri.find(':///') + 4 : ]
                self.set_filename(filename, uri, False)
            else:
                file = open(filename, 'rb')
                self.puzzle = cPickle.load(file)
                self.set_filename(filename, None, False)
                file.close()
            self.puzzle.grid.puzzle = self.puzzle
            #Update the display
            self.update_all_widgets()
            self.set_dirty(False)
            return True
        except:
            #Loading the file failed in some way or another
            error_dialog = gtk.MessageDialog(self.main_window
                              , gtk.DIALOG_MODAL | gtk.DIALOG_DESTROY_WITH_PARENT
                              , gtk.MESSAGE_ERROR
                              , gtk.BUTTONS_CLOSE,
                              "Unable to open file" )
            error_dialog.format_secondary_text(filename)
            error_dialog.run()
            error_dialog.destroy()
            return False

    def open_file_with_dialog(self):
        """Open an Open dialogue and opens the selected file"""
        
        self.set_edit_mode(False)
        #Initialise the dialog
        buttons = (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL, gtk.STOCK_OPEN, gtk.RESPONSE_OK)
        chooser = gtk.FileChooserDialog("Open WordSearch", self.main_window, 
                                        gtk.FILE_CHOOSER_ACTION_OPEN, buttons)
        filter = gtk.FileFilter()
        #Create the file filters
        filter.set_name("FindThatWord files")
        filter.add_pattern("*." + FILE_EXT)
        chooser.add_filter(filter)
        filter2 = gtk.FileFilter()
        filter2.set_name("All files")
        filter2.add_pattern("*")
        chooser.add_filter(filter2)
        chooser.set_filter(filter)
        #Set the default directory
        if self.filename:
            chooser.set_filename(self.filename)
        #Run the dialog
        if chooser.run() == gtk.RESPONSE_OK:
            #Not all platforms can handle URIs...
            if RECENT_CHOOSER:
                new_uri = chooser.get_uri()
                if self.load_file(new_uri, "URI"):
                    self.set_filename( chooser.get_filename(), new_uri, False )
            else:
                new_filename = chooser.get_filename()
                if self.load_file(new_filename, "Filename"):
                    self.set_filename( chooser.get_filename(), None, False )
            chooser.destroy()
            return True
        else:
            chooser.destroy()
            return None

    """
    ***********************************************************
    *                                                         *
    * Rendering functions                                 *
    *                                                         *
    ***********************************************************
    """
    def draw_as_png(self, filename):
        """Write a PNG containing the puzzle to filname"""
        #create a cairo context.  Cairo PNGs have no page size information, so we'll assume 200 pixels per inch
        dpi = 300
        paper_width = int( dpi * self.page_setup.get_paper_width(gtk.UNIT_INCH) )
        paper_height = int( dpi * self.page_setup.get_paper_height(gtk.UNIT_INCH) )
        margin_top = int( dpi * self.page_setup.get_top_margin(gtk.UNIT_INCH) )
        margin_right = int( dpi * self.page_setup.get_right_margin(gtk.UNIT_INCH) )
        margin_bottom = int( dpi * self.page_setup.get_bottom_margin(gtk.UNIT_INCH) )
        margin_left = int( dpi * self.page_setup.get_left_margin(gtk.UNIT_INCH) )
        surface = cairo.ImageSurface(cairo.FORMAT_RGB24, paper_width, paper_height)
        result_area = cairo.Context( surface )
        #Draw the puzzle
        self.draw_as_cairo(result_area, paper_width, paper_height, margin_top, margin_right, margin_bottom, margin_left, dpi, False)
        surface.write_to_png(filename)
    
    def draw_as_pdf(self, filename):
        """Write a PDF containing the puzzle to filname"""
        #create a cairo context.  Cairo PDF surfaces work in Points (72 Points = 1 inch)
        ppi = 72
        paper_width = int( ppi * self.page_setup.get_paper_width(gtk.UNIT_INCH) )
        paper_height = int( ppi * self.page_setup.get_paper_height(gtk.UNIT_INCH) )
        margin_top = int( ppi * self.page_setup.get_top_margin(gtk.UNIT_INCH) )
        margin_right = int( ppi * self.page_setup.get_right_margin(gtk.UNIT_INCH) )
        margin_bottom = int( ppi * self.page_setup.get_bottom_margin(gtk.UNIT_INCH) )
        margin_left = int( ppi * self.page_setup.get_left_margin(gtk.UNIT_INCH) )
        surface = cairo.PDFSurface(filename, paper_width, paper_height)
        result_area = cairo.Context( surface )
        #Draw the puzzle
        self.draw_as_cairo(result_area, paper_width, paper_height, margin_top, margin_right, margin_bottom, margin_left, ppi, False)
        surface.finish()
        
    def draw_as_svg(self, filename):
        """Write a PNG containing the puzzle to filname"""
        #create a cairo context.  Cairo SVG surfaces work in Points (72 Points = 1 inch)
        ppi = 72
        paper_width = int( ppi * self.page_setup.get_paper_width(gtk.UNIT_INCH) )
        paper_height = int( ppi * self.page_setup.get_paper_height(gtk.UNIT_INCH) )
        margin_top = int( ppi * self.page_setup.get_top_margin(gtk.UNIT_INCH) )
        margin_right = int( ppi * self.page_setup.get_right_margin(gtk.UNIT_INCH) )
        margin_bottom = int( ppi * self.page_setup.get_bottom_margin(gtk.UNIT_INCH) )
        margin_left = int( ppi * self.page_setup.get_left_margin(gtk.UNIT_INCH) )
        surface = cairo.SVGSurface(filename, paper_width, paper_height)
        result_area = cairo.Context( surface )
        #Draw the puzzle
        self.draw_as_cairo(result_area, paper_width, paper_height, margin_top, margin_right, margin_bottom, margin_left, ppi, False)
        surface.finish()
        
    def draw_as_text(self, filename):
        """Write a text stream containing the puzzle to filname"""
        result = self.puzzle.draw_as_text(self.show_solution, self.show_title, self.show_grid, self.show_words)
        export_file = open(filename, "w")
        export_file.write(result)
        export_file.close()

    def draw_as_widget(self):
        """Draw the puzzle onto the ResultsArea screen widget"""
        #create a cairo context and fill it with a white background
        results_area_cairo_widget = self.widget_tree.get_widget("ResultsAreaCairo")
        result_area = results_area_cairo_widget.window.cairo_create()
        result_size_x, result_size_y = results_area_cairo_widget.window.get_size()
        #Set the dimensions to scale to the page dimensions  The widget already has the correct aspect ratio
        paper_height = self.page_setup.get_paper_height(gtk.UNIT_INCH)
        paper_width = self.page_setup.get_paper_width(gtk.UNIT_INCH)
        dpi = result_size_y / paper_height
        margin_top = dpi * self.page_setup.get_top_margin(gtk.UNIT_INCH)
        margin_right = dpi * self.page_setup.get_right_margin(gtk.UNIT_INCH)
        margin_bottom = dpi * self.page_setup.get_bottom_margin(gtk.UNIT_INCH)
        margin_left = dpi * self.page_setup.get_left_margin(gtk.UNIT_INCH)
        #Draw the puzzle
        self.draw_as_cairo(result_area, result_size_x, result_size_y, margin_top, margin_right, margin_bottom, margin_left, dpi, True)

    def draw_as_cairo(self, surface, size_x, size_y, margin_top, margin_right, margin_bottom, margin_left, dpi, highlight_selected):
        """Draws the puzzle onto a cairo surface.  dpi is the number of desired pixels per 'inch' - on the screen, this is a 
        scaled inch that represents on inch on the final printed output"""
        surface.set_source_rgb(1, 1, 1)
        surface.rectangle(0, 0, size_x, size_y)
        surface.fill()
        #Find the selected word
        tree_model, iter = self.words_view_widget_selection.get_selected()
        if iter and highlight_selected:
            selected_row = int(tree_model.get_string_from_iter(iter))
            selected_word = self.puzzle.get_word(selected_row)
        else:
            selected_word = None
        #Display the results
        self.puzzle.draw_as_cairo(surface, 
                                  int(margin_top), int(margin_left),
                                  int(size_x - margin_left - margin_right), int(size_y - margin_top - margin_bottom),
                                  dpi,
                                  self.show_solution, selected_word, 
                                  self.show_title, self.show_grid, self.show_words)
    
    """
    ***********************************************************
    *                                                         *
    * Printing functions                                      *
    *                                                         *
    ***********************************************************
    """
    def draw_to_printer(self, print_operation, print_context, page_no):
        """Render the puzzle to the provided print surface"""
        #create a cairo context.  Cairo printer surfaces work in Points (72 Points = 1 inch)
        ppi = 72
        paper_width = int( ppi * self.page_setup.get_page_width(gtk.UNIT_INCH) )
        paper_height = int( ppi * self.page_setup.get_page_height(gtk.UNIT_INCH) )
        #Drawing is relative to the margins, so margins aren't required
        margin_top = 0
        margin_right = 0
        margin_bottom = 0
        margin_left = 0
        result_area = print_context.get_cairo_context()
        #Draw the puzzle
        self.draw_as_cairo(result_area, paper_width, paper_height, 0, 0, 0, 0, ppi, False)
    
    def show_print_dialogue(self):
        """Display a print dialogue box and print the puzzle"""
        
        print_operation = gtk.PrintOperation()
        if self.print_settings != None: 
            print_operation.set_print_settings(self.print_settings)
        print_operation.connect("draw_page", self.draw_to_printer)
        print_operation.set_n_pages(1)
        print_operation.set_default_page_setup(self.page_setup)
        print_result = print_operation.run(gtk.PRINT_OPERATION_ACTION_PRINT_DIALOG, self.main_window)
        if print_result == gtk.PRINT_OPERATION_RESULT_APPLY:
            settings = print_operation.get_print_settings()

    """
    ***********************************************************
    *                                                         *
    * Signal handlers                                         *
    *                                                         *
    ***********************************************************
    """
    def on_MainWindow_delete_event(self, widget, response):
        """Intercept main window closure if data is unsaved"""
        return not self.confirm_lose_changes()
        
    def on_MainWindow_destroy(self, widget):
        """Quit the main application"""
        gtk.main_quit()

    def on_FileQuitMenuItem_activate(self, widget):
        """Leave the application"""
        if self.confirm_lose_changes():
            gtk.main_quit()        
        
    def on_FileNewMenuItem_activate(self, widget):
        """File | New - Start a new project file, blank out
        the current project and start from scratch"""
        if self.confirm_lose_changes():
            self.new_puzzle()
            
    def on_RecentChooser_activate(self, widget):
        """Open a file from the recently used files list"""
        if self.confirm_lose_changes():
            self.load_file(widget.get_current_uri(), "URI")
        
    def on_FileOpenMenuItem_activate(self, widget):
        """File > Open menu item"""
        if self.confirm_lose_changes():
            self.open_file_with_dialog()

    def on_FileSaveMenuItem_activate(self, widget):
        """File > Save menu item"""
        if self.filename:
            self.save_file()
        else:
            self.save_file_as()

    def on_FileSaveAsMenuItem_activate(self, widget):
        """File > Save As menu item"""
        self.save_file_as()
    
    def on_FileExportMenuItem_activate(self, widget):
        """File > Export menu item"""
        self.export_file()
        
    def on_FilePageSetupMenuItem_activate(self, widget):
        """File > Page setup menmu item"""
        self.page_setup = gtk.print_run_page_setup_dialog(self.main_window,
                                                     self.page_setup, 
                                                     self.print_settings)
        self.update_results_area_aspect_frame()
        
    def on_FilePrintMenuItem_activate(self, widget):
        self.show_print_dialogue()        

    def on_HelpAboutMenuItem_activate(self, widget):
        """Help > About Menu Item"""
        about_dialog = gtk.AboutDialog()
        about_dialog.set_name(APP_NAME)
        about_dialog.set_version(APP_VERSION)
        about_dialog.set_copyright(COPYRIGHT)
        licence_filename = os.path.join(self.local_path, "COPYING")
        licence_file = open(licence_filename,"r")
        licence = licence_file.read()
        licence_file.close()
        about_dialog.set_license(licence)
        about_dialog.set_comments("A program for making wordsearches")
        about_dialog.set_authors(AUTHORS)
        about_dialog.set_program_name(APP_NAME)
        about_dialog.run()
        about_dialog.destroy()
    
    def on_NewIcon_clicked(self, widget):
        """New icon clicked"""
        if self.confirm_lose_changes():
            self.new_puzzle()

    def on_OpenIcon_clicked(self, widget):
        """Open icon clicked"""
        self.on_FileOpenMenuItem_activate(widget)
        
    def on_SaveIcon_clicked(self, widget):
        """Save icon clicked"""
        self.on_FileSaveMenuItem_activate(widget)
    
    def on_RefreshIcon_clicked(self, widget):
        """Refresh icon clicked"""
        if not self.puzzle.populate_grid():
            self.display_failure()
        self.set_dirty(True)
        self.update_results_widget()
        
    def on_ExportIcon_clicked(self, widget):
        self.export_file()
        
    def on_PrintIcon_clicked(self, widget):
        """Print icon clicked"""
        self.show_print_dialogue()

    def on_PuzzleTitleEntry_changed(self, widget):
        """Change made to puzzle title"""
        self.puzzle.set_title( widget.get_text() )
        self.update_results_widget()
        self.set_dirty(True)
        
    def on_NarrativeWidget_changed(self, widget):
        """Change made to puzzle narrative"""
        start = widget.get_start_iter()
        end = widget.get_end_iter()
        self.puzzle.set_narrative( widget.get_text(start, end) )
        self.update_results_widget()
        self.set_dirty(True)
        
    def on_WordsListWidgetSelection_changed(self, widget):
        """New word selected in the wordlist widget"""
        #Look up widgets
        edit_button_widget = self.widget_tree.get_widget("EditButton")
        delete_button_widget = self.widget_tree.get_widget("DeleteButton")
        move_up_button_widget = self.widget_tree.get_widget("MoveUpButton")
        move_down_button_widget = self.widget_tree.get_widget("MoveDownButton")
        
        tree_model, iter = self.words_view_widget_selection.get_selected()
        if iter is None:
            #No word has been selected; hide various buttons
            edit_button_widget.set_sensitive(False)
            delete_button_widget.set_sensitive(False)
            move_up_button_widget.set_sensitive(False)
            move_down_button_widget.set_sensitive(False)
        else:
            #A word has been selected.  Enable / disable buttons according
            #to whether it's the first, last or middle word in the list
            selected_row = int(tree_model.get_string_from_iter(iter))
            edit_button_widget.set_sensitive(True)
            delete_button_widget.set_sensitive(True)
            if self.puzzle.get_word_count() < 2:
                move_up_button_widget.set_sensitive(False)
                move_down_button_widget.set_sensitive(False)
            elif selected_row == 0:
                move_up_button_widget.set_sensitive(False)
                move_down_button_widget.set_sensitive(True)
            elif selected_row == self.puzzle.get_word_count() - 1:
                move_up_button_widget.set_sensitive(True)
                move_down_button_widget.set_sensitive(False)
            else:
                move_up_button_widget.set_sensitive(True)
                move_down_button_widget.set_sensitive(True)
            #Now redraw the grid to change the colour of the selected word
            self.draw_as_widget()
    
    def on_EditButton_clicked(self, widget):
        """Edit a word that already exists in the puzzle"""
        tree_model, iter = self.words_view_widget_selection.get_selected()
        selected_row = int(tree_model.get_string_from_iter(iter))
        self.edited_word = self.puzzle.get_word(selected_row)
        self.set_edit_mode(True)
        old_word = self.edited_word.get_word()
        old_description = self.edited_word.get_clue()
        self.new_word_entry_widget.set_text(old_word)
        if old_word <> old_description:
            self.new_description_entry_widget.set_text(old_description)
        
    def on_DeleteButton_clicked(self, widget):
        """Delete a word from the puzzle"""
        tree_model, iter = self.words_view_widget_selection.get_selected()
        selected_row = int(tree_model.get_string_from_iter(iter))
        if self.edit_mode and self.puzzle.get_word(selected_row) == self.edited_word:
            #Deal with deleting the word that's currently being edited, 
            self.set_edit_mode(False)
        self.puzzle.delete_word(selected_row)
        tree_model.remove(iter)
        self.update_results_widget()
        self.update_ascending_button()
        self.set_dirty(True)
        
    def on_MoveUpButton_clicked(self, widget):
        """Move a word up in the puzzle"""
        tree_model, iter = self.words_view_widget_selection.get_selected()
        selected_row = int(tree_model.get_string_from_iter(iter))
        self.puzzle.move_word_up(selected_row)
        self.update_words_list()
        self.update_results_widget()
        self.set_dirty(True)
        #reinstate the selection
        self.words_view_widget_selection.select_iter(tree_model.get_iter(selected_row - 1))

    def on_MoveDownButton_clicked(self, widget):
        """Move a word down in the puzzle"""
        tree_model, iter = self.words_view_widget_selection.get_selected()
        selected_row = int(tree_model.get_string_from_iter(iter))
        self.puzzle.move_word_up(selected_row + 1)
        self.update_words_list()
        self.update_results_widget()
        self.set_dirty(True)
        #reinstate the selection
        self.words_view_widget_selection.select_iter(tree_model.get_iter(selected_row + 1))

    def on_AscendingButton_clicked(self, widget):
        """Sort the puzzle words alphabetically"""
        self.puzzle.sort_wordlist()
        self.update_words_list()
        self.update_results_widget()
        self.set_dirty(True)
    
    def on_NewWordEntry_changed(self, widget):
        """Enable / disable the Add / Update buttons according to the newly typed word"""
        self.update_add_button()

    def on_NewDescriptionEntry_changed(self, widget):
        """Enable / disable the Add / Update buttons according to the newly typed word"""
        self.update_add_button()
        
    def on_AddButton_clicked(self, widget):
        """Add a word to the puzzle"""
        #Get the data from the GUI
        new_word = self.new_word_entry_widget.get_text()
        description = self.new_description_entry_widget.get_text()
        #Add it to the puzzle
        if not self.puzzle.add_word(new_word, description):
            self.display_failure()
        self.new_word_entry_widget.set_text("")
        self.new_description_entry_widget.set_text("")
        self.update_words_list()
        self.update_results_widget()
        self.update_ascending_button()
        self.set_dirty(True)
        
    def on_ApplyButton_clicked(self, widget):
        """Update the word being edited"""
        #Get the data from the GUI
        new_word = self.new_word_entry_widget.get_text()
        description = self.new_description_entry_widget.get_text()
        if not self.edited_word.update(new_word, description):
            self.display_failure()
        #Clear out evidence of the editing process
        self.set_edit_mode(False)
        self.new_word_entry_widget.set_text("")
        self.new_description_entry_widget.set_text("")
        #And display the results
        self.update_words_list()
        self.update_results_widget()
        self.set_dirty(True)
    
    def on_CancelButton_clicked(self, widget):
        """Cancel editing the word"""
        self.set_edit_mode(False)
        self.new_word_entry_widget.set_text("")
        self.new_description_entry_widget.set_text("")
    
    def on_HiddenMessageCheckButton_toggled(self, widget):
        """Toggle the hidden message option"""
        self.puzzle.grid.random_padding = not widget.get_active()
        self.update_hidden_message_widget()
        self.on_HiddenMessageEntry_changed(widget)
        self.set_dirty(True)
        
    def on_HiddenMessageEntry_changed(self, widget):
        """Update the hidden message"""
        self.puzzle.grid.padding = self.widget_tree.get_widget("HiddenMessageEntry").get_text()
        self.puzzle.grid.add_padding()
        self.update_results_widget()
        self.set_dirty(True)
                    
    def on_ForceSizeCheckButton_toggled(self, widget):
        """Toggle the forced-size option and resize as appropriate"""
        self.puzzle.set_is_forced_size(widget.get_active())
        self.widget_tree.get_widget("xSpin").set_text(str(self.puzzle.force_x))
        self.widget_tree.get_widget("ySpin").set_text(str(self.puzzle.force_y))
        self.update_grid_size_widget()
        if not self.puzzle.resize_grid():
            self.display_failure()
        self.update_results_widget()
        self.set_dirty(True)
    
    def on_ShowTitleCheckButton_toggled(self, widget):
        """Toggle the show entire solution option and print if its working"""
        self.show_title = widget.get_active()
        self.update_results_widget()
    
    def on_ShowGridCheckButton_toggled(self, widget):
        """Toggle the show entire solution option and print if its working"""
        self.show_grid = widget.get_active()
        self.update_results_widget()
    
    def on_ShowWordlistCheckButton_toggled(self, widget):
        """Toggle the show entire solution option and print if its working"""
        self.show_words = widget.get_active()
        self.update_results_widget()
    
    def on_ShowSolutionCheckButton_toggled(self, widget):
        """Toggle the show solution options and print if its working"""
        self.show_solution = widget.get_active()
        self.update_results_widget()
    
    def on_xSpin_output(self, widget):
        """Increase or decrease the puzzle's forced width"""
        try:
            self.puzzle.force_x = widget.get_value_as_int()
        except:
            self.puzzle.force_x = 2
        if not self.puzzle.resize_grid():
            self.display_failure()
        self.update_results_widget()
        self.set_dirty(True)

    def on_ySpin_output(self, widget):
        """Increase or decrease the puzzle's forced height"""
        try:
            self.puzzle.force_y = widget.get_value_as_int()
        except:
            self.puzzle.force_y = 2
        if not self.puzzle.resize_grid():
            self.display_failure()
        self.update_results_widget()
        self.set_dirty(True)
        
    def on_ResultsArea_expose_event(self, widget, signal):
        """Draw the puzzle"""
        self.update_results_widget()
        
"""
***********************************************************
*                                                         *
* Main Loop                                               *
*                                                         *
***********************************************************
"""
if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[len(sys.argv) - 1] == "--help":
        print APP_NAME + " " + APP_VERSION
        sys.exit(0)
    puzzle = FindThatWord()
    gtk.main()
