#!/usr/bin/env python

import requests
from datetime import date
from datetime import datetime
from egym import (
    Session,
    Exercise,
    Set
)

class Api(object):
    """A python interface into the eGym API"""
    userid = None

    def __init__(self,
            email=None,
            password=None,
            token=None,
            base_url=None):
        if base_url is None:
            self.base_url = 'https://www.egym.de/egym-rest/mobile/'
        else:
            self.base_url = base_url

        self.email = email
        self.password = password
        if token is None:
            self.GetUserLogin()
        else:
            self.token = token

    def GetUserLogin(self):
        endpoint = 'v2/auth/login'
        headers = self.buildHeaders()
        res = requests.post(url=self.base_url+endpoint,
                            json={'email': self.email, 'password': self.password},
                            headers=headers)
        self.token = res.json()['accessToken']
        self.userid = res.json()['userId']

    def GetUserSessions(self, start, end):
        endpoint = 'v2/user/sessions'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            params={'start': start, 'end': end},
                            headers=headers)
        dates = []
        for s in res.json():
            dates.append(datetime.strptime(s, "%Y-%m-%d").date())
        return dates

    def GetSessionData(self, date):
        endpoint = 'v2/user/sessions/{}'.format(date)
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        data = res.json()
        session = Session.NewFromJsonDict(res.json())
        return session

    def GetUserDashboard(self):
        endpoint = 'v2/user/dashboard'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def GetUserProfile(self):
        endpoint = 'v2/user/profile'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def GetMuscleAnalysis(self):
        endpoint= 'v2/user/analysis/muscle-analysis'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def GetBioAge(self):
        endpoint= 'v2/user/analysis/bioage'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def GetBodyData(self):
        endpoint= 'v2/user/analysis/bodydata'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def GetMaxForce(self):
        endpoint= 'v3/user/analysis/maxforce/?limit=500'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def GetRanking(self):
        endpoint= 'v2/user/ranking/gym'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def GetFriends(self):
        endpoint= 'v2/user/ranking/fitnessteam'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            headers=headers)
        return res.json()

    def buildHeaders(self):
        headers = {
            'User-Agent': 'Mozilla/5.0 (Linux; Android 7.0; Pixel C Build/NRD90M; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/52.0.2743.98 Safari/537.36',
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Timezone': 'UTC',
            'Accept-Language': 'de-DE',
            }
        if self.userid != None and self.token != None:
            headers['Authorization'] = "Egym {}:{}".format(self.userid, self.token)
        return headers
