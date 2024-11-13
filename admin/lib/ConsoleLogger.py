from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from typing import Any, Optional, Coroutine



class RichConsoleLogger:
    console: Console
    progress: Progress
    overall_task: Optional[TaskID]
    progress_table: Table

    def __init__(self):
        self.console = Console()


    def begin_download(self):
        self.progress_table = Table.grid()
        self.progress_table.add_row(Panel(self.progress, title="Download Progress", border_style="green", padding=(1, 1)))

    async def run(self, total_tasks, iter: Coroutine[Any, Any, None]):
        with Progress() as progress:
            self.progress = progress
            self.overall_task = progress.add_task("[yellow]Overall Progress", total=total_tasks)
            await iter

    async def update_message(self, new_message: str):
        if self.overall_task is not None:
            self.progress.update(self.overall_task, description=new_message)

    async def update_progress(self):
        if self.overall_task is not None:
            self.progress.update(self.overall_task, advance=1)

    def write(self, *args, **kwargs):
        self.progress.print(*args, **kwargs)