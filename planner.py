from dataclasses import dataclass
import pandas as pd


# =====================================================
# DATA CLASSES
# =====================================================

@dataclass
class Player:

    name: str
    power: int

    leader: bool = False
    support: bool = False
    undercellar: bool = False


@dataclass
class PlannerResult:

    teams: dict
    team_power: dict
    undercellars: list
    roamer: Player | None


# =====================================================
# MAIN FUNCTION
# =====================================================

def generate_assignments(
    players: pd.DataFrame,
    leaders: dict,
    supports: dict,
    roamer: str,
    team_weights: dict,
):

    players = players.copy()

    players["Power"] = pd.to_numeric(players["Power"])

    # -------------------------------------------------

    teams = {
        "stables": [],
        "bell": [],
        "enemy1": [],
        "enemy2": [],
    }

    team_power = {
        "stables": 0,
        "bell": 0,
        "enemy1": 0,
        "enemy2": 0,
    }

    assigned = set()

    undercellars = []

    # =====================================================
    # UNDERCELLARS
    # =====================================================

    if len(players) > 25:

        weakest = (
            players
            .sort_values("Power")
            .head(2)
        )

        undercellars = weakest["Player Name"].tolist()

    # =====================================================
    # LEADERS
    # =====================================================

    for team, leader_name in leaders.items():

        if leader_name == "":
            continue

        row = players[
            players["Player Name"].str.lower() == leader_name.lower()
        ]

        if row.empty:
            continue

        player = Player(
            name=row.iloc[0]["Player Name"],
            power=int(row.iloc[0]["Power"]),
            leader=True,
            undercellar=row.iloc[0]["Player Name"] in undercellars,
        )

        teams[team].append(player)

        team_power[team] += player.power

        assigned.add(player.name.lower())

    # =====================================================
    # SUPPORT PLAYERS
    # =====================================================

    for team, support_name in supports.items():

        if support_name == "":
            continue

        row = players[
            players["Player Name"].str.lower() == support_name.lower()
        ]

        if row.empty:
            continue

        player = Player(
            name=row.iloc[0]["Player Name"],
            power=int(row.iloc[0]["Power"]),
            support=True,
            undercellar=row.iloc[0]["Player Name"] in undercellars,
        )

        teams[team].append(player)

        team_power[team] += player.power

        assigned.add(player.name.lower())

    # =====================================================
    # ROAMER
    # =====================================================

    roamer_player = None

    if roamer != "":

        row = players[
            players["Player Name"].str.lower() == roamer.lower()
        ]

        if not row.empty:

            roamer_player = Player(
                name=row.iloc[0]["Player Name"],
                power=int(row.iloc[0]["Power"])
            )

            assigned.add(roamer_player.name.lower())

    # =====================================================
    # REMAINING PLAYERS
    # =====================================================

    remaining = players[
        ~players["Player Name"].str.lower().isin(assigned)
    ].copy()

    remaining = remaining.sort_values(
        by="Power",
        ascending=False
    )

    total_power = players["Power"].sum()

    weight_sum = sum(team_weights.values())

    targets = {
        team: total_power * team_weights[team] / weight_sum
        for team in team_weights
    }

    # =====================================================
    # BALANCE
    # =====================================================

    for _, row in remaining.iterrows():

        player = Player(
            name=row["Player Name"],
            power=int(row["Power"]),
            undercellar=row["Player Name"] in undercellars,
        )

        best_team = min(
            teams.keys(),
            key=lambda t:
            (team_power[t] + player.power) / targets[t]
        )

        teams[best_team].append(player)

        team_power[best_team] += player.power

    # =====================================================
    # SORT EACH TEAM
    # =====================================================

    for team in teams:

        teams[team].sort(
            key=lambda p: p.power,
            reverse=True
        )

    # =====================================================
    # RETURN
    # =====================================================

    return PlannerResult(
        teams=teams,
        team_power=team_power,
        undercellars=undercellars,
        roamer=roamer_player,
    )