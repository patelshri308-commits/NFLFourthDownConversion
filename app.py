import streamlit as st

st.title("NFL Fourth-Down Decision Simulator")

st.write(
    "Estimate whether going for it on fourth down is reasonable based on distance, field position, score state, and time remaining."
)

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

st.divider()

st.subheader("Estimated Decision")

# Simple Version 1 prototype logic
# Later, this will be replaced with the trained conversion probability model.

if yards_to_go <= 2:
    conversion_probability = 0.70
elif yards_to_go <= 5:
    conversion_probability = 0.50
else:
    conversion_probability = 0.25

# Slight adjustment for score/time context
if score_differential < 0 and game_seconds_remaining < 900:
    conversion_probability += 0.05
elif score_differential > 7:
    conversion_probability -= 0.03

conversion_probability = max(0.05, min(conversion_probability, 0.95))

# Estimate success value based on field position
if yardline_100 <= 20:
    ep_success = 3.0
elif yardline_100 <= 50:
    ep_success = 2.3
else:
    ep_success = 1.5

# Estimate failure cost based on field position
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

st.metric("Conversion Probability", f"{conversion_probability:.1%}")
st.metric("Expected Value of Going For It", round(ev_go, 2))

if ev_go > 0:
    st.success("Recommendation: Go For It")
else:
    st.error("Recommendation: Do Not Go For It")

st.divider()

st.subheader("How to Read This")

st.write("""
- **Conversion Probability** estimates the chance of successfully gaining the required yards.
- **Expected Value** compares the benefit of converting against the cost of failing.
- A positive expected value suggests going for it may be reasonable.
- A negative expected value suggests the risk may outweigh the reward.
""")

st.divider()

st.caption(
    "Version 1 prototype. This simulator uses simplified decision logic for now and will later be connected to the trained fourth-down conversion model."
)
