import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'  # Suppress deprecation warning

import csv
import random
import json
from collections import Counter
import tkinter as tk
from tkinter import ttk
from threading import Thread
import time
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from typing import List
from claude_prompt import generate_claude_prompt, call_claude
from datetime import datetime

# --- CONFIGURATION ---
CONFIG = {
    'num_agents': 20,
    'rounds_per_game': (3, 7),  # tuple means random between 3 and 7
    'generations': 50,
    'eliminate_n': 5,  # Number of worst to eliminate each generation
    'clone_n': 5,      # Number of best to clone each generation
    'strategies': [
        'Always Trust',
        'Always Cheat',
        'Tit-for-Tat',
        'Grudger',
        'Detective',
        'Simpleton',
        'Random',
        'Copykitten',
    ],
    'output_csv': 'trust_sim_results.csv',
    'gui_update_delay': 0.2,  # seconds between GUI updates
}

# --- STRATEGIES ---
class Strategy:
    def __init__(self, name):
        self.name = name
    def decide(self, history):
        raise NotImplementedError
    def __repr__(self):
        return self.name

class AlwaysTrust(Strategy):
    def __init__(self):
        super().__init__('Always Trust')
    def decide(self, history):
        return 'TRUST'

class AlwaysCheat(Strategy):
    def __init__(self):
        super().__init__('Always Cheat')
    def decide(self, history):
        return 'CHEAT'

class TitForTat(Strategy):
    def __init__(self):
        super().__init__('Tit-for-Tat')
    def decide(self, history):
        if not history:
            return 'TRUST'
        return history[-1][0]

class Grudger(Strategy):
    def __init__(self):
        super().__init__('Grudger')
        self.grudge = False
    def decide(self, history):
        if not history:
            self.grudge = False
            return 'TRUST'
        if any(opp == 'CHEAT' for opp, _ in history):
            self.grudge = True
        return 'CHEAT' if self.grudge else 'TRUST'

class Detective(Strategy):
    def __init__(self):
        super().__init__('Detective')
        self.switched = False
    def decide(self, history):
        moves = len(history)
        if not self.switched:
            for opp, _ in history:
                if opp == 'CHEAT':
                    self.switched = True
                    break
        if self.switched:
            if not history:
                return 'TRUST'
            return history[-1][0]
        else:
            if moves == 0: return 'TRUST'
            if moves == 1: return 'CHEAT'
            if moves == 2: return 'TRUST'
            if moves == 3: return 'TRUST'
            self.switched = True
            return 'CHEAT'

class Simpleton(Strategy):
    def __init__(self):
        super().__init__('Simpleton')
    def decide(self, history):
        if not history:
            return 'TRUST'
        opp, own = history[-1]
        if own == 'TRUST' and opp == 'CHEAT':
            return 'CHEAT'
        else:
            return own

class RandomStrategy(Strategy):
    def __init__(self):
        super().__init__('Random')
    def decide(self, history):
        return random.choice(['TRUST', 'CHEAT'])

class Copykitten(Strategy):
    def __init__(self):
        super().__init__('Copykitten')
    def decide(self, history):
        if len(history) < 2:
            return 'TRUST'
        # Only cheats if opponent cheated twice in a row
        if history[-1][0] == 'CHEAT' and history[-2][0] == 'CHEAT':
            return 'CHEAT'
        return 'TRUST'

# --- AGENT ---
class Agent:
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        self.strategy = self._make_strategy(strategy_name)
        self.score = 0
        self.history = []
    def _make_strategy(self, name):
        return {
            'Always Trust': AlwaysTrust(),
            'Always Cheat': AlwaysCheat(),
            'Tit-for-Tat': TitForTat(),
            'Grudger': Grudger(),
            'Detective': Detective(),
            'Simpleton': Simpleton(),
            'Random': RandomStrategy(),
            'Copykitten': Copykitten(),
        }[name]
    def reset(self):
        self.strategy = self._make_strategy(self.strategy_name)
        self.score = 0
        self.history = []
    def clone(self):
        return Agent(self.strategy_name)

