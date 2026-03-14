"""
Example: Basic usage of LINE Bot Task Queue
"""

from plugin import TaskQueuePlugin

# Mock LINE Bot
class MockBot:
    def push_message(self, user_id, message):
        print(f"Push to {user_id}: {message}")

bot = MockBot()

# Initialize plugin
task_queue = TaskQueuePlugin(bot, storage_type="sqlite")

# Register task handlers
@task_queue.register("hello")
def handle_hello(user_id, params, worker):
    """Simple hello task"""
    name = params.get("name", "World")
    return f"Hello, {name}!"

@task_queue.register("long_process")
def handle_long_process(user_id, params, worker):
    """Long running task with progress updates"""
    import time
    
    total_steps = 10
    for i in range(total_steps):
        # Update progress (get job_id from storage)
        progress = int((i + 1) / total_steps * 100)
        
        # Simulate work
        time.sleep(0.1)
    
    return "Process completed!"

# Submit tasks
print("Submitting tasks...")

job1 = task_queue.submit("user123", "hello", {"name": "John"})
print(f"Job 1 ID: {job1}")

job2 = task_queue.submit("user123", "long_process", {})
print(f"Job 2 ID: {job2}")

# Check status
import time
time.sleep(1)

status = task_queue.get_status(job1)
print(f"Job 1 status: {status}")

# Wait for completion
time.sleep(6)

status = task_queue.get_status(job2)
print(f"Job 2 status: {status}")

result = task_queue.get_result(job2)
print(f"Job 2 result: {result}")

# Get user jobs
jobs = task_queue.get_user_jobs("user123")
print(f"User jobs: {len(jobs)}")
