**NFL Fourth-Down Decision Simulator**

An interactive sports analytics project focused on modeling NFL fourth-down decision-making using historical play-by-play data from nflverse. The project combines exploratory data analysis, machine learning, feature engineering, and expected value modeling to evaluate whether teams should go for it on fourth down in different game situations.

**Live App**

Try the interactive simulator here:
NFL Fourth-Down Decision Simulator￼

⸻

**Project Goals**

This project was designed to explore how NFL teams behave on fourth down and how factors such as:

* yards to go
* field position
* score differential
* game time remaining

influence fourth-down conversion outcomes and strategic decision-making.

The project evolved from exploratory analytics into a decision-support simulator capable of estimating:

* fourth-down conversion probability
* expected value of going for it
* recommendation logic based on game context

⸻

**Features**

* Exploratory fourth-down analytics using nflverse play-by-play data
* Logistic Regression and Random Forest modeling
* Football-specific feature engineering
* Situational interaction modeling
* Expected value framework for fourth-down decisions
* Interactive Streamlit simulator
* Real-time recommendation engine

⸻

**Example Simulator Inputs**

* 4th & distance
* field position
* score differential
* time remaining

**Example Outputs**

* estimated conversion probability
* expected value of going for it
* go-for-it recommendation
* contextual decision explanation

⸻

**Key Analytical Findings**

* Short-yardage situations produce the strongest positive conversion signals.
* Field position becomes significantly more meaningful when combined with distance.
* Game state and coaching behavior appear to influence fourth-down outcomes beyond pure football execution.
* Nonlinear models slightly improved predictive performance, suggesting contextual interaction effects exist within fourth-down decision-making.

⸻

**Models Used**

Logistic Regression

Used as the initial interpretable baseline model for estimating fourth-down conversion probability.

Random Forest Classifier

Used to capture nonlinear relationships and contextual interaction effects between football situations and game state variables.

⸻

**Data Sources**

* nflverse play-by-play dataset
    nflverse Play-by-Play Data￼
* Pro Football Reference
    Pro Football Reference￼

⸻

**Technologies Used**

* Python
* pandas
* scikit-learn
* matplotlib
* Streamlit

⸻

**Version 1 Limitations**

This project is currently a Version 1 prototype and has several intentionally simplified components:

* punt and field goal alternatives are not yet modeled
* expected value calculations are simplified
* weather, personnel, play design, and defensive alignments are not included
* the simulator focuses only on go-for-it decision evaluation

Future iterations may include:

* win probability modeling
* punt/field goal expected value comparison
* calibration analysis
* richer contextual football variables
* historical coaching decision review

⸻

**Author**

**Shri Patel**

* LinkedIn: https://www.linkedin.com/in/shripatel2003
