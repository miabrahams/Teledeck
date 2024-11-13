import json
from datetime import datetime
import uuid
from pathlib import Path
from typing import Any



class DataLogger:
    def __init__(self, update_path: Path):
        self.data = []
        self.update_path = update_path

    def add_data(self, datum: Any):
        self.data.append(datum)

    def save_to_json(self, data: Any):
        self.update_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        unique_id = str(uuid.uuid4())[:4]
        filename = self.update_path / f"data_{timestamp}_{unique_id}.json"
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)
        return filename

    def save_data(self):
        if len(self.data) > 0:
            filename = self.save_to_json(self.data)
            return filename
        return None
