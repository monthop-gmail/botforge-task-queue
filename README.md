# BotForge Task Queue

MCP plugin สำหรับจัดการ long-running tasks แก้ปัญหา webhook timeout

## Features

- Background task processing
- Job queue management
- Progress tracking
- Job status tracking
- Push notification เมื่อเสร็จ
- Storage: SQLite (default) / Redis

## Installation

```bash
git clone https://github.com/monthop-gmail/botforge-task-queue.git
cd botforge-task-queue
pip install -r requirements.txt
```

## MCP Server (stdio)

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
| `task_queue_submit` | ส่งงานใหม่เข้าคิว (params: user_id, task_type, params) |
| `task_queue_status` | ตรวจสอบสถานะงาน (params: job_id) |
| `task_queue_result` | ดึงผลลัพธ์ของงาน (params: job_id) |
| `task_queue_cancel` | ยกเลิกงาน (params: job_id) |
| `task_queue_user_jobs` | ดึงรายการงานทั้งหมดของผู้ใช้ (params: user_id, limit) |

## License

MIT
