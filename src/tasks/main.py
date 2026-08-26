import re
import json
from pathlib import Path

class Task:
    def __init__(self, tasks_file="tasks.json"):
        self.tasks_file = Path(tasks_file)
        self.tasks: dict = {}
        self.readJson()

    def is_valid_time(self, time_str: str) -> bool:
        """Validate 24‑hour time (HH:MM) with optional leading zero for hour."""
        pattern = r'^([01]?\d|2[0-3]):([0-5]\d)$'
        return bool(re.match(pattern, time_str))

    def is_valid_title(self, title: str) -> bool:
        """Title must be 1–100 characters and not only whitespace."""
        return 1 <= len(title) <= 100 and title.strip() != ""

    def addTask(self, time: str, title: str) -> bool:
        """Add a task if both time and title are valid. Return True on success."""
        if self.is_valid_time(time) and self.is_valid_title(title):
            self.tasks[time] = title
            self.saveJson()
            return True
        else:
            print("❌ Invalid time or title format.")
            print("   Time must be HH:MM (e.g., 09:30 or 9:30).")
            print("   Title must be 1–100 characters and not empty.")
            return False

    def readJson(self):
        """Load tasks from JSON file. If missing, start with empty dict."""
        try:
            with open(self.tasks_file, 'r') as f:
                self.tasks = json.load(f)
            print("📂 Loaded tasks:", self.tasks)
        except FileNotFoundError:
            print("⚠️ No tasks file found. Starting with empty tasks.")
            self.tasks = {}
        except json.JSONDecodeError:
            print("⚠️ Invalid JSON in tasks file. Starting fresh.")
            self.tasks = {}

    def saveJson(self):
        """Save current tasks to JSON file."""
        try:
            with open(self.tasks_file, 'w') as f:
                json.dump(self.tasks, f, indent=4)
        except Exception as e:
            print(f"❌ Could not save tasks: {e}")

    def returnTasks(self) -> dict:
        """Return the tasks dictionary."""
        return self.tasks
