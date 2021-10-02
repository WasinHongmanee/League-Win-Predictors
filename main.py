import requests
from time import sleep
import csv
import os.path
from random import randint
import sys


def restart(): #restarts script due to global rate limit
    print('restarting')
    os.execv(sys.executable, ['python'] + sys.argv)


def get_account_id(api: str, summoner_id: str) -> str:
    url = f'https://na1.api.riotgames.com/lol/summoner/v4/summoners/{summoner_id}?api_key={api}'
    file = requests.get(url).json()
    return file['accountId']


def get_summoner_ids(api: str, region: str) -> list:
    url = f'https://{region}.api.riotgames.com/lol/league/v4/challengerleagues/by-queue/RANKED_SOLO_5x5?api_key={api}'
    response = requests.get(url)
    if response.status_code != 200:
        restart()
    file = response.json()['entries']
    summoner_ids = []
    upper = randint(1, 10) * 10
    lower = upper - 10
    for summoners in file:
        summoner_ids.append(summoners['summonerId'])
    return summoner_ids[lower:upper]


def get_account_ids(api: str, region: str, summoner_ids: list) -> list:
    account_ids = []
    print('Printing URLS to selected summoners...')
    for id in summoner_ids:
        url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/{id}?api_key={api}"
        print(url)
        sleep(.1)
        response = requests.get(url)
        if response.status_code != 200:
            restart()
        file = response.json()
        account_ids.append(file['accountId'])
    return account_ids


def get_game_ids(api: str, region: str, account_ids: list) -> list:
    games = []
    for account_id in account_ids:
        url = f'https://{region}.api.riotgames.com/lol/match/v4/matchlists/by-account/{account_id}?queue=420&season=13&api_key={api}'
        sleep(.2)
        response = requests.get(url)
        if response.status_code != 200:
            restart()
        file = response.json()['matches']
        for dicts in file:
            games.append(dicts['gameId'])
    return games


def get_game_data(api: str, region: str, match: str) -> dict:
    blue_kills = 0
    red_kills = 0
    blue_assists = 0
    red_assists = 0
    blue_gold = 0
    red_gold = 0
    blue_turret = 0
    red_turret = 0
    blue_win = False
    firstBlood = 'NA'
    firstDragon = 'NA'
    firstHerald = 'NA'
    firstTower = 'NA'
    blue_xp = 0
    red_xp = 0

    url = f'https://{region}.api.riotgames.com/lol/match/v4/matches/{match}?api_key={api}'
    response = requests.get(url)
    if response.status_code != 200:
        restart()
    if response.json()['gameDuration'] < 850:  # checks remake games
        return {'Blue Win': 'Remake', 'First Blood': firstBlood, 'First Dragon': firstDragon,
                'First Rift Herald': firstHerald, 'First Tower': firstTower,
                'Blue kills': blue_kills, 'Red kills': red_kills, 'Blue assists': blue_assists,
                'Red assists': red_assists,
                'Blue gold': blue_gold, 'Red gold': red_gold, 'Gold Diff': blue_gold - red_gold,
                'Blue towers': blue_turret, 'Red towers': red_turret, 'Blue xp': blue_xp, 'Red xp': red_xp}
    if response.json()['teams'][0]['win'] == 'Win':
        blue_win = True

    url = f'https://{region}.api.riotgames.com/lol/match/v4/timelines/by-match/{match}?api_key={api}'
    response = requests.get(url)
    if response.status_code != 200:
        restart()
    file = response.json()['frames'][10]['participantFrames']  # checks 10 minute mark
    for key in file:
        if (file[key]['participantId'] <= 5):
            blue_gold = blue_gold + file[key]['totalGold']
            blue_xp = blue_xp + file[key]['xp']
        else:
            red_gold = red_gold + file[key]['totalGold']
            red_xp = red_xp + file[key]['xp']

    response = requests.get(url)
    if response.status_code != 200:
        restart()
    file = response.json()
    for i in range(0, 11):
        fileFrame = file['frames'][i]['events']
        for event in fileFrame:
            if event['type'] == 'CHAMPION_KILL':
                if event['killerId'] <= 5:  # kill goes to blue team
                    if blue_kills == 0 and red_kills == 0:
                        firstBlood = True
                    blue_kills = blue_kills + 1
                    blue_assists = blue_assists + len(event['assistingParticipantIds'])
                else:
                    if red_kills == 0 and blue_kills == 0:
                        firstBlood = False
                    red_kills = red_kills + 1
                    red_assists = red_assists + len(event['assistingParticipantIds'])
            if event['type'] == 'BUILDING_KILL':
                if event['killerId'] <= 5:
                    blue_turret = blue_turret + 1
                    if blue_turret == 1:
                        firstTower = 'Blue'
                else:
                    red_turret = red_turret + 1
                    if red_turret == 1:
                        firstTower = 'Red'
            if event['type'] == 'ELITE_MONSTER_KILL':
                if event['monsterType'] == 'DRAGON':
                    if event['killerId'] <= 5:
                        firstDragon = True
                    else:
                        firstDragon = False
                else:
                    if event['killerId'] <= 5:
                        firstHerald = True
                    else:
                        firstHerald = False

    row = {'Match ID': match, 'Blue Win': blue_win, 'First Blood': firstBlood, 'First Dragon': firstDragon,
           'First Rift Herald': firstHerald, 'First Tower': firstTower,
           'Blue kills': blue_kills, 'Red kills': red_kills, 'Blue assists': blue_assists, 'Red assists': red_assists,
           'Blue gold': blue_gold, 'Red gold': red_gold, 'Gold Diff': blue_gold - red_gold,
           'Blue towers': blue_turret, 'Red towers': red_turret, 'Blue xp': blue_xp, 'Red xp': red_xp}
    return row


if __name__ == '__main__':
    region = str('NA1')
    api = str('ENTER API KEY') #enter developer api key
    summoner_ids = get_summoner_ids(api, region)  # summoner_ids is a list
    account_ids = get_account_ids(api, region, summoner_ids)  # account_ids is a list
    matches = get_game_ids(api, region, account_ids)  # matches is a list

    all_match_data = []
    fields = ['Match ID', 'Blue Win', 'First Blood', 'First Dragon',
              'First Rift Herald', 'First Tower',
              'Blue kills', 'Red kills', 'Blue assists', 'Red assists',
              'Blue gold', 'Red gold', 'Gold Diff',
              'Blue towers', 'Red towers', 'Blue xp', 'Red xp']
    filename = "gamesbyrow.csv"
    print('Appending matches to CSV...')
    with open(filename, 'a', newline='') as f: #opens file and either writes headers or appends matches to csv
        fileEmpty = os.stat(filename).st_size == 0
        csvwriter = csv.DictWriter(f, fieldnames=fields)
        if fileEmpty:
            csvwriter.writeheader()  # file doesn't exist yet, write a header
        for match in matches:
            sleep(5)
            row = get_game_data(api, region, match)
            print(row)
            csvwriter.writerow(row)
            f.flush()
