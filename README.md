# FindThatWord

## About

FindThatWord is a simple program that helps create wordsearch puzzles.  It should be of use to teachers, parents and the intellectually curious.

## License

FindThatWord is completely free to use and distribute for personal, educational or business purposes.  Restrictions apply if you wish to modify the program and then distribute the modified version of the software.

Full details are contained within the file COPYING which is distributed with FindThatWord.

## Prerequisites

FindThatWord will work on any modern operating system including Linux, Windows and OS X.

If an installation package is available for your platform, use that and ignore the following instructions.  If you need or want to install by hand, here are some requirements:

- Python. FTW was developed on 2.5.2, but earlier versions should be OK. Python 3.0 won't work.
- PyGTK version 2.10 or higher. The remaining requirements will probably be installed if you have PyGTK: python bindings for Glade, Cairo, Pango and GnomeVFS
- FindThatWord runs out of the box on Ubuntu Linux 8.10

## Installation

To install for one user, unpack the files into a suitable folder and double-click on the file `FindThatWord.py`. On Linux, you might first need to mark the file as executable (the method can varies but try right-clicking on it).

If that fails, your system is probably set up in a non-standard way.  Try these two commands instead (obviously you need to modify the first!):

```bash
cd /path/to/folder/containing/ftw/src
python findthatword.py
```

System wide installation varies by platform and is outside the scope of this document.

If you want to try, you'll need to:
- copy the ftw files to some place that's accessible to all users (/usr/local is a good choice on Linux)
- create a menu item for all users. These are typically stored as `.desktop` files in `/usr/share/applications` and you will need to create your own
- You can link the desktop file to the icons provided with FTW

## Finally

Have fun.  If you like the software, email me at jonny@jonespenarth.me.uk
