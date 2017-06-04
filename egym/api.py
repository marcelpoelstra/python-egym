#!/usr/bin/env python

import requests

class Api(object):
    """A python interface into the eGym API"""
    userid = None

    def __init__(self,
            email=None,
            password=None,
            token=None,
            base_url=None):
        if base_url is None:
            self.base_url = 'https://www.egym.de/egym-rest/mobile/v2/'
        else:
            self.base_url = base_url

        self.email = email
        self.password = password
        if token is None:
            self.GetUserLogin()
        else:
            self.token = token

    def GetUserLogin(self):
        endpoint = 'auth/login'
        post_headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
            'Content-Type': 'application/json'}
        res = requests.post(url=self.base_url+endpoint,
                            json={'email': self.email, 'password': self.password},
                            headers=post_headers)
        self.token = res.json()['accessToken']
        self.userid = res.json()['userId']

    def GetUserActivities(self):
        return "Bla"

    def GetUserSessions(self):
        endpoint = 'user/sessions'
        post_headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
            'Content-Type': 'application/json'}
        res = requests.get(url=self.base_url+endpoint,
                            json={'token': self.token},
                            headers=post_headers)
        return res.json()
