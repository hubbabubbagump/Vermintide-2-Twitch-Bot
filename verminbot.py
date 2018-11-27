from video import VideoCapturer
from textrecognition import ImageRecognition
import configparser
import sys
from twitchchat import TwitchChat
import threading
import requests
import time
from PyQt5.QtWidgets import *
from PyQt5.QtCore import pyqtSlot, QThread
from PyQt5 import QtGui

FRAME_GRAB_DELAY = 5
ANALYZE_DELAY = 20

CONFIG_FILE_NAME = '.twitch.cfg'

class RunThread(QThread):
    def __init__(self, oauth_token, channel, mods):
        QThread.__init__(self)
        self.oauth_token = oauth_token
        self.channel = channel
        self.modlist = mods
        self.pause = False

    def __del__(self):
        self.wait()

    def grab_frame(self, streamVideo):
        # FETCH FRAME OF STREAM
        frame = streamVideo.read()
        streamVideo.saveFrame()
        if frame is not None:
            return True
        else:
            return False

    def analyzeFrame(self):
        # GOOGLE IMAGE OCR
        analyzer = ImageRecognition()
        left, right = analyzer.analyze(self.modlist)

        if not left and not right:
            return ""
        elif not left:
            return "#B"
        elif not right:
            return "#A"

        leftIndex = self.modlist.index(left)
        rightIndex = self.modlist.index(right)
        if leftIndex < rightIndex:
            return "#A"
        else:
            return "#B"

    def pauseThread(self):
        self.pause = True

    def unpause(self):
        self.pause = False

    def updateModifierList(self, newList):
        self.modlist = newList

    def run(self):
        streamVideo = VideoCapturer('https://www.twitch.tv/' + self.channel)

        # TWITCH CHAT BOT
        bot = TwitchChat(self.oauth_token, self.channel)
        print("Starting bot...")
        t = threading.Thread(target=bot.start).start()
        bot.add_message("Beep boop I am a bot")
        time.sleep(5)

        bot.add_message("Beginning frame analysis...")
        i = 1
        frameSet = False
        QUIT = False
        while not QUIT:
            if not self.pause and (i % FRAME_GRAB_DELAY == 0):
                frameSet = self.grab_frame(streamVideo)

            if not self.pause and (i % ANALYZE_DELAY == 0) and (frameSet):
                inputText = self.analyzeFrame()
                # inputText = ""
                if inputText:
                    bot.add_message(inputText)
                else:
                    # bot.add_message('No corresponding text found on screen ' + str(i))
                    pass

            if not self.pause and i > 300:
                i = 1
            elif not self.pause:
                i += 1

            time.sleep(1)

        t.join()

class GUI(QWidget):
    def __init__(self, oauth_token, channel, mods):
        super().__init__()
        self.oauth = oauth_token
        self.channel = channel
        self.modifiers = mods
        self.runThread = RunThread(oauth_token, channel, mods)
        self.isRunning = False
        self.isPaused = False
        self.initUI()
    
    def initUI(self):
        grid = QGridLayout()
        self.setLayout(grid)

        self.resize(400, 400)
        self.setWindowIcon(QtGui.QIcon('icon.png'))
        self.setWindowTitle("Vermintide 2 Twitch Bot")

        oauth_label = QLabel('OAuth Token')
        self.oauth_edit = QLineEdit(self.oauth)

        twitch_chan = QLabel('Twitch Channel')
        self.twitch_edit = QLineEdit(self.channel)

        self.run = QPushButton('Run', self)
        self.run.clicked.connect(self.runBot)
        edit = QPushButton('Save', self)
        edit.clicked.connect(self.save)

        mods = QLabel('Modifiers')
        self.modlist = QListWidget()
        self.modlist.addItems(self.modifiers)
        self.modlist.setDragDropMode(self.modlist.InternalMove)
        
        grid.setSpacing(10)

        grid.addWidget(oauth_label, 1, 0)
        grid.addWidget(self.oauth_edit, 1, 1)
        grid.addWidget(twitch_chan, 2, 0)
        grid.addWidget(self.twitch_edit, 2, 1)
        grid.addWidget(mods, 3, 0)
        grid.addWidget(self.modlist, 3, 1)
        grid.addWidget(self.run, 4, 1)
        grid.addWidget(edit, 4, 0)

        self.show()

    @pyqtSlot()
    def runBot(self):
        if not self.isRunning:
            self.runThread.start()
            self.run.setText('Pause')
            self.isRunning = True
            self.isPaused = False
        elif self.isPaused:
            self.run.setText('Pause')
            self.runThread.unpause()
            self.isPaused = False
        else:
            self.run.setText('Run')
            self.runThread.pauseThread()
            self.isPaused = True


    @pyqtSlot()
    def save(self):
        config = configparser.ConfigParser()
        config.read(CONFIG_FILE_NAME)
        config.set('TWITCH', 'oauth_token', self.oauth_edit.text())
        config.set('TWITCH', 'twitch_channel', self.twitch_edit.text())
        self.modifiers = [str(self.modlist.item(i).text()) for i in range(self.modlist.count())]
        config.set('V2', 'mods', ','.join(self.modifiers))
        with open(CONFIG_FILE_NAME, 'w') as configfile:
            config.write(configfile)
        self.runThread.updateModifierList(self.modifiers)

def setup():
    config = configparser.ConfigParser()
    config.read(CONFIG_FILE_NAME)
    return config

def createGUI(oauth_token, channel, mods):
    app = QApplication([])
    window = GUI(oauth_token, channel, mods)
    sys.exit(app.exec_())

def main():
    settings = setup()
    mods = settings['V2']['mods']
    modlist = mods.split(',')

    channel = settings['TWITCH']['twitch_channel']
    oauth_token = settings['TWITCH']['oauth_token']

    createGUI(oauth_token, channel, modlist)
    run(channel, oauth_token, modlist)

        

if __name__ == "__main__":
    main()