# --- PAYOFF MATRIX LOGIC ---
# Payoff Matrix: (Agent Move, Opponent Move) -> (Agent Points, Opponent Points)
PAYOFF_MATRIX = {
    ('TRUST', 'TRUST'): (2, 2),    # Both Trust
    ('TRUST', 'CHEAT'): (-1, 3),   # Agent Trust, Opponent Cheat
    ('CHEAT', 'TRUST'): (3, -1),   # Agent Cheat, Opponent Trust
    ('CHEAT', 'CHEAT'): (0, 0),    # Both Cheat
}

def play_match_record(agent, opponent, rounds):
    agent.history = []
    opponent.history = []
    match_history = []
    for _ in range(rounds):
        agent_move = agent.strategy.decide(agent.history)
        opponent_move = opponent.strategy.decide(opponent.history)
        payoff_agent, payoff_opp = PAYOFF_MATRIX[(agent_move, opponent_move)]
        agent.score += payoff_agent
        opponent.score += payoff_opp
        agent.history.append((opponent_move, agent_move))
        opponent.history.append((agent_move, opponent_move))
        match_history.append({
            'agent_move': agent_move,
            'opponent_move': opponent_move,
            'agent_payoff': payoff_agent,
            'opponent_payoff': payoff_opp,
            'agent_strategy': agent.strategy_name,
            'opponent_strategy': opponent.strategy_name,
        })
    return match_history

def run_tournament_record(agents, rounds_per_game):
    matches = []
    for i, agent in enumerate(agents):
        for j, opponent in enumerate(agents):
            if i < j:
                rounds = random.randint(*rounds_per_game) if isinstance(rounds_per_game, tuple) else rounds_per_game
                match_history = play_match_record(agent, opponent, rounds)
                matches.append({
                    'agent_index': i,
                    'opponent_index': j,
                    'agent_strategy': agent.strategy_name,
                    'opponent_strategy': opponent.strategy_name,
                    'rounds': match_history
                })
    return matches

def evolve_population(agents, eliminate_n, clone_n):
    agents = sorted(agents, key=lambda a: a.score)
    survivors = agents[eliminate_n:]
    best = agents[-clone_n:]
    clones = [b.clone() for b in best]
    new_agents = survivors + clones
    # Reset all for next generation
    for a in new_agents:
        a.reset()
    return new_agents

def strategy_distribution(agents):
    return dict(Counter(a.strategy_name for a in agents))

def log_round_to_csv(row, csv_file='trust_sim_results.csv'):
    header = [
        'generation', 'match_id', 'round', 'main_agent_strategy', 'opponent_strategy',
        'main_agent_action', 'opponent_action', 'main_agent_payoff', 'opponent_payoff',
        'main_agent_total_score', 'opponent_total_score', 'claude_reasoning', 'history_included', 'timestamp',
        'payoff_matrix'  # New field
    ]
    file_exists = os.path.isfile(csv_file)
    write_header = not file_exists or os.path.getsize(csv_file) == 0
    # Add payoff_matrix to the row
    import json
    row = dict(row)  # Make a copy to avoid mutating input
    row['payoff_matrix'] = json.dumps(PAYOFF_MATRIX)
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

