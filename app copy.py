import streamlit as st
import pandas as pd
from datetime import datetime, time
from planner import generate_assignments
from config import DEFAULT_LEADERS, DEFAULT_ROAMER

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Swordland Planner",
    page_icon="⚔️",
    layout="wide"
)

st.title("⚔️ Swordland Assignment Planner")

# =====================================================
# SESSION STATE
# =====================================================

SELECTION_KEYS = [
    "leader_stables",
    "leader_bell",
    "leader_enemy1",
    "leader_enemy2",
    "support_stables",
    "support_bell",
    "support_enemy1",
    "support_enemy2",
    "roamer",
]

if "selection" not in st.session_state:

    st.session_state.selection = {
        key: ""
        for key in SELECTION_KEYS
    }

# =====================================================
# UPLOAD
# =====================================================

uploaded_file = st.file_uploader(
    "Upload players.xlsx",
    type=["xlsx"]
)

if uploaded_file is None:
    st.info("Upload a players.xlsx file to begin.")
    st.stop()

df = pd.read_excel(uploaded_file)

df["Power"] = pd.to_numeric(
    df["Power"],
    errors="coerce"
)

# =====================================================
# LEGION
# =====================================================

legion = st.radio(
    "Legion",
    ["L1", "L2"],
    horizontal=True
)

# =====================================================
# EVENT DETAILS
# =====================================================

st.divider()

st.header("📅 Event Details")

c1, c2 = st.columns(2)

with c1:

    event_date = st.date_input(
        "Event Date"
    )

#from datetime import time

with c2:

    event_time_label = st.radio(
        "Event Time (UTC)",
        [
            "12:00 UTC",
            "14:00 UTC",
            "19:00 UTC",
        ],
        horizontal=True,
        index=2
    )

event_times = {
    "12:00 UTC": time(12, 0),
    "14:00 UTC": time(14, 0),
    "19:00 UTC": time(19, 0),
}

event_time = event_times[event_time_label]

#from datetime import datetime

event_datetime = datetime.combine(
    event_date,
    event_time
)

players = df[
    df["Legion"].astype(str).str.upper() == legion
].copy()

if players.empty:
    st.warning(f"No players found for {legion}")
    st.stop()

players = players.sort_values(
    by="Power",
    ascending=False
).reset_index(drop=True)

# =====================================================
# PLAYER LOOKUPS
# =====================================================

player_lookup = {}
reverse_lookup = {}

for _, row in players.iterrows():

    label = f"{row['Player Name']} ({int(row['Power']):,})"

    player_lookup[label] = row["Player Name"]
    reverse_lookup[row["Player Name"]] = label

# =====================================================
# DEFAULTS
# =====================================================

def apply_default(state_key, player_name):

    if st.session_state.selection[state_key] != "":
        return

    if player_name in reverse_lookup:

        st.session_state.selection[state_key] = player_name


apply_default(
    "leader_stables",
    DEFAULT_LEADERS["stables"]
)

apply_default(
    "roamer",
    DEFAULT_ROAMER
)

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def available_labels(current_key):

    used = set()

    for key, value in st.session_state.selection.items():

        if key == current_key:
            continue

        if value != "":
            used.add(value)

    labels = []

    current = st.session_state.selection[current_key]

    if current != "" and current in reverse_lookup:
        labels.append(reverse_lookup[current])

    labels.append("")

    for label, player in player_lookup.items():

        if player not in used:

            if label not in labels:
                labels.append(label)

    return labels


def select_player(
    title,
    state_key,
):

    labels = available_labels(state_key)

    current = st.session_state.selection[state_key]

    if current != "" and current in reverse_lookup:

        current_label = reverse_lookup[current]

        if current_label in labels:
            index = labels.index(current_label)
        else:
            index = 0

    else:

        index = 0

    selected_label = st.selectbox(
        title,
        labels,
        index=index,
        key=f"ui_{state_key}"
    )

    if selected_label == "":

        st.session_state.selection[state_key] = ""

        return ""

    player = player_lookup[selected_label]

    st.session_state.selection[state_key] = player

    return player


