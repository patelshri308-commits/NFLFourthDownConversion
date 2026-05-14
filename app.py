import pandas as pd
import streamlit as st
from sklearn.ensemble import RandomForestClassifier

st.title("NFL Fourth-Down Decision Simulator")

st.write(
    "Estimate whether going for it on fourth down is reasonable based on distance, field position, score state, and time remaining."
)

@st.cache_data
def load_data():
    return pd.read_csv("fourth_down_model_data.csv")

@st.cache_resource
def train_model(data):
    situation_dummies = pd.get_dummies(data["situation"], prefix="situation")

    X = pd.concat(
        [
            data[["score_differential", "game_seconds_remaining"]],
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
    f"Situation: 4th & {yards_to_go} from the {yardline_100}-yardline "
    f"with {game_seconds_remaining} seconds remaining."
)

# Distance bucket
if yards_to_go <= 2:
    distance_bucket = "Short"
elif yards_to_go <= 5:
    distance_bucket = "Medium"
else:
    distance_bucket = "Long"

# Field zone
if yardline_100 <= 20:
    field_zone = "Red Zone"
elif yardline_100 <= 50:
    field_zone = "Opponent Territory"
elif yardline_100 <= 80:
    field_zone = "Midfield Area"
else:
    field_zone = "Own Territory"

situation = f"{distance_bucket}_{field_zone}"
situation_col = f"situation_{situation}"

# Build model input row
input_row = pd.DataFrame(0, index=[0], columns=model_columns)

input_row.loc[0, "score_differential"] = score_differential
input_row.loc[0, "game_seconds_remaining"] = game_seconds_remaining

if situation_col in input_row.columns:
    input_row.loc[0, situation_col] = 1

conversion_probability = model.predict_proba(input_row)[0, 1]

if conversion_probability >= 0.70:
    confidence = "High"
elif conversion_probability >= 0.45:
    confidence = "Moderate"
else:
    confidence = "Low"

# Expected points logic
if yardline_100 <= 20:
    ep_success = 3.0
elif yardline_100 <= 50:
    ep_success = 2.3
else:
    ep_success = 1.5

if yardline_100 <= 20:
    ep_failure = -0.8
elif yardline_100 <= 50:
    ep_failure = -1.5
else:
    ep_failure = -2.5

ev_go = (
    conversion_probability * ep_success
    +
    (1 - conversion_probability) * ep_failure
)

st.divider()

st.subheader("Estimated Decision")

st.metric("Conversion Probability", f"{conversion_probability:.1%}")
st.metric("Expected Value of Going For It", round(ev_go, 2))
st.metric("Conversion Confidence", confidence)

if ev_go > 0:
    st.success("Recommendation: Go For It")
else:
    st.error("Recommendation: Do Not Go For It")

st.subheader("Decision Explanation")

if ev_go > 0:
    st.write(
        "The model recommends going for it because the expected value is positive. "
        "This means the estimated reward of converting outweighs the estimated cost of failing."
    )
else:
    st.write(
        "The model recommends not going for it because the expected value is negative. "
        "This means the estimated cost of failing outweighs the estimated reward of converting."
    )

if yards_to_go <= 2:
    st.write("- Short yardage improves the likelihood of conversion.")
elif yards_to_go <= 5:
    st.write("- Medium distance creates a more balanced risk/reward decision.")
else:
    st.write("- Long distance lowers the likelihood of conversion.")

if yardline_100 <= 20:
    st.write("- Red zone field position increases the value of converting but also changes the risk profile.")
elif yardline_100 <= 50:
    st.write("- Opponent territory creates a strong decision point because punting or kicking may have limited value.")
else:
    st.write("- Own-side field position increases the cost of failing.")

st.divider()

st.subheader("Model Context")

st.write(f"""
**Situation Type:** {situation}  

- **Distance Bucket:** {distance_bucket}
- **Field Zone:** {field_zone}
- **Score Differential:** {score_differential}
- **Game Seconds Remaining:** {game_seconds_remaining}
""")

st.divider()

st.caption(
    "Version 1 prototype. Conversion probability is estimated using a Random Forest model trained on nflverse fourth-down attempt data. Expected value logic is simplified and intended for analytical/educational purposes."
)

