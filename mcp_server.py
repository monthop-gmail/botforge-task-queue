"""
MCP Server สำหรับ BotForge Task Queue Plugin
ให้บริการจัดการ task queue ผ่าน Model Context Protocol (stdio transport)
"""

import json
import asyncio
import sys
import os
import importlib
import time
import uuid

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import storage, queue, and worker modules directly by file path to avoid
# relative-import issues with plugin.py and name collisions with stdlib queue.
_pkg_dir = os.path.dirname(os.path.abspath(__file__))


def _load_module(name: str):
    """Load a module from the package directory by file path."""
    spec = importlib.util.spec_from_file_location(name, os.path.join(_pkg_dir, f"{name}.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_storage_mod = _load_module("storage")
_queue_mod = _load_module("queue")
_worker_mod = _load_module("worker")

SQLiteStorage = _storage_mod.SQLiteStorage
TaskQueue = _queue_mod.TaskQueue
TaskWorker = _worker_mod.TaskWorker

# ---------------------------------------------------------------------------
# Initialize MCP server
# ---------------------------------------------------------------------------
server = Server("botforge-task-queue")

# Plugin-equivalent state (initialized lazily)
_storage = None
_queue = None
_worker = None


def _ensure_initialized():
    """เตรียม storage, queue, และ worker ให้พร้อมใช้งาน"""
    global _storage, _queue, _worker
    if _storage is not None:
        return

    db_path = os.path.join(_pkg_dir, "mcp_jobs.db")
    _storage = SQLiteStorage(db_path)
    _queue = TaskQueue(max_size=1000)
    _worker = TaskWorker(_queue, _storage, bot=None)
    _worker.start()


# ---------------------------------------------------------------------------
# Helper wrappers matching TaskQueuePlugin public API
# ---------------------------------------------------------------------------

def _submit(user_id: str, task_type: str, params: dict) -> str:
    _ensure_initialized()
    job_id = _queue.add(user_id, task_type, params)
    _storage.set(job_id, {
        "job_id": job_id,
        "user_id": user_id,
        "task_type": task_type,
        "status": "queued",
        "progress": 0,
        "created_at": time.time(),
    })
    return job_id


def _get_status(job_id: str):
    _ensure_initialized()
    return _storage.get(job_id)


def _get_result(job_id: str):
    _ensure_initialized()
    data = _storage.get(job_id)
    if data and data.get("status") == "completed":
        return data.get("result")
    return None


def _cancel(job_id: str) -> bool:
    _ensure_initialized()
    data = _storage.get(job_id)
    if not data:
        return False
    if data.get("status") in ("completed", "failed"):
        return False
    _storage.set(job_id, {
        **data,
        "status": "cancelled",
        "updated_at": time.time(),
    })
    return True


def _get_user_jobs(user_id: str, limit: int = 10):
    _ensure_initialized()
    return _storage.get_by_user(user_id, limit)


# ---------------------------------------------------------------------------
# MCP tool definitions
# ---------------------------------------------------------------------------

@server.list_tools()
async def list_tools() -> list[Tool]:
    """คืนรายการ tools ที่พร้อมใช้งาน"""
    return [
        Tool(
            name="task_queue_submit",
            description=(
                "ส่งงานใหม่เข้าคิว (Submit a new task to the queue) - "
                "สร้าง job ใหม่และคืนค่า job_id สำหรับติดตามสถานะ"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "รหัสผู้ใช้ (User ID)",
                    },
                    "task_type": {
                        "type": "string",
                        "description": "ประเภทของงาน (Task type name)",
                    },
                    "params": {
                        "type": "object",
                        "description": "พารามิเตอร์สำหรับงาน (Task parameters)",
                        "default": {},
                    },
                },
                "required": ["user_id", "task_type"],
            },
        ),
        Tool(
            name="task_queue_status",
            description=(
                "ตรวจสอบสถานะงาน (Get job status) - "
                "คืนค่าสถานะปัจจุบัน: queued, processing, completed, failed, cancelled"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "รหัสงาน (Job ID)",
                    },
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="task_queue_result",
            description=(
                "ดึงผลลัพธ์ของงาน (Get job result) - "
                "คืนค่าผลลัพธ์เมื่องานเสร็จสมบูรณ์ หรือ null หากยังไม่เสร็จ"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "รหัสงาน (Job ID)",
                    },
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="task_queue_cancel",
            description=(
                "ยกเลิกงาน (Cancel a job) - "
                "ยกเลิกงานที่อยู่ในคิวหรือกำลังประมวลผล คืนค่าสำเร็จหรือไม่"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "job_id": {
                        "type": "string",
                        "description": "รหัสงาน (Job ID)",
                    },
                },
                "required": ["job_id"],
            },
        ),
        Tool(
            name="task_queue_user_jobs",
            description=(
                "ดึงรายการงานทั้งหมดของผู้ใช้ (Get all jobs for a user) - "
                "แสดงประวัติงานล่าสุดของผู้ใช้ เรียงตามเวลาสร้างจากใหม่ไปเก่า"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "รหัสผู้ใช้ (User ID)",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "จำนวนงานสูงสุดที่ต้องการ (Maximum number of jobs to return)",
                        "default": 10,
                    },
                },
                "required": ["user_id"],
            },
        ),
    ]