# =====================================================
# OVERVIEW
# =====================================================

st.success(f"{len(players)} players loaded.")

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Players",
        len(players)
    )

with col2:
    st.metric(
        "Total Power",
        f"{players['Power'].sum():,}"
    )

# =====================================================
# LEADERS
# =====================================================

st.divider()

st.header("👑 Leaders")

c1, c2 = st.columns(2)

with c1:

    leader_stables = select_player(
        "🏇 Stables / Reformation",
        "leader_stables"
    )

    leader_enemy1 = select_player(
        "⚔️ Enemy Sanctuary",
        "leader_enemy1"
    )

with c2:

    leader_bell = select_player(
        "🔔 Bell Tower / Mercenary",
        "leader_bell"
    )

    leader_enemy2 = select_player(
        "🛡️ Our Sanctuary",
        "leader_enemy2"
    )

leaders = {
    "stables": leader_stables,
    "bell": leader_bell,
    "enemy1": leader_enemy1,
    "enemy2": leader_enemy2,
}

# =====================================================
# SUPPORT PLAYERS
# =====================================================

st.divider()

st.header("🤝 Support Players")

c1, c2 = st.columns(2)

with c1:

    support_stables = select_player(
        "Support - Stables",
        "support_stables"
    )

    support_enemy1 = select_player(
        "Support - Enemy Sanctuary",
        "support_enemy1"
    )

with c2:

    support_bell = select_player(
        "Support - Bell Tower",
        "support_bell"
    )

    support_enemy2 = select_player(
        "Support - Our Sanctuary",
        "support_enemy2"
    )

supports = {
    "stables": support_stables,
    "bell": support_bell,
    "enemy1": support_enemy1,
    "enemy2": support_enemy2,
}

# =====================================================
# ROAMER
# =====================================================

st.divider()

st.header("🚶 Roamer")

roamer = select_player(
    "Roamer",
    "roamer"
)

# =====================================================
# TEAM WEIGHTS
# =====================================================

st.divider()

st.header("⚖️ Team Weights")

c1, c2, c3, c4 = st.columns(4)

with c1:

    weight_stables = st.number_input(
        "Stables",
        value=1.15,
        step=0.05,
        format="%.2f"
    )

with c2:

    weight_bell = st.number_input(
        "Bell",
        value=1.05,
        step=0.05,
        format="%.2f"
    )

with c3:

    weight_enemy1 = st.number_input(
        "Enemy Sanctuary",
        value=1.00,
        step=0.05,
        format="%.2f"
    )

with c4:

    weight_enemy2 = st.number_input(
        "Our Sanctuary",
        value=1.00,
        step=0.05,
        format="%.2f"
    )

weights = {
    "stables": weight_stables,
    "bell": weight_bell,
    "enemy1": weight_enemy1,
    "enemy2": weight_enemy2,
}

# =====================================================
# GENERATE
# =====================================================

st.divider()

generate = st.button(
    "⚔️ Generate Assignments",
    use_container_width=True
)

if generate:

    result = generate_assignments(
        players=players,
        leaders=leaders,
        supports=supports,
        roamer=roamer,
        team_weights=weights,
    )

    st.session_state["result"] = result

# =====================================================
# RESULTS
# =====================================================

