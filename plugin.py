"""
Main Plugin Interface
"""

from typing import Any, Dict, Optional
from .queue import TaskQueue
from .worker import TaskWorker
from .storage import JobStorage, SQLiteStorage, RedisStorage


class TaskQueuePlugin:
    """
    LINE Bot Task Queue Plugin
    
    Usage:
        task_queue = TaskQueuePlugin(bot)
        
        @task_queue.register("task_name")
        def handle_task(user_id, params, worker):
            # Do something
            return result
        
        # Submit task
        job_id = task_queue.submit(user_id, "task_name", params)
    """
    
    def __init__(
        self,
        bot=None,
        storage_type: str = "sqlite",
        db_path: str = "jobs.db",
        redis_url: str = "redis://localhost:6379",
        max_queue_size: int = 1000
    ):
        """
        Initialize plugin
        
        Args:
            bot: LINE Bot API object
            storage_type: "sqlite" or "redis"
            db_path: Path to SQLite database
            redis_url: Redis connection URL
            max_queue_size: Maximum queue size
        """
        self.bot = bot
        
        # Initialize storage
        if storage_type == "redis":
            self.storage = RedisStorage(redis_url)
        else:
            self.storage = SQLiteStorage(db_path)
        
        # Initialize queue
        self.queue = TaskQueue(max_size=max_queue_size)
        
        # Initialize worker
        self.worker = TaskWorker(self.queue, self.storage, bot)
        self.worker.start()
    
    def register(self, task_type: str):
        """
        Register task handler
        
        Usage:
            @plugin.register("process_file")
            def handle_file(user_id, params, worker):
                # Process file
                return result
        """
        return self.worker.register(task_type)
    
    def submit(
        self,
        user_id: str,
        task_type: str,
        params: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Submit task to queue
        
        Args:
            user_id: LINE user ID
            task_type: Type of task
            params: Task parameters
        
        Returns:
            job_id: Job ID for tracking
        """
        job_id = self.queue.add(user_id, task_type, params or {})
        
        # Store initial job data
        self.storage.set(job_id, {
            "job_id": job_id,
            "user_id": user_id,
            "task_type": task_type,
            "status": "queued",
            "progress": 0,
            "created_at": __import__("time").time()
        })
        
        return job_id
    
    def get_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get job status
        
        Returns:
            {"status": "queued|processing|completed|failed", "progress": 0-100, "message": ""}
        """
        return self.storage.get(job_id)
    
    def get_result(self, job_id: str) -> Optional[Any]:
        """
        Get job result
        
        Returns:
            Result data or None if not completed
        """
        data = self.storage.get(job_id)
        if data and data.get("status") == "completed":
            return data.get("result")
        return None
    
    def cancel(self, job_id: str) -> bool:
        """
        Cancel job
        
        Returns:
            True if cancelled, False if not found or already completed
        """
        data = self.storage.get(job_id)
        if not data:
            return False
        
        if data.get("status") in ["completed", "failed"]:
            return False
        
        self.storage.set(job_id, {
            **data,
            "status": "cancelled",
            "updated_at": __import__("time").time()
        })
        return True
    
    def update_progress(self, job_id: str, percent: int, message: str = ""):
        """
        Update job progress (call from task handler)
        
        Args:
            job_id: Job ID
            percent: Progress percentage (0-100)
            message: Progress message
        """
        self.worker.update_progress(job_id, percent, message)
    
    def get_user_jobs(self, user_id: str, limit: int = 10):
        """
        Get jobs by user
        
        Args:
            user_id: LINE user ID
            limit: Maximum number of jobs to return
        
        Returns:
            List of job data
        """
        return self.storage.get_by_user(user_id, limit)
    
    def stop(self):
        """Stop the worker"""
        self.worker.stop()
