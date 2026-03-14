# BotForge Task Queue

Local plugin สำหรับจัดการ long-running tasks ใน LINE Bot แก้ปัญหา webhook timeout

Plugin สำหรับ BotForge - ระบบรวม AI agents มากมาย

## Features

- ✅ Background task processing
- ✅ Job queue management
- ✅ Progress tracking
- ✅ Job status tracking
- ✅ Push notification เมื่อเสร็จ
- ✅ แก้ปัญหา webhook timeout (10 วินาที)

## Installation

```bash
cd /workspace/projects/botforge-plugin
pip install -r requirements.txt
```

## Quick Start

```python
from botforge_plugin import TaskQueuePlugin

# Initialize plugin
task_queue = TaskQueuePlugin(
    bot=line_bot,
    storage_type="sqlite"  # หรือ "redis"
)

# Submit task
job_id = task_queue.submit(
    user_id="U123456",
    task_type="process_file",
    params={"file": "document.pdf"}
)

# Check status
status = task_queue.get_status(job_id)
# {"status": "processing", "progress": 50, "message": "กำลังประมวลผล..."}

# Get result
result = task_queue.get_result(job_id)
```

## Usage with LINE Bot

```python
from botforge_plugin import TaskQueuePlugin

task_queue = TaskQueuePlugin(bot)

@webhook
def handler(event):
    user_id = event.source.user_id
    
    # ส่งงานเข้า queue
    job_id = task_queue.submit(
        user_id=user_id,
        task_type="long_process",
        params={"message": event.message.text}
    )
    
    # ตอบกลับทันที
    reply(event.reply_token, f"🎫 Job ID: {job_id}\nกำลังประมวลผล...")
    
    return 200
```

## Task Types

```python
# Register task handler
@task_queue.register("process_file")
def process_file(user_id, params):
    # Do something
    result = do_work(params)
    return result

@task_queue.register("generate_report")
def generate_report(user_id, params):
    # Generate report
    return report_data
```

## Progress Updates

```python
@task_queue.register("long_task")
def long_task(user_id, params):
    for i in range(10):
        # Update progress
        task_queue.update_progress(i * 10, f"Step {i}/10")
        do_step(i)
    
    return result
```

## Storage Options

### SQLite (Default)
```python
task_queue = TaskQueuePlugin(bot, storage_type="sqlite")
```

### Redis
```python
task_queue = TaskQueuePlugin(
    bot,
    storage_type="redis",
    redis_url="redis://localhost:6379"
)
```

## API Reference

### TaskQueuePlugin

| Method | Description |
|--------|-------------|
| `submit(user_id, task_type, params)` | ส่งงานเข้า queue |
| `get_status(job_id)` | เช็คสถานะงาน |
| `get_result(job_id)` | ดึงผลลัพธ์ |
| `cancel(job_id)` | ยกเลิกงาน |
| `update_progress(job_id, percent, message)` | อัปเดตความคืบหน้า |
| `get_user_jobs(user_id, limit)` | ดึงรายการงานของ user |
| `register(task_type)` | Register task handler |

## MCP Server (AI Agent Integration)

รองรับ MCP Protocol ผ่าน **stdio transport** ให้ AI agent เรียกใช้ task queue ได้โดยตรง

### รัน MCP Server

```bash
python mcp_server.py
```

### ตั้งค่าฝั่ง AI Agent

```json
{
  "mcpServers": {
    "task-queue": {
      "command": "python",
      "args": ["mcp_server.py"],
      "cwd": "/path/to/botforge-task-queue"
    }
  }
}
```

### MCP Tools

| Tool | Description |
|------|-------------|
| `task_queue_submit` | ส่งงานใหม่เข้าคิว |
| `task_queue_status` | ตรวจสอบสถานะงาน |
| `task_queue_result` | ดึงผลลัพธ์ของงาน |
| `task_queue_cancel` | ยกเลิกงาน |
| `task_queue_user_jobs` | ดึงรายการงานทั้งหมดของผู้ใช้ |

## License

MIT
