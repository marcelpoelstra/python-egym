#!/usr/bin/env python

class Api(object):
    """A python interface into the eGym API"""

    def __init__(self,
            user=None,
            password=None,
            token=None,
            base_url=None):
        if base_url is None:
            self.base_url = 'https://www.'
        else:
            self.base_url = base_url

    def GetUserActivities(self):
        return "Bla"
