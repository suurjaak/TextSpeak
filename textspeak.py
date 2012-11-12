#-*- coding: utf-8 -*-
"""
Simple text-to-speech program, uses the Google Translate text-to-speech online
service. Since the public Google TTS only supports text up to 100 characters,
the text is divided into smaller chunks and the resulting MP3 files are merged.

Idea and parsing from http://glowingpython.blogspot.com/2012/11/
text-to-speech-with-correct-intonation.html

@author      Erki Suurjaak
@created     07.11.2012
@modified    12.11.2012
"""
import base64
import datetime
import os
import Queue
import shutil
import sys
import threading
import time
import traceback
import urllib2
import wx
import wx.lib.newevent
import wx.lib.scrolledpanel
import wx.lib.sized_controls
import wx.media


"""Event class and event binder for new results."""
ResultEvent, EVT_RESULT = wx.lib.newevent.NewEvent()

"""
The number of silent chunks inserted between text chunks, for shorter pauses
(after commas and like) and longer pauses (between sentences).
"""
SILENCE_COUNT_SHORT = 2
SILENCE_COUNT_LONG = 3

"""A chunk of silence of about 350 milliseconds, as base64-encoded MP3."""
SILENCE = (
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
LANGUAGES = [
    ("af", "Afrikaans"), ("sq", "Albanian"), ("ca", "Catalan"),
    ("zh", "Chinese (Mandarin)"), ("hr", "Croatian"), ("cs", "Czech"),
    ("da", "Danish"), ("nl", "Dutch"), ("en", "English"), ("fi", "Finnish"),
    ("el", "Greek"), ("hu", "Hungarian"), ("is", "Icelandic"),
    ("id", "Indonesian"), ("lv", "Latvian"), ("mk", "Macedonian"),
    ("no", "Norwegian"), ("pl", "Polish"), ("pt", "Portuguese"),
    ("ro", "Romanian"), ("ru", "Russian"), ("sr", "Serbian"), ("sk", "Slovak"),
    ("sw", "Swahili"), ("sv", "Swedish"), ("tr", "Turkish"),
    ("vi", "Vietnamese"), ("cy", "Welsh")
]

class TextSpeakWindow(wx.Frame):
    """TextSpeak GUI window."""

    def __init__(self):
        wx.Frame.__init__(
            self, parent=None, title="Simple TextSpeak", size=(700, 500)
        )

        self.data = {}
        self.text = None
        self.panels_history = []
        # In Windows 7 and Vista the wx.media.MediaCtrl fires state change
        # events unreliably, so cannot use sequential play.
        self.mc_hack = hasattr(sys, "getwindowsversion") \
                       and sys.getwindowsversion()[0] > 5
        icons = wx.IconBundle()
        for s in [-1, 32]:
            icons.AddIcon(wx.ArtProvider_GetIcon(
                wx.ART_TICK_MARK, wx.ART_FRAME_ICON, (s, s)))
        self.SetIcons(icons)

        panel_main = wx.lib.sized_controls.SizedPanel(self)
        panel_main.SetSizerType("vertical")

        splitter = self.splitter_main = wx.SplitterWindow(
            parent=panel_main, style=wx.BORDER_NONE
        )
        splitter.SetMinimumPaneSize(50)
        splitter.SetSizerProps(expand=True, proportion=1)

        panel = wx.lib.sized_controls.SizedPanel(splitter)
        panel.SetSizerType("vertical")
        gauge = self.gauge = wx.Gauge(panel)
        gauge.ToolTipString = "Audio data chunks"
        gauge.SetSizerProps(expand=True)
        text = self.edit_text = wx.TextCtrl(
            panel, size=(-1, 50), style=wx.TE_MULTILINE | wx.TE_RICH2)
        text.SetSizerProps(expand=True, proportion=1)
        panel_buttons = wx.lib.sized_controls.SizedPanel(panel)
        panel_buttons.SetSizerType("grid", {"cols":3})
        self.button_go = wx.Button(panel_buttons, label="&Text to speech")
        self.button_save = wx.Button(panel_buttons, label="&Save MP3")
        self.button_save.Enabled = False
        self.list_lang = wx.ComboBox(parent=panel_buttons, value="English",
            choices=[i[1] for i in LANGUAGES], style=wx.CB_READONLY)
        wx.AcceleratorTable([(wx.ACCEL_ALT, ord("T"), self.button_go.Id),
            (wx.ACCEL_ALT, ord("S"), self.button_go.Id)])

        mc = self.mediactrl = wx.media.MediaCtrl(panel, size=(-1, 70))
        mc.ShowPlayerControls(wx.media.MEDIACTRLPLAYERCONTROLS_DEFAULT)
        mc.SetSizerProps(expand=True)

        panel_list = self.panel_list = \
            wx.lib.scrolledpanel.ScrolledPanel(splitter)
        panel_list.BackgroundColour = "WHITE"
        panel_list.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_info = wx.StaticText(panel_main,
            label="Simple text-to-speech program, feeds the text in chunks to"
                  " the Google Translate online service and combines received"
                  " MP3s into one file.")
        self.text_info.SetSizerProps(expand=True)

        self.out_queue = Queue.Queue()
        self.mp3_loader = TextToMP3Loader(self, self.out_queue)

        if not self.mc_hack:
            mc.Bind(wx.media.EVT_MEDIA_LOADED, self.on_media_loaded)
            mc.Bind(wx.media.EVT_MEDIA_FINISHED, self.on_media_finished)
        self.Bind(EVT_RESULT, self.on_result_event)
        self.Bind(wx.EVT_BUTTON, self.on_text_to_speech, self.button_go)
        self.Bind(wx.EVT_BUTTON, self.on_save_mp3, self.button_save)
        self.Bind(wx.EVT_CLOSE, lambda evt: self.cleanup())
        self.dialog_save = wx.FileDialog(
            parent=self,
            defaultDir=os.getcwd(),
            style=wx.FD_OVERWRITE_PROMPT | wx.FD_SAVE | wx.RESIZE_BORDER
        )

        self.Center(wx.HORIZONTAL)
        self.Position.top = 50
        sashPos = 3 * self.Size.width / 4
        splitter.SplitVertically(panel, panel_list, sashPosition=sashPos)
        self.Show(True)
        self.edit_text.SetFocus()


    def on_result_event(self, event):
        """Handler for a result chunk from TextToMP3Loader."""
        text_id, filename = event.TextId, event.Filename
        chunks, count, index = event.Chunks, event.Count, event.Index
        data = self.data[text_id]
        data["count"] = count
        data["chunks"] = chunks
        data["filenames"].append(filename)
        is_first = (self.text_id == text_id) \
                   and (len(data["filenames"]) == 1)
        is_last = (index == data["count"] - 1)
        if is_last and (wx.media.MEDIASTATE_PLAYING != self.mediactrl.State
                        or self.mc_hack):
            # All chunks finished, merge them into one
            self.merge_chunks(data)
            data["completed"] = True
            self.text_id = text_id
            if not is_first or self.mc_hack:
                self.mediactrl.DONTPLAY = True
                self.mediactrl.Load(data["filenames"][0])
                wx.CallLater(500, self.mediactrl.Play)
            self.button_save.Enabled = True
        if is_first and not self.mc_hack:
            # First result: set playing at once
            data["current"] = data["filenames"][-1]
            self.mediactrl.Load(data["current"])


    def on_save_mp3(self, event):
        """Handler for clicking to save the merged MP3 file."""
        data = self.data[self.text_id]
        self.dialog_save.Filename = data["filenames"][0]
        if wx.ID_OK == self.dialog_save.ShowModal():
            shutil.copyfile(data["filenames"][0], self.dialog_save.GetPath())


    def on_text_to_speech(self, event):
        """Handler for the speak button, sends entered text for processing."""
        text = self.edit_text.Value.strip()
        lang = LANGUAGES[self.list_lang.Selection][0]
        text_present = [i for i in self.data.values()
                        if i["text"] == text and i["lang"] == lang]
        if not text_present:
            self.text_id = wx.NewId()
            data = self.data[self.text_id] = {"filenames": [], "lang": lang,
                "lang_text": LANGUAGES[self.list_lang.Selection][1],
                "text": text, "current": None, "count": 0, "id": self.text_id,
                "datetime": datetime.datetime.now(), "stopped": False,
                "completed": False
            }
            self.out_queue.put(data)
            self.button_save.Enabled = False
            # Create panel in history list
            p = wx.lib.sized_controls.SizedPanel(self.panel_list,
                size=(150, 100))
            self.panel_list.SetupScrolling(scroll_x=False)
            self.panel_list.BackgroundColour = "LIGHT GRAY"
            p.SetSizerType("vertical")
            p.BackgroundColour = "WHITE"
            p_top = wx.lib.sized_controls.SizedPanel(p)
            p_top.SetSizerType("horizontal")
            t_date = wx.StaticText(
                p_top, label="%s\n%s" % (
                    data["datetime"].strftime("%H:%M %d.%m.%Y"),
                    data["lang_text"])
            )
            t_date.ForegroundColour = "GRAY"
            h = wx.HyperlinkCtrl(p_top, id=wx.NewId(), label="Open", url="")
            h.text_id = data["id"]
            self.Bind(wx.EVT_HYPERLINK, self.on_open_text, h)
            t_text = wx.StaticText(p, label=text[:200].replace("\n", " "))
            t_text.ForegroundColour = "LIGHT GRAY"
            self.panel_list.Sizer.Insert(0, p, border=2, proportion=1,
                                         flag=wx.ALL | wx.EXPAND)
            self.panels_history.append(p)
            self.panel_list.Layout()
            t_text.Wrap(p.Size.width)
            self.panel_list.Refresh()
        elif text_present[0]["id"] != self.text_id:
            self.mediactrl.Load(text_present[0]["filenames"][0])
            if self.mc_hack:
                wx.CallLater(500, self.mediactrl.Play)
        else:
            self.mediactrl.Play()


    def on_open_text(self, event):
        """Handler for opening a text from history, loads and plays it."""
        self.text_id = event.EventObject.text_id
        data = self.data[self.text_id]
        self.edit_text.Value = data["text"]
        self.list_lang.Value = data["lang_text"]
        self.mediactrl.Load(data["filenames"][0])
        if self.mc_hack:
            wx.CallLater(500, self.mediactrl.Play)


    def on_media_loaded(self, event):
        """Handler for MediaCtrl finishing loading media, sets it to play."""
        if hasattr(self.mediactrl, "DONTPLAY"):
            delattr(self.mediactrl, "DONTPLAY")
        else:
            self.mediactrl.Play()
        data = self.data[self.text_id]
        index = data["filenames"].index(data["current"])
        self.gauge.SetValue(100.0 * (index + 1) / data["count"])


    def on_media_finished(self, event):
        """
        Handler for when MediaCtrl finishes playing something, loads the next
        chunk if available.
        """
        data = self.data[self.text_id]
        index = data["filenames"].index(data["current"]) \
                if data["current"] in data["filenames"] else -1
        if (index < data["count"] - 1 
        and len(data["filenames"]) > index + 1):
            # Next chunk available, set it playing
            filename = data["filenames"][index + 1]
            data["current"] = filename
            self.mediactrl.Load(filename)
        if index == data["count"] - 1 and not data["completed"]:
            # All chunks finished, merge them into one
            self.merge_chunks(data)
            data["completed"] = True
            # Load large file in MediaCtrl in place of last chunk, skip replay
            # as we already played it all in chunks
            self.mediactrl.DONTPLAY = True
            self.mediactrl.Load(data["filenames"][0])
            self.button_save.Enabled = True


    def merge_chunks(self, data):
        """Merges all the audio chunks in data into one file."""
        fn = "speech_%s_%d.mp3" % (data["lang"], time.mktime(time.localtime()))
        with open(fn, "wb") as f:
            # MP3s can be simply concatenated together, result is legible.
            for i, filename in enumerate(data["filenames"]):
                f.write(open(filename, "rb").read())
                # Add silence only for separators like commas and periods.
                silence_count = 0
                if data["chunks"][i][-1] in [".","?","!"]:
                    silence_count = SILENCE_COUNT_LONG
                elif data["chunks"][i][-1] in [",",":",";","(",")"]:
                    silence_count = SILENCE_COUNT_SHORT
                f.write(base64.decodestring(SILENCE) * silence_count)
                try:
                    os.unlink(filename)
                except Exception, e:
                    print "Failed to unlink %s (%s)" % (filename, e)
        data["filenames"] = [fn]
        data["count"] = 1
        data["current"] = fn


    def cleanup(self):
        """Deletes the MP3 files created during this run."""
        for f in [i for d in self.data.values() for i in d["filenames"]]:
            try:
                os.unlink(f)
            except Exception, e:
                print "Failed to unlink %s (%s)" % (f, e)
        self.Destroy()



class TextToMP3Loader(threading.Thread):
    """Background thread for loading smaller MP3 files from Google TTS."""
    GOOGLE_TRANSLATE_URL = "http://translate.google.com/" \
                           "translate_tts?tl=%s&q=%s"


    def __init__(self, event_handler, in_queue):
        threading.Thread.__init__(self)
        self.daemon = True # Daemon threads do not keep application running
        self.event_handler = event_handler
        self.in_queue = in_queue
        self.is_running = False
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [("User-agent",
            "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) "
            "Simple TextSpeak")]
        self.start()


    def run(self):
        self.is_running = True
        while self.is_running:
            data = self.in_queue.get()
            text_chunks = self.parse_text(data["text"].encode("utf-8"))
            for i, sentence in enumerate(text_chunks):
                url = self.GOOGLE_TRANSLATE_URL % (
                    data["lang"], urllib2.quote(sentence))
                response = self.opener.open(url)
                filename = "speech_temp_%s_%d_%02d.mp3" % (
                    data["lang"], data["id"], i)
                with open(filename, "wb") as f:
                    f.write(response.read())
                event = ResultEvent(TextId=data["id"], Chunks=text_chunks,
                    Count=len(text_chunks), Index=i, Filename=filename)
                wx.PostEvent(self.event_handler, event)


    def parse_text(self, text):
        """
        Returns a list of sentences with less than 100 characters.

        @from http://glowingpython.blogspot.com/2012/11/
        text-to-speech-with-correct-intonation.html
        """
        MAXLEN = 100
        toSay = []
        punct = [",",":",";",".","?","!","(",")"] # punctuation
        words = text.split(" ") if len(text) > MAXLEN else []
        sentence = "" if len(text) > MAXLEN else text
        for w in filter(None, words):
            if w[len(w)-1] in punct: # encountered a punctuation mark
                if (len(sentence)+len(w)+1 < 100): # is there enough space?
                    sentence += " "+w # add the word
                    toSay.append(sentence.strip()) # save the sentence
                else:
                    toSay.append(sentence.strip()) # save the sentence
                    toSay.append(w.strip()) # save the word as a sentence
                sentence = "" # start another sentence
            else:
                if (len(sentence)+len(w)+1 < 100):
                    sentence += " "+w # add the word
                else:
                    toSay.append(sentence.strip()) # save the sentence
                    sentence = w # start a new sentence
        if len(sentence) > 0:
            toSay.append(sentence.strip())
        return toSay


    
if "__main__" == __name__:
    app = wx.App(0)
    window = TextSpeakWindow()
    try:
        app.MainLoop()
    except Exception, e:
        traceback.print_exc()
    if window:
        window.cleanup()
