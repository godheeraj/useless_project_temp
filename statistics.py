"""
statistics.py — Combat statistics tracker, high scores storage,
and the humorous Kerala Survival Rating assessment engine.
"""

import os
import json
import time
from datetime import datetime
import config

DEFAULT_LEADERBOARD = [
    {"name": "DHEERAJ", "score": 920, "kills": 64, "rating": "98%", "date": "2026-09-01"},
    {"name": "AMAL", "score": 810, "kills": 56, "rating": "91%", "date": "2026-09-02"},
    {"name": "ARJUN", "score": 670, "kills": 45, "rating": "84%", "date": "2026-09-03"},
    {"name": "ANANDHU", "score": 420, "kills": 31, "rating": "72%", "date": "2026-09-04"},
    {"name": "UNKNOWN", "score": 12, "kills": 1, "rating": "14%", "date": "2026-09-05"}
]

class CombatStats:
    """Tracks useless, humorous combat metrics during gameplay."""
    def __init__(self):
        self.reset()

    def reset(self):
        self.score = 0
        self.current_combo = 0
        self.best_combo = 0
        self.level_reached = 1

        self.encountered = 0
        self.killed = 0
        self.escaped = 0

        self.slaps_attempted = 0
        self.missed_slaps = 0
        self.webs_fired = 0
        self.finger_bullets_fired = 0

        self.reaction_times = []
        self.start_time = time.time()

    def record_encounter(self):
        self.encountered += 1

    def record_kill(self, gesture_type, reaction_time=0.45):
        self.killed += 1
        self.current_combo += 1
        if self.current_combo > self.best_combo:
            self.best_combo = self.current_combo

        # Score with combo multiplier
        multiplier = min(self.current_combo, config.MAX_COMBO_MULTIPLIER)
        self.score += config.SCORE_PER_KILL * multiplier

        if reaction_time is not None and reaction_time > 0.05:
            self.reaction_times.append(reaction_time)

    def record_miss(self, gesture_type):
        self.current_combo = 0
        if gesture_type == "SLAP":
            self.slaps_attempted += 1
            self.missed_slaps += 1
        elif gesture_type == "WEB":
            self.webs_fired += 1
        elif gesture_type == "GUN":
            self.finger_bullets_fired += 1

    def record_action(self, gesture_type):
        if gesture_type == "SLAP":
            self.slaps_attempted += 1
        elif gesture_type == "WEB":
            self.webs_fired += 1
        elif gesture_type == "GUN":
            self.finger_bullets_fired += 1

    def compute_report(self):
        """Generates the full humorous Mosquito Combat Report."""
        total_actions = max(1, self.slaps_attempted + self.webs_fired + self.finger_bullets_fired)
        accuracy = min(100.0, (self.killed / total_actions) * 100.0)
        kill_rate = min(100.0, (self.killed / max(1, self.encountered)) * 100.0)

        avg_reaction = (
            sum(self.reaction_times) / len(self.reaction_times)
            if self.reaction_times else 0.42
        )

        # Humorous Kerala Survival Rating:
        # Heavily influenced by kills and best combo, penalized slightly by missed slaps
        base_survival = (kill_rate * 0.65) + (self.best_combo * 3.2) - (self.missed_slaps * 0.35)
        kerala_survival = float(round(max(18.0, min(99.4, base_survival + 15.0)), 1))

        # Threat Level
        if self.killed < 15:
            threat_level = "Catastrophic (Run for your life)"
        elif self.killed < 35:
            threat_level = "Moderately Concerning"
        elif self.killed < 55:
            threat_level = "Mosquito Militia Suppressed"
        else:
            threat_level = "Extinction Level Event for Mosquitoes"

        # Humorous Rank Title
        assigned_title = config.RANKING_TITLES[0][2]
        for min_k, max_k, title in config.RANKING_TITLES:
            if min_k <= self.killed <= max_k:
                assigned_title = title
                break

        return {
            "score": self.score,
            "killed": self.killed,
            "encountered": self.encountered,
            "escaped": max(0, self.encountered - self.killed),
            "best_combo": self.best_combo,
            "missed_slaps": self.missed_slaps,
            "webs_fired": self.webs_fired,
            "finger_bullets": self.finger_bullets_fired,
            "accuracy": round(accuracy, 1),
            "kill_rate": round(kill_rate, 1),
            "reaction_time": round(avg_reaction, 2),
            "kerala_survival": f"{kerala_survival}%",
            "threat_level": threat_level,
            "title": assigned_title
        }

class LeaderboardManager:
    """Manages high scores saved in data/scores.json."""
    def __init__(self, filepath=config.SCORES_FILE):
        self.filepath = filepath
        self._ensure_file()

    def _ensure_file(self):
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        if not os.path.exists(self.filepath):
            self._write_scores(DEFAULT_LEADERBOARD)

    def _read_scores(self):
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return DEFAULT_LEADERBOARD.copy()

    def _write_scores(self, scores):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(scores, f, indent=2)
        except Exception as e:
            print("[LeaderboardManager] Error writing scores:", e)

    def get_top_scores(self, limit=5):
        scores = self._read_scores()
        scores.sort(key=lambda s: s.get("score", 0), reverse=True)
        return scores[:limit]

    def add_score(self, name, score, kills, rating):
        scores = self._read_scores()
        scores.append({
            "name": name.upper()[:12] if name else "PLAYER",
            "score": int(score),
            "kills": int(kills),
            "rating": str(rating),
            "date": datetime.now().strftime("%Y-%m-%d")
        })
        scores.sort(key=lambda s: s.get("score", 0), reverse=True)
        self._write_scores(scores[:15])
