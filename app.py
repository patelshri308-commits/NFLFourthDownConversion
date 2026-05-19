import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier

st.set_page_config(
    page_title="NFL Fourth-Down Decision Simulator",
    page_icon="🏈",
    layout="centered"
)

st.title("NFL Fourth-Down Decision Simulator")

st.write(
    "Compare fourth-down options using conversion probability, expected value, "
    "field goal logic, punt logic, and basic score-time strategy."
)


@st.cache_data
def load_data():
    return pd.read_csv("fourth_down_model_data.csv")


@st.cache_resource
def train_model(data):
    situation_dummies = pd.get_dummies(data["situation"], prefix="situation")

    X = pd.concat(
        [
            data[["ydstogo", "score_differential", "game_seconds_remaining"]],
            situation_dummies
        ],
        axis=1
    )

    y = data["converted"]

    model = RandomForestClassifier(
        n_estimators=200,
        max_depth=5,
        random_state=42
    )

    model.fit(X, y)

    return model, X.columns


def get_distance_bucket(yards_to_go):
    if yards_to_go <= 2:
        return "Short"
    elif yards_to_go <= 5:
        return "Medium"
    else:
        return "Long"


def get_field_zone(yardline_100):
    if yardline_100 <= 20:
        return "Red Zone"
    elif yardline_100 <= 50:
        return "Opponent Territory"
    elif yardline_100 <= 80:
        return "Midfield Area"
    else:
        return "Own Territory"


def get_field_bin(yardline_100):
    if yardline_100 <= 10:
        return "Inside 10"
    elif yardline_100 <= 20:
        return "10-20"
    elif yardline_100 <= 40:
        return "20-40"
    elif yardline_100 <= 60:
        return "40-60"
    elif yardline_100 <= 80:
        return "60-80"
    else:
        return "80-100"


def estimate_success_value(yardline_100, yards_to_go, base_ep_success):
    if yardline_100 <= 5 and yards_to_go <= 2:
        return 5.5
    elif yardline_100 <= 10 and yards_to_go <= 2:
        return 4.5
    else:
        return base_ep_success


def estimate_failure_value(yardline_100):
    if yardline_100 <= 10:
        return -0.5
    elif yardline_100 <= 20:
        return -0.8
    elif yardline_100 <= 40:
        return -1.5
    elif yardline_100 <= 60:
        return -2.0
    else:
        return -2.5


def estimate_fg_probability(distance):
    if distance < 30:
        return 0.95
    elif distance < 40:
        return 0.88
    elif distance < 50:
        return 0.75
    elif distance < 60:
        return 0.55
    else:
        return 0.25


def estimate_fg_miss_cost(yardline_100):
    if yardline_100 <= 20:
        return -0.8
    elif yardline_100 <= 35:
        return -1.2
    elif yardline_100 <= 50:
        return -1.8
    else:
        return -2.5


def estimate_fg_ev(yardline_100):
    field_goal_distance = yardline_100 + 17
    fg_probability = estimate_fg_probability(field_goal_distance)
    miss_cost = estimate_fg_miss_cost(yardline_100)

    fg_ev = (fg_probability * 3) + ((1 - fg_probability) * miss_cost)

    return {
        "field_goal_distance": field_goal_distance,
        "fg_probability": fg_probability,
        "miss_cost": miss_cost,
        "fg_ev": fg_ev
    }


def estimate_punt_ev(yardline_100):
    if yardline_100 <= 40:
        net_punt = 30
    elif yardline_100 <= 60:
        net_punt = 40
    else:
        net_punt = 45

    opponent_start_yardline = max(1, yardline_100 - net_punt)

    if opponent_start_yardline <= 10:
        punt_ev = 0.6
    elif opponent_start_yardline <= 20:
        punt_ev = 0.3
    elif opponent_start_yardline <= 40:
        punt_ev = -0.2
    elif opponent_start_yardline <= 60:
        punt_ev = -0.7
    else:
        punt_ev = -1.2

    return {
        "net_punt": net_punt,
        "opponent_start_yardline": opponent_start_yardline,
        "punt_ev": punt_ev
    }


def estimate_go_for_it_value(
    yards_to_go,
    yardline_100,
    score_differential,
    game_seconds_remaining,
    situation_model,
    model_columns
):
    distance_bucket = get_distance_bucket(yards_to_go)
    field_zone = get_field_zone(yardline_100)
    situation = f"{distance_bucket}_{field_zone}"
    situation_col = f"situation_{situation}"

    input_row = pd.DataFrame(0, index=[0], columns=model_columns)

    input_row.loc[0, "ydstogo"] = yards_to_go
    input_row.loc[0, "score_differential"] = score_differential
    input_row.loc[0, "game_seconds_remaining"] = game_seconds_remaining

    if situation_col in input_row.columns:
        input_row.loc[0, situation_col] = 1

    conversion_probability = situation_model.predict_proba(input_row)[0, 1]

    estimated_success_yardline = max(yardline_100 - yards_to_go, 1)
    success_bin = get_field_bin(estimated_success_yardline)

    base_success_values = {
        "Inside 10": 2.65,
        "10-20": 2.17,
        "20-40": 2.68,
        "40-60": 2.40,
        "60-80": 2.08,
        "80-100": 1.27
    }

    base_ep_success = base_success_values.get(success_bin, 0)

    ep_success = estimate_success_value(
        yardline_100,
        yards_to_go,
        base_ep_success
    )

    ep_failure = estimate_failure_value(yardline_100)

    ev_go = (
        conversion_probability * ep_success
        +
        (1 - conversion_probability) * ep_failure
    )

    return {
        "conversion_probability": conversion_probability,
        "ep_success": ep_success,
        "ep_failure": ep_failure,
        "ev_go": ev_go,
        "distance_bucket": distance_bucket,
        "field_zone": field_zone,
        "situation": situation
    }


