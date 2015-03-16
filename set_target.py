import sys

import Tkinter as tk
import cv2
import easygui
import pdb

import numpy as np
import multiprocessing as mp

import pyaudio
import wave

"""
## Classes:

# mainImage
#    contains video feed and dictionary of Targets
#    image is subprocessed to each target and processed independently
#    contains Logger to record threshold events and events Triggered

Gui

# Target
#    contains roi and functions to analyze pixels within roi
#    specification of TriggerEvent
#    function to run 2 subprocesses
#       1. real-time compute of ROI stats and updates buffer
#           if pixel means over threshold
#              add value to buffer
#              if time_increment: 
#                  check if buffer mean over thresh
#       2. subprocess that periodically checks if buffer over some threshold

TriggerEvent
       contains multiple functions for possible output events 

Protocol 
Initialize main feed
Take background image
Define target regions on image
    Load config file containing
        buffer size
        time period
        number events per time period
             or 
        number events before refractory
        datetime active 
        
    Specify TriggerEvent

"""
class TriggerGui:
    def __init__(self):
        self.main = tk.Tk()
        self.mainfeed = None

        start_feed_button = tk.Button(self.main, text="Start feed", 
                                       command=self.start_feed)
        add_target_button = tk.Button(self.main, text= "Add target manually",
                                      command=self.launch_target_window)
        start_targets_button = tk.Button(self.main, text="Start target monitoring",
                                          command=self.start_targets)
        stop_targets_button = tk.Button(self.main, text="Stop target monitoring",
                                          command=self.stop_targets)
        start_feed_button.grid(row=0,column=0)
        add_target_button.grid(row=1,column=0)
        start_targets_button.grid(row=2,column=0)
        stop_targets_button.grid(row=3,column=0)
        self.main.mainloop()

    def start_feed(self):
        self.mainfeed = MainFeed()

    def launch_target_window(self):
        targetgui = TargetGui(self)

    def start_targets(self):
        self.mainfeed.start_targets()
        
    def stop_targets(self):
        self.mainfeed.stop_targets()

class TargetGui:
    def __init__(self, parent):
        self.parent = parent
        self.target_name = None
        self.gui = tk.Tk()
        self.label = tk.Label(self.gui, text="Target name")
        self.entry = tk.Entry(self.gui, variable=self.target_name)
        self.button = tk.Button(self.gui, text="OK", command=self.define_target)

        self.label.pack()
        self.entry.pack()
        self.button.pack()

        self.gui.mainloop()

    def define_target(self):
        self.parent.mainfeed.add_target(self.entry.get())
        self.gui.destroy()

class MainFeed:
    def __init__(self):
        self.window_name = "MainFeed"
        self.frame = None
        self.gui = None
        self.targets = {}
        self.cap = cv2.VideoCapture(0)
        cv2.namedWindow(self.window_name)    
        
        ## Take initial image
        while(1):
            ret,self.frame = capture_grey(self.cap)
            if ret:
                cv2.imshow(self.window_name,self.frame)
                k = cv2.waitKey(60) & 0xFF
                if k == 13:
                    break
        #self.cap.release()

    def add_target(self, target_name):
        ## Target definition
        if not target_name in self.targets:
            target = Target(self.window_name, target_name, self.frame)
            cv2.setMouseCallback(self.window_name,target.draw_rectangle)
            while(1):
                cv2.imshow(self.window_name,self.frame)
                k = cv2.waitKey(60) & 0xFF
                if k == 27: # ESC pressed
                    break
                    return 1
                elif k == 13: # Enter pressed
                    cv2.setMouseCallback(self.window_name,target.mouse_none)
                    self.targets[target_name] = target
                    print target.get_target_coords()
                    return 0
        else:
            print "Target name exists. Choose another."
            return 1

    ## TODO get multiprocessing to work
    def start_targets(self):
        self.camera_process = mp.Process(target=self.start_targets_worker)
        self.camera_process.start()
        
    def stop_targets(self):
        if not self.camera_process == None:
            self.camera_process.join()
        else:
            print "Monitoring not running."

    def start_targets_worker(self):
        while(1):
            ret,self.frame = capture_grey(self.cap)
            if ret:
                cv2.imshow(self.window_name, self.frame)
                [target.check_target(self.frame) 
                      for target in self.targets.itervalues()]
        #pool = mp.Pool(len(self.targets))
        #pool.map(start_targets_worker, self.targets.itervalues())
    #                start_targets_worker(self.targets.itervalues().next(), self)
                k = cv2.waitKey(200) & 0xFF
                if k == 27:
                    cv2.destroyAllWindows()
                    break
    

class Target:
    def __init__(self, window_name, target_name, frame):
        self.window_name = window_name
        self.target_name = target_name
        self.frame = frame
        self.ix, self.iy, self.fx, self.fy = -1,-1,-1,-1
        self.thresh = 100
    
    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            cv2.imshow(self.window_name,self.frame)
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

    # TODO buffer roi mean to prevent spurious triggering
    def check_target(self, frame):
        """Continually compute the mean pixel value within defined target
        Trigger sound playback whenever mean exceeds threshold 
        """
        cs = self.get_target_coords()

        cv2.rectangle(frame,(cs[0], cs[1]), (cs[2], cs[3]), (255, 0, 0), 1)
        #cv2.imshow(self.window_name, frame)

        roi_mean = np.mean(np.mean(frame[cs[0]:cs[2], cs[1]:cs[3]], 0),0)
        print roi_mean
        if roi_mean > self.thresh:
            print "Trigger:",self.target_name, roi_mean
            self.trigger_event()

        

    def trigger_event(self):
        pass

def capture_grey(cap):
    ret,frame = cap.read()
    if ret: 
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return ret,frame
    
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




