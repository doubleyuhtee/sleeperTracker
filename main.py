import json
import os
import threading
from os.path import exists
from sleeper_wrapper import League, Players, Stats
import time
import requests
import configparser

import graphit
import schedule
from flask import Flask
app = Flask(__name__)

config = configparser.ConfigParser()
config.read("secrets")

csv_header = "timestamp,week,matchup_number,team1,team1_projected,team1_score,team2,team2_projected,team2_score,graphbreak\n"


@app.route('/')
def latest():
    files = [x for x in os.listdir("static") if "week" in x]
    files.sort()
    return app.send_static_file(files[-1])


@app.route('/<requested_week>')
def serve_week(requested_week=0):
    print(json.dumps(requested_week))
    return app.send_static_file(f"week{requested_week}.html")


def current_seconds_time():
    return round(time.time())


def get_nfl_state():
    return requests.get("https://api.sleeper.app/v1/state/nfl").json()


def write_break_marker():
    nfl_state = get_nfl_state()
    week = nfl_state["display_week"]
    now = current_seconds_time()
    if not exists(f"static/raw/data{week}.csv"):
        open(f"static/raw/data{week}.csv", 'w')\
            .write(csv_header)
    with open(f"static/raw/data{week}.csv", "a+") as file:
        file.write(f"{now},week,matchup_number,team1,team1_projected,team1_score,team2,team2_projected,team2_score,True")


def calculate_scores(stats, week_projection, matchups, users, rosters):
    matchup_map = {}
    for m in matchups:
        matchup_roster = [r for r in rosters if r['roster_id'] == m['roster_id']][0]
        current_points = sum(m['starters_points'])
        team_owner = [x for x in users if matchup_roster['owner_id'] == x['user_id']][0]
        display_name = team_owner['metadata']['team_name'] if 'team_name' in team_owner['metadata'] else team_owner['display_name']
        # print(display_name)
        projected = 0
        for p in m['starters']:
            plr_proj = stats.get_player_week_score(week_projection, p)
            if plr_proj:
                projected = projected + plr_proj["pts_ppr"] if "pts_ppr" in plr_proj and plr_proj["pts_ppr"] else 0
        # print(str(current_points) + " / " + str(projected))
        if m['matchup_id'] in matchup_map:
            matchup_map[m['matchup_id']]['p2'] = {
                "current": current_points,
                "projected": projected,
                "team_name": display_name
            }
        else:
            matchup_map[m['matchup_id']] = {'p1': {
                "current": current_points,
                "projected": projected,
                "team_name": display_name}
            }
    return matchup_map


def record_data():
    try:
        if not exists("playerData"):
            players = Players()
            open("playerData", 'w').write(json.dumps(players.get_all_players(), indent=2))

        nfl_state = get_nfl_state()
        week = nfl_state["week"]
        year = nfl_state["league_season"]
        print(f"{current_seconds_time()} {week} {year}")
        league_id = config['league']['id']
        league = League(league_id)
        matchups = league.get_matchups(week)
        users = league.get_users()
        rosters = league.get_rosters()

        stats = Stats()
        weekproj = stats.get_week_projections("regular", year, week)
        matchup_map = calculate_scores(stats, weekproj, matchups, users, rosters)
        # print(json.dumps(matchup_map, indent=2))
        if not exists(f"static/raw/data{week}.csv"):
            open(f"static/raw/data{week}.csv", 'w')\
                .write(csv_header)
        with open(f"static/raw/data{week}.csv", "a+") as file:
            now = current_seconds_time()
            for matchup in matchup_map:
                file.write(f"{now},{week},{matchup},{matchup_map[matchup]['p2']['team_name']},{matchup_map[matchup]['p2']['projected']},{matchup_map[matchup]['p2']['current']},{matchup_map[matchup]['p1']['team_name']},{matchup_map[matchup]['p1']['projected']},{matchup_map[matchup]['p1']['current']}\n")

        graphit.generate(week)
    except Exception as e:
        print(e)


schedule.every().hour.do(record_data)
schedule.every().day.at("11:00").do(record_data)
schedule.every().sunday.at("05:00").do(record_data)
schedule.every().sunday.at("11:58").do(record_data)
schedule.every().sunday.at("12:01").do(record_data)
schedule.every().sunday.at("12:10").do(record_data)
schedule.every().sunday.at("12:20").do(record_data)
schedule.every().sunday.at("12:30").do(record_data)
schedule.every().sunday.at("12:40").do(record_data)
schedule.every().sunday.at("12:50").do(record_data)

schedule.every().monday.at("00:00").do(write_break_marker)
schedule.every().monday.at("17:50").do(write_break_marker)
schedule.every().tuesday.at("00:00").do(write_break_marker)
schedule.every().thursday.at("18:00").do(write_break_marker)
schedule.every().friday.at("00:00").do(write_break_marker)
schedule.every().sunday.at("11:00").do(write_break_marker)
for i in range(13, 24):
    for m in range(5, 60, 5):
        schedule.every().sunday.at(f"{i}:{m:02}").do(record_data)
for i in range(18, 23):
    for m in range(5, 60, 5):
        schedule.every().monday.at(f"{i}:{m:02}").do(record_data)


def monitor_scores():
    record_data()
    print("starting to monitor")
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == '__main__':
    print("serving")
    threading.Thread(target=monitor_scores).start()
    app.run()
