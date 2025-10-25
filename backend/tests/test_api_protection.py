"""
API Protection Tests
Testet die neuen Plan-based und Org-based Guards
"""

import pytest
from fastapi import HTTPException
from app.auth.dependencies import has_plan, require_admin
from app.auth.models import UserRole
from app.utils.auth_helpers import require_org_ownership, is_resource_accessible


class TestPlanHierarchy:
    """Test Plan-Hierarchie"""
    
    def test_has_plan_community(self):
        """Community user hat Zugriff auf Community Features"""
        user = {"user_id": "test", "plan": "community", "role": "viewer"}
        assert has_plan(user, "community") is True
    
    def test_has_plan_pro_vs_community(self):
        """Pro user hat Zugriff auf Community Features"""
        user = {"user_id": "test", "plan": "pro", "role": "viewer"}
        assert has_plan(user, "community") is True
    
    def test_has_plan_community_vs_pro(self):
        """Community user hat KEINEN Zugriff auf Pro Features"""
        user = {"user_id": "test", "plan": "community", "role": "viewer"}
        assert has_plan(user, "pro") is False
    
    def test_has_plan_enterprise_all(self):
        """Enterprise user hat Zugriff auf alle Features"""
        user = {"user_id": "test", "plan": "enterprise", "role": "viewer"}
        assert has_plan(user, "community") is True
        assert has_plan(user, "pro") is True
        assert has_plan(user, "plus") is True
        assert has_plan(user, "enterprise") is True
    
    def test_has_plan_invalid_plan(self):
        """Ungültiger Plan gibt False zurück"""
        user = {"user_id": "test", "plan": "invalid", "role": "viewer"}
        assert has_plan(user, "pro") is False


class TestOrgOwnership:
    """Test Org-Isolation"""
    
    def test_require_org_ownership_same_org(self):
        """User hat Zugriff auf eigene Org-Resources"""
        # Should not raise
        require_org_ownership("org_123", "org_123")
    
    def test_require_org_ownership_different_org(self):
        """User hat KEINEN Zugriff auf fremde Org-Resources"""
        with pytest.raises(HTTPException) as exc:
            require_org_ownership("org_123", "org_456")
        assert exc.value.status_code == 403
    
    def test_require_org_ownership_no_user_org(self):
        """User ohne Org hat keinen Zugriff"""
        with pytest.raises(HTTPException) as exc:
            require_org_ownership("org_123", None)
        assert exc.value.status_code == 403
    
    def test_require_org_ownership_both_none(self):
        """Single-user accounts (beide None) erlaubt"""
        # Should not raise
        require_org_ownership(None, None)


class TestResourceAccessibility:
    """Test is_resource_accessible Logic"""
    
    def test_admin_has_access(self):
        """Admin hat immer Zugriff"""
        assert is_resource_accessible(
            resource_org_id="org_123",
            resource_created_by="other_user",
            user_org_id="org_456",
            user_id="admin_user",
            user_role="admin"
        ) is True
    
    def test_creator_has_access(self):
        """Creator hat Zugriff auf eigene Resources"""
        assert is_resource_accessible(
            resource_org_id="org_123",
            resource_created_by="user_1",
            user_org_id="org_456",
            user_id="user_1",
            user_role="viewer"
        ) is True
    
    def test_org_member_has_access(self):
        """Org-Mitglied hat Zugriff auf Org-Resources"""
        assert is_resource_accessible(
            resource_org_id="org_123",
            resource_created_by="other_user",
            user_org_id="org_123",
            user_id="user_1",
            user_role="viewer"
        ) is True
    
    def test_no_access(self):
        """User ohne Rechte hat keinen Zugriff"""
        assert is_resource_accessible(
            resource_org_id="org_123",
            resource_created_by="other_user",
            user_org_id="org_456",
            user_id="user_1",
            user_role="viewer"
        ) is False


class TestAdminAccess:
    """Test Admin-only Access"""
    
    @pytest.mark.asyncio
    async def test_require_admin_admin_user(self):
        """Admin User hat Zugriff"""
        admin_user = {"user_id": "admin", "role": UserRole.ADMIN.value}
        result = require_admin(admin_user)
        assert result == admin_user
    
    @pytest.mark.asyncio
    async def test_require_admin_non_admin(self):
        """Nicht-Admin User hat keinen Zugriff"""
        regular_user = {"user_id": "user", "role": UserRole.VIEWER.value}
        with pytest.raises(HTTPException) as exc:
            require_admin(regular_user)
        assert exc.value.status_code == 403


@pytest.mark.asyncio
class TestPlanGuardsIntegration:
    """Integration Tests für Plan-Guards (benötigen FastAPI TestClient)"""
    
    async def test_community_can_access_trace(self, test_client):
        """Community user kann Trace nutzen"""
        # Simplified test - würde in Praxis JWT Token erstellen
        # Dieser Test ist ein Placeholder für echte Integration-Tests
        pass
    
    async def test_community_cannot_access_pro_features(self, test_client):
        """Community user kann Pro-Features NICHT nutzen"""
        # Simplified test
        pass


# Fixtures für Integration-Tests
@pytest.fixture
def test_client():
    """FastAPI TestClient Fixture"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
