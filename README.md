# Evolution of Trust Simulator

This project simulates the evolution of trust using a population of agents playing repeated games (like the Prisoner's Dilemma) with various strategies. The simulation is visualized with a Tkinter GUI, showing a payoff matrix for each match between two agents, and provides controls to animate, pause, and step through the simulation.

---

## Features

- **Agent Strategies:** Includes classic and modern strategies like Always Trust, Always Cheat, Tit-for-Tat, Grudger, Detective, Simpleton, Random, and Copykitten.
- **Tournament Simulation:** All agents play matches against each other in each generation.
- **Evolution:** The worst-performing agents are eliminated, and the best are cloned for the next generation.
- **GUI Visualization:** 
  - Shows a 2x2 payoff matrix for each match, using clear labels: "TRUST" and "CHEAT".
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
  Each agent is assigned a strategy. Strategies determine how agents play each round based on history. All moves are now represented as the full strings "TRUST" and "CHEAT" for maximum clarity.

- **Game Logic:**  
  - `play_match_record`: Plays a match between two agents, records every round (moves and payoffs).
  - `run_tournament_record`: Runs all possible matches for the current population, storing all match/round data for animation.

- **Payoff Matrix:**
  - The payoff matrix is now:
    - Both TRUST: Agent +1, Opponent +1
    - Both CHEAT: Agent 0, Opponent 0
    - Agent TRUST, Opponent CHEAT: Agent -1, Opponent +3
    - Agent CHEAT, Opponent TRUST: Agent +3, Opponent -1
  - The code and UI use these full move names everywhere.

- **Evolution:**  
  After each generation, the worst agents are eliminated and the best are cloned.

- **GUI (Tkinter):**
  - **Matrix Display:** Shows the current round's moves and payoffs in a 2x2 matrix, with clear "TRUST"/"CHEAT" labels.
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
  Edit the `PAYOFF_MATRIX` dictionary in `trust_simulator.py`.

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

---

## CSV Output

Each round of the simulation is logged to a CSV file (`trust_sim_results.csv`) with the following fields:

- `generation`: The generation number.
- `match_id`: Unique identifier for the match.
- `round`: The round number within the match.
- `main_agent_strategy`: The strategy of the main agent (can be 'Claude' if using Claude integration).
- `opponent_strategy`: The strategy of the opponent agent.
- `main_agent_action`: The action taken by the main agent ('TRUST' or 'CHEAT').
- `opponent_action`: The action taken by the opponent agent.
- `main_agent_payoff`: The payoff received by the main agent for this round.
- `opponent_payoff`: The payoff received by the opponent for this round.
- `main_agent_total_score`: Cumulative score for the main agent in the match so far.
- `opponent_total_score`: Cumulative score for the opponent in the match so far.
- `claude_reasoning`: If using Claude, the reasoning returned by the model for the main agent's move.
- `history_included`: Whether the round included history in the prompt (boolean).
- `timestamp`: ISO timestamp of the round.
- `payoff_matrix`: The full payoff matrix used for the game, as a JSON string (e.g. `{"('TRUST', 'TRUST')": [2, 2], ...}`).

This makes the simulation fully reproducible and suitable for research.

---

## Claude 3 Integration (Optional)

The simulator can use Anthropic's Claude 3 model as the main agent. This requires:
- `claude_prompt.py` (provided in this repo)
- `claude_api_key.py` (not tracked in git; you must create this file with your API key)
- The `requests` Python package

Claude's decisions and reasoning are logged in the CSV for every round.

---

## Additional Setup for Claude Integration

1. Install the `requests` package:
   ```sh
   pip3 install requests
   ```
2. Create a file named `claude_api_key.py` in the project directory with the following content:
   ```python
   CLAUDE_API_KEY = "sk-...your-anthropic-api-key..."
   ```
   **Do not commit this file to git.**

---

## .gitignore and Security

- The `.gitignore` file ensures that sensitive files like `claude_api_key.py` and Python bytecode are not tracked by git.
- Never share your API key or commit it to version control.

---

## Recent Major Changes

- **CSV Logging:** Every round now logs the full payoff matrix as a JSON string for reproducibility.
- **Claude 3 Integration:** The main agent can use Anthropic Claude 3 for decision making, with reasoning logged for each move.
- **Setup:** Requires `requests` and a local `claude_api_key.py` for Claude integration.
- **Security:** `.gitignore` added to protect sensitive files.

# ... existing code ... 