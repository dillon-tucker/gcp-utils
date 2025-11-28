"""
Example usage of the Cloud Tasks controller.

This example demonstrates:
- Creating and managing task queues
- Creating HTTP tasks with payloads
- Scheduling tasks for future execution
- Listing and managing tasks
- Pausing and resuming queues
"""

import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import CloudTasksController


def main() -> None:
    """Demonstrate Cloud Tasks controller functionality."""

    # Initialize controller (automatically loads from .env)
    tasks = CloudTasksController()

    print("=" * 80)
    print("Cloud Tasks Controller Example")
    print("=" * 80)

    # 1. Create a task queue
    print("\n1. Creating task queue...")
    queue_name = "example-queue"
    try:
        queue = tasks.create_queue(
            queue_name=queue_name,
            max_dispatches_per_second=10.0,
            max_concurrent_dispatches=5,
        )
        print(f"[OK] Created queue: {queue['name']}")
        print(
            f"  Max dispatches/sec: {queue.get('rateLimits', {}).get('maxDispatchesPerSecond', 'N/A')}"
        )
        print(
            f"  Max concurrent: {queue.get('rateLimits', {}).get('maxConcurrentDispatches', 'N/A')}"
        )
    except Exception as e:
        print(f"[FAIL] Failed to create queue: {e}")
        print("  Queue might already exist - continuing...")

    # 2. Get queue details
    print("\n2. Getting queue details...")
    try:
        queue = tasks.get_queue(queue_name)
        print(f"[OK] Retrieved queue: {queue['name']}")
        print(f"  State: {queue.get('state', 'UNKNOWN')}")
    except Exception as e:
        print(f"[FAIL] Failed to get queue: {e}")

    # 3. List all queues
    print("\n3. Listing all queues...")
    try:
        queues = tasks.list_queues()
        print(f"[OK] Found {len(queues)} queue(s):")
        for queue in queues:
            print(
                f"  - {queue['name'].split('/')[-1]} (State: {queue.get('state', 'UNKNOWN')})"
            )
    except Exception as e:
        print(f"[FAIL] Failed to list queues: {e}")

    # 4. Create an immediate HTTP task
    print("\n4. Creating immediate HTTP task...")
    try:
        task = tasks.create_http_task(
            queue=queue_name,
            url="https://httpbin.org/post",
            http_method="POST",
            payload={
                "message": "Hello from Cloud Tasks!",
                "timestamp": datetime.now().isoformat(),
                "task_type": "immediate",
            },
            headers={"Content-Type": "application/json"},
        )
        print(f"[OK] Created task: {task.name.split('/')[-1]}")
        print(f"  URL: {task.http_request.url}")
        print(f"  Method: {task.http_request.http_method}")
        print(f"  Schedule time: {task.schedule_time}")
    except Exception as e:
        print(f"[FAIL] Failed to create task: {e}")

    # 5. Create a scheduled HTTP task (delayed by 1 minute)
    print("\n5. Creating scheduled HTTP task (1 minute delay)...")
    try:
        future_time = datetime.now() + timedelta(minutes=1)
        task = tasks.create_http_task(
            queue=queue_name,
            url="https://httpbin.org/post",
            http_method="POST",
            payload={
                "message": "This task was scheduled!",
                "scheduled_for": future_time.isoformat(),
            },
            delay_seconds=60,  # Schedule for 1 minute from now
        )
        print(f"[OK] Created scheduled task: {task.name.split('/')[-1]}")
        print(f"  Scheduled for: {task.schedule_time}")
        print("  Delay: 60 seconds")
        scheduled_task_name = task.name.split("/")[-1]
    except Exception as e:
        print(f"[FAIL] Failed to create scheduled task: {e}")
        scheduled_task_name = None

    # 6. Create tasks with different priorities
    print("\n6. Creating tasks with custom headers...")
    try:
        task = tasks.create_http_task(
            queue=queue_name,
            url="https://example.com/webhook",
            http_method="POST",
            payload={
                "event": "user_signup",
                "user_id": "12345",
            },
            headers={
                "Content-Type": "application/json",
                "X-Custom-Header": "custom-value",
                "X-Priority": "high",
            },
        )
        print(f"[OK] Created task with custom headers: {task.name.split('/')[-1]}")
        print(f"  Headers: {len(task.http_request.headers)} header(s)")
    except Exception as e:
        print(f"[FAIL] Failed to create task with headers: {e}")

    # 7. List tasks in queue
    print("\n7. Listing tasks in queue...")
    try:
        task_list = tasks.list_tasks(queue_name, page_size=10)
        print(f"[OK] Found {len(task_list)} task(s) in queue:")
        for task in task_list[:5]:  # Show first 5
            task_id = task.name.split("/")[-1]
            print(
                f"  - {task_id[:20]}... ({task.http_request.http_method} {task.http_request.url})"
            )
        if len(task_list) > 5:
            print(f"  ... and {len(task_list) - 5} more")
    except Exception as e:
        print(f"[FAIL] Failed to list tasks: {e}")

    # 8. Get specific task details
    print("\n8. Getting task details...")
    if scheduled_task_name:
        try:
            task = tasks.get_task(queue_name, scheduled_task_name)
            print(f"[OK] Retrieved task: {task.name.split('/')[-1][:30]}...")
            print(f"  URL: {task.http_request.url}")
            print(f"  Method: {task.http_request.http_method}")
            print(f"  Schedule time: {task.schedule_time}")
        except Exception as e:
            print(f"[FAIL] Failed to get task: {e}")
    else:
        print("  [SKIP] No scheduled task to retrieve")

    # 9. Pause queue (stops task processing)
    print("\n9. Pausing queue...")
    try:
        queue = tasks.pause_queue(queue_name)
        print(f"[OK] Paused queue: {queue['name']}")
        print(f"  State: {queue.get('state', 'UNKNOWN')}")
        print("  Tasks will not be dispatched until queue is resumed")
    except Exception as e:
        print(f"[FAIL] Failed to pause queue: {e}")

    # 10. Resume queue
    print("\n10. Resuming queue...")
    try:
        queue = tasks.resume_queue(queue_name)
        print(f"[OK] Resumed queue: {queue['name']}")
        print(f"  State: {queue.get('state', 'UNKNOWN')}")
        print("  Task processing will continue")
    except Exception as e:
        print(f"[FAIL] Failed to resume queue: {e}")

    # 11. Delete a specific task
    print("\n11. Deleting scheduled task...")
    if scheduled_task_name:
        try:
            tasks.delete_task(queue_name, scheduled_task_name)
            print(f"[OK] Deleted task: {scheduled_task_name[:30]}...")
        except Exception as e:
            print(f"[FAIL] Failed to delete task: {e}")
    else:
        print("  [SKIP] No scheduled task to delete")

    # 12. Purge queue (delete all tasks)
    print("\n12. Purging queue (deleting all tasks)...")
    try:
        result = tasks.purge_queue(queue_name)
        print(f"[OK] Purged queue: {result['name']}")
        print("  All tasks have been deleted from the queue")
    except Exception as e:
        print(f"[FAIL] Failed to purge queue: {e}")

    # 13. Cleanup - Delete queue
    print("\n13. Cleaning up - deleting queue...")
    try:
        tasks.delete_queue(queue_name)
        print(f"[OK] Deleted queue: {queue_name}")
    except Exception as e:
        print(f"[FAIL] Failed to delete queue: {e}")

    # Example use cases
    print("\n" + "=" * 80)
    print("Common Use Cases:")
    print("=" * 80)
    print(
        """
1. Email Processing Queue:
   - Send welcome emails after user signup
   - Process newsletter subscriptions
   - Handle password reset emails

2. Data Processing Pipeline:
   - Process uploaded images (resize, optimize)
   - Generate reports asynchronously
   - Import/export large datasets

3. Integration Tasks:
   - Call third-party APIs with rate limiting
   - Sync data between systems
   - Send webhooks to external services

4. Scheduled Operations:
   - Send daily digest emails
   - Clean up expired data
   - Generate periodic reports

5. Retry Logic:
   - Cloud Tasks automatically retries failed tasks
   - Configure retry parameters per queue
   - Dead letter queues for permanently failed tasks
"""
    )

    print("=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
