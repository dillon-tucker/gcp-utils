"""
Example usage of Cloud Scheduler controller.

This example demonstrates:
- Creating HTTP-triggered scheduled jobs
- Creating Pub/Sub-triggered scheduled jobs
- Managing job lifecycle (pause, resume, run)
- Updating job schedules
- Integration with Cloud Functions and Cloud Run

Requirements:
- Valid GCP project with Cloud Scheduler API enabled
- .env file with GCP_PROJECT_ID set
"""

from gcp_utils.controllers import CloudSchedulerController

# Initialize controller (auto-loads from .env)
scheduler = CloudSchedulerController()


def example_create_http_job() -> None:
    """
    Create an HTTP-triggered scheduled job.

    This job calls an HTTP endpoint on a schedule (e.g., daily backup).
    """
    print("\n=== Creating HTTP Scheduled Job ===")

    try:
        job = scheduler.create_http_job(
            job_id="daily-backup",
            schedule="0 2 * * *",  # Run at 2 AM every day
            uri="https://my-api.example.com/api/backup",
            http_method="POST",
            headers={
                "Content-Type": "application/json",
                "X-API-Key": "my-api-key",
            },
            body=b'{"type": "full", "notify": true}',
            time_zone="America/New_York",
            description="Daily backup job",
        )

        print(f"✓ HTTP job created: {job.name}")
        print(f"  Schedule: {job.schedule} ({job.time_zone})")
        print(f"  Next run: {job.schedule_time}")

    except Exception as e:
        print(f"✗ Error creating job: {e}")


def example_create_pubsub_job() -> None:
    """
    Create a Pub/Sub-triggered scheduled job.

    This job publishes a message to a Pub/Sub topic on a schedule.
    """
    print("\n=== Creating Pub/Sub Scheduled Job ===")

    try:
        job = scheduler.create_pubsub_job(
            job_id="hourly-processing",
            schedule="0 * * * *",  # Run every hour
            topic_name="data-processing",  # Will be prefixed with project path
            data=b'{"action": "process_new_data"}',
            attributes={
                "priority": "high",
                "source": "scheduler",
            },
            time_zone="UTC",
            description="Hourly data processing trigger",
        )

        print(f"✓ Pub/Sub job created: {job.name}")
        print(f"  Schedule: {job.schedule} ({job.time_zone})")

    except Exception as e:
        print(f"✗ Error creating job: {e}")


def example_advanced_http_job_with_auth() -> None:
    """
    Create an HTTP job with OAuth authentication.

    This is useful for calling authenticated GCP services like Cloud Functions
    or Cloud Run.
    """
    print("\n=== Creating Authenticated HTTP Job ===")

    try:
        job = scheduler.create_http_job(
            job_id="call-cloud-function",
            schedule="*/15 * * * *",  # Every 15 minutes
            uri="https://us-central1-my-project.cloudfunctions.net/my-function",
            http_method="POST",
            oauth_service_account="my-service-account@my-project.iam.gserviceaccount.com",
            body=b'{"task": "process"}',
            time_zone="America/Los_Angeles",
            description="Call Cloud Function every 15 minutes",
        )

        print(f"✓ Authenticated job created: {job.name}")
        print("  Will use OAuth token from service account")

    except Exception as e:
        print(f"✗ Error creating job: {e}")


def example_update_job_schedule() -> None:
    """
    Update an existing job's schedule.

    This is useful for changing when a job runs without recreating it.
    """
    print("\n=== Updating Job Schedule ===")

    try:
        job = scheduler.update_job(
            job_id="daily-backup",
            schedule="0 3 * * *",  # Change from 2 AM to 3 AM
            update_mask=["schedule"],
        )

        print(f"✓ Job schedule updated: {job.name}")
        print(f"  New schedule: {job.schedule}")

    except Exception as e:
        print(f"✗ Error updating job: {e}")


