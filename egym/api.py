#!/usr/bin/env python

import requests
import logging

# These two lines enable debugging at httplib level (requests->urllib3->http.client)
# You will see the REQUEST, including HEADERS and DATA, and RESPONSE with HEADERS but without DATA.
# The only thing missing will be the response.body which is not logged.
try:
    import http.client as http_client
except ImportError:
    # Python 2
    import httplib as http_client
http_client.HTTPConnection.debuglevel = 1

# You must initialize logging, otherwise you'll not see debug output.
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)
requests_log = logging.getLogger("requests.packages.urllib3")
requests_log.setLevel(logging.DEBUG)
requests_log.propagate = True

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
        headers = self.buildHeaders()
        res = requests.post(url=self.base_url+endpoint,
                            json={'email': self.email, 'password': self.password},
                            headers=headers)
        self.token = res.json()['accessToken']
        self.userid = res.json()['userId']

    def GetUserSessions(self):
        endpoint = 'user/sessions'
        headers = self.buildHeaders()
        res = requests.get(url=self.base_url+endpoint,
                            data={'end': '04.06.2017'},
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
