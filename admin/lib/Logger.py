from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from typing import Any, Optional, Coroutine, List
import json
from datetime import datetime
import uuid
from pathlib import Path




class RichLogger:
    console: Optional[Console]
    progress_table: Table
    progress: Progress
    _channels_task: Optional[TaskID]
    _messages_task: Optional[TaskID]
    data: List
    update_path: Path

    def __init__(self, update_path: Path):
        self.progress_table = Table.grid()
        self.progress = Progress()
        self.console = None
        self._channels_task = None
        self._messages_task = None
        self.data = []
        self.update_path = update_path

    @property
    def channels_task(self):
        if self._channels_task is None:
            raise ValueError("attempted to access channel_task before starting")
        return self._channels_task

    @property
    def messages_task(self):
        if self._messages_task is None:
            raise ValueError("attempted to access download_task before starting")
        return self._messages_task


    async def run(self, channels_estimate, iter: Coroutine[Any, Any, None]):
        self.progress_table.add_row(Panel(self.progress, title="Update Progress", border_style="green", padding=(1, 1)))
        with Live(self.progress_table, refresh_per_second=10) as live:
            self.console = live.console
            self._channels_task = self.progress.add_task("[green]Channel Scan Progress", total=channels_estimate)
            self._messages_task = self.progress.add_task("[yellow]Download Progress", total=channels_estimate * 5)
            await iter

    def setNumChannels(self, c: int):
        self.progress.update(self.channels_task, total=c)

    def setNumMessages(self, m: int):
        self.progress.update(self.messages_task, total=m)

    def finish_channel(self):
        self.progress.update(self.channels_task, advance=1)

    def finish_message(self):
        self.progress.update(self.messages_task, advance=1)


    def write(self, *args, **kwargs):
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)

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