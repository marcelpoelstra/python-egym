class EgymModel(object):
    def __init__(self, **kwargs):
        self.param_defaults = {}

class Activity(EgymModel):

    def __init__(self, **kwargs):
        self.param_defaults = {
                'date': None
                'value': None}


