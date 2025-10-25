from __future__ import annotations
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field
from datetime import datetime

from app.security.security_enhancements import (
    kms, rbac, soc2_controls,
    UserRole, Permission, SecurityPolicy
)

router = APIRouter()


# Mock user dependency for demo
async def get_current_user() -> str:
    """Mock user - in real implementation, get from auth"""
    return "user_123"


class EncryptDataRequest(BaseModel):
    data: str = Field(..., description="Data to encrypt (base64 encoded)")
    key_id: str = Field(..., description="Encryption key ID")


class DecryptDataRequest(BaseModel):
    encrypted_data: str = Field(..., description="Encrypted data (base64 encoded)")
    key_id: str = Field(..., description="Decryption key ID")


class CreatePolicyRequest(BaseModel):
    policy_id: str = Field(..., description="Policy ID")
    name: str = Field(..., description="Policy name")
    description: str = Field(..., description="Policy description")
    roles: List[str] = Field(..., description="Allowed roles")
    permissions: List[str] = Field(..., description="Granted permissions")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Policy conditions")


class AssignRoleRequest(BaseModel):
    user_id: str = Field(..., description="User ID")
    role: str = Field(..., description="Role to assign")


@router.post("/kms/keys", tags=["Security Enhancements"])
async def create_encryption_key(
    key_id: str = Query(..., description="Key ID to create"),
    current_user: str = Depends(get_current_user)
):
    """Create a new encryption key"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        key = await kms.create_key(key_id)
        return {
            "key_id": key.key_id,
            "algorithm": key.algorithm,
            "created_at": key.created_at.isoformat(),
            "expires_at": key.expires_at.isoformat() if key.expires_at else None,
            "status": "created"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key creation failed: {str(e)}")


@router.post("/kms/encrypt", tags=["Security Enhancements"])
async def encrypt_data(
    req: EncryptDataRequest,
    current_user: str = Depends(get_current_user)
):
    """Encrypt data with specified key"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.WRITE_EVIDENCE):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        import base64
        data_bytes = base64.b64decode(req.data)
        encrypted = await kms.encrypt_data(data_bytes, req.key_id)

        if encrypted is None:
            raise HTTPException(status_code=404, detail="Key not found")

        encrypted_b64 = base64.b64encode(encrypted).decode()
        return {"encrypted_data": encrypted_b64}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Encryption failed: {str(e)}")


