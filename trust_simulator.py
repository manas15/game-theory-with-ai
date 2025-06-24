# This code is intended to be run with Python 3.9 (Homebrew version on macOS) for proper Tkinter GUI support.
# Do NOT use the system Python on macOS, as it is not supported for GUI use and may result in blank windows.
#
import os
os.environ['TK_SILENCE_DEPRECATION'] = '1'  # Suppress deprecation warning

import csv
import random
import json
import string
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
        'match_id', 'round', 'main_agent_strategy', 'opponent_strategy',
        'main_agent_action', 'opponent_action', 'main_agent_payoff', 'opponent_payoff',
        'main_agent_total_score', 'opponent_total_score', 'claude_reasoning', 'history_included', 'timestamp',
        'payoff_matrix'
    ]
    file_exists = os.path.isfile(csv_file)
    write_header = not file_exists or os.path.getsize(csv_file) == 0
    # Add payoff_matrix to the row with string keys for JSON
    payoff_matrix_str_keys = {f"{k[0]}-{k[1]}": v for k, v in PAYOFF_MATRIX.items()}
    row = dict(row)  # Make a copy to avoid mutating input
    row['payoff_matrix'] = json.dumps(payoff_matrix_str_keys)
    with open(csv_file, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=header)
        if write_header:
            writer.writeheader()
        writer.writerow(row)

