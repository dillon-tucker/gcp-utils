"""
Example usage of FirestoreController.

This example demonstrates common Firestore operations including
document CRUD, querying, batch operations, and transactions.
"""

from gcp_utilities.config import GCPSettings
from gcp_utilities.controllers import FirestoreController
from gcp_utilities.models.firestore import FirestoreQuery, QueryOperator


def main():
    # Initialize settings
    settings = GCPSettings(project_id="my-gcp-project")

    # Create controller
    firestore = FirestoreController(settings)

    # Create documents
    print("Creating documents...")
    user1 = firestore.create_document(
        collection="users",
        data={
            "name": "John Doe",
            "email": "john@example.com",
            "age": 30,
            "active": True,
        },
        document_id="user1",
    )
    print(f"Created: {user1.id}")

    user2 = firestore.create_document(
        collection="users",
        data={
            "name": "Jane Smith",
            "email": "jane@example.com",
            "age": 25,
            "active": True,
        },
        document_id="user2",
    )
    print(f"Created: {user2.id}")

    # Get a document
    print("\nGetting document...")
    doc = firestore.get_document("users", "user1")
    print(f"Retrieved: {doc.data}")

    # Update document
    print("\nUpdating document...")
    updated = firestore.update_document(
        collection="users",
        document_id="user1",
        data={"age": 31, "city": "San Francisco"},
        merge=True,
    )
    print(f"Updated: {updated.data}")

    # List documents
    print("\nListing documents...")
    docs = firestore.list_documents(
        collection="users",
        order_by="age",
        direction="ASCENDING",
    )
    for doc in docs:
        print(f"  - {doc.id}: {doc.data.get('name')} (age: {doc.data.get('age')})")

    # Query documents
    print("\nQuerying documents (age > 25)...")
    queries = [
        FirestoreQuery(
            field="age",
            operator=QueryOperator.GREATER_THAN,
            value=25,
        )
    ]
    results = firestore.query_documents(
        collection="users",
        queries=queries,
    )
    for result in results:
        print(f"  - {result.id}: {result.data}")

    # Batch write operations
    print("\nPerforming batch write...")
    operations = [
        {
            "operation": "set",
            "collection": "users",
            "document_id": "user3",
            "data": {"name": "Bob Wilson", "age": 35, "active": False},
        },
        {
            "operation": "update",
            "collection": "users",
            "document_id": "user2",
            "data": {"city": "New York"},
        },
        {
            "operation": "delete",
            "collection": "users",
            "document_id": "user3",
        },
    ]
    firestore.batch_write(operations)
    print("Batch write completed")

    # Transaction example
    print("\nRunning transaction...")

    def update_user_age(transaction, user_id: str, age_increment: int):
        """Transaction function to safely update user age."""
        doc_ref = firestore.client.collection("users").document(user_id)
        snapshot = doc_ref.get(transaction=transaction)

        if not snapshot.exists:
            raise ValueError(f"User {user_id} not found")

        current_age = snapshot.get("age")
        new_age = current_age + age_increment

        transaction.update(doc_ref, {"age": new_age})
        return new_age

    new_age = firestore.run_transaction(update_user_age, "user1", 1)
    print(f"User age updated to: {new_age}")

    # Check if collection exists
    print("\nChecking collection existence...")
    exists = firestore.collection_exists("users")
    print(f"Collection 'users' exists: {exists}")

    # Get subcollections
    print("\nGetting subcollections...")
    subcollections = firestore.get_subcollections("users", "user1")
    print(f"Subcollections: {subcollections}")

    # Delete specific documents
    print("\nDeleting documents...")
    firestore.delete_document("users", "user1")
    firestore.delete_document("users", "user2")
    print("Documents deleted")

    # Delete entire collection
    print("\nDeleting collection...")
    deleted_count = firestore.delete_collection("users", batch_size=50)
    print(f"Deleted {deleted_count} documents from collection")


if __name__ == "__main__":
    main()
