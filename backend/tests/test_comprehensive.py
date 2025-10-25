"""
Comprehensive Test Suite for Blockchain Forensics Platform

Tests cover:
- API endpoints (unit & integration)
- Models and business logic
- Database operations
- Authentication and authorization
- Alert engine functionality
- Error handling and edge cases
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from app.main import app
from app.models.case import Case, CaseStatus, CasePriority, CaseQuery
from app.models.comment import Comment, CommentStatus
from app.models.user import User, UserRole, UserStatus
from app.models.notification import Notification, NotificationType, NotificationPriority
from app.services.alert_engine import Alert, AlertType, AlertSeverity


class TestCaseManagement:
    """Test case management functionality"""

    def test_create_case(self):
        """Test case creation"""
        case = Case(
            title="Test Investigation",
            description="Test case for blockchain investigation",
            priority=CasePriority.HIGH,
            category="financial_crime"
        )

        assert case.title == "Test Investigation"
        assert case.status == CaseStatus.OPEN
        assert case.priority == CasePriority.HIGH
        assert case.category == "financial_crime"

    def test_case_status_transitions(self):
        """Test valid case status transitions"""
        case = Case(
            title="Test Case",
            description="Test status transitions"
        )

        # Valid transitions
        case.status = CaseStatus.INVESTIGATING
        assert case.status == CaseStatus.INVESTIGATING

        case.status = CaseStatus.PENDING_REVIEW
        assert case.status == CaseStatus.PENDING_REVIEW

        case.status = CaseStatus.CLOSED
        assert case.status == CaseStatus.CLOSED
        assert case.closed_at is not None

    def test_case_evidence_management(self):
        """Test evidence management in cases"""
        from app.models.case import add_evidence, get_case_evidence

        case = Case(title="Evidence Test", description="Test evidence")

        # Add evidence
        evidence = add_evidence(
            case_id=case.id,
            name="Transaction Record",
            description="Blockchain transaction evidence",
            evidence_type="transaction",
            hash_value="abc123"
        )

        assert evidence is not None
        assert evidence.case_id == case.id
        assert evidence.name == "Transaction Record"

        # Get case evidence
        case_evidence = get_case_evidence(case.id)
        assert len(case_evidence) == 1
        assert case_evidence[0].id == evidence.id


class TestCommentSystem:
    """Test comment system functionality"""

    def test_create_comment(self):
        """Test comment creation"""
        comment = Comment(
            entity_type="case",
            entity_id="case_123",
            content="This is a test comment",
            author_id="user_456",
            author_name="Test User"
        )

        assert comment.content == "This is a test comment"
        assert comment.author_id == "user_456"
        assert comment.status == CommentStatus.ACTIVE

    def test_comment_threading(self):
        """Test comment threading functionality"""
        from app.models.comment import create_comment, get_comment_replies

        # Create parent comment
        parent = create_comment(
            entity_type="case",
            entity_id="case_123",
            content="Parent comment",
            author_id="user_1"
        )

        # Create reply
        reply = create_comment(
            entity_type="case",
            entity_id="case_123",
            content="Reply to parent",
            author_id="user_2",
            parent_id=parent.id
        )

        assert reply.parent_id == parent.id
        assert reply.thread_id == parent.id

        # Get replies
        replies = get_comment_replies(parent.id)
        assert len(replies) == 1
        assert replies[0].id == reply.id

    def test_comment_lifecycle(self):
        """Test comment status changes"""
        comment = Comment(
            entity_type="case",
            entity_id="case_123",
            content="Test comment",
            author_id="user_1"
        )

        # Update comment
        from app.models.comment import update_comment
        updated = update_comment(comment.id, "Updated content", "user_1")
        assert updated.content == "Updated content"
        assert updated.edited_at is not None

        # Delete comment
        from app.models.comment import delete_comment
        deleted = delete_comment(comment.id, "user_1")
        assert deleted.status == CommentStatus.DELETED


class TestUserManagement:
    """Test user management functionality"""

    def test_user_creation(self):
        """Test user creation with role assignment"""
        user = User(
            email="test@example.com",
            username="testuser",
            hashed_password="hashed_password",
            role=UserRole.INVESTIGATOR,
            first_name="Test",
            last_name="User"
        )

        assert user.email == "test@example.com"
        assert user.role == UserRole.INVESTIGATOR
        assert user.status == UserStatus.ACTIVE
        assert user.display_name == "Test User"

    def test_user_authentication(self):
        """Test user authentication logic"""
        from app.models.user import authenticate_user

        # Create test user
        user = User(
            email="auth@example.com",
            username="authtest",
            hashed_password="correct_password_hash",
            salt="test_salt"
        )

        # Test correct password
        authenticated = authenticate_user("auth@example.com", "correct_password")
        assert authenticated is not None

        # Test incorrect password
        failed_auth = authenticate_user("auth@example.com", "wrong_password")
        assert failed_auth is None

    def test_user_permissions(self):
        """Test user permission checking"""
        from app.models.user import has_permission

        admin_user = User(
            email="admin@test.com",
            username="admin",
            hashed_password="hash",
            role=UserRole.ADMIN
        )

        investigator_user = User(
            email="investigator@test.com",
            username="investigator",
            hashed_password="hash",
            role=UserRole.INVESTIGATOR
        )

        # Admin should have all permissions
        assert has_permission(admin_user, "case", "delete") == True
        assert has_permission(admin_user, "user", "admin") == True

        # Investigator should not have admin permissions
        assert has_permission(investigator_user, "user", "admin") == False


class TestNotificationSystem:
    """Test notification system"""

    def test_notification_creation(self):
        """Test notification creation"""
        notification = Notification(
            user_id="user_123",
            type=NotificationType.ALERT,
            title="High Risk Alert",
            message="A high-risk address has been detected",
            priority=NotificationPriority.HIGH,
            related_entity_type="alert",
            related_entity_id="alert_456"
        )

        assert notification.user_id == "user_123"
        assert notification.type == NotificationType.ALERT
        assert notification.priority == NotificationPriority.HIGH
        assert notification.is_read == False

    def test_notification_marking(self):
        """Test notification read/unread functionality"""
        from app.models.notification import mark_notification_read, mark_all_notifications_read

        notification = Notification(
            user_id="user_123",
            type=NotificationType.ALERT,
            title="Test Alert",
            message="Test message"
        )

        # Mark as read
        read_notification = mark_notification_read(notification.id, "user_123")
        assert read_notification.is_read == True
        assert read_notification.read_at is not None

        # Mark all as read
        count = mark_all_notifications_read("user_123")
        assert count >= 1


class TestAlertEngine:
    """Test alert engine functionality"""

    def test_alert_creation(self):
        """Test alert creation and properties"""
        alert = Alert(
            alert_type=AlertType.HIGH_RISK_ADDRESS,
            severity=AlertSeverity.HIGH,
            title="High Risk Address Detected",
            description="Address shows suspicious activity",
            metadata={"risk_score": 0.95},
            address="0x123...",
            tx_hash="0xabc..."
        )

        assert alert.alert_type == AlertType.HIGH_RISK_ADDRESS
        assert alert.severity == AlertSeverity.HIGH
        assert alert.acknowledged == False
        assert alert.address == "0x123..."
        assert "alert_" in alert.alert_id

    def test_alert_deduplication(self):
        """Test alert deduplication logic"""
        from app.services.alert_engine import alert_engine

        # Create duplicate event
        event1 = {
            "address": "0x123",
            "risk_score": 0.95,
            "risk_factors": ["Suspicious pattern"]
        }

        event2 = {
            "address": "0x123",
            "risk_score": 0.95,
            "risk_factors": ["Suspicious pattern"]
        }

        # Process events
        alerts1 = asyncio.run(alert_engine.process_event(event1))
        alerts2 = asyncio.run(alert_engine.process_event(event2))

        # Should only create one alert due to deduplication
        assert len(alerts1) == 1
        assert len(alerts2) == 0  # Duplicate suppressed

    def test_alert_acknowledgment(self):
        """Test alert acknowledgment"""
        from app.services.alert_engine import alert_engine

        alert = Alert(
            alert_type=AlertType.LARGE_TRANSFER,
            severity=AlertSeverity.MEDIUM,
            title="Large Transfer",
            description="Large value transfer detected"
        )

        alert_engine.alerts.append(alert)

        # Acknowledge alert
        success = alert_engine.acknowledge_alert(alert.alert_id)
        assert success == True
        assert alert.acknowledged == True

        # Try to acknowledge non-existent alert
        failure = alert_engine.acknowledge_alert("non_existent")
        assert failure == False


class TestAPIEndpoints:
    """Test API endpoints integration"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data

    def test_api_root(self):
        """Test API root endpoint"""
        response = self.client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "Blockchain Forensics Platform" in data["message"]

    def test_comments_api(self):
        """Test comments API endpoints"""
        # Test GET comments (empty)
        response = self.client.get("/api/v1/comments?entity_type=case&entity_id=case_123")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test POST comment
        comment_data = {
            "content": "Test comment via API",
            "is_internal": False,
            "metadata": {}
        }
        response = self.client.post(
            "/api/v1/comments?entity_type=case&entity_id=case_123&author_id=user_123",
            json=comment_data
        )
        assert response.status_code == 201
        comment_response = response.json()
        assert comment_response["content"] == "Test comment via API"
        assert comment_response["entity_id"] == "case_123"

    def test_cases_api(self):
        """Test cases API endpoints"""
        # Test GET cases (empty)
        response = self.client.get("/api/v1/cases")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

        # Test POST case
        case_data = {
            "title": "API Test Case",
            "description": "Testing case creation via API",
            "priority": "high",
            "tags": ["test", "api"],
            "category": "testing"
        }
        response = self.client.post("/api/v1/cases", json=case_data)
        assert response.status_code == 201
        case_response = response.json()
        assert case_response["title"] == "API Test Case"
        assert case_response["priority"] == "high"


