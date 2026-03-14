# BotForge Task Queue

Plugin สำหรับจัดการ long-running tasks ใน LINE Bot แก้ปัญหา webhook timeout

## Features

- Background task processing
- Job queue management
- Progress tracking
- Job status tracking
- Push notification เมื่อเสร็จ
- แก้ปัญหา webhook timeout (10 วินาที)

## Installation

```bash
git clone https://github.com/monthop-gmail/botforge-task-queue.git
cd botforge-task-queue
pip install -r requirements.txt
```

## Quick Start

```python
from plugin import TaskQueuePlugin

# Initialize plugin
task_queue = TaskQueuePlugin(
    bot=line_bot,
    storage_type="sqlite"  # หรือ "redis"
)

# Register task handler (รับ 3 params: user_id, params, worker)
@task_queue.register("process_file")
def process_file(user_id, params, worker):
    result = do_work(params)
    return result

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
from plugin import TaskQueuePlugin

task_queue = TaskQueuePlugin(bot=line_bot_api)

@task_queue.register("long_process")
def long_process(user_id, params, worker):
    result = do_something_heavy(params["message"])
    return result

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id

    # ส่งงานเข้า queue
    job_id = task_queue.submit(
        user_id=user_id,
        task_type="long_process",
        params={"message": event.message.text}
    )

    # ตอบกลับทันที (ไม่ timeout)
    line_bot_api.reply_message(
        event.reply_token,
        TextSendMessage(text=f"รับงานแล้ว Job: {job_id}")
    )
```

## Progress Updates

```python
@task_queue.register("long_task")
def long_task(user_id, params, worker):
    for i in range(10):
        # อัพเดท progress ผ่าน worker
        worker.update_progress(params["_job_id"], (i + 1) * 10, f"Step {i+1}/10")
        do_step(i)

    return "Done!"
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

| Method | Description |
|--------|-------------|
| `submit(user_id, task_type, params)` | ส่งงานเข้า queue คืนค่า job_id |
| `get_status(job_id)` | เช็คสถานะงาน |
| `get_result(job_id)` | ดึงผลลัพธ์ |
| `cancel(job_id)` | ยกเลิกงาน |
| `get_user_jobs(user_id, limit)` | ดึงรายการงานของ user |
| `register(task_type)` | Decorator สำหรับ register task handler |
| `stop()` | หยุด worker |

Handler ที่ register จะรับ 3 params: `(user_id, params, worker)`
- `params["_job_id"]` — job ID สำหรับอัพเดท progress
- `worker.update_progress(job_id, percent, message)` — อัพเดทความคืบหน้า

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
