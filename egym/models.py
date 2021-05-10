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
            'template': 0,
            'sessionDate': 0,
            'sessionIsoDate': 0, 
            'exercises': [],
            'points': 0,
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))

        if 'exercises' in kwargs:
            ex = []
            for e in kwargs.get('exercises'):
                ex.append(Exercise.NewFromJsonDict(e))
            self.exercises = ex 

    def getTemplate(self):
        return self.getTemplate

    def getSessionDate(self):
        return self.sessionDate
    
    def getIsoDate(self):
        return self.sessionIsoDate

    def getExercises(self):
        return self.exercises

    def getPoints(self):
        return self.points

class Exercise(EgymModel):

    def __init__(self, **kwargs):
        self.param_defaults = {
            'exerciseType': 0,
            'uniqueExerciseClientId': 0,
            'exerciseId': 0,
            'generalExerciseId': 0,
            'duration': 0,
            'targetSpeed': 0,
            'distance': 0,
            'sets': [], 
            'done': 0,
            'dataSource': 0,
            'points': 0,
            'created': 0,
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))
        
        if 'sets' in kwargs:
            sets = []
            for e in kwargs.get('sets'):
                sets.append(Set.NewFromJsonDict(e))
            self.sets = sets

    def getExerciseType(self):
        return self.exerciseType

    def getUniqueExerciseClientId(self):
        return self.uniqueExerciseClientId

    def getExerciseId(self):
        return self.exerciseId

    def getGeneralExerciseId(self):
        return self.generalExerciseId

    def getDuration(self):
        return self.duration
    
    def getTargetSpeed(self):
        return int(self.targetSpeed)
    
    def getDistance(self):
        return self.distance

    def getDone(self):
        return self.done

    def getDataSource(self):
        return self.dataSource

    def getExPoints(self):
        return self.points

    def getCreated(self):
        return self.created

    def getSets(self):
        return self.sets

class Set(EgymModel):
               
    def __init__(self, **kwargs):
        self.param_defaults = {
            "setType": 0,
            "numberOfReps": 0,
            "weight": 0,
        }
        for (param, default) in self.param_defaults.items():
            setattr(self, param, kwargs.get(param, default))

    def getSetType(self):
        return self.setType

    def getWeight(self):
        return self.weight

    def getReps(self):
        return self.numberOfReps
