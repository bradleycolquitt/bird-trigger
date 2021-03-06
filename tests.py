#! /usr/bin/env python

import time
import set_target as st

def setup_two_feeds():
    sf = st.SuperFeed()
    sf.add_feed("feed0", 0)
    sf.add_feed("feed1", 1)
    return sf

def define_targets():
    sf = setup_two_feeds()
    sf.feeds[0].define_target("target0", (45, 45, 200, 200), "motion")
    sf.feeds[0].define_target("target0-1", (250, 250, 400, 400), "detect")
    sf.feeds[1].define_target("target1", (45, 45, 200, 200))
    return sf

def test_start_all_feeds(sf):
    sf.start_all_feeds()

def test_activate_feed(sf):
    sf.activate_feed(0)
    sf.start_subset_feeds()

def test_activate2_feed(sf):
    [sf.activate_feed(x) for x in [0,1]]
    sf.start_subset_feeds()

def test_target_event(sf):
    sf.feeds[0].activate_targets()
    sf.feeds[0].start_targets()

def test_target_active(sf):
    sf.feeds[0].activate_targets()
    sf.feeds[1].activate_targets()
    sf.start_all_feeds()