if "result" in st.session_state:

    result = st.session_state["result"]

    tab_assignments, tab_export = st.tabs(
    [
        "⚔️ Assignments",
        "📋 Kingshot Messages"
    ]
    )

    with tab_assignments:

        building_titles = {
            "bell": "🔔 Bell Tower / Mercenary",
            "stables": "🏇 Stables / Reformation",
            "enemy1": "⚔️ Enemy Sanctuary & Abbeys",
            "enemy2": "🛡️ Our Sanctuary & Abbeys",
        }
        # =====================================================
        # SUMMARY TABLE
        # =====================================================

        summary = []

        for team in ["bell", "stables", "enemy1", "enemy2"]:

            summary.append({
                "Building": building_titles[team],
                "Players": len(result.teams[team]),
                "Total Power": result.team_power[team]
            })

        summary_df = pd.DataFrame(summary)

        st.subheader("📊 Team Summary")

        st.dataframe(
            summary_df,
            use_container_width=True,
            hide_index=True,
        )


        # =====================================================
        # BUILDING CARDS
        # =====================================================

        col1, col2 = st.columns(2)

        team_order = [
            ("bell", col1),
            ("stables", col2),
            ("enemy1", col1),
            ("enemy2", col2),
        ]

        for team_key, column in team_order:

            with column:

                with st.container(border=True):

                    st.subheader(building_titles[team_key])

                    st.caption(
                        f"{len(result.teams[team_key])} Players"
                    )

                    st.metric(
                        "Total Power",
                        f"{result.team_power[team_key]:,}"
                    )

                    st.divider()

                    for player in result.teams[team_key]:

                        badges = []

                        if player.leader:
                            badges.append("👑")

                        if player.support:
                            badges.append("🤝")

                        if player.undercellar:
                            badges.append("💰")

                        badge_text = " ".join(badges)

                        left, right = st.columns([4, 1])

                        with left:

                            if badge_text:

                                st.write(
                                    f"{badge_text} **{player.name}**"
                                )

                            else:

                                st.write(
                                    f"**{player.name}**"
                                )

                        with right:

                            st.write(
                                f"{player.power:,}"
                            )

        # =====================================================
        # ROAMER / UNDERCELLARS
        # =====================================================

        st.divider()

        left, right = st.columns(2)

        with left:

            st.subheader("🚶 Roamer")

            if result.roamer:

                st.success(
                    f"{result.roamer.name}\n\n"
                    f"{result.roamer.power:,}"
                )

            else:

                st.info("None Assigned")

        with right:

            st.subheader("💰 Undercellars")

            if result.undercellars:

                for player in result.undercellars:

                    st.write(f"• {player}")

            else:

                st.info("None Assigned")

        # =====================================================
        # DEBUG
        # =====================================================

        with st.expander("🔧 Planner Data"):

            st.write("Leaders")
            st.json(leaders)

            st.write("Supports")
            st.json(supports)

            st.write("Roamer")
            st.write(roamer)

            st.write("Weights")
            st.json(weights)


    with tab_export:

        st.header("📋 Application Export")

        announcement = f"""SWORDLAND SHOWDOWN LEGION ({legion[-1]}) TEAMS:

📅 {event_date.strftime("%d/%m")} @ {event_time_label}

The following lists show the teams along with the buildings they will be occupying.

👻 {result.roamer.name if result.roamer else "No Roamer"} will be floating throughout the map targeting enemy cities.

It’s important to garrison quickly in order to hold off single attacks. Additionally, don’t forget to save a march to collect loot from buildings.

📝 View additional instructions with the battlefield map in Discord 🙏
"""

        def team_text(title, players):
            text = title + "\n\n"
            for player in players:
                text += player.name + "\n"
            return text

        exports = [
            ("Part 1 - Announcement", announcement),
            ("Part 2 - Stables",
            team_text("🚨 Stables/Reformation", result.teams["stables"])),
            ("Part 3 - Bell Tower",
            team_text("🚨 Bell Tower/Mercenary", result.teams["bell"])),
            ("Part 4 - Enemy Sanctuary",
            team_text("🚨 Enemy Sanctuary", result.teams["enemy1"])),
            ("Part 5 - Our Sanctuary",
            team_text("🚨 Our Sanctuary", result.teams["enemy2"])),
        ]

        for title, body in exports:

            st.subheader(title)

            st.caption(f"{len(body)} characters")

            st.code(
                body,
                language=None
            )


    