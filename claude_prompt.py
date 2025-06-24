import requests
from claude_api_key import CLAUDE_API_KEY
import json

def generate_claude_prompt(history):
    """
    history: list of dicts with keys: round, agent_move, opponent_move, agent_payoff, opponent_payoff
    Returns a string prompt for Claude.
    """
    prompt = []
    prompt.append("AI Agent: Game Theory Decision Prompt\nObjective: You are an AI agent participating in a two-player game. Your sole objective is to maximize your own payoff.\n")
    prompt.append("Game Rules:\n\nThere are two players: 'AI Agent' (you) and 'Opponent.'\nEach player chooses one of two actions simultaneously: 'Trust' or 'Cheat.'\n")
    prompt.append("The payoffs for each combination of actions are as follows (Your Payoff, Opponent's Payoff):\n")
    prompt.append("If you choose 'Trust' and Opponent chooses 'Trust': (+2,+2)\nIf you choose 'Trust' and Opponent chooses 'Cheat': (−1,+3)\nIf you choose 'Cheat' and Opponent chooses 'Trust': (+3,−1)\nIf you choose 'Cheat' and Opponent chooses 'Cheat': (0,0)\n")
    prompt.append("Multi-Round Game Context:\nThis game will be played over multiple rounds. Before each new round, you will be provided with the outcomes of all previous rounds.\n")
    if history:
        prompt.append("Previous Outcomes (if any):\nA list of past game outcomes will be provided in the format:\n[(Round N Action: Your_Action, Opponent_Action, Your_Payoff, Opponent_Payoff), ...]\n")
        history_str = ", ".join([
            f"(Round {h['round']}: {h['agent_move']}, {h['opponent_move']}, {h['agent_payoff']}, {h['opponent_payoff']})"
            for h in history
        ])
        prompt.append(f"History: [{history_str}]\n")
    else:
        prompt.append("No previous rounds.\n")
    prompt.append("\nTask:\nAnalyze the payoff matrix and consider the history of previous outcomes to determine your optimal strategy for the current round. Assuming the opponent is also a rational agent aiming to maximize their own payoff, what action should you choose in this game to maximize your own outcome?\n\nYour Response:\nReply strictly in the following JSON format (do not include any other text):\n{\"action\": \"Trust or Cheat\", \"reason\": \"5-7 word explanation\"}\n")
    return "".join(prompt)


def call_claude(prompt, max_retries=1):
    """
    Calls the Claude 3 Messages API with the given prompt and returns (move, reasoning).
    Retries once if JSON parsing fails. Logs full response text and status code on error.
    """
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": "claude-3-opus-20240229",
        "max_tokens": 100,
        "temperature": 0.2,
        "messages": [
            {"role": "user", "content": prompt}
        ]
    }
    for attempt in range(max_retries + 1):
        response = requests.post(url, headers=headers, json=data, timeout=30)
        print(f"Claude API HTTP status: {response.status_code}")
        print(f"Claude API raw response: {response.text}")
        try:
            response.raise_for_status()
            resp_json = response.json()
            # Claude 3 Messages API returns the content as a list of blocks
            content = resp_json["content"][0]["text"].strip()
            result = json.loads(content)
            move = result.get("action", "TRUST").upper()
            if move not in ("TRUST", "CHEAT"):
                move = "TRUST"
            reasoning = result.get("reason", "No reasoning provided.")[:40]
            return move, reasoning
        except Exception as e:
            print(f"Claude API error: {e}")
            if attempt < max_retries:
                continue
            else:
                # Instead of raising, return a safe fallback
                return "TRUST", f"Claude error: see logs"
    # Fallback in case all attempts fail
    return "TRUST", "Claude error: see logs" 