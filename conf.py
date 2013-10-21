# -*- coding: utf-8 -*-
"""
Application settings, and functionality to save/load some of them from
an external file. Configuration file has simple INI file format,
and all values are kept in JSON.

------------------------------------------------------------------------------
This file is part of TextSpeak - a simple text-to-speech program.
Released under the MIT License.

@author      Erki Suurjaak
@created     21.10.2013
@modified    21.10.2013
------------------------------------------------------------------------------
"""
from ConfigParser import RawConfigParser
import datetime
import json
import os
import sys

"""Program title, version number and version date."""
Title = "TextSpeak"
Version = "2.1"
VersionDate = "21.10.2013"
VersionText = u"© Erki Suurjaak\nv%s, %s" % (Version, VersionDate)

if getattr(sys, 'frozen', False):
    # Running as a pyinstaller executable
    ApplicationDirectory = os.path.dirname(sys.executable)
    ApplicationFile = os.path.realpath(sys.executable)
else:
    ApplicationDirectory = os.path.dirname(__file__)
    ApplicationFile = os.path.join(ApplicationDirectory, "textspeak.py")

"""Name of file where FileDirectives are kept."""
ConfigFile = "%s.ini" % os.path.join(ApplicationDirectory, Title.lower())

"""List of attribute names that can be saved to and loaded from ConfigFile."""
FileDirectives = ["LastLanguage", "LastText", "WindowPosition", "WindowSize", ]

"""---------------------------- FileDirectives: ----------------------------"""

"""Last selected language code."""
LastLanguage = None

"""Last text entered in window."""
LastText = ""

"""Main window position, (x, y)."""
WindowPosition = None

"""Main window size in pixels, [w, h] or [-1, -1] for maximized."""
WindowSize = [1080, 710]

"""---------------------------- /FileDirectives ----------------------------"""

"""Short information shown at window bottom."""
InfoText = "Simple text-to-speech program, feeds the text in chunks to " \
           "the Google Translate online service and combines received " \
           "MP3s into one file."

"""
The number of silent chunks inserted between text chunks, for shorter pauses
(after commas and like) and longer pauses (between sentences).
"""
SilenceCountShort = 2
SilenceCountLong  = 4

"""
Marker in entered text to insert a silence break, chopping up the sentence
if inside one.
"""
SilenceMarker = "\n"

"""Silence for ~350 milliseconds, as base64-encoded MP3 (32Kbps 16KHz mono)."""
Silence = (
"//JIwITXABmDpmJUGITYtt2jqDK1cxCwimjmHZDQGLRDRA7hGPO7HRlzuRjybL/kVyf/3T//2VyT"
"2t//yST9GkY7oRT53I3qdCKdG+yuShJ8in79X/88mro5FcmHcDMRjnRqEV6Md3Y4IQHFoEHJ/RWU"
"J2Nol+30rL91OGCoLEtSDE1QxIZyjUTAKRUSBnDo//JIwAsOGxKAXoZUGMZIaCtB7oEbvaOf6Nyg"
"KRoYMQzIrK/lSNmgihPQerwk7s8ke6BWMT/ioCJFidX/IhL/////////////////////////////"
"////////////////////////////////////////////////////////////////////////////"
"//////JIwAysUgAAAlwAAAAA////AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA//JIwC6+0xVAAlwAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
"AAAAAAAA"
)

# Languages supported by Google Translate TTS, as [(two-letter code: name), ]
Languages = [
    ("af", "Afrikaans"), ("sq", "Albanian"), ("ar", "Arabic"),
    ("hy", "Armenian"), ("bs", "Bosnian"), ("ca", "Catalan"),
    ("zh", "Chinese (Mandarin)"), ("hr", "Croatian"), ("cs", "Czech"),
    ("da", "Danish"), ("nl", "Dutch"), ("en", "English"), ("eo", "Esperanto"),
    ("fi", "Finnish"), ("fr", "French"), ("de", "German"), ("el", "Greek"),
    ("hi", "Hindi"), ("hu", "Hungarian"), ("is", "Icelandic"),
    ("id", "Indonesian"), ("it", "Italian"), ("ja", "Japanese"),
    ("ko", "Korean"), ("la", "Latin"), ("lv", "Latvian"), ("mk", "Macedonian"),
    ("no", "Norwegian"), ("pl", "Polish"), ("pt", "Portuguese"),
    ("ro", "Romanian"), ("ru", "Russian"), ("sr", "Serbian"), ("sk", "Slovak"),
    ("es", "Spanish"), ("sw", "Swahili"), ("sv", "Swedish"), ("th", "Thai"),
    ("tr", "Turkish"), ("ta", "Tamil"), ("vi", "Vietnamese"), ("cy", "Welsh"),
]

URLHomepage = "http://github.com/suurjaak/TextSpeak"

def load():
    """Loads FileDirectives from ConfigFile into this module's attributes."""
    section = "*"
    module = sys.modules[__name__]
    parser = RawConfigParser()
    parser.optionxform = str # Force case-sensitivity on names
    try:
        parser.read(ConfigFile)
        for name in FileDirectives:
            try: # parser.get can throw an error if not found
                value_raw = parser.get(section, name)
                success = False
                # First, try to interpret as JSON
                try:
                    value = json.loads(value_raw)
                    success = True
                except:
                    pass
                if not success:
                    # JSON failed, try to eval it
                    try:
                        value = eval(value_raw)
                        success = True
                    except:
                        # JSON and eval failed, fall back to string
                        value = value_raw
                        success = True
                if success:
                    setattr(module, name, value)
            except:
                pass
    except Exception, e:
        pass # Fail silently


def save():
    """Saves FileDirectives into ConfigFile."""
    section = "*"
    module = sys.modules[__name__]
    parser = RawConfigParser()
    parser.optionxform = str # Force case-sensitivity on names
    parser.add_section(section)
    try:
        f = open(ConfigFile, "wb")
        f.write("# %s configuration autowritten on %s.\n" % (
            ConfigFile, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        for name in FileDirectives:
            try:
                value = getattr(module, name)
                parser.set(section, name, json.dumps(value))
            except:
                pass
        parser.write(f)
        f.close()
    except Exception, e:
        pass # Fail silently
