from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from typing import Any, Optional, Coroutine, List, Any
import json
from datetime import datetime
import uuid
from pathlib import Path




class RichLogger:
    console: Optional[Console]
    progress_table: Table
    progress: Progress
    overall_task: Optional[TaskID]
    data: List
    update_path: Path

    def __init__(self, update_path: Path):
        # TODO: Sort out when overall_task is defined?
        self.progress = Progress()
        self.console = None
        self.overall_task = None
        self.data = []
        self.update_path = update_path


    async def run(self, total_tasks, iter: Coroutine[Any, Any, None]):

        self.progress_table = Table.grid()
        self.progress_table.add_row(Panel(self.progress, title="Download Progress", border_style="green", padding=(1, 1)))

        with Live(self.progress_table, refresh_per_second=10) as live:
            self.console = live.console
            self.overall_task = self.progress.add_task("[yellow]Overall Progress", total=total_tasks)
            await iter

    async def update_message(self, new_message: str):
        if self.overall_task is not None:
            self.progress.update(self.overall_task, description=new_message)

    async def update_progress(self):
        if self.overall_task is not None:
            self.progress.update(self.overall_task, advance=1)

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