import sys
import Tkinter as tk
import cv2
import pdb
import logging
import numpy as np
import multiprocessing as mp
from collections import deque

import triggers
"""

"""

PLATFORM=sys.platform
ENTER=13
ESC=27
if PLATFORM == "linux2":
    ENTER = 10


############# LOGGING ############

module_logger = logging.getLogger("bird_trigger")
module_logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#fh = logging.FileHandler('super.log')
#fh.setLevel(logging.INFO)
#formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
#fh.setFormatter(formatter)
#module_logger.addHandler(fh)
#module_logger.info("Created SuperFeed, initialized logging.")

# # create logger with 'spam_application'
# logger = logging.getLogger('spam_application')
# logger.setLevel(logging.DEBUG)
# # create file handler which logs even debug messages
# fh = logging.FileHandler('spam.log')
# fh.setLevel(logging.DEBUG)
# # create console handler with a higher log level
# ch = logging.StreamHandler()
# ch.setLevel(logging.ERROR)
# # create formatter and add it to the handlers
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# fh.setFormatter(formatter)
# ch.setFormatter(formatter)
# # add the handlers to the logger
# logger.addHandler(fh)
# logger.addHandler(ch)

# logger.info('creating an instance of auxiliary_module.Auxiliary')

class SuperGui(tk.Frame):
    def __init__(self):
        self.main = tk.Tk()
        self.superfeed = SuperFeed()

        start_feed_button = tk.Button(self.main, text="Start feed", 
                                       command=self.start_feed)
        self.device_entry = tk.Entry(self.main)
        self.feed_name_entry = tk.Entry(self.main)
        self.device_label = tk.Label(self.main, text="Device")
        self.feed_name_label = tk.Label(self.main, text="Feed name")

        start_feed_button.grid(row=1,column=0)
        self.feed_name_entry.grid(row=1,column=1)
        self.feed_name_label.grid(row=0,column=1)
        self.device_label.grid(row=0,column=2)
        self.device_entry.grid(row=1,column=2)

        self.main.mainloop()

    def start_feed(self):
        feed_name = self.feed_name_entry.get()
        device = self.device_entry.get()
        self.superfeed.add_feed(feed_name, device)

        try:
            self.superfeed.feeds[device].start_feed()
            feedgui = FeedGui(self, self.superfeed.feeds[device])
        except KeyError:
            print "Feed initialization failed."

    def launch_target_window(self):
        targetgui = TargetGui(self)

    def start_targets(self):
        self.mainfeed.start_targets()

    def stop_targets(self):
        self.mainfeed.stop_targets()

class FeedGui:
    def __init__(self, parent, feed):
        #pdb.set_trace()
        self.parent = parent
        self.feed = feed
        self.main = tk.Toplevel()

        add_target_button = tk.Button(self.main, text= "Add target manually",
                                      command=self.launch_target_window)
        start_targets_button = tk.Button(self.main, text="Start target monitoring",
                                          command=self.start_targets)
        stop_targets_button = tk.Button(self.main, text="Stop target monitoring",
                                          command=self.stop_targets)
        #start_feed_button.grid(row=0,column=0)
        #self.start_feed_entry.grid(row=0,column=1)
        add_target_button.grid(row=1,column=0)
        start_targets_button.grid(row=2,column=0)
        stop_targets_button.grid(row=3,column=0)

        #self.main.mainloop()

    def launch_target_window(self):
        targetgui = TargetGui(self)

    def start_targets(self):
        self.feed.start_targets()

    def stop_targets(self):
        self.feed.stop_targets()

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
        self.gui.quit()
        #self.gui.destroy()

