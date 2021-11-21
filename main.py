import json

from sleeper_wrapper import League

import configparser

config = configparser.ConfigParser()
config.read("secrets")


def record_data(week: int):
    league_id = config['league']['id']
    league = League(league_id)

    print(json.dumps(league.get_matchups(week), indent=4))


if __name__ == '__main__':
    record_data(11)
