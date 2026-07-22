
from dataclasses import dataclass
import pandas as pd

@dataclass
class Player:
    name: str
    power: int
    leader: bool = False
    support: bool = False

@dataclass
class PlannerResult:
    teams: dict
    team_power: dict

def generate_tri_assignments(players: pd.DataFrame, leaders: dict, supports: dict, team_weights: dict):
    players = players.copy()
    players["Power"] = pd.to_numeric(players["Power"])

    teams = {"purple": [], "red": [], "yellow": []}
    team_power = {"purple": 0, "red": 0, "yellow": 0}
    assigned = set()

    for team, leader_name in leaders.items():
        if not leader_name:
            continue
        row = players[players["Player Name"].str.lower() == leader_name.lower()]
        if row.empty:
            continue
        p = Player(row.iloc[0]["Player Name"], int(row.iloc[0]["Power"]), leader=True)
        teams[team].append(p)
        team_power[team] += p.power
        assigned.add(p.name.lower())

    for team, support_name in supports.items():
        if not support_name:
            continue
        row = players[players["Player Name"].str.lower() == support_name.lower()]
        if row.empty:
            continue
        p = Player(row.iloc[0]["Player Name"], int(row.iloc[0]["Power"]), support=True)
        teams[team].append(p)
        team_power[team] += p.power
        assigned.add(p.name.lower())

    remaining = players[~players["Player Name"].str.lower().isin(assigned)].copy()
    remaining = remaining.sort_values("Power", ascending=False)

    total_power = players["Power"].sum()
    weight_sum = sum(team_weights.values())
    targets = {k: total_power * team_weights[k] / weight_sum for k in team_weights}

    for _, row in remaining.iterrows():
        p = Player(row["Player Name"], int(row["Power"]))
        best = min(teams.keys(), key=lambda t: (team_power[t] + p.power) / targets[t])
        teams[best].append(p)
        team_power[best] += p.power

    for team in teams:
        teams[team].sort(key=lambda x: x.power, reverse=True)

    return PlannerResult(teams=teams, team_power=team_power)