def example_pause_and_resume_job() -> None:
    """
    Pause and resume a scheduled job.

    This is useful for temporarily disabling jobs without deleting them.
    """
    print("\n=== Pausing Job ===")

    try:
        # Pause the job
        response = scheduler.pause_job("daily-backup")
        print(f"✓ Job paused: {response.name}")
        print(f"  State: {response.state}")

        # Resume the job
        print("\n=== Resuming Job ===")
        response = scheduler.resume_job("daily-backup")
        print(f"✓ Job resumed: {response.name}")
        print(f"  State: {response.state}")

    except Exception as e:
        print(f"✗ Error: {e}")


def example_run_job_manually() -> None:
    """
    Manually trigger a job to run immediately.

    This is useful for testing jobs without waiting for the scheduled time.
    """
    print("\n=== Running Job Manually ===")

    try:
        response = scheduler.run_job("daily-backup")

        print(f"✓ Job triggered: {response.name}")
        print(f"  Attempt time: {response.attempt_time}")
        print("\n  Check job logs to see execution results")

    except Exception as e:
        print(f"✗ Error running job: {e}")


def example_list_jobs() -> None:
    """
    List all scheduled jobs in the project.
    """
    print("\n=== Listing All Jobs ===")

    try:
        response = scheduler.list_jobs()

        print(f"Found {len(response.jobs)} jobs:")
        for job in response.jobs:
            print(f"\n  Job: {job.name}")
            print(f"    Schedule: {job.schedule}")
            print(f"    Timezone: {job.time_zone}")
            print(f"    State: {job.state}")
            if job.description:
                print(f"    Description: {job.description}")

    except Exception as e:
        print(f"✗ Error listing jobs: {e}")


def example_get_job_details() -> None:
    """
    Get detailed information about a specific job.
    """
    print("\n=== Getting Job Details ===")

    try:
        job = scheduler.get_job("daily-backup")

        print(f"Job: {job.name}")
        print(f"  Schedule: {job.schedule}")
        print(f"  Timezone: {job.time_zone}")
        print(f"  State: {job.state}")
        print(f"  Description: {job.description}")
        print(f"  Last attempt: {job.last_attempt_time}")
        print(f"  Next scheduled: {job.schedule_time}")

    except Exception as e:
        print(f"✗ Error getting job: {e}")


def example_delete_job() -> None:
    """
    Delete a scheduled job.

    CAUTION: This permanently deletes the job.
    """
    print("\n=== Deleting Job ===")

    try:
        scheduler.delete_job("daily-backup")
        print("✓ Job deleted successfully")

    except Exception as e:
        print(f"✗ Error deleting job: {e}")


def example_common_schedules() -> None:
    """
    Examples of common cron schedule patterns.
    """
    print("\n=== Common Schedule Patterns ===")

    schedules = {
        "Every minute": "* * * * *",
        "Every 5 minutes": "*/5 * * * *",
        "Every 15 minutes": "*/15 * * * *",
        "Every hour": "0 * * * *",
        "Every 6 hours": "0 */6 * * *",
        "Every day at midnight": "0 0 * * *",
        "Every day at 9 AM": "0 9 * * *",
        "Every Monday at 9 AM": "0 9 * * 1",
        "First day of month at midnight": "0 0 1 * *",
        "Every weekday at 6 PM": "0 18 * * 1-5",
    }

    print("Use these patterns in your schedule:")
    for desc, pattern in schedules.items():
        print(f"  {desc:30} -> {pattern}")


if __name__ == "__main__":
    print("Cloud Scheduler Controller Example")
    print("=" * 50)

    # Run examples
    # example_create_http_job()
    # example_create_pubsub_job()
    # example_advanced_http_job_with_auth()
    # example_update_job_schedule()
    # example_pause_and_resume_job()
    # example_run_job_manually()
    example_list_jobs()
    # example_get_job_details()
    # example_delete_job()  # Uncomment to test deletion
    example_common_schedules()

    print("\n" + "=" * 50)
    print("Example completed!")