@router.post("/kms/decrypt", tags=["Security Enhancements"])
async def decrypt_data(
    req: DecryptDataRequest,
    current_user: str = Depends(get_current_user)
):
    """Decrypt data with specified key"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.READ_EVIDENCE):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        import base64
        encrypted_bytes = base64.b64decode(req.encrypted_data)
        decrypted = await kms.decrypt_data(encrypted_bytes, req.key_id)

        if decrypted is None:
            raise HTTPException(status_code=400, detail="Decryption failed")

        decrypted_b64 = base64.b64encode(decrypted).decode()
        return {"decrypted_data": decrypted_b64}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decryption failed: {str(e)}")


@router.post("/kms/rotate", tags=["Security Enhancements"])
async def rotate_key(
    key_id: str = Query(..., description="Key ID to rotate"),
    current_user: str = Depends(get_current_user)
):
    """Rotate an encryption key"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        new_key = await kms.rotate_key(key_id)
        if not new_key:
            raise HTTPException(status_code=404, detail="Key not found")

        return {
            "old_key_id": key_id,
            "new_key_id": new_key.key_id,
            "status": "rotated"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key rotation failed: {str(e)}")


@router.get("/kms/audit", tags=["Security Enhancements"])
async def get_kms_audit_log(
    limit: int = Query(100, ge=1, le=1000),
    current_user: str = Depends(get_current_user)
):
    """Get KMS audit log"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.AUDIT_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        audit_log = kms.get_audit_log(limit)
        return {"audit_events": audit_log}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audit retrieval failed: {str(e)}")


@router.post("/rbac/policies", tags=["Security Enhancements"])
async def create_policy(
    req: CreatePolicyRequest,
    current_user: str = Depends(get_current_user)
):
    """Create a new security policy"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        roles = {UserRole(role) for role in req.roles}
        permissions = {Permission(perm) for perm in req.permissions}

        policy = SecurityPolicy(
            policy_id=req.policy_id,
            name=req.name,
            description=req.description,
            roles=roles,
            permissions=permissions,
            conditions=req.conditions
        )

        rbac.add_policy(policy)
        return {"status": "Policy created", "policy_id": req.policy_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy creation failed: {str(e)}")


@router.get("/rbac/policies", tags=["Security Enhancements"])
async def list_policies(current_user: str = Depends(get_current_user)):
    """List all security policies"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        policies = rbac.list_policies()
        return {"policies": policies}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Policy listing failed: {str(e)}")


@router.post("/rbac/assign-role", tags=["Security Enhancements"])
async def assign_user_role(
    req: AssignRoleRequest,
    current_user: str = Depends(get_current_user)
):
    """Assign role to user"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        role = UserRole(req.role)
        rbac.assign_role(req.user_id, role)
        return {"status": "Role assigned", "user_id": req.user_id, "role": req.role}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Role assignment failed: {str(e)}")


@router.get("/rbac/user/{user_id}/permissions", tags=["Security Enhancements"])
async def get_user_permissions(
    user_id: str,
    current_user: str = Depends(get_current_user)
):
    """Get permissions for a user"""
    try:
        # Check permission (user can check their own, admin can check anyone's)
        if current_user != user_id and not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        permissions = rbac.get_user_permissions(user_id)
        role = rbac.get_user_role(user_id)

        return {
            "user_id": user_id,
            "role": role.value if role else None,
            "permissions": [p.value for p in permissions]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permission retrieval failed: {str(e)}")


@router.post("/rbac/check", tags=["Security Enhancements"])
async def check_permission(
    user_id: str = Query(..., description="User ID"),
    permission: str = Query(..., description="Permission to check"),
    context: Dict[str, Any] = None,
    current_user: str = Depends(get_current_user)
):
    """Check if user has permission"""
    try:
        # Check permission to perform this check
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        perm = Permission(permission)
        has_permission = rbac.check_permission(user_id, perm, context)

        return {
            "user_id": user_id,
            "permission": permission,
            "has_permission": has_permission
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Permission check failed: {str(e)}")


@router.get("/soc2/assessment", tags=["Security Enhancements"])
async def run_soc2_assessment(current_user: str = Depends(get_current_user)):
    """Run SOC2 security assessment"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.AUDIT_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        assessment = await soc2_controls.run_security_assessment()
        return {"assessment": assessment}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Assessment failed: {str(e)}")


@router.post("/maintenance/cleanup", tags=["Security Enhancements"])
async def run_maintenance_cleanup(current_user: str = Depends(get_current_user)):
    """Run maintenance cleanup tasks"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        # Run cleanup tasks
        await kms.cleanup_expired_keys()

        return {"status": "Maintenance cleanup completed"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Maintenance failed: {str(e)}")


@router.get("/stats", tags=["Security Enhancements"])
async def get_security_stats(current_user: str = Depends(get_current_user)):
    """Get security system statistics"""
    try:
        # Check permission
        if not rbac.check_permission(current_user, Permission.ADMIN_ACCESS):
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        stats = {
            "kms": {
                "active_keys": len([k for k in kms.keys.values() if k.is_active]),
                "total_keys": len(kms.keys),
                "audit_events": len(kms.audit_log)
            },
            "rbac": {
                "policies": len(rbac.policies),
                "assigned_users": len(rbac.user_roles),
                "roles": [r.value for r in UserRole]
            },
            "permissions": [p.value for p in Permission],
            "timestamp": datetime.now().isoformat()
        }
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats retrieval failed: {str(e)}")
