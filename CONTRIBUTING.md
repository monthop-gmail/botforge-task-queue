# Contributing to BotForge Plugins

## โครงสร้าง Plugin

```
botforge-plugin/
├── <plugin-name>/
│   ├── __init__.py      # Plugin init + metadata
│   ├── plugin.py        # Main plugin class
│   ├── README.md        # Plugin documentation
│   └── ...
```

## การตั้งชื่อ

- **Repo:** `botforge-plugin`
- **Plugin name:** `botforge-<name>` (เช่น `botforge-task-queue`)
- **Package:** `botforge_<name>` (เช่น `botforge_task_queue`)

## Metadata

ใน `__init__.py`:

```python
__plugin_name__ = "botforge-task-queue"
__plugin_description__ = "Background task queue for LINE Bot"
__version__ = "1.0.0"
```

## การเพิ่ม Plugin ใหม่

1. สร้าง folder ใหม่ใน `botforge-plugin/`
2. เพิ่ม files ตามโครงสร้าง
3. อัปเดต README หลัก
4. Submit PR

## License

MIT
