import streamlink
import cv2

class VideoCapturer:
    def __init__(self, link):
        self.streamURL = link
        self.res = ['720p', '1080p', 'audio_only', 'best', 'worst']
        self.frame = None

    def read(self):
        streams = streamlink.streams(self.streamURL)
        if not streams:
            return None
        
        for resolution in self.res:
            if resolution in streams:
                url = streams[resolution].url
                break
        vid = cv2.VideoCapture(url)

        succ, frame = vid.read()
        if succ:
            vid.release()
            self.frame = frame
            return frame
        else:
            print("No frame to read!\n")
            self.frame = None

        vid.release()
        return None

    def displayImage(self):
        if self.frame is not None:
            cv2.namedWindow("Image")
            cv2.imshow("Image", self.frame)
            cv2.waitKey(0)
        else:
            print("No frame to display!\n")

    def saveFrame(self):
        if self.frame is not None:
            print("Saving frame...")
            cv2.imwrite('frame.jpg', self.frame)
        else:
            print("Unable to save frame")

