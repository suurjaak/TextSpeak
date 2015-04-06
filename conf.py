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
@modified    06.04.2015
------------------------------------------------------------------------------
"""
from ConfigParser import RawConfigParser
import datetime
import json
import os
import sys

"""Program title, version number and version date."""
Title = "TextSpeak"
Version = "1.4.2c"
VersionDate = "06.04.2015"
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
FileDirectives = ["LastLanguage", "LastText", "LastVolume",
                  "WindowPosition", "WindowSize", ]

"""---------------------------- FileDirectives: ----------------------------"""

"""Language code of last selected language."""
LastLanguage = "en"

"""Text entered last in window."""
LastText = ""

"""Sound volume of the media control (0..1)."""
LastVolume = 0.5

"""Main window position, (x, y)."""
WindowPosition = None

"""Main window size in pixels, [w, h] or [-1, -1] for maximized."""
WindowSize = [680, 500]

"""---------------------------- /FileDirectives ----------------------------"""

"""Short information shown at window bottom."""
InfoText = "Simple text-to-speech program, feeds text in blocks to " \
           "the Google Translate online service and combines received " \
           "audio into one MP3."

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

"""Silence for ~250 milliseconds, as base64-encoded MP3 (32Kbps 16KHz mono)."""
Silence = (
"//NIxAAUBFYQFgBNzQDkSH8A3RjZAeDAAAxkD4xsCZI0b//+//m/5IkY2WQF8e9f9idpmAgQhDkM"
"iHYghBMmDhdsZjkIiP7PJkEHtyZPYbPHsmn/fMQj9k/7Jk7kDD29frU1puaWahro0zO7mk76OV7f"
"//+/TrsmRdHopTgnEKY/zhCVrYUlSjSkYxc31sYJ//NIxDMYxF4YCgCTscTrvcoYkfGHEd+MSNAQ"
"hcRzMlVVIkp9EToiWk2S6ouwm9QTnBIKGR4iOmzzDzi05gyB2/d7EpREpcxUuuo87iCEU4yWcsg0"
"ijOfFkdyV0//39H29GVERDMdzzOAKaraGBpt3nUYxglkkWIdXQH2oQ3SpYiQ+KhtETwGlJU2DxCg"
"YJgM//NIxFMa7F4YDACTsbOtrF1VrmIhMYFe0YLhUuZCx0kIC5EQsyoAOSNFVI5mFF3VM3Dhj+y6"
"FCQ5UMKOxqDUOJHuStBVKG5kthR+VSDXzb2+FbvkRzNUPIYCi01G1u6ly/UDOFlOYMOK0xBkHQGb"
"KrBkNzkjjQHTIrj9aiZf6CoACUST6lL/Q3+ImMYz//////NIxGoWU5pEHgBHo////KyP/oWaUuXU"
"rdeY2agkLKAodFStRyy82NfDCqtUMKoCArOBgJmYMBVMQU1FMy45OC4yVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVV//NIxJMOrBZMHgFH0lVVVVVVVVVMQU1FMy45OC4yVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV//NIxNsAAANIAAAAAFVVVVVVVVVM"
"QU1FMy45OC4yVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVVVVVV//NIxP8AAANIAAAAAFVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
"VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV"
)

# Languages supported by Google Translate TTS, as [(two-letter code: name), ]
Languages = [
    ("ar", "Arabic"), ("zh-CN", "Chinese (Simplified)"),
    ("zh", "Chinese (Mandarin)"), ("cs", "Czech"), ("da", "Danish"),
    ("nl", "Dutch"), ("en", "English"),  ("fi", "Finnish"),
    ("fr", "French"), ("de", "German"), ("el", "Greek"),
    ("ht", "Haitian Creole"), ("hi", "Hindi"), ("hu", "Hungarian"),
    ("it", "Italian"), ("id", "Indonesian"), ("ja", "Japanese"),
    ("ko", "Korean"), ("la", "Latin"), ("no", "Norwegian"), ("pl", "Polish"),
    ("pt", "Portuguese"), ("ru", "Russian"), ("sk", "Slovak"),
    ("es", "Spanish"), ("sv", "Swedish"), ("th", "Thai"), ("tr", "Turkish"), 
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
