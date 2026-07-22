import streamlit as st
import pandas as pd
from datetime import datetime, time
from planner import generate_assignments
from config import DEFAULT_LEADERS, DEFAULT_ROAMER
import json
from pathlib import Path
import re
from config import DEFAULT_LEADERS, DEFAULT_ROAMER, DEFAULT_SHEET_URL
import streamlit.components.v1 as components


def show_swordland(page):

    # =====================================================
    # PAGE CONFIG
    # =====================================================

    st.set_page_config(
        page_title="KNG - Swordland Planner",
        page_icon="⚔️",
        layout="centered"
    )

    if page in ["swordland_create"]:
        st.title("➕ Create Plan - SS")
    else:
        st.title("📂 Load Plan - SS")

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

    if st.session_state.page == "swordland_create":

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
        # ROSTER SOURCE
        # =====================================================

        def clear_sheet_url():
            st.session_state.sheet_url = ""

        # Initialize once
        if "sheet_url" not in st.session_state:
            st.session_state.sheet_url = DEFAULT_SHEET_URL

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

        # if st.button("🔄 Change Spreadsheet"):

        #     st.session_state.roster_df = None

        #     if "selection" in st.session_state:
        #         del st.session_state["selection"]

        #     st.rerun()
        
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

            power = int(row["Power"]) if pd.notna(row["Power"]) else 0

            label = f"{row['Player Name']} ({power:,})"

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

        # def available_labels(current_key):

        #     used = set()

        #     for key, value in st.session_state.selection.items():

        #         if key == current_key:
        #             continue

        #         if value != "":
        #             used.add(value)

        #     labels = []

        #     current = st.session_state.selection[current_key]

        #     if current != "" and current in reverse_lookup:
        #         labels.append(reverse_lookup[current])

        #     labels.append("")

        #     for label, player in player_lookup.items():

        #         if player not in used:

        #             if label not in labels:
        #                 labels.append(label)

        #     return labels

        def available_labels(current_key, top_n=None):

            used = set()

            for key, value in st.session_state.selection.items():

                if key == current_key:
                    continue

                if value != "":
                    used.add(value)

            labels = []

            current = st.session_state.selection[current_key]

            # Keep the current selection visible
            if current != "" and current in reverse_lookup:
                labels.append(reverse_lookup[current])

            labels.append("")

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


        # def select_player(
        #     title,
        #     state_key,
        # ):
        def select_player(
            title,
            state_key,
            top_n=None,
        ):

            # labels = available_labels(state_key)
            labels = available_labels(state_key, top_n)

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


        def save_plan(
            result,
            legion,
            event_date,
            event_time_label,
        ):

            path = PLANS_FOLDER / f"{legion}.json"

            plan = {
            "title": f"{legion} - {event_date.strftime('%d/%m')} - {event_time_label}",
            "event_date": event_date.isoformat(),
            "event_time": event_time_label,
            "legion": legion,
            "roamer": (
                result.roamer.name
                if result.roamer
                else ""
            ),
            "undercellars": result.undercellars,
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
                        "undercellar": p.undercellar,
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
        # LEADERS
        # =====================================================

        st.divider()

        st.header("👑 Leaders")

        c1, c2 = st.columns(2)

        with c1:

            leader_stables = select_player(
                "🏇 Stables / Reformation",
                "leader_stables",
                top_n=10,
            )

            leader_enemy1 = select_player(
                "⚔️ Enemy Sanctuary",
                "leader_enemy1",
                top_n=10,
            )

        with c2:

            leader_bell = select_player(
                "🔔 Bell Tower / Mercenary",
                "leader_bell",
                top_n=10,
            )

            leader_enemy2 = select_player(
                "🛡️ Our Sanctuary",
                "leader_enemy2",
                top_n=10,
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
                "support_stables",
                top_n=10,
            )

            support_enemy1 = select_player(
                "Support - Enemy Sanctuary",
                "support_enemy1",
                top_n=10,
            )

        with c2:

            support_bell = select_player(
                "Support - Bell Tower",
                "support_bell",
                top_n=10,
            )

            support_enemy2 = select_player(
                "Support - Our Sanctuary",
                "support_enemy2",
                top_n=10,
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
                            st.markdown(f"""
                                <div style="display:flex;justify-content:space-between;align-items:center;">
                                    <div>{badge_text} <b>{player.name}</b></div>
                                    <div><b>{player.power:,}</b></div>
                                </div>
                                """, unsafe_allow_html=True)
                        

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

            # st.subheader("Next Step")

            # st.info(
            #     "Your plan has been saved. You can now open it to copy the "
            #     "Application and Discord messages."
            # )

            # if st.button(
            #     f"📂 Open {legion} Plan",
            #     use_container_width=True,
            #     type="secondary",
            # ):

            #     st.session_state.loaded_legion = legion
            #     st.session_state.mode = "load"

            #     if "result" in st.session_state:
            #         del st.session_state["result"]

            #     st.rerun()


    if st.session_state.page == "swordland_load":

        legion = st.radio(
            "Legion",
            ["L1", "L2"],
            horizontal=True,
        )

        plan_file = PLANS_FOLDER / f"{legion}.json"

        if not plan_file.exists():
            st.warning(f"No saved plan found for {legion}.")
            st.stop()

        with open(plan_file, encoding="utf-8") as f:
            plan = json.load(f)

        st.success(f"Loaded {plan['title']}")

        announcement = f"""SWORDLAND SHOWDOWN LEGION ({plan["legion"][-1]}) TEAMS:

    📅 {datetime.fromisoformat(plan["event_date"]).strftime("%d/%m")} @ {plan["event_time"]}

    The following lists show the teams along with the buildings they will be occupying.

    👻 {plan["roamer"] if plan["roamer"] else "No Roamer"} will be floating throughout the map targeting enemy cities.

    It’s important to garrison quickly in order to hold off single attacks. Additionally, don’t forget to save a march to collect loot from buildings.

    📝 View additional instructions with the battlefield map in Discord 🙏
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
            ("Stables",
            team_text("🚨 Stables/Reformation", plan["teams"]["stables"])),
            ("Bell Tower",
            team_text("🚨 Bell Tower/Mercenary", plan["teams"]["bell"])),
            ("Enemy Sanctuary",
            team_text("🚨 Enemy Sanctuary", plan["teams"]["enemy1"])),
            ("Our Sanctuary",
            team_text("🚨 Our Sanctuary", plan["teams"]["enemy2"])),
        ]

        TEAM_NAMES = {
            "bell": "🗼 Bell Tower/Mercenary",
            "stables": "🗼 Stables/Reformation",
            "enemy1": "🗼 Enemy Sanctuary & Abbeys",
            "enemy2": "🗼 Our Sanctuary & Abbeys",
        }

        legion_name = (
            "⚔️ SWORDLAND LEGION 1️⃣ ⚔️"
            if plan["legion"] == "L1"
            else "⚔️ SWORDLAND LEGION 2️⃣ ⚔️"
        )

        discord_lines = []

        # =====================================================
        # HEADER
        # =====================================================

        discord_lines.append(legion_name)
        discord_lines.append("")
        event_date = datetime.fromisoformat(plan["event_date"])

        discord_lines.append(
            f"🗓️ Today {event_date.day}/{event_date.month}"
        )

        discord_lines.append(
            f"⏰ {plan['event_time']}"
        )
        discord_lines.append("")
        discord_lines.append(
            "The following members have been assigned to the following buildings:"
        )
        discord_lines.append("")

        # =====================================================
        # BUILDINGS
        # =====================================================

        for team in ["bell", "stables", "enemy1", "enemy2"]:

            discord_lines.append(TEAM_NAMES[team])

            ordered = sorted(
                plan["teams"][team],
                key=lambda p: (
                    not p["leader"],
                    not p["support"],
                    -p["power"]
                )
            )

            for player in ordered:

                line = player["name"]

                if player["leader"]:
                    line = f"👑 {line}"

                elif player["support"]:
                    line = f"🤝 {line}"

                discord_lines.append(line)

            discord_lines.append("")

        # =====================================================
        # ROAMER
        # =====================================================

        discord_lines.append(
            f"🚶 Roamer: {plan['roamer'] if plan['roamer'] else 'None Assigned'}"
        )

        # discord_lines.append("")

        # # =====================================================
        # # UNDERCELLARS
        # # =====================================================

        # if plan["undercellars"]:

        #     discord_lines.append(
        #         f"💰 Undercellars: {' / '.join(plan['undercellars'])}"
        #     )

        # else:

        #     discord_lines.append(
        #         "💰 Undercellars: None Assigned"
        #     )

        discord_lines.append("")
        discord_lines.append("")
        discord_lines.append("📝 NOTES:")
        discord_lines.append("")
        discord_lines.append(
            "1) Priority buildings are marked in Blue and Green."
        )
        discord_lines.append("")
        discord_lines.append(
            "2) Please look for and collect loot when dropped from buildings. Don't forget about Undercellars which appear in Phase 3 of the event."
        )
        discord_lines.append("")
        discord_lines.append(
            "3) When the center 🏰 opens, I will speed in and hopefully take it right away. Please send reinforcements 🙏"
        )

        discord_message = "\n".join(discord_lines)

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

        st.caption(f"{len(discord_message)} characters")

        st.code(
            discord_message,
            language=None,
        )

    