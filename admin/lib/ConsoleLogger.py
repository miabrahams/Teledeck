from rich.console import Console
from rich.progress import Progress, TaskID
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from typing import Any, Optional, Coroutine



class RichConsoleLogger:
    console: Optional[Console]
    progress_table: Table
    progress: Progress
    overall_task: Optional[TaskID]

    def __init__(self):
        # TODO: Sort out when overall_task is defined. Or maybe just
        self.progress = Progress()
        self.console = None
        self.overall_task = None


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