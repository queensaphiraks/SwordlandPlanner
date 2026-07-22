import streamlit as st
import pandas as pd

from datetime import datetime, time
from pathlib import Path

import json
import re

from planner_tri import generate_tri_assignments

from config import (
    DEFAULT_SHEET_URL_TRI,
)

import streamlit.components.v1 as components


def show_tri(page):

    # =====================================================
    # PAGE CONFIG
    # =====================================================

    st.set_page_config(
        page_title="KNG - Tri Planner",
        page_icon="🤝",
        layout="centered"
    )

    if page == "tri_create":
        st.title("➕ Create Plan - Tri")
    else:
        st.title("📂 Load Plan - Tri")

    if st.button(
        "⬅ Back to Menu",
        key="back_home",
        width="content",
    ):

        # Clear planner state
        for key in [
            "result",
            "selection",
            "roster_df",
            "loaded_legion",
        ]:
            st.session_state.pop(key, None)

        st.session_state.page = "home"
        st.rerun()



    PLANS_FOLDER = Path("plans")
    PLANS_FOLDER.mkdir(exist_ok=True)

    # =====================================================
    # CACHED ROSTER
    # =====================================================

    if "roster_df" not in st.session_state:
        st.session_state.roster_df = None

    if "roster_loaded" not in st.session_state:
        st.session_state.roster_loaded = False

    if st.session_state.page == "tri_create":

        # =====================================================
        # SESSION STATE
        # =====================================================

        SELECTION_KEYS = [

            "leader_purple",
            "leader_red",
            "leader_yellow",

            "support_purple",
            "support_red",
            "support_yellow",

        ]

        if "selection" not in st.session_state:

            st.session_state.selection = {
                key: ""
                for key in SELECTION_KEYS
            }

        # =====================================================
        # ROSTER SOURCE
        # =====================================================

        def clear_sheet_url():
            st.session_state.sheet_url = ""

        # Initialize once
        if "sheet_url" not in st.session_state:
            st.session_state.sheet_url = DEFAULT_SHEET_URL_TRI

        # ----------------------------------------------------
        # No roster loaded yet
        # ----------------------------------------------------

        if st.session_state.roster_df is None:

            st.text_input(
                "Google Spreadsheet URL",
                key="sheet_url",
            )

            col1, col2 = st.columns(2)

            with col1:
                load_sheet = st.button(
                    "📥 Load Spreadsheet",
                    use_container_width=True,
                )

            with col2:
                st.button(
                    "🗑 Clear",
                    on_click=clear_sheet_url,
                    use_container_width=True,
                )

            if load_sheet:

                match = re.search(
                    r"/spreadsheets/d/([a-zA-Z0-9-_]+)",
                    st.session_state.sheet_url
                )

                if not match:
                    st.error("Invalid Google Spreadsheet URL.")
                    st.stop()

                sheet_id = match.group(1)

                csv_url = (
                    f"https://docs.google.com/spreadsheets/d/"
                    f"{sheet_id}/export?format=csv"
                )

                try:

                    df = pd.read_csv(csv_url)

                    st.session_state.roster_df = df

                    st.rerun()

                except Exception:

                    st.error(
                        "Unable to read the spreadsheet."
                    )

                    st.stop()

            st.stop()

        df = st.session_state.roster_df.copy()

        st.success("✅ Google Spreadsheet Loaded")
        
        df["Power"] = (
            df["Power"]
            .astype(str)
            .str.replace(",", "", regex=False)
        )

        df["Power"] = pd.to_numeric(
            df["Power"],
            errors="coerce"
        )

        # Remove rows with missing player names or power
        df = df.dropna(subset=["Player Name", "Power"]).copy()

        # =====================================================
        # LEGION
        # =====================================================

        default_legion = st.session_state.get(
            "loaded_legion",
            "L1"
        )

        legion = st.radio(
            "Legion",
            ["L1", "L2"],
            horizontal=True,
            index=0 if default_legion == "L1" else 1,
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
                    "21:00 UTC",
                ],
                horizontal=True,
                index=2
            )

        event_times = {
            "12:00 UTC": time(12, 0),
            "14:00 UTC": time(14, 0),
            "19:00 UTC": time(19, 0),
            "21:00 UTC": time(21, 0),
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

            power = int(row["Power"]) if pd.notna(row["Power"]) else 0

            label = f"{row['Player Name']} ({power:,})"

            player_lookup[label] = row["Player Name"]
            reverse_lookup[row["Player Name"]] = label

        # =====================================================
        # HELPER FUNCTIONS
        # =====================================================

        def available_labels(current_key, top_n=None):
            used = {
                value
                for key, value in st.session_state.selection.items()
                if key != current_key and value != ""
            }

            labels = [""]

            current = st.session_state.selection[current_key]
            if current and current in reverse_lookup:
                labels.append(reverse_lookup[current])

            count = 0

            for label, player in player_lookup.items():

                if player in used:
                    continue

                if label not in labels:
                    labels.append(label)
                    count += 1

                if top_n is not None and count >= top_n:
                    break

            return labels


        def select_player(title, state_key, top_n=None):

            labels = available_labels(state_key, top_n)

            current = st.session_state.selection[state_key]

            if current and current in reverse_lookup:
                current_label = reverse_lookup[current]
                index = labels.index(current_label)
            else:
                index = 0

            selected_label = st.selectbox(
                title,
                labels,
                index=index,
                key=f"ui_{state_key}",
            )

            if selected_label == "":
                st.session_state.selection[state_key] = ""
                return ""

            player = player_lookup[selected_label]
            st.session_state.selection[state_key] = player
            return player


        def save_plan(
            result,
            legion,
            event_date,
            event_time_label,
        ):

            path = PLANS_FOLDER / f"tri_{legion}.json"

            plan = {
            "title": f"{legion} - {event_date.strftime('%d/%m')} - {event_time_label}",
            "event_date": event_date.isoformat(),
            "event_time": event_time_label,
            "legion": legion,
            "teams": {}
        }

            for team, players in result.teams.items():

                plan["teams"][team] = []

                for p in players:

                    plan["teams"][team].append({
                        "name": p.name,
                        "power": p.power,
                        "leader": p.leader,
                        "support": p.support,
                    })

            with open(path, "w", encoding="utf-8") as f:

                json.dump(
                    plan,
                    f,
                    indent=4,
                    ensure_ascii=False,
                )

            return path

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
        # TRI TEAMS
        # =====================================================

        st.divider()

        st.header("🎨 Tri Teams")

        c1, c2, c3 = st.columns(3)

        with c1:

            st.subheader("🟣 Purple")

            leader_purple = select_player("Leader", "leader_purple", top_n=10)
            support_purple = select_player("Support", "support_purple", top_n=10)


        with c2:

            st.subheader("🔴 Red")

            leader_red = select_player("Leader", "leader_red", top_n=10)
            support_red = select_player("Support", "support_red", top_n=10)


        with c3:

            st.subheader("🟡 Yellow")

            leader_yellow = select_player("Leader", "leader_yellow", top_n=10)
            support_yellow = select_player("Support", "support_yellow", top_n=10)

        leaders = {
            "purple": leader_purple,
            "red": leader_red,
            "yellow": leader_yellow,
        }

        supports = {
            "purple": support_purple,
            "red": support_red,
            "yellow": support_yellow,
        }

        # =====================================================
        # TEAM WEIGHTS
        # =====================================================

        st.divider()

        st.header("⚖️ Team Weights")

        c1, c2, c3 = st.columns(3)

        with c1:
            
            weight_purple = st.number_input(
                "🟣 Purple Team",
                value=1.00,
                step=0.05,
                format="%.2f",
            )

        with c2:

            weight_red = st.number_input(
                "🔴 Red Team",
                value=1.10,
                step=0.05,
                format="%.2f",
            )

        with c3:

            weight_yellow = st.number_input(
                "🟡 Yellow Team",
                value=0.90,
                step=0.05,
                format="%.2f",
            )

        weights = {
            "red": weight_red,
            "purple": weight_purple,
            "yellow": weight_yellow,
        }


        # =====================================================
        # GENERATE
        # =====================================================

        st.divider()

        leaders_selected = all(leaders.values())

        generate = st.button(
            "⚔️ Generate Assignments",
            use_container_width=True,
            disabled=not leaders_selected,
        )

        if not leaders_selected:
            st.info("Select a leader for each team to enable generation.")

        if generate:

            missing = [
                team.capitalize()
                for team, leader in leaders.items()
                if leader == ""
            ]

            if missing:
                st.error(
                    "Please select a leader for: "
                    + ", ".join(missing)
                )
                st.stop()

            result = generate_tri_assignments(
                players=players,
                leaders=leaders,
                supports=supports,
                team_weights=weights,
            )

            st.session_state["result"] = result

            plan_path = save_plan(
                result,
                legion,
                event_date,
                event_time_label,
            )

            st.session_state.loaded_legion = legion

            st.success(
                f"Plan saved to {plan_path.name}"
            )

        # =====================================================
        # RESULTS
        # =====================================================

        if "result" in st.session_state:

            result = st.session_state["result"]

            team_titles = {
                "purple": "🟣 Purple",
                "red": "🔴 Red",
                "yellow": "🟡 Yellow",
            }

            # =====================================================
            # SUMMARY TABLE
            # =====================================================

            summary = []

            for team in [
                "purple",
                "red",
                "yellow",
            ]:

                summary.append(
                {
                    "Team": team_titles[team],
                    "Players": len(result.teams[team]),
                    "Total Power": result.team_power[team],
                }
)

            summary_df = pd.DataFrame(summary)

            st.subheader("📊 Team Summary")

            st.dataframe(
                summary_df,
                use_container_width=True,
                hide_index=True,
            )


            # =====================================================
            # TEAM CARDS
            # =====================================================

            col1, col2, col3 = st.columns(3)

            team_order = [
                ("purple", col1),
                ("red", col2),
                ("yellow", col3),
            ]

            def format_power(power: int) -> str:
                if power >= 1_000_000_000:
                    return f"{power / 1_000_000_000:.1f}B".rstrip("0").rstrip(".")
                if power >= 1_000_000:
                    return f"{power / 1_000_000:.0f}M"
                if power >= 1_000:
                    return f"{power / 1_000:.0f}K"
                return str(power)

            for team_key, column in team_order:

                with column:

                    with st.container(border=True):

                        st.subheader(team_titles[team_key])

                        st.caption(
                            f"{len(result.teams[team_key])} Players"
                        )

                        st.metric(
                            "Total Power",
                            format_power(result.team_power[team_key]),
                        )

                        st.divider()

                        for player in result.teams[team_key]:

                            badges = []

                            if player.leader:
                                badges.append("👑")

                            if player.support:
                                badges.append("🤝")

                            badge_text = " ".join(badges)
                            st.markdown(f"""
                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                    <div>{badge_text} <b>{player.name}</b></div>
                                    <div><b>{format_power(player.power)}</b></div>
                                </div>
                                """, unsafe_allow_html=True)
                        
            # =====================================================
            # OPEN CURRENT PLAN
            # =====================================================

            st.divider()

            if st.button(
                "⬅ Back to Main Menu",
                key="back_bottom",
                use_container_width=True,
            ):
                if "result" in st.session_state:
                    del st.session_state["result"]

                if "selection" in st.session_state:
                    del st.session_state["selection"]

                st.session_state.roster_df = None
                st.session_state.page = "home"

                st.rerun()


    if st.session_state.page == "tri_load":

        legion = st.radio(
            "Legion",
            ["L1", "L2"],
            horizontal=True,
        )

        plan_file = PLANS_FOLDER / f"tri_{legion}.json"

        if not plan_file.exists():
            st.warning(f"No saved plan found for {legion}.")
            st.stop()

        with open(plan_file, encoding="utf-8") as f:
            plan = json.load(f)

        st.success(f"Loaded {plan['title']}")

        # ----------------------------------------------------
        # Team leaders
        # ----------------------------------------------------

        def get_leader(team):
            return next(
                p["name"]
                for p in plan["teams"][team]
                if p["leader"]
            )

        purple_leader = get_leader("purple")
        red_leader = get_leader("red")
        yellow_leader = get_leader("yellow")

        announcement = f"""TRI ALLIANCE LEGION ({plan["legion"][-1]}) TEAMS:

    📅 {datetime.fromisoformat(plan["event_date"]).strftime("%d/%m")} @ {plan["event_time"]}

    🏆 Mission Goal

    Choke off enemy access to the center while protecting our own.

    🔥 Once the event starts, flags will be posted over critical locations with the names of the team leaders and any updated instructions.\n\n
    """

        def team_text(title, players):

            text = title + "\n\n"

            # Leader first, then Support, then everyone else
            ordered_players = sorted(
                players,
                key=lambda p: (
                    not p["leader"],
                    not p["support"],
                    -p["power"]
                )
            )

            for player in ordered_players:

                line = player["name"]

                if player["leader"]:
                    line += " 👑"

                elif player["support"]:
                    line += " 🤝"

                text += line + "\n"

            return text

        exports = [
            ("Announcement", announcement),

            (
                "Purple Team",
                team_text(
                    "💜 Purple Team",
                    plan["teams"]["purple"]
                ),
            ),

            (
                "Red Team",
                team_text(
                    "❤️ Red Team",
                    plan["teams"]["red"]
                ),
            ),

            (
                "Yellow Team",
                team_text(
                    "💛 Yellow Team",
                    plan["teams"]["yellow"]
                ),
            ),
        ]

        team_emojis = {
            "purple": "💜",
            "red": "❤️",
            "yellow": "💛",
        }

        team_titles = {
            "purple": "PURPLE TEAM",
            "red": "RED TEAM",
            "yellow": "YELLOW TEAM",
        }

        legion_name = {
            "L1": "⚔️ TRI LEGION 1️⃣ ⚔️",
            "L2": "⚔️ TRI LEGION 2️⃣ ⚔️",
        }.get(plan["legion"], "⚔️ TRI LEGION ⚔️")

        
        # =====================================================
        # HEADER
        # =====================================================

        loaded_date = datetime.fromisoformat(
            plan["event_date"]
        )

        event_date = loaded_date.strftime("%d/%m")

        event_time = plan["event_time"]

        discord_message = ""

        discord_message += f"{legion_name}\n\n"
        discord_message += (
            f"🏰 Tri-Alliance Today {event_date} 🗓️\n"
        )

        discord_message += (
            f"⏰ START TIME: {event_time}\n\n"
        )
        discord_message += "1️⃣ Blue: Starting point\n\n"
        discord_message += "2️⃣ Purple / Red / Yellow: Protect these positions\n\n"
        discord_message += "3️⃣ Green: Pinch off the enemy\n\n"

        discord_message += "🏆 **MISSION GOAL**\n"
        discord_message += "Choke off enemy access to the center while protecting our own.\n\n"

        discord_message += (
            "🔥 Once the event starts, flags will be posted over critical spots "
            "with the names of the team leaders and updated instructions if plans change.\n\n"
        )

        # ----------------------------------------------------
        # Team Leads
        # ----------------------------------------------------

        discord_message += "**TEAM LEADS**\n"

        discord_message += f"💜 Left Team: {purple_leader}\n"
        discord_message += f"❤️ Middle Team: {red_leader}\n"
        discord_message += f"💛 Right Team: {yellow_leader}\n\n"

        # ----------------------------------------------------
        # Teams
        # ----------------------------------------------------

        for team in ["purple", "red", "yellow"]:

            power = sum(
                p["power"]
                for p in plan["teams"][team]
            )

            discord_message += (
                f"{team_emojis[team]} **{team_titles[team]}**\n"
            )

            for player in plan["teams"][team]:
                badges = []

                if player["leader"]:
                    badges.append("👑")

                if player["support"]:
                    badges.append("🤝")

                badge_text = ""
                if badges:
                    badge_text = " " + " ".join(badges)

                discord_message += (
                    f"{player['name']}{badge_text}\n"
                )

                # power += player["power"]

            # discord_message += (
            #     f"\n⚡ Total Power: {power:,}\n\n"
            # )

        discord_message += (
            "━━━━━━━━━━━━━━━━━━━━━━\n\n"
        )

        discord_message += (
            "📝 **NOTE**\n"
            "Some players are listed as substitutes because we have a full roster. "
            "If a slot becomes available, substitutes may enter within the first 3 minutes of the battle.\n"
        )

        # ------------------------------------------
        # Kingshot Export
        # ------------------------------------------

        for title, body in exports:

            st.subheader(title)

            st.caption(f"{len(body)} characters")

            st.code(
                body,
                language=None
            )

        # ------------------------------------------
        # Discord Export
        # ------------------------------------------
        st.divider()
        st.header("💬 Discord Message")
        st.caption(f"{len(discord_message):,} characters")
        st.code(discord_message, language=None)

    