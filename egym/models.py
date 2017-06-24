import json

class EgymModel(object):
    """ Base class from which all egym models will inherit. """

    def __init__(self, **kwargs):
        self.param_defaults = {}

    def __str__(self):
        """ Returns a string representation of EgymModel. By default
        this is the same as AsJsonString(). """
        return self.AsJsonString()

    def AsJsonString(self):
        """ Returns the EgymModel as a JSON string based on key/value
        pairs returned from the AsDict() method. """
        return json.dumps(self.AsDict(), sort_keys=True)

    def AsDict(self):
        """ Create a dictionary representation of the object. Please see inline
        comments on construction when dictionaries contain EgymModels. """
        data = {}

        for (key, value) in self.param_defaults.items():

            if isinstance(getattr(self, key, None), (list, tuple, set)):
                data[key] = list()
                for subobj in getattr(self, key, None):
                    if getattr(subobj, 'AsDict', None):
                        data[key].append(subobj.AsDict())
                    else:
                        data[key].append(subobj)

            elif getattr(getattr(self, key, None), 'AsDict', None):
                data[key] = getattr(self, key).AsDict()

            elif getattr(self, key, None):
                data[key] = getattr(self, key, None)
        return data

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
            'sessionIsoDate': None, 
            'exercises': None
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))

        if 'exercises' in kwargs:
            ex = []
            for e in kwargs.get('exercises'):
                ex.append(Exercise.NewFromJsonDict(e))
            self.exercises = ex

class Exercise(EgymModel):

    def __init__(self, **kwargs):
        self.param_defaults = {
            'exerciseId': None,
            'eGymCircleExercises': None,
            'done': None,
            'sets': None, 
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))
        if 'eGymCircleExercises' in kwargs:
            ex = []
            for e in kwargs.get('eGymCircleExercises'):
                ex.append(Exercise.NewFromJsonDict(e))
            self.eGymCircleExercises = ex
        
        if 'sets' in kwargs:
            sets = []
            for e in kwargs.get('sets'):
                sets.append(Set.NewFromJsonDict(e))
            self.sets = sets

class Set(EgymModel):
               
    def __init__(self, **kwargs):
        self.param_defaults = {
            "numberOfReps": None,
            "weight": None,
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))