# ---------------------------------------------------------------------------
# MCP tool dispatcher
# ---------------------------------------------------------------------------

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """เรียกใช้ tool ตามชื่อและพารามิเตอร์ที่ระบุ"""
    try:
        if name == "task_queue_submit":
            user_id = arguments["user_id"]
            task_type = arguments["task_type"]
            params = arguments.get("params", {})

            job_id = _submit(user_id, task_type, params)
            result = {
                "success": True,
                "job_id": job_id,
                "message": "ส่งงานเข้าคิวสำเร็จ (Job submitted successfully)",
            }

        elif name == "task_queue_status":
            job_id = arguments["job_id"]
            status = _get_status(job_id)

            if status is None:
                result = {
                    "success": False,
                    "error": f"ไม่พบงาน (Job not found): {job_id}",
                }
            else:
                result = {"success": True, "data": status}

        elif name == "task_queue_result":
            job_id = arguments["job_id"]
            job_result = _get_result(job_id)

            if job_result is None:
                status = _get_status(job_id)
                if status is None:
                    result = {
                        "success": False,
                        "error": f"ไม่พบงาน (Job not found): {job_id}",
                    }
                else:
                    result = {
                        "success": False,
                        "error": (
                            f"งานยังไม่เสร็จสมบูรณ์ (Job not completed yet), "
                            f"สถานะปัจจุบัน: {status.get('status')}"
                        ),
                        "current_status": status.get("status"),
                    }
            else:
                result = {"success": True, "result": job_result}

        elif name == "task_queue_cancel":
            job_id = arguments["job_id"]
            cancelled = _cancel(job_id)

            if cancelled:
                result = {
                    "success": True,
                    "message": f"ยกเลิกงานสำเร็จ (Job cancelled): {job_id}",
                }
            else:
                result = {
                    "success": False,
                    "error": (
                        f"ไม่สามารถยกเลิกงานได้ (Cannot cancel job): {job_id} - "
                        "อาจไม่พบงาน หรืองานเสร็จสิ้นแล้ว"
                    ),
                }

        elif name == "task_queue_user_jobs":
            user_id = arguments["user_id"]
            limit = arguments.get("limit", 10)

            jobs = _get_user_jobs(user_id, limit)
            result = {
                "success": True,
                "user_id": user_id,
                "total": len(jobs),
                "jobs": jobs,
            }

        else:
            result = {
                "success": False,
                "error": f"ไม่รู้จัก tool นี้ (Unknown tool): {name}",
            }

    except Exception as e:
        result = {
            "success": False,
            "error": f"เกิดข้อผิดพลาด (Error): {str(e)}",
        }

    return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False, default=str))]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    """เริ่มต้น MCP server ด้วย stdio transport"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream)


if __name__ == "__main__":
    asyncio.run(main())