class SuperFeed:
    def __init__(self):
        self.window_name = "SuperFeed"
        self.feeds = {}
        self.feeds_active = set() # set of feed names
        self.p = None

        # To hold results form individual feeds
        # Consistent print out
        self.queue = mp.Queue()

        ### Logging ###
        self.superlog = logging.getLogger('bird_trigger.super')
        self.superlog.setLevel(logging.DEBUG)
        fh = logging.FileHandler('super.log')
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.superlog.addHandler(fh)

        self.superlog.info("Created SuperFeed, initialized logging.")

    def add_feed(self, feed_name, device):
        self.feeds[device] = MainFeed(self, feed_name, device)
        self.superlog.info("Created feed, name: {0}, device: {1}".format(feed_name, device))

    def activate_feed(self, device):
        if not device in self.feeds_active:
            self.feeds_active.add(device)
            self.superlog.info("Activated feed, name: {0}, device: {1}".format(self.feeds[device].feed_name, device))
            return 0
        else:
            return 1

    def deactivate_feed(self, device):
        try:
            self.feeds_active.remove(device)
            self.superlog.info("Deactivated feed, name: {0}, device: {1}".format(self.feeds[device].feed_name, device))
            return 0
        except KeyError:
            return 1

    def deactivate_all_feeds(self):
        self.feeds_active.clear()
        self.superlog.info("Deactivated all feeds.")

    def start_all_feeds(self):
        if not self.p == None:
            self.stop_feeds()
        #self.queue = mp.Queue()
        self.p = mp.Process(target=self._start_all_feeds)
        self.superlog.info("Started all feeds.")
        self.p.start()
        self.p.join()
        #print self.queue.get()
        #while (self.p.is_alive()):
        #    pass
           # print self.queue.get()

    def _start_all_feeds(self):
        while True:
            for feed in self.feeds.itervalues():
                ret, frame = feed.read()
                if ret:
                    feed.read_targets(self.queue)
                    #print self.queue.get()
                    cv2.imshow(feed.feed_name, frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ESC: break

    def start_subset_feeds(self):
        if not self.p == None:
            self.stop_feeds()
        self.queue = mp.Queue()
        self.p = mp.Process(target=self._start_subset_feeds, args=(self.queue,))
        self.superlog.info("Started subset of feeds: {0}".format(self.feeds_active))
        self.p.start()
        self.p.join()
        self.superlog.info("Stopped subset of feeds: {0}".format(self.feeds_active))
        #print self.queue.get()
        #while (self.p.is_alive()):
        #    print self.queue.get()

    def _start_subset_feeds(self, queue):
        if len(self.feeds_active) > 0:
            while True:
                for device in self.feeds_active:
                    ret, frame = self.feeds[device].read()
                    if ret:
                        self.feeds[device].read_targets(self.queue)
                        cv2.imshow(self.feeds[device].feed_name, frame)
                k = cv2.waitKey(1) & 0xFF
                if k == ESC: break
        else:
            print "No feeds active."

    def start_all_targets(self):
        while True:
            for feed in self.feeds.itervalues():
                ret, frame = feed.read()
                if ret:
                    cv2.imshow(feed.feed_name, frame)
                    feed.read_targets()
            k = cv2.waitKey(1) & 0xFF
            if k == ESC: break

    def stop_feeds(self):
        self.p.terminate()
        self.p = None

    def remove_feed(self, device):
        self.feeds[device] = None

class MainFeed:
    def __init__(self, parent, feed_name, device=0):
        self.parent = parent
        self.feed_name = feed_name
        self.device = device
        self.frame = None
        self.gui = None
        self.targets = {}
        self.targets_active = False
        self.cap = cv2.VideoCapture(device)

        ### Logging ###
        self.mainlog = logging.getLogger('bird_trigger.super.main' + str(self.device))
        self.mainlog.setLevel(logging.DEBUG)
        fh = logging.FileHandler('main{0}.log'.format(self.device))
        fh.setLevel(logging.INFO)
        fh.setFormatter(formatter)
        self.mainlog.addHandler(fh)

    def read(self):
        ret, self.frame = capture_grey(self.cap)
        return ret, self.frame

    ############## Target methods ###############
    def activate_targets(self):
         self.targets_active = True
         self.mainlog.info("Activated all targets.")

    def deactivate_targets(self):
         self.targets_active = False
         self.mainlog.info("Deactivated all targets.")

    # def start_feed(self):
    #     while(1):
    #         ret,self.frame = capture_grey(self.cap)
    #         if ret:
    #             cv2.imshow(self.feed_name,self.frame)
    #         k = cv2.waitKey(50) & 0xFF
    #         if k == ENTER or k == ESC:
    #             break

    def add_target(self, target_name, mode="motion"):
        """Allows user to define target region using mouse"""
        if not target_name in self.targets:
            target = Target(self, self.feed_name, target_name, self.frame, mode)
            cv2.setMouseCallback(self.feed_name,target.draw_rectangle)
            while(1):
                cv2.imshow(self.feed_name,self.frame)
                k = cv2.waitKey(60) & 0xFF
                if k == ESC:
                    break
                    #return 1
                elif k == ENTER:
                    cv2.setMouseCallback(self.feed_name,target.mouse_none)
                    self.targets[target_name] = target
                    print target.get_target_coords()
                    return 0
        else:
            print "Target name exists. Choose another."
            return 1

    def define_target(self, target_name, positions, mode="motion"):
        """Target defined by given positions"""
        if not target_name in self.targets:
            target = Target(self, self.feed_name, target_name, self.frame, mode)
            target.set_target_coords(positions)
            self.targets[target_name] = target
        else:
            print "Target name exists. Choose another."

    def start_targets(self):
        while(1):
            ret,self.frame = capture_grey(self.cap)
            if ret:
                self.read_targets(self.parent.queue)
                cv2.imshow(self.feed_name, self.frame)
            k = cv2.waitKey(1) & 0xFF
            if k == ESC:
                break

    def stop_targets(self):
        if not self.camera_process == None:
            self.camera_process.join()
        else:
            print "Monitoring not running."

    # def start_targets_worker(self):
    #     while(1):
    #         ret,self.frame = capture_grey(self.cap)
    #         if ret:
    #             cv2.imshow(self.feed_name, self.frame)
    #             [target.check_target(self.frame)
    #                   for target in self.targets.itervalues()]
    #             k = cv2.waitKey(200) & 0xFF
    #             if k == 27:
    #                 cv2.destroyAllWindows()
    #                 break

    def read_targets(self, queue):
        if self.targets_active:
            val = None
            for target in self.targets.itervalues():
                cs = target.get_target_coords()
                cv2.rectangle(self.frame,(cs[0], cs[1]), (cs[2], cs[3]), (255, 0, 0), 1)
                val = target.check_target(self.frame)
                queue.put(val)

class Target:
    def __init__(self, parent, feed_name, target_name, frame, mode):
        self.parent = parent
        self.feed_name = feed_name
        self.target_name = target_name
        self.frame = frame
        self.ix, self.iy, self.fx, self.fy = -1,-1,-1,-1
        self.thresh = 100
        self.buffer_size = 10
        self.buffer = np.zeros(self.buffer_size)

        self.buffer_frame = deque(maxlen=3)
        self.mode = mode

    def draw_rectangle(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            cv2.imshow(self.feed_name,self.frame)
            self.ix,self.iy = x,y

        elif event == cv2.EVENT_LBUTTONUP:
            cv2.rectangle(self.frame,(self.ix,self.iy),(x,y),(255,0,0),1)
            self.fx,self.fy = x,y

    def mouse_none(self, event, x, y, flags, param):
        """Null function for mouse callback"""
        pass

    def set_target_coords(self, coords):
        #pdb.set_trace()
        self.ix, self.iy, self.fx, self.fy = coords

        #initialize frame deque
        for i in range(2):
            ret,frame = capture_grey(self.parent.cap)
            self.buffer_frame.append(frame[coords[0]:coords[2], coords[1]:coords[3]])

    def get_target_coords(self):
        """Get coordinates of defined target region"""
        assert self.ix >= 0 and self.iy >= 0, "Target region hasn't been defined yet."
        return (self.ix, self.iy, self.fx, self.fy)
    
    def get_roi_pixels(self):
        """Return pixels of stored frame within defined target """
        coords = self.get_target_coords()
        return self.frame[coords[0]:coords[2], coords[1]:coords[3]]

    def check_target(self, frame):
        if self.mode == "detect":
            return self.check_target_detect(frame)
        elif self.mode == "motion":
            return self.check_target_motion(frame)

    def check_target_detect(self, frame):
        """Continually compute the mean pixel value within defined target
        Trigger sound playback whenever mean exceeds threshold
        """
        cs = self.get_target_coords()

        cv2.rectangle(frame,(cs[0], cs[1]), (cs[2], cs[3]), (255, 0, 0), 1)
        self.buffer = np.roll(self.buffer, -1)
        self.buffer[-1] = np.mean(np.mean(frame[cs[0]:cs[2], cs[1]:cs[3]], 0),0)

        buffer_mean = np.mean(self.buffer)

        if buffer_mean < self.thresh:
            print "Trigger:",self.target_name, buffer_mean
            self.trigger_event()
            return (self.target_name, buffer_mean)

    def check_target_motion(self, frame):
        """Compute absolute difference between series of images to detect motion"""
        cs = self.get_target_coords()

        self.buffer_frame.append(frame[cs[0]:cs[2], cs[1]:cs[3]])
        motion = diff_image_ratio(self.buffer_frame)
        changes = detect_motion(motion, 20)

        if changes > 10:
            print "Trigger:",self.target_name, changes
            self.trigger_event()
            return (self.target_name, changes)

    def trigger_event(self):
        pass

def capture_grey(cap):
    ret,frame = cap.read()
    if ret:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    return ret,frame

def diff_image_ratio(images):
    d1 = cv2.absdiff(images[0], images[1])
    d2 = cv2.absdiff(images[1], images[2])
    motion = cv2.bitwise_and(d1,d2)
    motion = cv2.threshold(motion, 35, 255, cv2.THRESH_BINARY)
    return cv2.erode(motion[1], np.ones((5,5),np.uint8))

    #return np.sum(cv2.bitwise_and(d1,d2)) / np.prod(np.shape(d1))
    #return cv2.bitwise_and(d1, d2)

def diff_image_ratio2(images):
    diffs = [cv2.absdiff(images[i],images[i+1]) for i in xrange(len(images)-1)]
    return np.mean([np.mean(x) for x in diffs])
    #return np.sum(cv2.bitwise_and(d1,d2)) / np.prod(np.shape(d1))
    #return cv2.bitwise_and(d1, d2)

def detect_motion(motion, max_deviation):
    motion_mean = np.mean(motion)
    motion_sd = np.std(motion)

    number_of_changes = 0
    if motion_sd < max_deviation:
        number_of_changes = np.sum(motion[motion==255])

    return number_of_changes

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
