"""
Job Storage - เก็บสถานะและผลลัพธ์ของ jobs
"""

import json
import time
import sqlite3
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False


class JobStorage(ABC):
    """Abstract base class for job storage"""
    
    @abstractmethod
    def set(self, job_id: str, data: Dict[str, Any]):
        pass
    
    @abstractmethod
    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    def delete(self, job_id: str):
        pass


class SQLiteStorage(JobStorage):
    """SQLite-based job storage"""
    
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                job_id TEXT PRIMARY KEY,
                user_id TEXT,
                task_type TEXT,
                status TEXT,
                progress INTEGER,
                message TEXT,
                result TEXT,
                created_at REAL,
                updated_at REAL,
                completed_at REAL
            )
        """)
        conn.commit()
        conn.close()
    
    def set(self, job_id: str, data: Dict[str, Any]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if exists
        cursor.execute("SELECT job_id FROM jobs WHERE job_id = ?", (job_id,))
        exists = cursor.fetchone() is not None
        
        if exists:
            cursor.execute("""
                UPDATE jobs SET
                    user_id = ?, task_type = ?, status = ?,
                    progress = ?, message = ?, result = ?,
                    updated_at = ?, completed_at = ?
                WHERE job_id = ?
            """, (
                data.get("user_id"),
                data.get("task_type"),
                data.get("status"),
                data.get("progress", 0),
                data.get("message"),
                data.get("result"),
                time.time(),
                data.get("completed_at"),
                job_id
            ))
        else:
            cursor.execute("""
                INSERT INTO jobs (
                    job_id, user_id, task_type, status, progress,
                    message, result, created_at, updated_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                job_id,
                data.get("user_id"),
                data.get("task_type"),
                data.get("status"),
                data.get("progress", 0),
                data.get("message"),
                data.get("result"),
                data.get("created_at", time.time()),
                time.time(),
                data.get("completed_at")
            ))
        
        conn.commit()
        conn.close()
    
    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row is None:
            return None
        
        columns = [
            "job_id", "user_id", "task_type", "status", "progress",
            "message", "result", "created_at", "updated_at", "completed_at"
        ]
        return dict(zip(columns, row))
    
    def delete(self, job_id: str):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        conn.commit()
        conn.close()
    
    def get_by_user(self, user_id: str, limit: int = 10):
        """ดึง jobs ของ user"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM jobs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        rows = cursor.fetchall()
        conn.close()
        
        columns = [
            "job_id", "user_id", "task_type", "status", "progress",
            "message", "result", "created_at", "updated_at", "completed_at"
        ]
        return [dict(zip(columns, row)) for row in rows]


class RedisStorage(JobStorage):
    """Redis-based job storage"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        if not REDIS_AVAILABLE:
            raise ImportError("redis package is required")
        
        self.redis = redis.from_url(redis_url)
        self.ttl = 3600  # 1 hour
    
    def set(self, job_id: str, data: Dict[str, Any]):
        key = f"job:{job_id}"
        self.redis.setex(key, self.ttl, json.dumps(data))
        
        # Index by user
        user_id = data.get("user_id")
        if user_id:
            self.redis.sadd(f"user:{user_id}:jobs", job_id)
    
    def get(self, job_id: str) -> Optional[Dict[str, Any]]:
        key = f"job:{job_id}"
        data = self.redis.get(key)
        if data is None:
            return None
        return json.loads(data)
    
    def delete(self, job_id: str):
        key = f"job:{job_id}"
        self.redis.delete(key)
    
    def get_by_user(self, user_id: str, limit: int = 10):
        key = f"user:{user_id}:jobs"
        job_ids = list(self.redis.smembers(key))[:limit]
        jobs = []
        for job_id in job_ids:
            data = self.get(job_id.decode() if isinstance(job_id, bytes) else job_id)
            if data:
                jobs.append(data)
        return jobs