# --- GUI ---
class TrustSimGUI:
    match_history = []  # Always a list, class attribute fallback
    def __init__(self, root):
        self.root = root
        self.root.title("Evolution of Trust Simulator")
        self.root.geometry("900x650")
        # Use a slightly lighter but still dark color for better contrast
        self.bg_color = "#23272e"
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
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

        self.current_match_idx = 0
        self.current_round_idx = 0

        self._build_widgets()
        self.reset_simulation()
        print("GUI Initialization Complete")

    def _build_widgets(self):
        # Debug: Add a visible label at the top for testing rendering
        debug_label = tk.Label(self.main_container, text="Game Theory Simulator!", font=("Arial", 18, "bold"), fg="#f8f8f2", bg=self.bg_color)
        debug_label.pack(side=tk.TOP, pady=(10, 0))

        # --- Selection Form ---
        self.selection_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.selection_frame.pack(side=tk.TOP, fill=tk.X, pady=(5, 10))

        tk.Label(self.selection_frame, text="Number of Rounds:", font=("Arial", 12), fg="white", bg=self.bg_color).pack(side=tk.LEFT, padx=(10, 2))
        self.rounds_var = tk.StringVar(value="5")
        self.rounds_entry = ttk.Entry(self.selection_frame, textvariable=self.rounds_var, width=5)
        self.rounds_entry.pack(side=tk.LEFT, padx=(0, 15))

        tk.Label(self.selection_frame, text="Opponent Strategy:", font=("Arial", 12), fg="white", bg=self.bg_color).pack(side=tk.LEFT, padx=(10, 2))
        self.opp_strategy_var = tk.StringVar()
        self.opp_strategy_combo = ttk.Combobox(self.selection_frame, textvariable=self.opp_strategy_var, values=CONFIG['strategies'], state="readonly", width=18)
        self.opp_strategy_combo.set(CONFIG['strategies'][0])
        self.opp_strategy_combo.pack(side=tk.LEFT, padx=(0, 10))

        # --- Top control panel (Start/Reset buttons) ---
        top_frame = tk.Frame(self.main_container, bg=self.bg_color)
        top_frame.pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        self.start_btn = ttk.Button(top_frame, text="Start Simulation", command=self.start_simulation, width=15)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        self.reset_btn = ttk.Button(top_frame, text="Reset Simulation", command=self.reset_simulation, width=15)
        self.reset_btn.pack(side=tk.LEFT, padx=5)

        status_label = tk.Label(top_frame, textvariable=self.status_var, font=("Arial", 12), fg="white", bg=self.bg_color)
        status_label.pack(side=tk.LEFT, padx=10)

        # --- Match/Round info at top center ---
        match_round_label = tk.Label(self.main_container, textvariable=self.match_round_var, font=("Arial", 16, "bold"), fg="white", bg=self.bg_color)
        match_round_label.pack(side=tk.TOP, pady=(0, 10))

        # Main layout: left (agent), center (matrix), right (opponent)
        main_frame = tk.Frame(self.main_container, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Stick figure for AI agent (left)
        self.agent_canvas = tk.Canvas(main_frame, width=70, height=120, bg=self.bg_color, highlightthickness=0)
        self.agent_canvas.grid(row=0, column=0, padx=10, pady=10)
        self._draw_stick_figure(self.agent_canvas)
        self.agent_name_label = tk.Label(main_frame, text="AI agent", font=("Arial", 12, "bold"), fg="white", bg=self.bg_color)
        self.agent_name_label.grid(row=1, column=0)
        self.agent_total_label = tk.Label(main_frame, text="Total Points: 0", font=("Arial", 11, "bold"), fg="white", bg=self.bg_color)
        self.agent_total_label.grid(row=2, column=0)
        self.agent_round_label = tk.Label(main_frame, text="", font=("Arial", 14), fg="white", bg=self.bg_color)
        self.agent_round_label.grid(row=0, column=0, sticky='s', pady=(170, 0))

        # Center matrix with labels
        matrix_bg = '#ffffff'  # White matrix background
        matrix_outer = tk.Frame(main_frame, bg=matrix_bg, bd=2, relief='ridge')
        matrix_outer.grid(row=0, column=1, rowspan=5, padx=20, pady=10, sticky='n')

        # Top labels (Opponent)
        self.top_label_trust = tk.Label(matrix_outer, text="Opponent TRUSTS", font=("Arial", 11, "bold"), fg="black", bg=matrix_bg)
        self.top_label_trust.grid(row=0, column=1, padx=5, pady=2)
        self.top_label_cheat = tk.Label(matrix_outer, text="Opponent CHEATS", font=("Arial", 11, "bold"), fg="black", bg=matrix_bg)
        self.top_label_cheat.grid(row=0, column=2, padx=5, pady=2)

        # Side labels (AI agent)
        self.side_label_trust = tk.Label(matrix_outer, text="AI agent TRUSTS", font=("Arial", 11, "bold"), fg="black", bg=matrix_bg)
        self.side_label_trust.grid(row=1, column=0, padx=5, pady=10)
        self.side_label_cheat = tk.Label(matrix_outer, text="AI agent CHEATS", font=("Arial", 11, "bold"), fg="black", bg=matrix_bg)
        self.side_label_cheat.grid(row=2, column=0, padx=5, pady=10)

        # Matrix cells with color coding and icons
        self.matrix_labels: list[list[tk.Label]] = [[None, None], [None, None]]  # type: ignore
        # Define color and emoji/icon for each outcome
        matrix_styles = {
            ('TRUST', 'TRUST'): {'emoji': '🤝'},
            ('TRUST', 'CHEAT'): {'emoji': '💔'},
            ('CHEAT', 'TRUST'): {'emoji': '💰'},
            ('CHEAT', 'CHEAT'): {'emoji': '😐'},
        }
        choices = ['TRUST', 'CHEAT']
        for i, agent_move in enumerate(choices):
            for j, opponent_move in enumerate(choices):
                payoff = PAYOFF_MATRIX[(agent_move, opponent_move)]
                style = matrix_styles[(agent_move, opponent_move)]
                def sign(val):
                    return f"+{val}" if val > 0 else (f"{val}" if val < 0 else "0")
                label = tk.Label(
                    matrix_outer,
                    text=f"{style['emoji']}  AI: {sign(payoff[0])} | Opp: {sign(payoff[1])}",
                    width=22, height=3, borderwidth=1, relief="ridge",
                    bg=matrix_bg, fg="black", font=("Arial", 13)
                )
                label.grid(row=1+i, column=1+j, padx=5, pady=5)
                self.matrix_labels[i][j] = label  # type: ignore

        # Stick figure for Opponent (right)
        self.opp_canvas = tk.Canvas(main_frame, width=70, height=120, bg=self.bg_color, highlightthickness=0)
        self.opp_canvas.grid(row=0, column=2, padx=10, pady=10)
        self._draw_stick_figure(self.opp_canvas)
        self.opp_name_label = tk.Label(main_frame, text="Opponent", font=("Arial", 12, "bold"), fg="white", bg=self.bg_color)
        self.opp_name_label.grid(row=1, column=2)
        self.opp_total_label = tk.Label(main_frame, text="Total Points: 0", font=("Arial", 11, "bold"), fg="white", bg=self.bg_color)
        self.opp_total_label.grid(row=2, column=2)
        self.opp_round_label = tk.Label(main_frame, text="", font=("Arial", 14), fg="white", bg=self.bg_color)
        self.opp_round_label.grid(row=0, column=2, sticky='s', pady=(170, 0))

        # Place reasoning row immediately after main_frame (stick figures + matrix)
        self.reasoning_frame = tk.Frame(self.main_container, bg=self.bg_color)
        self.reasoning_frame.pack(after=main_frame, fill=tk.X, pady=(10, 0))
        self.claude_combined_var = tk.StringVar()
        self.claude_combined_label = tk.Label(
            self.reasoning_frame,
            textvariable=self.claude_combined_var,
            font=("Arial", 15, "bold"),
            fg="#222",
            bg="#f8f9fa",
            anchor='w',
            justify='left',
            wraplength=800,
            bd=2,
            relief='groove',
            padx=12,
            pady=8
        )
        self.claude_combined_label.pack(fill=tk.X, padx=10)

        # --- Round History Matrix ---
        self.round_history_outer = tk.Frame(self.main_container, bg=self.bg_color)
        self.round_history_outer.pack(fill=tk.X, pady=(10, 0))
        self.round_history_canvas = tk.Canvas(self.round_history_outer, height=110, bg=self.bg_color, highlightthickness=0)
        self.round_history_canvas.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.round_history_scroll = ttk.Scrollbar(self.round_history_outer, orient="horizontal", command=self.round_history_canvas.xview)
        self.round_history_scroll.pack(side=tk.BOTTOM, fill=tk.X)
        self.round_history_canvas.configure(xscrollcommand=self.round_history_scroll.set)
        self.round_history_frame = tk.Frame(self.round_history_canvas, bg=self.bg_color)
        self.round_history_canvas.create_window((0, 0), window=self.round_history_frame, anchor="nw")
        self.round_history_cells = []  # List of lists: rows, then columns
        self._init_round_history_matrix()
        self.round_history_frame.bind("<Configure>", lambda e: self.round_history_canvas.configure(scrollregion=self.round_history_canvas.bbox("all")))

        # Force update to help with macOS/Tkinter rendering issues
        self.root.update_idletasks()
        self.root.update()

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
        # Reset all cells to white matrix background
        matrix_bg = '#ffffff'
        choices = ['TRUST', 'CHEAT']
        for i, agent_move in enumerate(choices):
            for j, opponent_move in enumerate(choices):
                self.matrix_labels[i][j].config(bg=matrix_bg, fg='black', highlightbackground='#d3d3d3', highlightthickness=1)
        # Highlight the selected cell with a clear color
        idx1 = 0 if move1 == 'TRUST' else 1
        idx2 = 0 if move2 == 'TRUST' else 1
        self.matrix_labels[idx1][idx2].config(bg='#ffe066', fg='black', highlightbackground='#ffd600', highlightthickness=3)

    def update_agent_labels(self, agent1, agent2):
        self.agent_name_label.config(text=f"AI agent: {agent1['agent_strategy']}")
        self.opp_name_label.config(text=f"Opponent: {agent2['opponent_strategy']}")

    def reset_simulation(self):
        print("Resetting simulation...")
        self.running = False
        self.paused = False
        self.generation = 0
        self.status_var.set("Ready.")
        self.start_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)
        self.agents = [Agent(random.choice(CONFIG['strategies'])) for _ in range(CONFIG['num_agents'])]
        self.match_history = []  # Always a list
        self.current_match_idx = 0
        self.current_round_idx = 0
        self.agent_name_label.config(text="AI agent: ")
        self.opp_name_label.config(text="Opponent: ")
        self.agent_total_label.config(text="Total Points: 0")
        self.opp_total_label.config(text="Total Points: 0")
        self.agent_round_label.config(text="")
        self.opp_round_label.config(text="")
        self.claude_move_var.set("")
        self.claude_reason_var.set("")
        self.match_round_var.set("")
        self.highlight_cell('TRUST', 'TRUST')
        self.rounds_entry.state(["!disabled"])
        self.opp_strategy_combo.state(["!disabled"])
        self._init_round_history_matrix()
        print("Simulation reset complete")

    def start_simulation(self):
        print("Starting simulation...")
        if self.running:
            return
        self.running = True
        self.paused = False
        self.start_btn.config(state=tk.DISABLED)
        self.reset_btn.config(state=tk.DISABLED)
        self.rounds_entry.state(["disabled"])
        self.opp_strategy_combo.state(["disabled"])
        self.sim_thread = Thread(target=self._run_simulation)
        self.sim_thread.daemon = True
        self.sim_thread.start()

    def _run_simulation(self):
        print("Simulation thread started (single match mode)")
        try:
            rounds = int(self.rounds_var.get())
        except Exception:
            rounds = 5
        opp_strategy = self.opp_strategy_var.get() or CONFIG['strategies'][0]
        opponent = Agent(opp_strategy)
        match_history = []
        agent_score = 0
        opponent_score = 0
        match_id = ''.join(random.choices(string.digits, k=8))
        for round_num in range(1, rounds+1):
            if not self.running:
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
                    'opponent_index': 0,
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
        self.running = False
        self.start_btn.config(state=tk.NORMAL)
        self.reset_btn.config(state=tk.NORMAL)
        self.rounds_entry.state(["!disabled"])
        self.opp_strategy_combo.state(["!disabled"])
        self.status_var.set("Simulation complete.")
        print("Simulation thread ended (single match mode)")

    def _show_current_step(self):
        if not self.match_history or not isinstance(self.match_history, list):
            return
        if self.current_match_idx is None or self.current_round_idx is None:
            return
        if self.current_match_idx >= len(self.match_history):
            return
        match = self.match_history[self.current_match_idx]
        if 'rounds' not in match or not isinstance(match['rounds'], list) or not match['rounds']:
            return
        if self.current_round_idx >= len(match['rounds']):
            return
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
        # Show Claude's move and reasoning together in the reasoning row
        move = round_data['agent_move']
        reasoning = round_data.get('reasoning', '')
        if reasoning:
            self.claude_combined_var.set(f"Claude: {move} — {reasoning}")
        else:
            self.claude_combined_var.set(f"Claude: {move}")
        # Show match/round info at top center
        self.match_round_var.set(f"Match {match.get('opponent_index', 0)+1} | Round {round_data['round']}")
        self.status_var.set(f"Gen {self.generation} | Match {self.current_match_idx+1}/{len(self.match_history)} | Round {self.current_round_idx+1}/{len(match['rounds'])}")
        # Update round history matrix
        self._update_round_history_matrix(match['rounds'])

    def _init_round_history_matrix(self):
        # Clear previous
        for widget in self.round_history_frame.winfo_children():
            widget.destroy()
        self.round_history_cells = []
        # 5 rows: Header, AI move, Opp move, AI pts, Opp pts
        row_labels = ["Round", "AI Move", "Opp Move", "AI Pts", "Opp Pts"]
        for r, label in enumerate(row_labels):
            l = tk.Label(self.round_history_frame, text=label, font=("Arial", 10, "bold"), fg="white", bg=self.bg_color, padx=6, pady=2)
            l.grid(row=r, column=0, sticky="nsew")
        self.round_history_cells = [[] for _ in range(5)]

    def _update_round_history_matrix(self, match_history):
        # Remove old round columns
        for r in range(5):
            for cell in self.round_history_cells[r]:
                cell.destroy()
            self.round_history_cells[r] = []
        # Add new columns for each round
        emoji = {"TRUST": "🤝", "CHEAT": "💔"}
        for c, round_data in enumerate(match_history):
            # Round number
            l0 = tk.Label(self.round_history_frame, text=str(round_data['round']), font=("Arial", 10), fg="#ffe066", bg=self.bg_color, padx=6, pady=2, borderwidth=1, relief="ridge")
            l0.grid(row=0, column=c+1, sticky="nsew")
            # AI move
            agent_move = round_data.get('agent_move')
            l1 = tk.Label(self.round_history_frame, text=emoji.get(agent_move, str(agent_move) if agent_move is not None else ''), font=("Arial", 13), fg="#4dd0e1" if agent_move=="TRUST" else "#e57373", bg=self.bg_color, padx=6, pady=2)
            l1.grid(row=1, column=c+1, sticky="nsew")
            # Opp move
            opp_move = round_data.get('opponent_move')
            l2 = tk.Label(self.round_history_frame, text=emoji.get(opp_move, str(opp_move) if opp_move is not None else ''), font=("Arial", 13), fg="#64b5f6" if opp_move=="TRUST" else "#ffb74d", bg=self.bg_color, padx=6, pady=2)
            l2.grid(row=2, column=c+1, sticky="nsew")
            # AI pts
            pts = round_data['agent_payoff']
            l3 = tk.Label(self.round_history_frame, text=f"{('+' if pts>=0 else '')}{pts}", font=("Arial", 10, "bold"), fg=("#43a047" if pts>0 else ("#e53935" if pts<0 else "#888")), bg=self.bg_color, padx=6, pady=2)
            l3.grid(row=3, column=c+1, sticky="nsew")
            # Opp pts
            pts2 = round_data['opponent_payoff']
            l4 = tk.Label(self.round_history_frame, text=f"{('+' if pts2>=0 else '')}{pts2}", font=("Arial", 10, "bold"), fg=("#43a047" if pts2>0 else ("#e53935" if pts2<0 else "#888")), bg=self.bg_color, padx=6, pady=2)
            l4.grid(row=4, column=c+1, sticky="nsew")
            self.round_history_cells[0].append(l0)
            self.round_history_cells[1].append(l1)
            self.round_history_cells[2].append(l2)
            self.round_history_cells[3].append(l3)
            self.round_history_cells[4].append(l4)
        self.round_history_frame.update_idletasks()
        self.round_history_canvas.configure(scrollregion=self.round_history_canvas.bbox("all"))

def main():
    root = tk.Tk()
    app = TrustSimGUI(root)
    print("Starting main loop...")
    root.mainloop()
    print("Main loop ended")

if __name__ == "__main__":
    main()