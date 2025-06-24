# AI Agent vs Game Theory Strategies Simulator

This project analyzes the performance of AI agents (specifically Anthropic's Claude 3) against classic game theory strategies in repeated Prisoner's Dilemma games. The simulator provides a comprehensive GUI for real-time visualization and detailed CSV logging for research purposes.

---

## Project Goal

**Primary Objective:** Analyze how AI agents like Claude perform against established game theory strategies in repeated games, providing insights into AI decision-making patterns and strategic behavior.

---

## Features

### **Core Functionality**
- **AI Agent Analysis:** Claude 3 (Anthropic) plays against classic game theory strategies
- **User-Configurable Matches:** Select number of rounds and opponent strategy before each simulation
- **Real-Time Visualization:** Live GUI showing game progress with detailed payoff matrix
- **Comprehensive Logging:** Every round logged to CSV with full context for research

### **Game Theory Strategies Available**
1. **Always Trust** - Unconditionally cooperative
2. **Always Cheat** - Unconditionally selfish  
3. **Tit-for-Tat** - Copy opponent's last move, start with trust
4. **Grudger** - Trust until betrayed, then always cheat
5. **Detective** - Test opponent first, then adapt strategy
6. **Simpleton** - Simple learning based on last round outcome
7. **Random** - Random moves each round
8. **Copykitten** - Forgiving Tit-for-Tat (requires two consecutive cheats)

### **GUI Features**
- **Selection Form:** Choose number of rounds and opponent strategy
- **Payoff Matrix:** Visual 2x2 matrix showing all possible outcomes with emojis and colors
- **Live Round History:** Horizontal scrollable matrix showing all rounds with moves and points
- **Real-Time Updates:** Live display of current moves, scores, and Claude's reasoning
- **Stick Figure Visualization:** Visual representation of AI agent vs opponent

---

## Game Rules

**Prisoner's Dilemma Payoff Matrix:**
- **Both TRUST:** +2 points each
- **Both CHEAT:** 0 points each  
- **You TRUST, Opponent CHEATS:** You get -1, Opponent gets +3
- **You CHEAT, Opponent TRUSTS:** You get +3, Opponent gets -1

**Objective:** Maximize your own total points over multiple rounds.

---

## Installation & Setup

### Prerequisites
- **Python 3.9+** (Homebrew version recommended on macOS for GUI support)
- **pip** (Python package manager)

### Dependencies
```sh
pip3 install matplotlib requests
```

### Claude API Setup (Required)
1. Create `claude_api_key.py` in the project directory:
   ```python
   CLAUDE_API_KEY = "sk-...your-anthropic-api-key..."
   ```
2. **Important:** Never commit this file to version control

---

## Usage

### Running the Simulator
```sh
python3 trust_simulator.py
```

### How to Use
1. **Configure Match:** Select number of rounds and opponent strategy
2. **Start Simulation:** Click "Start Simulation" to begin
3. **Watch Live:** Observe Claude's decisions and reasoning in real-time
4. **Review Results:** Check the round history matrix and CSV output

### GUI Controls
- **Start Simulation:** Begin the match with selected parameters
- **Reset Simulation:** Clear results and return to configuration
- **Round History:** Scrollable matrix showing all rounds with moves and points

---

## CSV Data Output

Each round is logged to `trust_sim_results.csv` with the following fields:

| Field | Description |
|-------|-------------|
| `match_id` | Unique 8-digit identifier for the match |
| `round` | Round number within the match |
| `main_agent_strategy` | Always "Claude" |
| `opponent_strategy` | Selected opponent strategy |
| `main_agent_action` | Claude's move (TRUST/CHEAT) |
| `opponent_action` | Opponent's move (TRUST/CHEAT) |
| `main_agent_payoff` | Points earned by Claude this round |
| `opponent_payoff` | Points earned by opponent this round |
| `main_agent_total_score` | Claude's cumulative score |
| `opponent_total_score` | Opponent's cumulative score |
| `claude_reasoning` | Claude's explanation for its move |
| `history_included` | Whether round included previous history |
| `timestamp` | ISO timestamp of the round |
| `payoff_matrix` | Full payoff matrix as JSON |

---

## Strategy Analysis

### **Always Trust**
- **Behavior:** Always cooperates
- **Best Against:** Cooperative strategies
- **Weakness:** Exploited by cheaters

### **Always Cheat**  
- **Behavior:** Always defects
- **Best Against:** Naive cooperators
- **Weakness:** Mutual defection outcomes

### **Tit-for-Tat**
- **Behavior:** Start cooperative, then mirror opponent
- **Best Against:** Most strategies in repeated games
- **Strength:** Forgiving but retaliatory

### **Grudger**
- **Behavior:** Cooperative until betrayed, then always defect
- **Best Against:** Strategies that occasionally cheat
- **Weakness:** Cannot recover from misunderstandings

### **Detective**
- **Behavior:** Tests opponent first, then adapts
- **Best Against:** Simple strategies
- **Strength:** Can identify and exploit patterns

### **Simpleton**
- **Behavior:** Simple learning based on last round
- **Best Against:** Predictable strategies
- **Weakness:** Can be exploited by complex strategies

### **Random**
- **Behavior:** Random moves each round
- **Best Against:** No strategy consistently
- **Characteristic:** Unpredictable but suboptimal

### **Copykitten**
- **Behavior:** Forgiving Tit-for-Tat
- **Best Against:** Strategies that occasionally cheat
- **Strength:** More tolerant than standard Tit-for-Tat

---

## Research Applications

This simulator is designed for:
- **AI Behavior Analysis:** Understanding how Claude makes strategic decisions
- **Strategy Comparison:** Comparing AI performance against established strategies
- **Decision Pattern Analysis:** Studying AI reasoning and adaptation
- **Game Theory Research:** Testing theoretical predictions with AI agents

---

## Technical Details

### **Architecture**
- **GUI:** Tkinter-based interface with real-time updates
- **AI Integration:** Anthropic Claude 3 API for decision making
- **Data Logging:** Comprehensive CSV output for analysis
- **Visualization:** Multi-layered display with matrix, history, and reasoning

### **Key Components**
- `trust_simulator.py`: Main application with GUI and simulation logic
- `claude_prompt.py`: Claude API integration and prompt generation
- `claude_api_key.py`: API key configuration (user-created)
- `trust_sim_results.csv`: Detailed round-by-round data output

---

## Troubleshooting

### Common Issues
- **GUI not appearing:** Ensure you're using Homebrew Python on macOS
- **Claude API errors:** Check your API key and internet connection
- **CSV not updating:** Verify write permissions in the project directory

### Performance
- **API Rate Limits:** Claude API has rate limits; long matches may take time
- **GUI Responsiveness:** Large numbers of rounds may slow the interface

---

## License

MIT License

---

## Acknowledgments

- Inspired by the [Evolution of Trust](https://ncase.me/trust/) explorable explanation
- Built with Anthropic's Claude 3 API
- Uses classic game theory strategies from academic literature

---

## Future Enhancements

Potential areas for expansion:
- **Multiple AI Models:** Compare different AI agents
- **Strategy Evolution:** Allow strategies to adapt over time
- **Advanced Analytics:** Statistical analysis of AI performance patterns
- **Network Effects:** Multi-agent tournaments with AI participants 