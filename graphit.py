import csv

import plotly.graph_objects as go
from datetime import datetime


colors = ['#636EFA', '#EF553B', '#00CC96', '#AB63FA', '#FFA15A', '#19D3F3', '#FF6692', '#B6E880', '#FF97FF', '#FECB52',
          "#000000", "#FF0000", "#FF0000", "#FF0000"]


def generate(week: int):
    with open(f"static/raw/data{week}.csv") as csvfile:
        reader = csv.DictReader(csvfile)
        team_data = {}
        timestamps = []
        for row in reader:
            if 'graphbreak' in row and row['graphbreak']:
                continue
            team1_key = row['team1']
            team2_key = row['team2']
            if team1_key not in team_data:
                team_data[team1_key] = {'current': [], 'projected': [], "matchup": row["matchup_number"]}
            if team2_key not in team_data:
                team_data[team2_key] = {'current': [], 'projected': [], "matchup": row["matchup_number"]}
            time_as_string = datetime.fromtimestamp(int(row['timestamp']))
            if time_as_string not in timestamps:
                timestamps.append(time_as_string)
            team_data[team1_key]['projected'].append(float(row['team1_projected']))
            team_data[team1_key]['current'].append(float(row['team1_score']))
            team_data[team2_key]['projected'].append(float(row['team2_projected']))
            team_data[team2_key]['current'].append(float(row['team2_score']))

    color_pos = 0
    x_range = [min(timestamps), max(timestamps)]
    fig = go.Figure()

    fig.update_yaxes(range=[0, 200])
    fig.update_xaxes(range=x_range, tickformat="%a %H:%M")
    fig.update_xaxes(rangebreaks=[{'bounds': [1637560800, 1637625600], 'enabled':True}], tickformat="%a %H:%M")
    for t in team_data:
        fig.add_trace(go.Scatter(x=timestamps, y=team_data[t]['projected'], legendgroup=team_data[t]["matchup"], line=dict(dash='dash', color=colors[color_pos]), line_shape='hv', name="Proj " + t))
        fig.add_trace(go.Scatter(x=timestamps, y=team_data[t]['current'],  legendgroup=team_data[t]["matchup"], line=dict(color=colors[color_pos]), line_shape='hv', name="Curr " + t))
        color_pos = color_pos+1
    fig.write_html(f"static/week{week}.html")


if __name__ == "__main__":
    generate(7)
