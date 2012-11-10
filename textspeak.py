#-*- coding: utf-8 -*-
"""
Simple text-to-speech program, uses the Google Translate text-to-speech online
service. Since the public Google TTS only supports text up to 100 characters,
the text is divided into smaller chunks and the resulting MP3 files are merged.

Idea and parsing from
http://glowingpython.blogspot.com/2012/11/text-to-speech-with-correct-intonation.html

@author      Erki Suurjaak
@created     07.11.2012
@modified    10.11.2012
"""
import datetime
import os
import Queue
import shutil
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


class TextSpeakWindow(wx.Frame):
    """TextSpeak GUI window."""

    def __init__(self):
        wx.Frame.__init__(
            self, parent=None, title="Simple TextSpeak", size=(700, 500)
        )

        self.data = {}
        self.text = None
        self.panels_history = []

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
        gauge.ToolTipString = "Progress of receiving audio data chunks"
        gauge.SetSizerProps(expand=True)
        text = self.edit_text = wx.TextCtrl(panel, size=(-1, 50), style=wx.TE_MULTILINE | wx.TE_RICH2)
        text.SetSizerProps(expand=True, proportion=1)
        panel_buttons = wx.lib.sized_controls.SizedPanel(panel)
        panel_buttons.SetSizerType("grid", {"cols":2})
        self.button_go = wx.Button(panel_buttons, label="Speak &text")
        self.button_save = wx.Button(panel_buttons, label="&Save MP3")
        wx.AcceleratorTable([(wx.ACCEL_ALT, ord('T'), self.button_go.Id), (wx.ACCEL_ALT, ord('S'), self.button_go.Id)])
        self.button_save.Enabled = False
        self.button_save.SetSizerProps(halign="right")
        mc = self.mediactrl = wx.media.MediaCtrl(panel, size=(-1, 70))
        mc.ShowPlayerControls(wx.media.MEDIACTRLPLAYERCONTROLS_DEFAULT)
        mc.SetSizerProps(expand=True)

        panel_list = self.panel_list = wx.lib.scrolledpanel.ScrolledPanel(splitter)
        panel_list.BackgroundColour = "WHITE"
        panel_list.Sizer = wx.BoxSizer(wx.VERTICAL)

        self.text_info = wx.StaticText(panel_main,
            label="Simple text-to-speech program, feeds the text in chunks to"
                  " the Google Translate online service and combines received MP3s"
                  " into one file.")
        self.text_info.SetSizerProps(expand=True)

        self.out_queue = Queue.Queue()
        self.mp3_loader = TextToMP3Loader(self, self.out_queue)

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
        splitter.SplitVertically(panel, panel_list, sashPosition=3 * self.Size[0] / 4)
        self.Show(True)
        self.edit_text.SetFocus()


    def on_result_event(self, event):
        """Handler for a result chunk from TextToMP3Loader."""
        text_id, filename = event.TextId, event.Filename
        count, index = event.Count, event.Index
        self.data[text_id]["count"] = count
        self.data[text_id]["filenames"].append(filename)
        is_first = (self.text_id == text_id) \
                   and (len(self.data[text_id]["filenames"]) == 1)
        is_last = (index == self.data[text_id]["count"] - 1)
        if is_last and wx.media.MEDIASTATE_PLAYING != self.mediactrl.State:
            # All chunks finished, merge them into one
            self.merge_chunks(self.data[text_id])
            self.button_save.Enabled = True
            self.data[text_id]["completed"] = True
        if is_first:
            # First result: set playing at once
            self.data[text_id]["current"] = self.data[text_id]["filenames"][-1]
            self.mediactrl.Load(self.data[text_id]["current"])


    def on_save_mp3(self, event):
        """Handler for clicking to save the merged MP3 file."""
        data = self.data[self.text_id]
        self.dialog_save.Filename = data["filenames"][0]
        if wx.ID_OK == self.dialog_save.ShowModal():
            shutil.copyfile(data["filenames"][0], self.dialog_save.GetPath())


    def on_text_to_speech(self, event):
        """Handler for the speak button, sends entered text for processing."""
        text = self.edit_text.Value.strip()
        text_present = [i for i in self.data.values() if i["text"] == text]
        if not text_present:
            self.text_id = wx.NewId()
            data = self.data[self.text_id] = {"filenames": [],
                "text": text, "current": None, "count": 0, "id": self.text_id,
                "datetime": datetime.datetime.now(), "stopped": False,
                "completed": False
            }
            self.out_queue.put(data)
            self.button_save.Enabled = False
            # Create panel in history list
            p = wx.lib.sized_controls.SizedPanel(self.panel_list, size=(150, 100))
            self.panel_list.SetupScrolling(scroll_x=False, rate_y=20, scrollToTop=True)
            self.panel_list.BackgroundColour = 'LIGHT GRAY'
            p.SetSizerType("vertical")
            p.BackgroundColour = 'WHITE'
            p_top = wx.lib.sized_controls.SizedPanel(p)
            p_top.SetSizerType("horizontal")
            t_date = wx.StaticText(
                p_top, label=data["datetime"].strftime("%H:%M %d.%m.%Y"))
            #t_date.BackgroundColour = 'WHITE'
            t_date.ForegroundColour = 'GRAY'
            h = wx.HyperlinkCtrl(p_top, label="Open")
            h.text_id = data["id"]
            self.Bind(wx.EVT_HYPERLINK, self.on_open_text, h)
            t_text = wx.StaticText(p, label=text)
            t_text.ForegroundColour = 'LIGHT GRAY'
            self.panel_list.Sizer.Insert(0, p, border=2, proportion=1, flag=wx.ALL | wx.EXPAND)
            self.panels_history.append(p)
            self.panel_list.Layout()
            t_text.Wrap(p.Size.width)
            self.panel_list.Refresh()
        elif text_present[0]["id"] != self.text_id:
            self.mediactrl.Load(text_present[0]["filenames"][0])
        else:
            self.mediactrl.Play()


    def on_open_text(self, event):
        """Handler for opening a text from history, loads and plays it."""
        self.text_id = event.EventObject.text_id
        data = self.data[self.text_id]
        self.edit_text.Value = data["text"]
        self.mediactrl.Load(data["filenames"][0])


    def on_media_loaded(self, event):
        """Handler for when MediaCtrl finishes loading media, sets it playing."""
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
        index = data["filenames"].index(data["current"]) if data["current"] in data["filenames"] else -1
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
            self.mediactrl.DONTPLAY = True
            self.mediactrl.Load(data["filenames"][0])
            self.button_save.Enabled = True


    def merge_chunks(self, data):
        """Merges all the audio chunks in data into one file."""
        merged = "speech_%d.mp3" % time.mktime(time.localtime())
        with open(merged, "wb") as f:
            for filename in data["filenames"]:
                f.write(open(filename, "rb").read())
                try:
                    os.unlink(filename)
                except Exception, e:
                    print "Failed to unlink %s (%s)" % (filename, e)
        data["filenames"] = [merged]
        data["count"] = 1
        data["current"] = merged


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
    GOOGLE_TRANSLATE_URL = 'http://translate.google.com/translate_tts?tl=en&q='


    def __init__(self, event_handler, in_queue):
        threading.Thread.__init__(self)
        self.daemon = True # Daemon threads do not keep application running
        self.event_handler = event_handler
        self.in_queue = in_queue
        self.is_running = False
        self.opener = urllib2.build_opener()
        self.opener.addheaders = [('User-agent',
            'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0) '
            'Simple TextSpeak')]
        self.start()


    def run(self):
        self.is_running = True
        while self.is_running:
            data = self.in_queue.get()
            text_chunks = self.parse_text(data["text"].encode("utf-8"))
            for i, sentence in enumerate(text_chunks):
                url = self.GOOGLE_TRANSLATE_URL + urllib2.quote(sentence)
                response = self.opener.open(url)
                filename = "speech_temp_%d_%02d.mp3" % (data["id"], i)
                with open(filename, 'wb') as f:
                    f.write(response.read())
                event = ResultEvent(TextId=data["id"],
                    Count=len(text_chunks), Index=i, Filename=filename)
                wx.PostEvent(self.event_handler, event)


    def parse_text(self, text):
        """
        Returns a list of sentences with less than 100 characters.

        @from http://glowingpython.blogspot.com/2012/11/text-to-speech-with-correct-intonation.html
        """
        MAXLEN = 100
        toSay = []
        punct = [',',':',';','.','?','!'] # punctuation
        words = text.split(' ') if len(text) > MAXLEN else []
        sentence = '' if len(text) > MAXLEN else text
        for w in filter(None, words):
            if w[len(w)-1] in punct: # encountered a punctuation mark
                if (len(sentence)+len(w)+1 < 100): # is there enough space?
                    sentence += ' '+w # add the word
                    toSay.append(sentence.strip()) # save the sentence
                else:
                    toSay.append(sentence.strip()) # save the sentence
                    toSay.append(w.strip()) # save the word as a sentence
                sentence = '' # start another sentence
            else:
                if (len(sentence)+len(w)+1 < 100):
                    sentence += ' '+w # add the word
                else:
                    toSay.append(sentence.strip()) # save the sentence
                    sentence = w # start a new sentence
        if len(sentence) > 0:
            toSay.append(sentence.strip())
        return toSay


    
if "__main__" == __name__:
    app = wx.App()
    window = TextSpeakWindow()
    try:
        app.MainLoop()
    except Exception, e:
        traceback.print_exc()
    if window:
        window.cleanup()
