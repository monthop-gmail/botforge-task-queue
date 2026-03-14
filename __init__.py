"""
BotForge Task Queue
Local plugin สำหรับจัดการ long-running tasks ใน LINE Bot
"""

from .plugin import TaskQueuePlugin
from .queue import TaskQueue
from .worker import TaskWorker
from .storage import JobStorage, SQLiteStorage, RedisStorage

__version__ = "1.0.0"
__all__ = [
    "TaskQueuePlugin",
    "TaskQueue",
    "TaskWorker",
    "JobStorage",
    "SQLiteStorage",
    "RedisStorage",
]

# Plugin metadata
__plugin_name__ = "botforge-task-queue"
__plugin_description__ = "Background task queue for LINE Bot"
