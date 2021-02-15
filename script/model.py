import re, pickle, os
from tool import log as l
from collections import namedtuple


log = l("Model")



class PyTeam:
    def __init__(self, *args):
        self.team_id = args[0]
        self.name    = args[1]
        self.country = args[2]
        self.fixtures = []


class Score:
    # __slots__ = ("half_time", "fulltime", "extra_time", "penalty")
    def __init__(self, *args):
        self.half_time  = args[0]
        self.fulltime   = args[1]
        self.extra_time = args[2]
        self.penalty    = args[3]

class TeamFixture:
    # __slots__ = ("team_id", "name", "logo")
    def __init__(self, *args):
        self.team_id = args[0]
        self.name    = args[1]
        self.logo    = args[2]


class PyFixture( namedtuple("PyFixture",
                            ["fixture_id", "status","score","homeTeam","awayTeam", "goalsHomeTeam", "goalsAwayTeam"])):
    pass

if __name__ == '__main__':
    pass