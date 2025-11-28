"""
Example usage of the Cloud Run controller.

This example demonstrates:
- Deploying Cloud Run services from container images
- Updating service configuration
- Managing environment variables and secrets
- Traffic splitting and revisions
- Invoking services
- Service management and cleanup
"""

import sys
from pathlib import Path

# Add src to path for running without installation
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from gcp_utils.controllers import CloudRunController
from gcp_utils.models.cloud_run import TrafficTarget


def main() -> None:
    """Demonstrate Cloud Run controller functionality."""

    # Initialize controller (automatically loads from .env)
    cloud_run = CloudRunController()

    print("=" * 80)
    print("Cloud Run Controller Example")
    print("=" * 80)

    # 1. Deploy a simple service (using a public container image)
    print("\n1. Deploying Cloud Run service...")
    service_name = "example-hello-service"

    try:
        service = cloud_run.create_service(
            service_name=service_name,
            image="gcr.io/cloudrun/hello",  # Public Cloud Run sample image
            cpu="1000m",  # 1 vCPU
            memory="512Mi",  # 512 MB RAM
            max_instances=10,
            min_instances=0,  # Scale to zero when not in use
            timeout_seconds=300,
            allow_unauthenticated=True,  # Make publicly accessible
        )
        print(f"[OK] Deployed service: {service.name}")
        print(f"  URL: {service.url}")
        print(f"  Latest revision: {service.latest_revision}")
        print(f"  CPU: {service.cpu}")
        print(f"  Memory: {service.memory}")
    except Exception as e:
        print(f"[FAIL] Failed to deploy service: {e}")
        print("  Service might already exist - continuing...")

    # 2. Get service details
    print("\n2. Getting service details...")
    try:
        service = cloud_run.get_service(service_name)
        print(f"[OK] Retrieved service: {service.name}")
        print(f"  URL: {service.url}")
        print(f"  Latest created revision: {service.latest_created_revision}")
        print(f"  Latest ready revision: {service.latest_ready_revision}")
        print(f"  Ingress: {service.ingress}")
    except Exception as e:
        print(f"[FAIL] Failed to get service: {e}")

    # 3. List all Cloud Run services
    print("\n3. Listing all Cloud Run services...")
    try:
        services = cloud_run.list_services()
        print(f"[OK] Found {len(services)} service(s):")
        for svc in services:
            svc_name = svc.name.split("/")[-1]
            print(f"  - {svc_name}: {svc.url}")
    except Exception as e:
        print(f"[FAIL] Failed to list services: {e}")

    # 4. Deploy service with environment variables
    print("\n4. Deploying service with environment variables...")
    env_service_name = "example-env-service"

    try:
        service = cloud_run.create_service(
            service_name=env_service_name,
            image="gcr.io/cloudrun/hello",
            env_vars={
                "APP_ENV": "production",
                "LOG_LEVEL": "info",
                "API_VERSION": "v1",
            },
            cpu="500m",
            memory="256Mi",
            allow_unauthenticated=True,
        )
        print(f"[OK] Deployed service with environment variables: {service.name}")
        print(f"  URL: {service.url}")
        print(f"  Environment variables: {len(service.env_vars)} set")
    except Exception as e:
        print(f"[FAIL] Failed to deploy service with env vars: {e}")
        print("  Service might already exist - continuing...")

    # 5. Update service configuration
    print("\n5. Updating service configuration...")
    try:
        service = cloud_run.update_service(
            service_name=service_name,
            cpu="2000m",  # Increase to 2 vCPU
            memory="1Gi",  # Increase to 1 GB RAM
            max_instances=20,  # Allow more instances
            env_vars={
                "UPDATED": "true",
                "VERSION": "2.0",
            },
        )
        print(f"[OK] Updated service: {service.name}")
        print(f"  New CPU: {service.cpu}")
        print(f"  New memory: {service.memory}")
        print(f"  New max instances: {service.max_instances}")
        print(f"  New latest revision: {service.latest_revision}")
    except Exception as e:
        print(f"[FAIL] Failed to update service: {e}")

    # 6. Get service URL
    print("\n6. Getting service URL...")
    try:
        url = cloud_run.get_service_url(service_name)
        print(f"[OK] Service URL: {url}")
        print("  You can access the service at this URL")
    except Exception as e:
        print(f"[FAIL] Failed to get service URL: {e}")

    # 7. Invoke service (make HTTP request)
    print("\n7. Invoking service...")
    try:
        response = cloud_run.invoke_service(
            service_name=service_name,
            method="GET",
        )
        print("[OK] Service invoked successfully")
        print(f"  Status code: {response.get('status_code', 'N/A')}")
        print(f"  Response preview: {str(response.get('body', ''))[:100]}...")
    except Exception as e:
        print(f"[FAIL] Failed to invoke service: {e}")

    # 8. Deploy a new revision and split traffic
    print("\n8. Deploying new revision with traffic splitting...")
    try:
        # Deploy a new revision with different environment variable
        service = cloud_run.update_service(
            service_name=service_name,
            env_vars={
                "UPDATED": "true",
                "VERSION": "3.0",
                "CANARY": "true",
            },
        )
        new_revision = service.latest_revision
        print(f"[OK] Created new revision: {new_revision}")

        # Get the previous revision from traffic targets
        service = cloud_run.get_service(service_name)
        if len(service.traffic_targets) > 0:
            old_revision = service.traffic_targets[0].revision_name

            # Split traffic: 80% to old revision, 20% to new revision (canary deployment)
            print("  Splitting traffic: 80% old, 20% new (canary)...")
            service = cloud_run.update_traffic(
                service_name=service_name,
                traffic_targets=[
                    TrafficTarget(revision_name=old_revision, percent=80),
                    TrafficTarget(revision_name=new_revision, percent=20),
                ],
            )
            print("[OK] Updated traffic split")
            print("  Traffic distribution:")
            for target in service.traffic_targets:
                print(f"    - {target.revision_name}: {target.percent}%")
        else:
            print("  [SKIP] No previous revisions to split traffic with")
    except Exception as e:
        print(f"[FAIL] Failed to split traffic: {e}")

    # 9. Deploy with concurrency and request limits
    print("\n9. Deploying service with concurrency settings...")
    concurrent_service_name = "example-concurrent-service"

    try:
        service = cloud_run.create_service(
            service_name=concurrent_service_name,
            image="gcr.io/cloudrun/hello",
            cpu="1000m",
            memory="512Mi",
            max_instances=100,
            min_instances=1,  # Keep 1 instance always warm
            concurrency=80,  # Max 80 concurrent requests per instance
            allow_unauthenticated=True,
        )
        print(f"[OK] Deployed service with concurrency settings: {service.name}")
        print(f"  URL: {service.url}")
        print(f"  Concurrency: {service.concurrency} requests/instance")
        print(f"  Min instances: {service.min_instances}")
    except Exception as e:
        print(f"[FAIL] Failed to deploy concurrent service: {e}")
        print("  Service might already exist - continuing...")

    # 10. Invoke service with POST request
    print("\n10. Invoking service with POST request...")
    try:
        response = cloud_run.invoke_service(
            service_name=service_name,
            method="POST",
            json_payload={
                "message": "Hello from GCP Utils!",
                "action": "test",
            },
        )
        print("[OK] POST request successful")
        print(f"  Status code: {response.get('status_code', 'N/A')}")
    except Exception as e:
        print(f"[FAIL] Failed to invoke service with POST: {e}")

    # 11. Cleanup - Delete services
    print("\n11. Cleaning up services...")
    for svc_name in [service_name, env_service_name, concurrent_service_name]:
        try:
            cloud_run.delete_service(svc_name)
            print(f"[OK] Deleted service: {svc_name}")
        except Exception as e:
            print(f"[FAIL] Failed to delete service '{svc_name}': {e}")

    # Example use cases and deployment patterns
    print("\n" + "=" * 80)
    print("Common Use Cases & Deployment Patterns:")
    print("=" * 80)
    print(
        """
1. Web Applications:
   - Deploy containerized web apps
   - Automatic HTTPS
   - Scale to zero when idle
   - Pay only for actual usage

2. API Services:
   - RESTful APIs
   - GraphQL endpoints
   - Microservices architecture
   - Auto-scaling based on load

3. Background Workers:
   - Process queued tasks
   - Handle webhooks
   - Async job processing
   - Event-driven functions

4. Deployment Strategies:

   a) Blue-Green Deployment:
      - Deploy new version
      - Split traffic 0/100 (test new version)
      - Switch to 100/0 when ready
      - Keep old version for quick rollback

   b) Canary Deployment:
      - Deploy new version
      - Route 5-20% traffic to new version
      - Monitor metrics
      - Gradually increase traffic
      - Rollback if issues detected

   c) Rolling Deployment:
      - Update service configuration
      - Cloud Run automatically rolls out
      - New revisions replace old ones
      - Zero downtime updates

5. Resource Configuration:

   CPU/Memory Guidelines:
   - Startup tasks: 1000m CPU, 512Mi memory
   - Web apps: 1000-2000m CPU, 512Mi-2Gi memory
   - API services: 2000m CPU, 1-4Gi memory
   - CPU-intensive: 4000m+ CPU, 2-8Gi memory

   Concurrency Settings:
   - Low latency apps: 1-10 concurrent requests
   - Standard apps: 80-100 concurrent requests
   - High-throughput: 1000 concurrent requests

6. Security Best Practices:
   - Use Cloud Run IAM for authentication
   - Set allow_unauthenticated=False for private services
   - Use Secret Manager for sensitive data
   - Implement VPC connectors for private resources
   - Use service accounts with minimum permissions

7. Cost Optimization:
   - Set min_instances=0 for low-traffic services
   - Use appropriate CPU/memory allocation
   - Configure request timeout
   - Implement caching strategies
   - Use Cloud CDN for static content

8. Monitoring and Observability:
   - Cloud Run integrates with Cloud Logging
   - Cloud Monitoring for metrics
   - Set up alerts for errors and latency
   - Use Cloud Trace for distributed tracing
   - Monitor revision performance
"""
    )

    print("=" * 80)
    print("Example completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()
