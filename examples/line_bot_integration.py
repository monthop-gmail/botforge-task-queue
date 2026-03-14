"""
Example: Integration with LINE Bot
"""

from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage
from plugin import TaskQueuePlugin

# LINE Bot configuration
line_bot_api = LineBotApi("YOUR_CHANNEL_ACCESS_TOKEN")
handler = WebhookHandler("YOUR_CHANNEL_SECRET")

# Initialize task queue plugin
task_queue = TaskQueuePlugin(line_bot_api)

# Register task handlers
@task_queue.register("process_file")
def handle_process_file(user_id, params, worker):
    """Process file task"""
    file_url = params.get("file_url")
    
    # Download and process file
    worker.update_progress(params.get("_job_id"), 25, "Downloading file...")
    
    # Simulate processing
    worker.update_progress(params.get("_job_id"), 50, "Processing...")
    
    # Generate result
    worker.update_progress(params.get("_job_id"), 75, "Generating report...")
    
    worker.update_progress(params.get("_job_id"), 100, "Complete!")
    
    return f"File processed: {file_url}"

@task_queue.register("generate_report")
def handle_generate_report(user_id, params, worker):
    """Generate report task"""
    report_type = params.get("type", "summary")
    
    worker.update_progress(params.get("_job_id"), 10, "Fetching data...")
    worker.update_progress(params.get("_job_id"), 50, "Analyzing...")
    worker.update_progress(params.get("_job_id"), 90, "Formatting...")
    worker.update_progress(params.get("_job_id"), 100, "Done!")
    
    return f"Report generated: {report_type}"

# Webhook handler
@handler.add(MessageEvent, message=TextMessage)
def handle_text_message(event):
    user_id = event.source.user_id
    text = event.message.text
    
    # Check if it's a command
    if text.startswith("/process"):
        # Submit long-running task
        job_id = task_queue.submit(
            user_id=user_id,
            task_type="process_file",
            params={"file_url": "https://example.com/file.pdf"}
        )
        
        # Reply immediately
        line_bot_api.reply_message(
            event.reply_token,
            f"🎫 Job ID: {job_id}\nกำลังประมวลผลไฟล์..."
        )
        
        return
    
    elif text.startswith("/report"):
        # Submit report generation
        job_id = task_queue.submit(
            user_id=user_id,
            task_type="generate_report",
            params={"type": "monthly"}
        )
        
        line_bot_api.reply_message(
            event.reply_token,
            f"🎫 Job ID: {job_id}\nกำลังสร้างรายงาน..."
        )
        
        return
    
    elif text.startswith("/status"):
        # Check job status
        job_id = text.replace("/status", "").strip()
        if job_id:
            status = task_queue.get_status(job_id)
            if status:
                line_bot_api.reply_message(
                    event.reply_token,
                    f"Status: {status.get('status')}\nProgress: {status.get('progress')}%"
                )
            else:
                line_bot_api.reply_message(
                    event.reply_token,
                    "ไม่พบ Job ID นี้"
                )
        return
    
    # Default response
    line_bot_api.reply_message(
        event.reply_token,
        "ส่ง /process เพื่อประมวลผลไฟล์\nส่ง /report เพื่อสร้างรายงาน\nส่ง /status <job_id> เพื่อเช็คสถานะ"
    )

# Flask app
from flask import Flask, request, abort

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    signature = request.headers["X-Line-Signature"]
    body = request.get_data(as_text=True)
    
    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    
    return "OK"

if __name__ == "__main__":
    app.run(port=8000)
