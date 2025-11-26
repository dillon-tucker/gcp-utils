"""
Example usage of the Workflows controller.

This example demonstrates:
- Creating workflows with YAML/JSON definitions
- Executing workflows with arguments
- Monitoring execution status
- Listing and managing workflows
- Canceling executions
- Common workflow patterns
"""

import sys
from pathlib import Path
import time

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import WorkflowsController


def main() -> None:
    """Demonstrate Workflows controller functionality."""

    # Initialize controller (automatically loads from .env)
    workflows = WorkflowsController()

    print("=" * 80)
    print("Workflows Controller Example")
    print("=" * 80)

    # 1. Create a simple workflow
    print("\n1. Creating simple workflow...")
    workflow_name = "example-simple-workflow"

    # Simple workflow that makes an HTTP request
    simple_workflow = """
- step1:
    call: http.get
    args:
      url: https://httpbin.org/json
    result: api_response
- step2:
    return: ${api_response.body}
"""

    try:
        workflow = workflows.create_workflow(
            workflow_name=workflow_name,
            source_contents=simple_workflow,
            description="Simple workflow that fetches data from an API",
        )
        print(f"[OK] Created workflow: {workflow.name}")
        print(f"  Description: {workflow.description}")
        print(f"  State: {workflow.state}")
    except Exception as e:
        print(f"[FAIL] Failed to create workflow: {e}")
        print("  Workflow might already exist - continuing...")

    # 2. Create a workflow with parameters
    print("\n2. Creating workflow with parameters...")
    param_workflow_name = "example-param-workflow"

    parameterized_workflow = """
- init:
    assign:
      - name: ${args.name}
      - greeting: ${"Hello, " + name + "!"}
- logGreeting:
    call: sys.log
    args:
      text: ${greeting}
- returnResult:
    return: ${greeting}
"""

    try:
        workflow = workflows.create_workflow(
            workflow_name=param_workflow_name,
            source_contents=parameterized_workflow,
            description="Workflow that accepts parameters and returns a greeting",
        )
        print(f"[OK] Created parameterized workflow: {workflow.name}")
        print(f"  State: {workflow.state}")
    except Exception as e:
        print(f"[FAIL] Failed to create parameterized workflow: {e}")
        print("  Workflow might already exist - continuing...")

    # 3. Create a complex workflow with error handling
    print("\n3. Creating workflow with error handling...")
    complex_workflow_name = "example-complex-workflow"

    complex_workflow = """
- fetchData:
    try:
      call: http.get
      args:
        url: ${args.url}
      result: data
    except:
      as: e
      steps:
        - logError:
            call: sys.log
            args:
              text: ${"Error fetching data: " + e.message}
        - returnError:
            return: ${"Error: " + e.message}
- processData:
    switch:
      - condition: ${data.code == 200}
        steps:
          - success:
              return: ${data.body}
      - condition: true
        steps:
          - failure:
              return: "Request failed"
"""

    try:
        workflow = workflows.create_workflow(
            workflow_name=complex_workflow_name,
            source_contents=complex_workflow,
            description="Complex workflow with error handling and conditional logic",
        )
        print(f"[OK] Created complex workflow: {workflow.name}")
        print(f"  State: {workflow.state}")
    except Exception as e:
        print(f"[FAIL] Failed to create complex workflow: {e}")
        print("  Workflow might already exist - continuing...")

    # 4. List all workflows
    print("\n4. Listing all workflows...")
    try:
        all_workflows = workflows.list_workflows()
        print(f"[OK] Found {len(all_workflows)} workflow(s):")
        for wf in all_workflows:
            wf_name = wf.name.split("/")[-1]
            print(f"  - {wf_name}: {wf.description or 'No description'}")
    except Exception as e:
        print(f"[FAIL] Failed to list workflows: {e}")

    # 5. Get workflow details
    print("\n5. Getting workflow details...")
    try:
        workflow = workflows.get_workflow(workflow_name)
        print(f"[OK] Retrieved workflow: {workflow.name}")
        print(f"  State: {workflow.state}")
        print(f"  Revision ID: {workflow.revision_id}")
        print(f"  Created: {workflow.create_time}")
        print(f"  Updated: {workflow.update_time}")
    except Exception as e:
        print(f"[FAIL] Failed to get workflow: {e}")

    # 6. Execute simple workflow
    print("\n6. Executing simple workflow...")
    try:
        execution = workflows.execute_workflow(workflow_name)
        print(f"[OK] Started execution: {execution.name.split('/')[-1]}")
        print(f"  State: {execution.state}")
        execution_id = execution.name.split("/")[-1]
    except Exception as e:
        print(f"[FAIL] Failed to execute workflow: {e}")
        execution_id = None

    # 7. Execute parameterized workflow
    print("\n7. Executing parameterized workflow with arguments...")
    try:
        execution = workflows.execute_workflow(
            workflow_name=param_workflow_name, argument={"name": "GCP Utils"}
        )
        print(f"[OK] Started parameterized execution: {execution.name.split('/')[-1]}")
        print(f"  State: {execution.state}")
        print(f"  Argument: {execution.argument}")
        execution.name.split("/")[-1]
    except Exception as e:
        print(f"[FAIL] Failed to execute parameterized workflow: {e}")

    # 8. Wait for execution to complete and get result
    print("\n8. Waiting for execution to complete...")
    if execution_id:
        print("  Polling execution status...")
        max_wait = 30  # seconds
        wait_time = 0
        try:
            while wait_time < max_wait:
                execution = workflows.get_execution(workflow_name, execution_id)
                print(f"  Status: {execution.state} (waited {wait_time}s)")

                if execution.state in ["SUCCEEDED", "FAILED", "CANCELLED"]:
                    print(f"[OK] Execution completed with state: {execution.state}")
                    if execution.result:
                        print(f"  Result: {execution.result[:100]}...")
                    if execution.error:
                        print(f"  Error: {execution.error}")
                    break

                time.sleep(2)
                wait_time += 2
            else:
                print("  [TIMEOUT] Execution still running after 30 seconds")
        except Exception as e:
            print(f"[FAIL] Failed to get execution status: {e}")
    else:
        print("  [SKIP] No execution to wait for")

    # 9. List executions for a workflow
    print("\n9. Listing executions...")
    try:
        executions = workflows.list_executions(workflow_name, page_size=10)
        print(
            f"[OK] Found {len(executions)} execution(s) for workflow '{workflow_name}':"
        )
        for exec in executions[:3]:  # Show first 3
            exec_id = exec.name.split("/")[-1]
            print(f"  - {exec_id[:20]}... State: {exec.state}")
        if len(executions) > 3:
            print(f"  ... and {len(executions) - 3} more")
    except Exception as e:
        print(f"[FAIL] Failed to list executions: {e}")

    # 10. Execute workflow that will take a while (for cancellation demo)
    print("\n10. Executing long-running workflow for cancellation demo...")
    long_workflow_name = "example-long-workflow"
    long_workflow = """
- step1:
    call: sys.sleep
    args:
      seconds: 60
- step2:
    return: "Completed"
"""

    try:
        # Create long workflow
        workflows.create_workflow(
            workflow_name=long_workflow_name,
            source_contents=long_workflow,
            description="Long-running workflow for cancellation demo",
        )

        # Execute it
        execution = workflows.execute_workflow(long_workflow_name)
        long_execution_id = execution.name.split("/")[-1]
        print(f"[OK] Started long-running execution: {long_execution_id[:30]}...")

        # Wait a moment
        time.sleep(1)

        # Cancel it
        print("  Canceling execution...")
        result = workflows.cancel_execution(long_workflow_name, long_execution_id)
        print("[OK] Cancelled execution")
        print(f"  Final state: {result.state}")
    except Exception as e:
        print(f"[FAIL] Failed cancellation demo: {e}")

    # 11. Update workflow
    print("\n11. Updating workflow...")
    updated_workflow = """
- step1:
    call: http.get
    args:
      url: https://httpbin.org/uuid
    result: api_response
- step2:
    call: sys.log
    args:
      text: ${"UUID: " + api_response.body.uuid}
- step3:
    return: ${api_response.body}
"""

    try:
        workflow = workflows.update_workflow(
            workflow_name=workflow_name,
            source_contents=updated_workflow,
            description="Updated workflow that fetches a UUID",
        )
        print(f"[OK] Updated workflow: {workflow.name}")
        print(f"  New revision ID: {workflow.revision_id}")
    except Exception as e:
        print(f"[FAIL] Failed to update workflow: {e}")

    # 12. Cleanup - Delete workflows
    print("\n12. Cleaning up workflows...")
    for wf_name in [
        workflow_name,
        param_workflow_name,
        complex_workflow_name,
        long_workflow_name,
    ]:
        try:
            workflows.delete_workflow(wf_name)
            print(f"[OK] Deleted workflow: {wf_name}")
        except Exception as e:
            print(f"[FAIL] Failed to delete workflow '{wf_name}': {e}")

    # Example workflow patterns
    print("\n" + "=" * 80)
    print("Common Workflow Patterns:")
    print("=" * 80)
    print(
        """
1. API Integration Pattern:
   - Call external APIs
   - Transform data
   - Store results

2. Data Processing Pipeline:
   - Read from Cloud Storage
   - Process with Cloud Functions
   - Write to BigQuery

3. Error Handling Pattern:
   - Try/catch blocks
   - Retry with backoff
   - Log errors
   - Send notifications

4. Conditional Logic:
   - Switch statements
   - If conditions
   - Variable assignments

5. Parallel Execution:
   - Execute steps in parallel
   - Wait for all to complete
   - Aggregate results

6. Scheduled Workflows:
   - Use Cloud Scheduler to trigger
   - Run on cron schedule
   - Process batch jobs

7. Event-Driven Workflows:
   - Trigger from Pub/Sub
   - React to Cloud Storage events
   - Respond to Firestore changes

8. Microservice Orchestration:
   - Coordinate multiple services
   - Handle service dependencies
   - Implement sagas pattern

Example Workflow Definition (YAML):
-----------------------------------
- init:
    assign:
      - project: ${sys.get_env("GOOGLE_CLOUD_PROJECT_ID")}
      - zone: "us-central1-a"

- getInstanceList:
    call: googleapis.compute.v1.instances.list
    args:
      project: ${project}
      zone: ${zone}
    result: instanceList

- processInstances:
    for:
      value: instance
      in: ${instanceList.items}
      steps:
        - logInstance:
            call: sys.log
            args:
              text: ${"Instance: " + instance.name}

- returnResult:
    return: ${instanceList}
"""
    )

    print("=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
