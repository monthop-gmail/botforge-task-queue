"""
Task Queue Implementation
"""

import uuid
import time
from typing import Any, Dict, Optional
from collections import deque
from threading import Lock


class TaskQueue:
    """Queue สำหรับจัดการ tasks"""
    
    def __init__(self, max_size: int = 1000):
        self.queue = deque()
        self.max_size = max_size
        self.lock = Lock()
    
    def add(self, user_id: str, task_type: str, params: Dict[str, Any]) -> str:
        """เพิ่มงานเข้า queue"""
        with self.lock:
            if len(self.queue) >= self.max_size:
                raise Exception("Queue is full")
            
            job_id = str(uuid.uuid4())
            job = {
                "job_id": job_id,
                "user_id": user_id,
                "task_type": task_type,
                "params": params,
                "created_at": time.time(),
                "status": "queued"
            }
            self.queue.append(job)
            return job_id
    
    def get(self) -> Optional[Dict[str, Any]]:
        """ดึงงานออกจาก queue"""
        with self.lock:
            if len(self.queue) == 0:
                return None
            return self.queue.popleft()
    
    def size(self) -> int:
        """จำนวนงานใน queue"""
        with self.lock:
            return len(self.queue)
    
    def clear(self):
        """ล้าง queue"""
        with self.lock:
            self.queue.clear()
