import sys
import numpy as np
import cv2
import easygui
import pdb

import pyaudio
import wave

def capture_grey(cap):
    ret,frame = cap.read()
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return ret,frame

class Target:
    def __init__(self):
        self.frame = ""
        self.ix, self.iy, self.fx, self.fy = -1,-1,-1,-1
    
    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            cv2.imshow("image",self.frame)
            self.ix,self.iy = x,y

        elif event == cv2.EVENT_LBUTTONUP:
            cv2.rectangle(self.frame,(self.ix,self.iy),(x,y),(255,0,0),1)
            self.fx,self.fy = x,y

    def mouse_none(self, event, x, y, flags, param):
        """Null function for mouse callback"""
        pass

    def get_target_coords(self):
        """Get coordinates of defined target region"""
        assert self.ix >= 0 and self.iy >= 0, "Target region hasn't been defined yet."
        return (self.ix, self.iy, self.fx, self.fy)
    
    def get_roi_pixels(self):
        """Return pixels of stored frame within defined target """
        coords = self.get_target_coords()
        return self.frame[coords[0]:coords[2], coords[1]:coords[3]]

    def set_target(self):       
        cap = cv2.VideoCapture(0)              # Initialize camera
        cv2.namedWindow('image')    

        ## Take initial image
        while(1):
            ret,self.frame = capture_grey(cap)
            if ret:
                cv2.imshow("image",self.frame)
                k = cv2.waitKey(60) & 0xFF
                if k == 13:
                    break
        cap.release()

        ## Target definition
        cv2.setMouseCallback('image',self.draw_rectangle)
        while(1):
            cv2.imshow('image',self.frame)
            k = cv2.waitKey(60) & 0xFF
            if k == 27:
                break
            elif k == 13: # Enter has been pressed
                cv2.setMouseCallback('image',self.mouse_none)
                return self.get_target_coords()

    # TODO buffer roi mean to prevent spurious triggering
    def check_roi(self, thresh):
        """Continually compute the mean pixel value within defined target
        Trigger sound playback whenever mean exceeds threshold 
        """

        cs = target_obj.get_target_coords()
        cap = cv2.VideoCapture(0)      

        while(1):
            ret,frame = capture_grey(cap)

            cv2.rectangle(frame,(cs[0], cs[1]), (cs[2], cs[3]), (255, 0, 0), 1)
            cv2.imshow('image', frame)

            roi_mean = np.mean(np.mean(frame[cs[0]:cs[2], cs[1]:cs[3]], 0),0)
            print roi_mean
            if roi_mean > thresh:
                print "Trigger", roi_mean
                trigger_playback()
            
            k = cv2.waitKey(200) & 0xFF
            if k == 27:
                cv2.destroyAllWindows()
                break
    
def test_roi(target_obj):
    cs = target_obj.get_target_coords()
    print cs
    cap = cv2.VideoCapture(0)      
    while(1):
        ret,frame = capture_grey(cap)

        cv2.rectangle(frame,(cs[0], cs[1]), (cs[2], cs[3]), (255, 0, 0), 1)
        cv2.imshow('image', frame)
        
        print np.mean(np.mean(frame[cs[0]:cs[2], cs[1]:cs[3]], 0),0)
        k = cv2.waitKey(1000) & 0xFF
        if k == 27:
            cv2.destroyAllWindows()
            break

def trigger_playback():
    chunk = 1024
    wav = wave.open("/Users/bradcolquitt/projects/opencv/beep-01a.wav", "rb")
    p = pyaudio.PyAudio()  
    #open stream  
    stream = p.open(format = p.get_format_from_width(wav.getsampwidth()),  
                channels = wav.getnchannels(),  
                rate = wav.getframerate(),  
                output = True)  
    #read data  
    data = wav.readframes(chunk)  

    #paly stream  
    while data != '':  
        stream.write(data)  
        data = wav.readframes(chunk)  

    #stop stream  
    stream.stop_stream()  
    stream.close()  

    #close PyAudio  
    p.terminate()  

#target_obj = Target()
#target_coords = target_obj.set_target()
#print target_coords
#roi = target_obj.get_roi_pixels()
#print target_obj.get_target_coords()




