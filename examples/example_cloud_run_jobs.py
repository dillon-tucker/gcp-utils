"""
Example usage of Cloud Run Jobs controller.

Cloud Run Jobs are ideal for:
- Batch processing workloads
- Scheduled tasks and cron jobs
- Data processing pipelines
- One-time migrations
- Parallel task execution

This example demonstrates:
1. Creating a Cloud Run job
2. Running a job execution
3. Monitoring execution status
4. Managing parallel tasks
5. Updating job configuration
6. Listing executions and jobs
7. Cancelling running executions
8. Cleanup and deletion

Prerequisites:
- GCP project with Cloud Run API enabled
- Service account with Cloud Run Admin permissions
- Container image pushed to Container Registry or Artifact Registry
- .env file with GCP_PROJECT_ID configured
"""

import time

from gcp_utils.controllers import CloudRunController
from gcp_utils.models.cloud_run import ExecutionEnvironment, ExecutionStatus

# For this example, we'll use a simple batch processing job container
# In production, replace with your own container image
EXAMPLE_IMAGE = "hello-world"  # Simple example image


def main():
    """Demonstrate Cloud Run Jobs functionality."""

    # Initialize the controller
    # Automatically loads configuration from .env file
    run_ctrl = CloudRunController()

    print("=" * 80)
    print("Cloud Run Jobs Example")
    print("=" * 80)
    print()

    # =========================================================================
    # 1. Create a simple batch job
    # =========================================================================
    print("1. Creating a simple batch job...")
    print("-" * 80)

    try:
        job = run_ctrl.create_job(
            job_name="hello-world",
            image=EXAMPLE_IMAGE,
            task_count=1,  # Number of tasks per execution
            parallelism=1,  # Run tasks sequentially
            max_retries=3,  # Retry failed tasks up to 3 times
            timeout=600,  # 10 minute timeout per task
            cpu="1000m",  # 1 CPU per task
            memory="512Mi",  # 512MB memory per task
            env_vars={
                "ENVIRONMENT": "example",
                "LOG_LEVEL": "INFO",
            },
            labels={
                "team": "engineering",
                "purpose": "batch-processing",
            },
        )

        print(f"[OK] Created job: {job.name}")
        print(f"  - Image: {job.image}")
        print(f"  - Tasks: {job.task_count}")
        print(f"  - Parallelism: {job.parallelism}")
        print(f"  - Max Retries: {job.max_retries}")
        print(f"  - CPU: {job.cpu}")
        print(f"  - Memory: {job.memory}")
        print()

    except Exception as e:
        print(f"[ERROR] Failed to create job: {e}")
        print("  (Job may already exist - continuing with existing job)")
        job = run_ctrl.get_job("hello-world")
        print()

    # =========================================================================
    # 2. Get job details
    # =========================================================================
    print("2. Retrieving job details...")
    print("-" * 80)

    job_details = run_ctrl.get_job("hello-world")
    print(f"Job: {job_details.name}")
    print(f"  - Region: {job_details.region}")
    print(f"  - Created: {job_details.created}")
    print(f"  - Execution Count: {job_details.execution_count}")
    print(f"  - Latest Execution: {job_details.latest_execution or 'None'}")
    print()

    # =========================================================================
    # 3. Run a job execution
    # =========================================================================
    print("3. Running job execution...")
    print("-" * 80)

    try:
        execution = run_ctrl.run_job("hello-world")
        print(f"[OK] Started execution: {execution.execution_id}")
        print(f"  - Status: {execution.status.value}")
        print(f"  - Tasks: {execution.task_count}")
        print(f"  - Parallelism: {execution.parallelism}")
        print()

        # =====================================================================
        # 4. Monitor execution progress
        # =====================================================================
        print("4. Monitoring execution progress...")
        print("-" * 80)

        print("Waiting for execution to complete (checking every 5 seconds)...")
        max_wait_time = 300  # 5 minutes
        start_time = time.time()

        while time.time() - start_time < max_wait_time:
            # Get updated execution status
            execution = run_ctrl.get_execution(
                "hello-world", execution.execution_id
            )

            # Display progress
            print(
                f"  Status: {execution.status.value:15} | "
                f"Succeeded: {execution.succeeded_count:2}/{execution.task_count:2} | "
                f"Failed: {execution.failed_count:2} | "
                f"Running: {execution.running_count:2} | "
                f"Pending: {execution.pending_count:2}"
            )

            # Check if execution is complete
            if execution.status in [
                ExecutionStatus.SUCCEEDED,
                ExecutionStatus.FAILED,
                ExecutionStatus.CANCELLED,
            ]:
                print()
                print(f"[OK] Execution completed with status: {execution.status.value}")
                if execution.duration_seconds:
                    print(f"  Duration: {execution.duration_seconds} seconds")
                if execution.error_message:
                    print(f"  Error: {execution.error_message}")
                break

            time.sleep(5)
        else:
            print()
            print("⚠ Execution still running after 5 minutes")
            print("  You can check status later using get_execution()")

        print()

    except Exception as e:
        print(f"[ERROR] Failed to run job: {e}")
        print()

    # =========================================================================
    # 5. Create a parallel batch job
    # =========================================================================
    print("5. Creating a parallel batch job...")
    print("-" * 80)

    try:
        parallel_job = run_ctrl.create_job(
            job_name="example-parallel-processor",
            image=EXAMPLE_IMAGE,
            task_count=10,  # Create 10 tasks
            parallelism=3,  # Run 3 tasks in parallel
            max_retries=2,
            timeout=300,  # 5 minute timeout
            cpu="500m",  # Half CPU per task
            memory="256Mi",  # 256MB per task
            env_vars={
                "BATCH_SIZE": "100",
                "PARALLEL_MODE": "true",
            },
            execution_environment=ExecutionEnvironment.EXECUTION_ENVIRONMENT_GEN2,
        )

        print(f"[OK] Created parallel job: {parallel_job.name}")
        print(f"  - Tasks: {parallel_job.task_count} tasks")
        print(f"  - Parallelism: {parallel_job.parallelism} concurrent tasks")
        print(
            f"  - Total execution time: ~{(parallel_job.task_count / parallel_job.parallelism) * 5:.0f} minutes (with 5 min tasks)"
        )
        print()

    except Exception as e:
        print(f"Note: {e}")
        print()

    # =========================================================================
    # 6. Update job configuration
    # =========================================================================
    print("6. Updating job configuration...")
    print("-" * 80)

    try:
        updated_job = run_ctrl.update_job(
            "hello-world",
            parallelism=2,  # Increase parallelism
            env_vars={
                "ENVIRONMENT": "example",
                "LOG_LEVEL": "DEBUG",  # Changed from INFO to DEBUG
                "NEW_FEATURE": "enabled",  # Added new variable
            },
        )

        print(f"[OK] Updated job: {updated_job.name}")
        print(f"  - New parallelism: {updated_job.parallelism}")
        print(f"  - Environment variables: {len(updated_job.env_vars)}")
        print()

    except Exception as e:
        print(f"[ERROR] Failed to update job: {e}")
        print()

    # =========================================================================
    # 7. List all executions for a job
    # =========================================================================
    print("7. Listing all executions...")
    print("-" * 80)

    try:
        executions = run_ctrl.list_executions("hello-world")
        print(f"Found {len(executions)} execution(s):")
        print()

        for exec in executions[:5]:  # Show latest 5
            print(f"  Execution: {exec.execution_id}")
            print(f"    Status: {exec.status.value}")
            print(
                f"    Tasks: {exec.succeeded_count}/{exec.task_count} succeeded, {exec.failed_count} failed"
            )
            print(f"    Created: {exec.created}")
            if exec.duration_seconds:
                print(f"    Duration: {exec.duration_seconds}s")
            print()

    except Exception as e:
        print(f"[ERROR] Failed to list executions: {e}")
        print()

    # =========================================================================
    # 8. List all jobs
    # =========================================================================
    print("8. Listing all jobs in the region...")
    print("-" * 80)

    try:
        jobs = run_ctrl.list_jobs()
        print(f"Found {len(jobs)} job(s):")
        print()

        for job in jobs:
            print(f"  Job: {job.name}")
            print(f"    Image: {job.image}")
            print(f"    Tasks: {job.task_count} (parallelism: {job.parallelism})")
            print(f"    Executions: {job.execution_count}")
            if job.latest_execution:
                print(f"    Latest: {job.latest_execution}")
            print()

    except Exception as e:
        print(f"[ERROR] Failed to list jobs: {e}")
        print()

    # =========================================================================
    # 9. Cancel a running execution (example - only if one is running)
    # =========================================================================
    print("9. Cancelling execution (if running)...")
    print("-" * 80)

    try:
        # Get the latest execution
        executions = run_ctrl.list_executions("hello-world")
        if executions:
            latest = executions[0]
            if latest.status == ExecutionStatus.RUNNING:
                cancelled = run_ctrl.cancel_execution(
                    "hello-world", latest.execution_id
                )
                print(f"[OK] Cancelled execution: {cancelled.execution_id}")
                print(f"  Status: {cancelled.status.value}")
                print()
            else:
                print("  No running executions to cancel")
                print()
        else:
            print("  No executions found")
            print()

    except Exception as e:
        print(f"Note: {e}")
        print()

    # =========================================================================
    # 10. Cleanup: Delete jobs
    # =========================================================================
    print("10. Cleanup: Deleting example jobs...")
    print("-" * 80)

    cleanup = input("Delete example jobs? (y/N): ").lower().strip()
    if cleanup == "y":
        try:
            run_ctrl.delete_job("hello-world")
            print("[OK] Deleted: hello-world")
        except Exception as e:
            print(f"Note: {e}")

        try:
            run_ctrl.delete_job("example-parallel-processor")
            print("[OK] Deleted: example-parallel-processor")
        except Exception as e:
            print(f"Note: {e}")

        print()
        print("Cleanup complete!")
    else:
        print("Skipped cleanup - jobs remain in your project")

    print()

    # =========================================================================
    # Summary and Best Practices
    # =========================================================================
    print("=" * 80)
    print("Best Practices for Cloud Run Jobs")
    print("=" * 80)
    print()
    print("1. **Idempotency**: Design tasks to be safely retried")
    print("   - Use unique task identifiers (CLOUD_RUN_TASK_INDEX)")
    print("   - Handle partial completion gracefully")
    print()
    print("2. **Parallelism**: Balance throughput and cost")
    print("   - Higher parallelism = faster completion but more resources")
    print("   - Consider quota limits and downstream service capacity")
    print()
    print("3. **Timeouts**: Set appropriate task timeouts")
    print("   - Default: 600s (10 minutes)")
    print("   - Max: 3600s (1 hour)")
    print("   - Add buffer for retries and startup time")
    print()
    print("4. **Resource Allocation**: Right-size CPU and memory")
    print("   - Start conservative, monitor, then adjust")
    print("   - CPU: 1000m (1 CPU) is a good starting point")
    print("   - Memory: 512Mi minimum for most workloads")
    print()
    print("5. **Monitoring**: Track execution metrics")
    print("   - Use Cloud Logging for task-level logs")
    print("   - Monitor execution duration trends")
    print("   - Set up alerts for failed executions")
    print()
    print("6. **Cost Optimization**:")
    print("   - Use Gen2 execution environment (default)")
    print("   - Jobs are billed per task execution time")
    print("   - No charges when not running (unlike services)")
    print()
    print("7. **Scheduling**: Combine with Cloud Scheduler")
    print("   - Create HTTP trigger to run jobs on schedule")
    print("   - Use cron syntax for complex schedules")
    print()

    print("=" * 80)
    print("Common Use Cases")
    print("=" * 80)
    print()
    print("[OK] Data Processing")
    print("  - ETL pipelines")
    print("  - Report generation")
    print("  - Image/video processing")
    print()
    print("[OK] Batch Operations")
    print("  - Database migrations")
    print("  - Bulk email sending")
    print("  - File format conversions")
    print()
    print("[OK] Scheduled Tasks")
    print("  - Nightly data backups")
    print("  - Weekly analytics")
    print("  - Monthly billing runs")
    print()
    print("[OK] Machine Learning")
    print("  - Batch inference")
    print("  - Model training")
    print("  - Feature engineering")
    print()

    print("=" * 80)
    print("Example Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
