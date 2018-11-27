import irc.bot
import requests
import logging
import threading

class TwitchChat(irc.bot.SingleServerIRCBot):

    def __init__(self, oauth, channel):
        self.msg_lock = threading.Lock()
        self.isConnected = False

        # Check if oauth is valid and grab username and client id
        token = "OAuth " + oauth
        url = 'https://api.twitch.tv/kraken'
        headers = {'Accept': 'application/vnd.twitchtv.v5+json', 'Authorization': token}
        r = requests.get(url, headers=headers).json()
        if 'token' not in r:
            print("Invalid OAuth token")
            exit()
        
        self.oauth_token = oauth
        self.user_id = r['token']['user_id']
        self.client_id = r['token']['client_id']
        self.username = r['token']['user_name']
        self.channel_id = '#' + channel
        self.channel = channel

        server = 'irc.chat.twitch.tv'
        port = 6667
        self.message_queue = []

        print("Connecting to " + server + " on port " + str(port) + "...")
        irc.bot.SingleServerIRCBot.__init__(self, [(server, port, 'oauth:'+oauth)], self.username, self.username)
        print('Chat worker bot initialized on channel ' + self.channel_id)

    def on_welcome(self, c, e):
        # You must request specific capabilities before you can use them
        # c.cap('REQ', ':twitch.tv/membership')
        # c.cap('REQ', ':twitch.tv/tags')
        # c.cap('REQ', ':twitch.tv/commands')
        self.isConnected = True
        c.join(self.channel_id)
        threading.Timer(3, self.check_messages).start()
        # threading.Timer(5, self.grab_frame).start()
        # threading.Thread(target=self.do_command, args=(c, e, "hello",)).start()

    def on_disconnect(self, c, e):
        self.isConnected = False

        event_str = str(e)
        e_type = e.type
        e_source = e.source
        e_target = e.target

        print('[%s] Lost connection to Twitch.tv IRC.', self.worker_name)
        print('[%s] Event info: %s %s %s', self.worker_name, e_type, e_source, e_target)
        print('[%s] Even more info: %s ', self.worker_name, event_str)
        print('[%s] Attempting to reconnect...', self.worker_name)

    def on_pubmsg(self, c, e):
        self.do_command("test")
        return

    def do_command(self, msg):
        # c = self.connection
        self.connection.privmsg(self.channel_id, msg)

    def check_messages(self):
        if self.isConnected:
            self.msg_lock.acquire()
            try:
                for message in self.message_queue:
                    self.connection.privmsg(self.channel_id, message)
                self.message_queue.clear()
            finally:
                self.msg_lock.release()
                threading.Timer(3, self.check_messages).start()
        

    def add_message(self, msg):
        self.msg_lock.acquire()
        try:
            self.message_queue.append(msg)
        finally:
            self.msg_lock.release()

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
