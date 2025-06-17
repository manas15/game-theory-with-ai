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

# --- CONFIGURATION ---
CONFIG = {
    'num_agents': 20,
    'rounds_per_game': (3, 7),  # tuple means random between 3 and 7
    'generations': 50,
    'eliminate_n': 5,  # Number of worst to eliminate each generation
    'clone_n': 5,      # Number of best to clone each generation
    'strategies': [
        'Always Cooperate',
        'Always Defect',
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

class AlwaysCooperate(Strategy):
    def __init__(self):
        super().__init__('Always Cooperate')
    def decide(self, history):
        return 'C'

class AlwaysDefect(Strategy):
    def __init__(self):
        super().__init__('Always Defect')
    def decide(self, history):
        return 'D'

class TitForTat(Strategy):
    def __init__(self):
        super().__init__('Tit-for-Tat')
    def decide(self, history):
        if not history:
            return 'C'
        return history[-1][0]

class Grudger(Strategy):
    def __init__(self):
        super().__init__('Grudger')
        self.grudge = False
    def decide(self, history):
        if not history:
            self.grudge = False
            return 'C'
        if any(opp == 'D' for opp, _ in history):
            self.grudge = True
        return 'D' if self.grudge else 'C'

class Detective(Strategy):
    def __init__(self):
        super().__init__('Detective')
        self.switched = False
    def decide(self, history):
        moves = len(history)
        if not self.switched:
            for opp, _ in history:
                if opp == 'D':
                    self.switched = True
                    break
        if self.switched:
            if not history:
                return 'C'
            return history[-1][0]
        else:
            if moves == 0: return 'C'
            if moves == 1: return 'D'
            if moves == 2: return 'C'
            if moves == 3: return 'C'
            self.switched = True
            return 'D'

class Simpleton(Strategy):
    def __init__(self):
        super().__init__('Simpleton')
    def decide(self, history):
        if not history:
            return 'C'
        opp, own = history[-1]
        if own == 'C' and opp == 'D':
            return 'D'
        else:
            return own

class RandomStrategy(Strategy):
    def __init__(self):
        super().__init__('Random')
    def decide(self, history):
        return random.choice(['C', 'D'])

class Copykitten(Strategy):
    def __init__(self):
        super().__init__('Copykitten')
    def decide(self, history):
        if len(history) < 2:
            return 'C'
        # Only defects if opponent defected twice in a row
        if history[-1][0] == 'D' and history[-2][0] == 'D':
            return 'D'
        return 'C'

# --- AGENT ---
class Agent:
    def __init__(self, strategy_name):
        self.strategy_name = strategy_name
        self.strategy = self._make_strategy(strategy_name)
        self.score = 0
        self.history = []
    def _make_strategy(self, name):
        return {
            'Always Cooperate': AlwaysCooperate(),
            'Always Defect': AlwaysDefect(),
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

# --- GAME LOGIC ---
PAYOFF = {
    ('C', 'C'): (2, 2),
    ('C', 'D'): (-1, 3),
    ('D', 'C'): (3, -1),
    ('D', 'D'): (0, 0),
}

def play_match_record(agent1, agent2, rounds):
    agent1.history = []
    agent2.history = []
    match_history = []
    for _ in range(rounds):
        move1 = agent1.strategy.decide(agent1.history)
        move2 = agent2.strategy.decide(agent2.history)
        payoff1, payoff2 = PAYOFF[(move1, move2)]
        agent1.score += payoff1
        agent2.score += payoff2
        agent1.history.append((move2, move1))
        agent2.history.append((move1, move2))
        match_history.append({
            'move1': move1,
            'move2': move2,
            'payoff1': payoff1,
            'payoff2': payoff2,
            'agent1_strategy': agent1.strategy_name,
            'agent2_strategy': agent2.strategy_name,
        })
    return match_history

def run_tournament_record(agents, rounds_per_game):
    matches = []
    for i, a1 in enumerate(agents):
        for j, a2 in enumerate(agents):
            if i < j:
                if isinstance(rounds_per_game, tuple):
                    rounds = random.randint(*rounds_per_game)
                else:
                    rounds = rounds_per_game
                match_history = play_match_record(a1, a2, rounds)
                matches.append({
                    'agent1_index': i,
                    'agent2_index': j,
                    'agent1_strategy': a1.strategy_name,
                    'agent2_strategy': a2.strategy_name,
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

# --- GUI ---
class TrustSimGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Evolution of Trust Simulator")
        self.root.geometry("800x600")
        self.main_container = ttk.Frame(self.root)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.running = False
        self.paused = False
        self.sim_thread = None
        self.generation = 0
        self.max_generations = CONFIG['generations']
        self.status_var = tk.StringVar()
        self.status_var.set("Ready.")

        self._build_widgets()
        self.reset_simulation()
        print("GUI Initialization Complete")

    def _build_widgets(self):
        # Top control panel
        top_frame = ttk.Frame(self.main_container)
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
        status_label = ttk.Label(top_frame, textvariable=self.status_var, font=("Arial", 12))
        status_label.pack(side=tk.LEFT, padx=10)

        # Agent info
        self.agent_info_frame = ttk.Frame(self.main_container)
        self.agent_info_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))
        self.agent1_label = ttk.Label(self.agent_info_frame, text="Agent 1: ", font=("Arial", 12))
        self.agent1_label.pack(side=tk.LEFT, padx=20)
        self.agent2_label = ttk.Label(self.agent_info_frame, text="Agent 2: ", font=("Arial", 12))
        self.agent2_label.pack(side=tk.LEFT, padx=20)

        # Payoff matrix
        self.matrix_frame = ttk.Frame(self.main_container)
        self.matrix_frame.pack(expand=True)
        self.matrix_labels: list[list[tk.Label]] = [[None, None], [None, None]]  # type: ignore
        choices = ['C', 'D']
        for i, move1 in enumerate(choices):
            for j, move2 in enumerate(choices):
                payoff = PAYOFF[(move1, move2)]
                label = tk.Label(self.matrix_frame, text=f"{move1} vs {move2}\nP1: {payoff[0]}, P2: {payoff[1]}",
                                 width=18, height=5, borderwidth=2, relief="groove", bg='white', font=("Arial", 14))
                label.grid(row=i, column=j, padx=10, pady=10)
                self.matrix_labels[i][j] = label  # type: ignore

    def highlight_cell(self, move1, move2):
        for row in self.matrix_labels:
            for label in row:
                label.config(bg='white', fg='black')
        idx1 = 0 if move1 == 'C' else 1
        idx2 = 0 if move2 == 'C' else 1
        self.matrix_labels[idx1][idx2].config(bg='#90ee90', fg='black')

    def update_agent_labels(self, agent1, agent2):
        self.agent1_label.config(text=f"Agent 1: {agent1['agent1_strategy']}")
        self.agent2_label.config(text=f"Agent 2: {agent2['agent2_strategy']}")

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
        self.agent1_label.config(text="Agent 1: ")
        self.agent2_label.config(text="Agent 2: ")
        self.highlight_cell('C', 'C')
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
        self.highlight_cell(round_data['move1'], round_data['move2'])
        self.status_var.set(f"Gen {self.generation} | Match {self.current_match_idx+1}/{len(self.match_history)} | Round {self.current_round_idx+1}/{len(match['rounds'])}")

    def _run_simulation(self):
        print("Simulation thread started")
        while self.running and self.generation < self.max_generations:
            self.generation += 1
            self.status_var.set(f"Running generation {self.generation}/{self.max_generations}")
            # Run tournament and record all matches/rounds
            self.match_history = run_tournament_record(self.agents, CONFIG['rounds_per_game'])
            self.current_match_idx = 0
            self.current_round_idx = 0
            total_matches = len(self.match_history)
            while self.current_match_idx < total_matches and self.running:
                match = self.match_history[self.current_match_idx]
                rounds = match['rounds']
                for r_idx, round_data in enumerate(rounds):
                    if not self.running:
                        break
                    while self.paused:
                        time.sleep(0.05)
                    self.current_round_idx = r_idx
                    self.root.after(0, self._show_current_step)
                    time.sleep(CONFIG['gui_update_delay'])
                self.current_match_idx += 1
                self.current_round_idx = 0
            # Evolve population
            self.agents = evolve_population(self.agents, CONFIG['eliminate_n'], CONFIG['clone_n'])
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