from config import TOKEN, BASE_DIR
import requests, os, requests_cache, transaction, json, math, pickle, time
from ZODB import FileStorage, DB
from persistent import Persistent
from collections import namedtuple
from BTrees.OOBTree import OOBTree
from model import PyTeam, PyFixture, Score, TeamFixture
from tool import log as l
from itertools import count
# from psutil import virtual_memory
# len(root["fixture"].keys())
import resource
# from memory_profiler import memory_usage
# resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
# convert_size(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)

log = l("Api.py")

def get_size_memory():
    
    def convert_size(size_bytes):
       if size_bytes == 0:
           return "0B"
       size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
       i = int(math.floor(math.log(size_bytes, 1024)))
       p = math.pow(1024, i)
       s = round(size_bytes / p, 2)
       return "%s %s" % (s, size_name[i])

    result = convert_size(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    
    return result

class cdict(dict):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self._p_changed = 0

storage = FileStorage.FileStorage( os.path.join( BASE_DIR,  "storage", "Storage.fs"), pack_keep_old=False )
zopedb = DB(storage)
connection = zopedb.open()

root = connection.root()
# breakpoint()

# requests_cache.install_cache('demo_cache')

headers = {
    'x-rapidapi-host': "api-football-v1.p.rapidapi.com",
    'x-rapidapi-key': TOKEN
}

def error_connection_continue_work(f):
    
    def wrapper(*args, **kwargs):
        for c in count():
            
            try:
                res = f(*args, **kwargs)
                break
            except Exception as e:
                if c > 100:break
                log.error("Error: %s", str(e), exc_info = True )
                time.sleep(10)
                continue

        return res

    return wrapper

@error_connection_continue_work
def get_fixtures_team(team_id):
    url = f"https://api-football-v1.p.rapidapi.com/v2/fixtures/team/{team_id}"
    response = requests.get( url, headers=headers )
    return response.json()["api"]["fixtures"]


def get_teams():
    url = f"https://api-football-v1.p.rapidapi.com/v2/teams/team"
    response = requests.get( url, headers=headers)
    return response.json()

def get_teams_by_league(league_id):
    url = f"https://api-football-v1.p.rapidapi.com/v2/teams/league/{league_id}"
    response = requests.get( url, headers=headers)
    return response.json()["api"]["teams"]

def get_leagues():
    url = f"https://api-football-v1.p.rapidapi.com/v2/leagues"
    response = requests.get( url, headers=headers)
    return response.json()["api"]["leagues"]

def extract_teams():
    leagues = [ x for x in get_leagues() if x["season"] == 2020 or x["season"] == 2021]
    league_id = [x["league_id"] for x in leagues]
    teams = set()
    # result = get_teams_by_league(league_id[0])
    for e, lid in enumerate( league_id ):
        result = get_teams_by_league(lid)
        for team in result:
            teams.add( json.dumps(team) )
        log.info("%d", len(league_id) - e)
    
    root["teams"] = teams
    transaction.commit()

def update_teams():
    country = ["Spain", "Brazil", "France", "England", "Italy", 
        "Netherlands", "Greece", "Germany", "Austria", "Belgium", "Denmark", "Turkey",
        "Romania", "Norway"]
    teams = []
    for x in root["teams"]:
        serilaize = json.loads(x)
        if serilaize["founded"]:
            if serilaize["country"] in country:
                teams.append( serilaize )
    
    log.info(len(teams))
    exists  = list(  )

    for e, team in enumerate( teams ):
        if team["team_id"] in exists:
            continue
        
        data = get_fixtures_team(team["team_id"])
        root["fixture"][team["team_id"]] = data
        root["fixture"]._p_changed = 1
        transaction.commit()
        zopedb.cacheMinimize()


        log.info("%d. ALL: %d. Memory: %s", e, len(teams), get_size_memory() )
    zopedb.pack()
    log.info("penultimate %s", get_size_memory())
    # root["fixture"]._p_changed = 1
    # transaction.commit()
    log.info("End %s", get_size_memory())


def obj_building(path):

    def filter_year(item):
        years = ["2021", "2020"]
        result = False
        if item['event_date'][:4] in years:
            result = True
        return result

    TEAMS = []
    teams = {}
    for x in root["teams"]:
        data = json.loads(x)
        teams[data["team_id"]] = data

    for team_id in root['fixture']:
        # breakpoint()
        fixtures = root["fixture"][team_id]
        team = teams[team_id]
        pyteam = PyTeam(team["team_id"], team["name"], team["country"])
        fixtures = filter( filter_year, fixtures )
        for fixture in fixtures:
            params = (
                fixture['fixture_id'], fixture['status'],
                    Score( *(*fixture['score'].values(),) ).__dict__,
                    TeamFixture( *(*fixture['homeTeam'].values(),) ).__dict__,
                    TeamFixture( *(*fixture['awayTeam'].values(),) ).__dict__,
                       fixture['goalsHomeTeam'], fixture['goalsAwayTeam'],
            )

            pyfixture = PyFixture( *params )
            pyteam.fixtures.append( pyfixture._asdict() )

        # breakpoint()
        TEAMS.append( pyteam.__dict__ )
        zopedb.cacheMinimize()
        log.info( "Team: {}".format(team["name"]) )
    # breakpoint()

    with open(path, "wb") as f:
        pickle.dump(TEAMS, f)
    # breakpoint()

def export_teams(path):
    obj_building(path)


def main():
    update_teams()
    export_teams( os.path.join( BASE_DIR, "storage", "team.pk" ) )
    zopedb.pack()
    zopedb.close()

if __name__ == '__main__':
    main()
    # export_teams( os.path.join( os.getcwd(), "storage", "team.pk" ) )
    # export_teams( "/home/repente/prog/python/projects/AutomaticFox/Service/Telegram/script/component/flascore_wld/data/teams.pk" )
    # extract_teams()