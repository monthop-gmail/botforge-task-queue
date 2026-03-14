"""
Background Worker - ประมวลผล tasks จาก queue
"""

import threading
import time
import traceback
from typing import Callable, Dict, Any, Optional


class TaskWorker:
    """Worker สำหรับประมวลผล tasks"""
    
    def __init__(self, queue, storage, bot=None):
        self.queue = queue
        self.storage = storage
        self.bot = bot
        self.handlers: Dict[str, Callable] = {}
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def register(self, task_type: str):
        """Decorator สำหรับ register task handler"""
        def decorator(func: Callable):
            self.handlers[task_type] = func
            return func
        return decorator
    
    def start(self):
        """เริ่ม worker thread"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
    
    def stop(self):
        """หยุด worker"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _run(self):
        """Main worker loop"""
        while self.running:
            try:
                job = self.queue.get()
                if job:
                    self._process_job(job)
                else:
                    time.sleep(0.1)  # No job, wait a bit
            except Exception as e:
                print(f"Worker error: {e}")
                time.sleep(1)
    
    def _process_job(self, job: Dict[str, Any]):
        """ประมวลผล job"""
        job_id = job["job_id"]
        user_id = job["user_id"]
        task_type = job["task_type"]
        params = job.get("params", {})
        
        try:
            # Update status to processing
            self.storage.set(job_id, {
                **job,
                "status": "processing",
                "progress": 0,
                "updated_at": time.time()
            })
            
            # Get handler
            handler = self.handlers.get(task_type)
            if not handler:
                raise Exception(f"Unknown task type: {task_type}")
            
            # Execute handler
            result = handler(user_id, params, self)
            
            # Update status to completed
            self.storage.set(job_id, {
                **job,
                "status": "completed",
                "progress": 100,
                "result": result,
                "completed_at": time.time(),
                "updated_at": time.time()
            })
            
            # Send result to user
            if self.bot:
                self.bot.push_message(
                    user_id,
                    f"✅ เสร็จแล้ว!\n\n{result}"
                )
            
        except Exception as e:
            # Update status to failed
            self.storage.set(job_id, {
                **job,
                "status": "failed",
                "message": str(e),
                "updated_at": time.time()
            })
            
            # Send error to user
            if self.bot:
                self.bot.push_message(
                    user_id,
                    f"❌ เกิดข้อผิดพลาด:\n{str(e)}"
                )
    
    def update_progress(self, job_id: str, percent: int, message: str = ""):
        """อัปเดตความคืบหน้า"""
        data = self.storage.get(job_id)
        if data:
            self.storage.set(job_id, {
                **data,
                "progress": percent,
                "message": message,
                "updated_at": time.time()
            })
