from video import VideoCapturer
from textrecognition import ImageRecognition
import configparser
import sys
from twitchchat import TwitchChat
import threading
import requests
import time
import pygame

FRAME_GRAB_DELAY = 5
ANALYZE_DELAY = 15

def setup():
    config = configparser.ConfigParser()
    config.read('.twitch.cfg')
    return config

def is_stream_online(channel, clientid):
        url = 'https://api.twitch.tv/helix/users?login=' + channel
        headers = {'Client-ID': clientid}
        r = requests.get(url, headers=headers).json()
        if not 'data' in r or len(r['data']) == 0:
            return False
        
        channelid = r['data'][0]['id']

        url = 'https://api.twitch.tv/kraken/streams/' + channelid
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Client-ID': clientid}
        r = requests.get(url, headers=headers).json()

        if not 'stream' in r:
            return False

        if r['stream'] == None:
            return False

        return True

def grab_frame(streamVideo):
    # FETCH FRAME OF STREAM
    frame = streamVideo.read()
    streamVideo.saveFrame()
    if frame is not None:
        return True
    else:
        return False

def analyzeFrame(settings, modlist):
    # GOOGLE IMAGE OCR
    analyzer = ImageRecognition(settings['API']['key'])
    left, right = analyzer.analyze(modlist)

    if not left and not right:
        return ""
    elif not left:
        return "#B"
    elif not right:
        return "#A"

    leftIndex = modlist.index(left)
    rightIndex = modlist.index(right)
    if leftIndex < rightIndex:
        return "#A"
    else:
        return "#B"

def main():
    settings = setup()
    mods = settings['V2']['mods']
    modlist = mods.split(',')
    pygame.init()

    channel = settings['TWITCH']['twitch_channel']
    oauth_token = settings['TWITCH']['oauth_token']

    streamVideo = VideoCapturer('https://www.twitch.tv/' + channel)

    # TWITCH CHAT BOT
    bot = TwitchChat(oauth_token, channel)
    print("Starting bot...")
    t = threading.Thread(target=bot.start).start()
    bot.add_message("Beep boop I am a bot")
    time.sleep(5)

    bot.add_message("Beginning frame analysis...")
    i = 1
    frameSet = False
    QUIT = False
    while not QUIT:
        if (i % FRAME_GRAB_DELAY == 0):
            frameSet = grab_frame(streamVideo)

        if (i % ANALYZE_DELAY == 0) and (frameSet):
            # inputText = analyzeFrame(settings, modlist)
            inputText = ""
            if inputText:
                bot.add_message(inputText)
            else:
                # bot.add_message('No corresponding text found on screen ' + str(i))
                pass

        if i > 150:
            i = 1
        else:
            i += 1

        time.sleep(1)

    t.join()
        

if __name__ == "__main__":
    print("Press 'q' to exit the application")
    main()