def has_touchdown_urgency(score_differential, game_seconds_remaining):
    return score_differential <= -7 and game_seconds_remaining <= 600


def compare_decisions_with_strategy(
    go_ev,
    fg_ev,
    punt_ev,
    yards_to_go,
    score_differential,
    game_seconds_remaining
):
    options = {
        "Go For It": go_ev,
        "Attempt Field Goal": fg_ev,
        "Punt": punt_ev
    }

    base_recommendation = max(options, key=options.get)

    touchdown_urgency = has_touchdown_urgency(
        score_differential,
        game_seconds_remaining
    )

    if touchdown_urgency and yards_to_go <= 3:
        final_recommendation = "Go For It"
        strategy_note = (
            "Touchdown urgency is active, so the simulator favors going for it "
            "despite the base expected-value recommendation."
        )
    else:
        final_recommendation = base_recommendation
        strategy_note = (
            "Recommendation is based on the highest expected-value option."
        )

    return {
        "base_recommendation": base_recommendation,
        "final_recommendation": final_recommendation,
        "touchdown_urgency": touchdown_urgency,
        "strategy_note": strategy_note
    }


data = load_data()
model, model_columns = train_model(data)

st.divider()

st.subheader("Game Situation")

yards_to_go = st.slider("Yards To Go", 1, 20, 2)

yardline_100 = st.slider(
    "Yardline: Distance from Opponent End Zone",
    1,
    99,
    45
)

score_differential = st.slider(
    "Score Differential",
    -30,
    30,
    0,
    help="Positive means the offense is winning. Negative means the offense is trailing."
)

game_seconds_remaining = st.slider(
    "Game Seconds Remaining",
    0,
    3600,
    900
)

st.info(
    f"Situation: 4th & {yards_to_go} from {yardline_100} yards away from the opponent end zone, "
    f"score differential {score_differential}, with {game_seconds_remaining} seconds remaining."
)

go_result = estimate_go_for_it_value(
    yards_to_go=yards_to_go,
    yardline_100=yardline_100,
    score_differential=score_differential,
    game_seconds_remaining=game_seconds_remaining,
    situation_model=model,
    model_columns=model_columns
)

fg_result = estimate_fg_ev(yardline_100)
punt_result = estimate_punt_ev(yardline_100)

decision = compare_decisions_with_strategy(
    go_ev=go_result["ev_go"],
    fg_ev=fg_result["fg_ev"],
    punt_ev=punt_result["punt_ev"],
    yards_to_go=yards_to_go,
    score_differential=score_differential,
    game_seconds_remaining=game_seconds_remaining
)

st.divider()

st.subheader("Decision Recommendation")

if decision["final_recommendation"] == "Go For It":
    st.success("Recommendation: Go For It")
elif decision["final_recommendation"] == "Attempt Field Goal":
    st.info("Recommendation: Attempt Field Goal")
else:
    st.warning("Recommendation: Punt")

st.write(f"**Base EV Recommendation:** {decision['base_recommendation']}")
st.write(f"**Final Strategy Recommendation:** {decision['final_recommendation']}")

if decision["touchdown_urgency"]:
    st.warning("Touchdown urgency adjustment is active.")

st.caption(decision["strategy_note"])

st.divider()

st.subheader("Expected Value Comparison")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Go For It EV", round(go_result["ev_go"], 2))

with col2:
    st.metric("Field Goal EV", round(fg_result["fg_ev"], 2))

with col3:
    st.metric("Punt EV", round(punt_result["punt_ev"], 2))

st.divider()

st.subheader("Model Details")

st.metric(
    "Conversion Probability",
    f"{go_result['conversion_probability']:.1%}"
)

st.write(f"**Situation Type:** {go_result['situation']}")
st.write(f"**Distance Bucket:** {go_result['distance_bucket']}")
st.write(f"**Field Zone:** {go_result['field_zone']}")

st.write(f"**Field Goal Distance:** {fg_result['field_goal_distance']} yards")
st.write(f"**FG Make Probability:** {fg_result['fg_probability']:.1%}")
st.write(f"**Estimated Net Punt:** {punt_result['net_punt']} yards")
st.write(
    f"**Estimated Opponent Start After Punt:** "
    f"{punt_result['opponent_start_yardline']} yards from opponent end zone"
)

st.divider()

st.subheader("How to Interpret This")

st.write("""
This simulator compares three fourth-down decisions:

- **Go For It**: uses a Random Forest conversion model and expected value logic.
- **Field Goal**: estimates field goal distance, make probability, and missed-kick cost.
- **Punt**: estimates net punt distance and resulting field-position value.

The final recommendation may differ from the base expected-value recommendation when touchdown urgency is active.
""")

st.divider()

st.subheader("Version 2 Notes")

st.write("""
This is a Version 2 prototype.

Current limitations:
- Expected values are simplified estimates.
- The simulator does not yet use a full win-probability model.
- Weather, personnel, kicker quality, defensive alignment, and team-specific tendencies are not included.
- Touchdown urgency is handled with a simple strategy-aware rule.
""")

st.caption(
    "Built for educational and analytical purposes using nflverse fourth-down data."
)