class TestDatabaseIntegration:
    """Test database operations (when DB is available)"""

    @pytest.mark.skip(reason="Database integration tests require running DB")
    def test_postgres_connection(self):
        """Test PostgreSQL connection and operations"""
        # This would test actual database operations
        # when PostgreSQL is available in test environment
        pass

    @pytest.mark.skip(reason="Neo4j integration tests require running graph DB")
    def test_neo4j_connection(self):
        """Test Neo4j connection and graph operations"""
        # This would test actual graph database operations
        pass


class TestErrorHandling:
    """Test error handling and edge cases"""

    def test_404_errors(self):
        """Test 404 error responses"""
        client = TestClient(app)

        # Test non-existent endpoints
        response = client.get("/api/v1/non-existent")
        assert response.status_code == 404

        response = client.get("/api/v1/cases/non-existent-id")
        assert response.status_code == 404

    def test_validation_errors(self):
        """Test input validation errors"""
        client = TestClient(app)

        # Test invalid case creation
        invalid_case = {
            "title": "",  # Empty title should fail
            "description": "Test"
        }
        response = client.post("/api/v1/cases", json=invalid_case)
        assert response.status_code == 422  # Validation error

    def test_authentication_errors(self):
        """Test authentication and authorization errors"""
        client = TestClient(app)

        # Test accessing protected endpoint without auth
        response = client.get("/api/v1/users/me")
        assert response.status_code == 401  # Unauthorized

        # Test accessing admin endpoint without admin role
        response = client.get("/api/v1/admin/users")
        assert response.status_code == 403  # Forbidden


class TestPerformance:
    """Performance and load testing"""

    def test_large_dataset_handling(self):
        """Test handling of large datasets"""
        from app.models.case import query_cases

        # Create many test cases
        for i in range(100):
            Case(
                title=f"Performance Test Case {i}",
                description=f"Testing performance with case {i}",
                priority=CasePriority.MEDIUM
            )

        # Test query performance
        query = CaseQuery(limit=50, offset=0)
        results = query_cases(query)

        assert len(results) <= 50  # Pagination working
        assert all(isinstance(case, Case) for case in results)

    def test_concurrent_operations(self):
        """Test concurrent operations"""
        import threading

        results = []
        errors = []

        def create_case_worker(case_id):
            try:
                case = Case(
                    title=f"Concurrent Test {case_id}",
                    description=f"Testing concurrent creation {case_id}"
                )
                results.append(case.id)
            except Exception as e:
                errors.append(str(e))

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_case_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        assert len(errors) == 0  # No errors occurred
        assert len(results) == 10  # All cases created


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