# --- GUI ---
class TrustSimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Evolution of Trust Simulator")
        self.root.geometry("900x650")
        self.main_container = tk.Frame(self.root, bg="#222222")
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.running = False
        self.paused = False
        self.sim_thread = None
        self.generation = 0
        self.max_generations = CONFIG['generations']
        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")
        self.claude_reason_var = tk.StringVar()
        self.claude_reason_var.set("")
        self.claude_move_var = tk.StringVar()
        self.claude_move_var.set("")
        self.match_round_var = tk.StringVar()
        self.match_round_var.set("")

        self._build_widgets()
        self.reset_simulation()
        print("GUI Initialization Complete")

    def _build_widgets(self):
        # Top control panel
        top_frame = tk.Frame(self.main_container, bg="#222222")
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(top_frame, text="Start Simulation", command=self.start_simulation, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.pause_btn = ttk.Button(top_frame, text="Pause", command=self.pause_simulation, width=10, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        self.resume_btn = ttk.Button(top_frame, text="Resume", command=self.resume_simulation, width=10, state=tk.DISABLED)
        self.resume_btn.pack(side=tk.LEFT, padx=5)
        self.step_btn = ttk.Button(top_frame, text="Step Forward", command=self.step_forward, width=12, state=tk.DISABLED)
        self.step_btn.pack(side=tk.LEFT, padx=5)
        self.back_btn = ttk.Button(top_frame, text="Step Backward", command=self.step_backward, width=12, state=tk.DISABLED)
        self.back_btn.pack(side=tk.LEFT, padx=5)
        self.reset_btn = ttk.Button(top_frame, text="Reset Simulation", command=self.reset_simulation, width=15)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        # Match/Round info prominently at top center
        match_round_label = tk.Label(self.main_container, textvariable=self.match_round_var, font=("Arial", 16, "bold"), fg="white", bg="#222222")
        match_round_label.pack(side=tk.TOP, pady=(0, 10))

        status_label = tk.Label(top_frame, textvariable=self.status_var, font=("Arial", 12), fg="white", bg="#222222")
        status_label.pack(side=tk.LEFT, padx=10)

        # Main layout: left (agent), center (matrix), right (opponent)
        main_frame = tk.Frame(self.main_container, bg="#222222")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Stick figure for Main Agent (left)
        self.agent_canvas = tk.Canvas(main_frame, width=70, height=120, bg='#222222', highlightthickness=0)
        self.agent_canvas.grid(row=0, column=0, padx=10, pady=10)
        self._draw_stick_figure(self.agent_canvas)
        self.agent_name_label = tk.Label(main_frame, text="Main Agent", font=("Arial", 12, "bold"), fg="white", bg="#222222")
        self.agent_name_label.grid(row=1, column=0)
        self.agent_total_label = tk.Label(main_frame, text="Total Points: 0", font=("Arial", 11, "bold"), fg="white", bg="#222222")
        self.agent_total_label.grid(row=2, column=0)
        self.agent_round_label = tk.Label(main_frame, text="", font=("Arial", 14), fg="white", bg="#222222")
        self.agent_round_label.grid(row=0, column=0, sticky='s', pady=(170, 0))
        # Claude's move (large, bold, white)
        self.claude_move_label = tk.Label(main_frame, textvariable=self.claude_move_var, font=("Arial", 22, "bold"), fg="white", bg="#222222")
        self.claude_move_label.grid(row=3, column=0, pady=(10, 0))
        # Claude's reasoning (bold, white)
        self.claude_reason_label = tk.Label(main_frame, textvariable=self.claude_reason_var, font=("Arial", 12, "bold"), fg="white", bg="#222222")
        self.claude_reason_label.grid(row=4, column=0, pady=(5, 0))

        # Center matrix with labels
        matrix_outer = tk.Frame(main_frame, bg="#222222")
        matrix_outer.grid(row=0, column=1, rowspan=5, padx=20, pady=10)

        # Top labels (Opponent)
        self.top_label_trust = tk.Label(matrix_outer, text="Opponent TRUSTS", font=("Arial", 11, "bold"), fg="white", bg="#222222")
        self.top_label_trust.grid(row=0, column=1, padx=5, pady=2)
        self.top_label_cheat = tk.Label(matrix_outer, text="Opponent CHEATS", font=("Arial", 11, "bold"), fg="white", bg="#222222")
        self.top_label_cheat.grid(row=0, column=2, padx=5, pady=2)

        # Side labels (Agent)
        self.side_label_trust = tk.Label(matrix_outer, text="Agent TRUSTS", font=("Arial", 11, "bold"), fg="white", bg="#222222")
        self.side_label_trust.grid(row=1, column=0, padx=5, pady=10)
        self.side_label_cheat = tk.Label(matrix_outer, text="Agent CHEATS", font=("Arial", 11, "bold"), fg="white", bg="#222222")
        self.side_label_cheat.grid(row=2, column=0, padx=5, pady=10)

        # Matrix cells
        self.matrix_labels: list[list[tk.Label]] = [[None, None], [None, None]]  # type: ignore
        choices = ['TRUST', 'CHEAT']
        for i, agent_move in enumerate(choices):
            for j, opponent_move in enumerate(choices):
                payoff = PAYOFF_MATRIX[(agent_move, opponent_move)]
                def sign(val):
                    return f"+{val}" if val > 0 else (f"{val}" if val < 0 else "0")
                label = tk.Label(matrix_outer, text=f"{self._move_name(agent_move)} vs {self._move_name(opponent_move)}\nA: {sign(payoff[0])}, O: {sign(payoff[1])}",
                                 width=16, height=4, borderwidth=2, relief="groove", bg="#333333", fg="white", font=("Arial", 13, "bold"))
                label.grid(row=1+i, column=1+j, padx=5, pady=5)
                self.matrix_labels[i][j] = label  # type: ignore

        # Stick figure for Opponent (right)
        self.opp_canvas = tk.Canvas(main_frame, width=70, height=120, bg='#222222', highlightthickness=0)
        self.opp_canvas.grid(row=0, column=2, padx=10, pady=10)
        self._draw_stick_figure(self.opp_canvas)
        self.opp_name_label = tk.Label(main_frame, text="Opponent", font=("Arial", 12, "bold"), fg="white", bg="#222222")
        self.opp_name_label.grid(row=1, column=2)
        self.opp_total_label = tk.Label(main_frame, text="Total Points: 0", font=("Arial", 11, "bold"), fg="white", bg="#222222")
        self.opp_total_label.grid(row=2, column=2)
        self.opp_round_label = tk.Label(main_frame, text="", font=("Arial", 14), fg="white", bg="#222222")
        self.opp_round_label.grid(row=0, column=2, sticky='s', pady=(170, 0))

    def _draw_stick_figure(self, canvas):
        # Head
        canvas.create_oval(20, 20, 50, 50, fill='white', outline='black', width=2)
        # Body
        canvas.create_line(35, 50, 35, 90, fill='black', width=2)
        # Arms
        canvas.create_line(35, 60, 15, 80, fill='black', width=2)
        canvas.create_line(35, 60, 55, 80, fill='black', width=2)
        # Legs
        canvas.create_line(35, 90, 20, 110, fill='black', width=2)
        canvas.create_line(35, 90, 50, 110, fill='black', width=2)

    def _move_name(self, move):
        return move

    def highlight_cell(self, move1, move2):
        for row in self.matrix_labels:
            for label in row:
                label.config(bg='white', fg='black')
        idx1 = 0 if move1 == 'TRUST' else 1
        idx2 = 0 if move2 == 'TRUST' else 1
        self.matrix_labels[idx1][idx2].config(bg='#90ee90', fg='black')

    def update_agent_labels(self, agent1, agent2):
        self.agent_name_label.config(text=f"Main Agent: {agent1['agent_strategy']}")
        self.opp_name_label.config(text=f"Opponent: {agent2['opponent_strategy']}")

    def reset_simulation(self):
        print("Resetting simulation...")
        self.running = False
        self.paused = False
        self.generation = 0
        self.status_var.set("Ready.")
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.step_btn.config(state=tk.DISABLED)
        self.back_btn.config(state=tk.DISABLED)
        self.agents = [Agent(random.choice(CONFIG['strategies'])) for _ in range(CONFIG['num_agents'])]
        self.match_history = []
        self.current_match_idx = 0
        self.current_round_idx = 0
        self.agent_name_label.config(text="Main Agent: ")
        self.opp_name_label.config(text="Opponent: ")
        self.agent_total_label.config(text="Total Points: 0")
        self.opp_total_label.config(text="Total Points: 0")
        self.agent_round_label.config(text="")
        self.opp_round_label.config(text="")
        self.claude_move_var.set("")
        self.claude_reason_var.set("")
        self.match_round_var.set("")
        self.highlight_cell('TRUST', 'TRUST')
        print("Simulation reset complete")

    def start_simulation(self):
        print("Starting simulation...")
        if self.running:
            return
        self.running = True
        self.paused = False
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)
        self.step_btn.config(state=tk.DISABLED)
        self.back_btn.config(state=tk.DISABLED)
        self.sim_thread = Thread(target=self._run_simulation)
        self.sim_thread.daemon = True
        self.sim_thread.start()

    def pause_simulation(self):
        print("Pausing simulation...")
        self.paused = True
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.NORMAL)
        self.step_btn.config(state=tk.NORMAL)
        self.back_btn.config(state=tk.NORMAL)

    def resume_simulation(self):
        print("Resuming simulation...")
        self.paused = False
        self.pause_btn.config(state=tk.NORMAL)
        self.resume_btn.config(state=tk.DISABLED)
        self.step_btn.config(state=tk.DISABLED)
        self.back_btn.config(state=tk.DISABLED)

    def step_forward(self):
        print("Step forward...")
        self._advance_step(1)

    def step_backward(self):
        print("Step backward...")
        self._advance_step(-1)

    def _advance_step(self, direction):
        if not self.match_history:
            return
        idx = self.current_match_idx
        round_idx = self.current_round_idx
        if direction == 1:
            # Step forward
            if round_idx + 1 < len(self.match_history[idx]['rounds']):
                self.current_round_idx += 1
            elif idx + 1 < len(self.match_history):
                self.current_match_idx += 1
                self.current_round_idx = 0
        elif direction == -1:
            # Step backward
            if round_idx > 0:
                self.current_round_idx -= 1
            elif idx > 0:
                self.current_match_idx -= 1
                self.current_round_idx = len(self.match_history[self.current_match_idx]['rounds']) - 1
        self._show_current_step()

    def _show_current_step(self):
        if not self.match_history:
            return
        match = self.match_history[self.current_match_idx]
        round_data = match['rounds'][self.current_round_idx]
        self.update_agent_labels(match, match)
        self.highlight_cell(round_data['agent_move'], round_data['opponent_move'])
        # Calculate running totals
        agent_total = 0
        opp_total = 0
        for m in self.match_history[:self.current_match_idx]:
            for r in m['rounds']:
                agent_total += r['agent_payoff']
                opp_total += r['opponent_payoff']
        for r in match['rounds'][:self.current_round_idx+1]:
            agent_total += r['agent_payoff']
            opp_total += r['opponent_payoff']
        self.agent_total_label.config(text=f"Total Points: {agent_total}")
        self.opp_total_label.config(text=f"Total Points: {opp_total}")
        # Show round result labels
        payoff_agent = round_data['agent_payoff']
        payoff_opp = round_data['opponent_payoff']
        def payoff_color(val):
            if val > 0:
                return 'green'
            elif val < 0:
                return 'red'
            else:
                return 'gray'
        self.agent_round_label.config(text=f"{('+' if payoff_agent >= 0 else '')}{payoff_agent}", fg=payoff_color(payoff_agent))
        self.opp_round_label.config(text=f"{('+' if payoff_opp >= 0 else '')}{payoff_opp}", fg=payoff_color(payoff_opp))
        # Show Claude's move and reasoning in bold white
        self.claude_move_var.set(f"Claude: {round_data['agent_move']}")
        self.claude_reason_var.set(round_data.get('reasoning', ''))
        # Show match/round info at top center
        self.match_round_var.set(f"Match {match.get('opponent_index', 0)+1} | Round {round_data['round']}")
        self.status_var.set(f"Gen {self.generation} | Match {self.current_match_idx+1}/{len(self.match_history)} | Round {self.current_round_idx+1}/{len(match['rounds'])}")

    def _run_simulation(self):
        print("Simulation thread started")
        max_games = 50
        games_played = 0
        while self.running and self.generation < self.max_generations and games_played < max_games:
            self.generation += 1
            self.status_var.set(f"Running generation {self.generation}/{self.max_generations}")
            agents = self.agents
            matches = []
            for i, opponent in enumerate(agents):
                if not self.running or games_played >= max_games:
                    break
                match_history = []
                agent_score = 0
                opponent_score = 0
                rounds = random.randint(*CONFIG['rounds_per_game']) if isinstance(CONFIG['rounds_per_game'], tuple) else CONFIG['rounds_per_game']
                match_id = f"{self.generation}_{i+1}"
                for round_num in range(1, rounds+1):
                    if not self.running or games_played >= max_games:
                        break
                    prompt_history = [
                        {
                            'round': idx+1,
                            'agent_move': h['agent_move'],
                            'opponent_move': h['opponent_move'],
                            'agent_payoff': h['agent_payoff'],
                            'opponent_payoff': h['opponent_payoff']
                        } for idx, h in enumerate(match_history)
                    ]
                    prompt = generate_claude_prompt(prompt_history)
                    try:
                        agent_move, reasoning = call_claude(prompt)
                    except Exception as e:
                        self.root.after(0, lambda: self.claude_reason_var.set(f"Claude error: {e}"))
                        self.running = False
                        return
                    opponent_move = opponent.strategy.decide([
                        (h['agent_move'], h['opponent_move']) for h in match_history
                    ])
                    payoff_agent, payoff_opp = PAYOFF_MATRIX[(agent_move, opponent_move)]
                    agent_score += payoff_agent
                    opponent_score += payoff_opp
                    match_history.append({
                        'round': round_num,
                        'agent_move': agent_move,
                        'opponent_move': opponent_move,
                        'agent_payoff': payoff_agent,
                        'opponent_payoff': payoff_opp,
                        'agent_strategy': 'Claude',
                        'opponent_strategy': opponent.strategy_name,
                        'reasoning': reasoning
                    })
                    # Log to CSV
                    log_row = {
                        'generation': self.generation,
                        'match_id': match_id,
                        'round': round_num,
                        'main_agent_strategy': 'Claude',
                        'opponent_strategy': opponent.strategy_name,
                        'main_agent_action': agent_move,
                        'opponent_action': opponent_move,
                        'main_agent_payoff': payoff_agent,
                        'opponent_payoff': payoff_opp,
                        'main_agent_total_score': agent_score,
                        'opponent_total_score': opponent_score,
                        'claude_reasoning': reasoning,
                        'history_included': round_num > 1,
                        'timestamp': datetime.now().isoformat()
                    }
                    log_round_to_csv(log_row)
                    self.match_history = [
                        {
                            'agent_index': 0,
                            'opponent_index': i,
                            'agent_strategy': 'Claude',
                            'opponent_strategy': opponent.strategy_name,
                            'rounds': match_history
                        }
                    ]
                    self.current_match_idx = 0
                    self.current_round_idx = len(match_history)-1
                    self.root.after(0, self._show_current_step)
                    self.root.after(0, lambda r=reasoning: self.claude_reason_var.set(r))
                    time.sleep(CONFIG['gui_update_delay'])
                    games_played += 1
            self.agents = [Agent(random.choice(CONFIG['strategies'])) for _ in range(CONFIG['num_agents'])]
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.resume_btn.config(state=tk.DISABLED)
        self.step_btn.config(state=tk.DISABLED)
        self.back_btn.config(state=tk.DISABLED)
        self.status_var.set("Simulation complete.")
        print("Simulation thread ended")

def main():
    root = tk.Tk()
    app = TrustSimGUI(root)
    print("Starting main loop...")
    root.mainloop()
    print("Main loop ended")

if __name__ == "__main__":
    main()