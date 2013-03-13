"""
This version of roaster (not the same as github.com/expresso-math/roaster/roaster.py)
is purely function definitions for functions that live on the aforementioned file.

This is so we don't have to have opencv installed on Heroku -- it's hacky, but it seems
to work for now, at least!

Daniel Guilak <daniel.guilak@gmail.com> and Josef Lange <josef.d.lange@gmail.com>
Expresso
"""

def saveImage(imageVal):
    """
    Send binary image file and save it on the server as a PNG
    """
