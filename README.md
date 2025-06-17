# Evolution of Trust Simulator

This project simulates the evolution of trust using a population of agents playing repeated games (like the Prisoner's Dilemma) with various strategies. The simulation is visualized with a Tkinter GUI, showing a payoff matrix for each match between two agents, and provides controls to animate, pause, and step through the simulation.

---

## Features

- **Agent Strategies:** Includes classic strategies like Always Cooperate, Always Defect, Tit-for-Tat, Grudger, Detective, Simpleton, Random, and Copykitten.
- **Tournament Simulation:** All agents play matches against each other in each generation.
- **Evolution:** The worst-performing agents are eliminated, and the best are cloned for the next generation.
- **GUI Visualization:** 
  - Shows a 2x2 payoff matrix for each match.
  - Displays the current agents and their strategies.
  - Animates through all matches and rounds.
  - Controls for Pause, Resume, Step Forward, and Step Backward.

---

## Setup

### 1. Prerequisites

- **Python 3.9** (preferably installed via Homebrew on macOS for best Tkinter compatibility)
- **pip** (Python package manager)

### 2. Install Dependencies

Open a terminal in the project directory and run:

```sh
pip3 install matplotlib six python-dateutil
```

If you are using Homebrew Python (recommended on macOS):

```sh
/opt/homebrew/opt/python@3.9/bin/python3.9 -m pip install matplotlib six python-dateutil
```

### 3. Run the Simulator

**Recommended (Homebrew Python on macOS):**
```sh
/opt/homebrew/opt/python@3.9/bin/python3.9 trust_simulator.py
```

**Or, with your system Python:**
```sh
python3 trust_simulator.py
```

---

## How the Code Works

### Main Components

- **Agent & Strategy Classes:**  
  Each agent is assigned a strategy. Strategies determine how agents play each round based on history.

- **Game Logic:**  
  - `play_match_record`: Plays a match between two agents, records every round (moves and payoffs).
  - `run_tournament_record`: Runs all possible matches for the current population, storing all match/round data for animation.

- **Evolution:**  
  After each generation, the worst agents are eliminated and the best are cloned.

- **GUI (Tkinter):**
  - **Matrix Display:** Shows the current round's moves and payoffs in a 2x2 matrix.
  - **Agent Info:** Displays the strategies of the two agents currently playing.
  - **Controls:** Start, Pause, Resume, Step Forward, Step Backward, and Reset.
  - **Animation:** Animates through all matches and rounds, updating the matrix and agent info.

### Animation Controls

- **Start Simulation:** Begins the simulation and animates through all matches and rounds.
- **Pause:** Pauses the animation.
- **Resume:** Continues the animation from where it was paused.
- **Step Forward/Backward:** Step through rounds and matches one at a time.
- **Reset Simulation:** Resets everything to the initial state.

---

## Customization

- **Change Number of Agents, Generations, or Strategies:**  
  Edit the `CONFIG` dictionary at the top of `trust_simulator.py`.

- **Modify Payoff Matrix:**  
  Edit the `PAYOFF` dictionary in `trust_simulator.py`.

---

## Troubleshooting

- If the GUI does not appear or is blank, ensure you are using the correct Python version (preferably Homebrew Python on macOS).
- Make sure all dependencies are installed for the same Python interpreter you use to run the script.

---

## License

MIT License

---

## Acknowledgments

Inspired by the [Evolution of Trust](https://ncase.me/trust/) explorable explanation. 