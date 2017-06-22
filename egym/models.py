import json

class EgymModel(object):
    """ Base class from which all egym models will inherit. """

    def __init__(self, **kwargs):
        self.param_defaults = {}

    def __str__(self):
        """ Returns a string representation of EgymModel. By default
        this is the same as AsJsonString(). """
        return self.AsJsonString()

    @classmethod
    def NewFromJsonDict(cls, data, **kwargs):
        """ Create a new instance based on a JSON dict. Any kwargs should be
        supplied by the inherited, calling class.
        Args:
            data: A JSON dict, as converted from the JSON in the egym API.
        """

        json_data = data.copy()
        if kwargs:
            for key, val in kwargs.items():
                json_data[key] = val

        c = cls(**json_data)
        c._json = data
        return c

class Session(EgymModel):

    def __init__(self, **kwargs):
        self.param_defaults = {
            'date': None, 
            'exercises': None
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))


class Exercise(EgymModel):

    def __init__(self, **kwargs):
        self.param_defaults = {
            'exerciseId': None, 
            'generalExerciseId': None, 
            'done': None, 
            'numberOfReps': None, 
            'weight': None, 
            'exerciseType': None
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))
