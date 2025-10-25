"""
Feature Access End-to-End Tests
Tests für Plan-basierte Zugriffskontrolle über alle Module hinweg
"""
import pytest
from unittest.mock import patch
from fastapi import HTTPException

from app.models.user import User, SubscriptionPlan, SubscriptionStatus


@pytest.fixture
def community_user():
    """User mit Community Plan (kostenlos)"""
    return User(
        id="community-123",
        email="community@example.com",
        plan=SubscriptionPlan.COMMUNITY,
        subscription_status=SubscriptionStatus.ACTIVE,
        role="user"
    )


@pytest.fixture
def pro_user():
    """User mit Pro Plan ($49/mo)"""
    return User(
        id="pro-123",
        email="pro@example.com",
        plan=SubscriptionPlan.PRO,
        subscription_status=SubscriptionStatus.ACTIVE,
        subscription_id="sub_pro123",
        role="user"
    )


@pytest.fixture
def plus_user():
    """User mit Plus Plan ($199/mo)"""
    return User(
        id="plus-123",
        email="plus@example.com",
        plan=SubscriptionPlan.PLUS,
        subscription_status=SubscriptionStatus.ACTIVE,
        subscription_id="sub_plus123",
        role="user"
    )


@pytest.fixture
def admin_user():
    """Admin User (volle Rechte)"""
    return User(
        id="admin-123",
        email="admin@example.com",
        plan=SubscriptionPlan.ENTERPRISE,
        subscription_status=SubscriptionStatus.ACTIVE,
        role="admin"
    )


# ============================================================================
# TEST SUITE 1: Transaction Tracing Access
# ============================================================================

@pytest.mark.asyncio
async def test_community_user_can_trace_basic(community_user):
    """Community User kann Basic Tracing (depth=2)"""
    from app.services.trace_service import trace_service
    
    result = await trace_service.trace_forward(
        chain="ethereum",
        address="0x123",
        max_depth=2,
        user=community_user
    )
    
    # Community: max_depth automatisch auf 2 limitiert
    assert result['max_depth_used'] <= 2
    assert result['status'] == 'success'


@pytest.mark.asyncio
async def test_community_user_blocked_deep_trace(community_user):
    """Community User blockiert bei tieferem Tracing"""
    from app.services.trace_service import trace_service
    
    with pytest.raises(HTTPException) as exc_info:
        await trace_service.trace_forward(
            chain="ethereum",
            address="0x123",
            max_depth=5,  # Requires Pro+
            user=community_user
        )
    
    assert exc_info.value.status_code == 403
    assert "upgrade" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_pro_user_can_trace_deeper(pro_user):
    """Pro User kann tieferes Tracing (depth=5)"""
    from app.services.trace_service import trace_service
    
    result = await trace_service.trace_forward(
        chain="ethereum",
        address="0x123",
        max_depth=5,
        user=pro_user
    )
    
    assert result['max_depth_used'] <= 5
    assert result['status'] == 'success'


# ============================================================================
# TEST SUITE 2: Case Management Access
# ============================================================================

@pytest.mark.asyncio
async def test_community_user_can_create_cases(community_user):
    """Community User kann Cases erstellen"""
    from app.services.case_service import case_service
    
    result = await case_service.create_case(
        user=community_user,
        title="Test Case",
        description="Community test"
    )
    
    assert result['status'] == 'created'
    assert result['plan_tier'] == 'community'


@pytest.mark.asyncio
async def test_community_user_limited_cases(community_user):
    """Community User hat Case-Limit (z.B. 10)"""
    from app.services.case_service import case_service
    
    # Mock: User hat bereits 10 Cases
    with patch.object(case_service, 'count_user_cases', return_value=10):
        with pytest.raises(HTTPException) as exc_info:
            await case_service.create_case(
                user=community_user,
                title="Case #11",
                description="Over limit"
            )
        
        assert exc_info.value.status_code == 403
        assert "limit reached" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_pro_user_higher_case_limit(pro_user):
    """Pro User hat höheres Case-Limit (z.B. 100)"""
    from app.services.case_service import case_service
    
    # Mock: User hat 50 Cases
    with patch.object(case_service, 'count_user_cases', return_value=50):
        result = await case_service.create_case(
            user=pro_user,
            title="Case #51",
            description="Pro can create more"
        )
        
        assert result['status'] == 'created'


# ============================================================================
# TEST SUITE 3: Investigator (Graph Explorer) Access
# ============================================================================

@pytest.mark.asyncio
async def test_community_user_blocked_investigator(community_user):
    """Community User blockiert bei Investigator"""
    from app.api.v1.investigator import get_relationship_graph
    
    with pytest.raises(HTTPException) as exc_info:
        await get_relationship_graph(
            address="0x123",
            chain="ethereum",
            depth=2,
            current_user=community_user
        )
    
    assert exc_info.value.status_code == 403
    assert "pro" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_pro_user_can_use_investigator(pro_user):
    """Pro User kann Investigator nutzen"""
    from app.api.v1.investigator import get_relationship_graph
    
    with patch('app.services.graph_service.build_relationship_graph') as mock_graph:
        mock_graph.return_value = {'nodes': [], 'edges': []}
        
        result = await get_relationship_graph(
            address="0x123",
            chain="ethereum",
            depth=2,
            current_user=pro_user
        )
        
        assert 'nodes' in result
        assert 'edges' in result


# ============================================================================
# TEST SUITE 4: Correlation Engine Access
# ============================================================================

@pytest.mark.asyncio
async def test_community_user_blocked_correlation(community_user):
    """Community User blockiert bei Correlation"""
    from app.api.v1.correlation import detect_patterns
    
    with pytest.raises(HTTPException) as exc_info:
        await detect_patterns(
            addresses=["0x123", "0x456"],
            chain="ethereum",
            current_user=community_user
        )
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_pro_user_can_use_correlation(pro_user):
    """Pro User kann Correlation nutzen"""
    from app.api.v1.correlation import detect_patterns
    
    with patch('app.services.correlation_service.detect_patterns') as mock_corr:
        mock_corr.return_value = {'patterns': []}
        
        result = await detect_patterns(
            addresses=["0x123", "0x456"],
            chain="ethereum",
            current_user=pro_user
        )
        
        assert 'patterns' in result


# ============================================================================
# TEST SUITE 5: AI Agent Access
# ============================================================================

@pytest.mark.asyncio
async def test_community_user_blocked_ai_agent(community_user):
    """Community/Pro User blockiert bei AI Agent"""
    from app.api.v1.ai_agent import chat
    
    with pytest.raises(HTTPException) as exc_info:
        await chat(
            message="Analyze 0x123",
            current_user=community_user
        )
    
    assert exc_info.value.status_code == 403
    assert "plus" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_pro_user_also_blocked_ai_agent(pro_user):
    """Auch Pro User blockiert (AI Agent requires Plus+)"""
    from app.api.v1.ai_agent import chat
    
    with pytest.raises(HTTPException) as exc_info:
        await chat(
            message="Analyze 0x123",
            current_user=pro_user
        )
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_plus_user_can_use_ai_agent(plus_user):
    """Plus User kann AI Agent nutzen"""
    from app.api.v1.ai_agent import chat
    
    with patch('app.ai_agents.agent.ForensicAgent.chat') as mock_chat:
        mock_chat.return_value = {'answer': 'Analysis complete'}
        
        result = await chat(
            message="Analyze 0x123",
            current_user=plus_user
        )
        
        assert 'answer' in result


# ============================================================================
# TEST SUITE 6: Admin Features Access
# ============================================================================

@pytest.mark.asyncio
async def test_regular_user_blocked_analytics(pro_user):
    """Regular User (auch Pro/Plus) blockiert bei Analytics"""
    from app.api.v1.analytics import get_trend_data
    
    with pytest.raises(HTTPException) as exc_info:
        await get_trend_data(
            timeframe="7d",
            current_user=pro_user
        )
    
    assert exc_info.value.status_code == 403
    assert "admin" in str(exc_info.value.detail).lower()


@pytest.mark.asyncio
async def test_admin_can_access_analytics(admin_user):
    """Admin kann Analytics nutzen"""
    from app.api.v1.analytics import get_trend_data
    
    with patch('app.services.analytics_service.get_trends') as mock_trends:
        mock_trends.return_value = {'trends': []}
        
        result = await get_trend_data(
            timeframe="7d",
            current_user=admin_user
        )
        
        assert 'trends' in result


@pytest.mark.asyncio
async def test_regular_user_blocked_monitoring(plus_user):
    """Plus User blockiert bei Monitoring"""
    from app.api.v1.monitoring import get_system_health
    
    with pytest.raises(HTTPException) as exc_info:
        await get_system_health(current_user=plus_user)
    
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_admin_can_access_monitoring(admin_user):
    """Admin kann Monitoring nutzen"""
    from app.api.v1.monitoring import get_system_health
    
    with patch('app.services.monitoring_service.get_health') as mock_health:
        mock_health.return_value = {'status': 'healthy'}
        
        result = await get_system_health(current_user=admin_user)
        
        assert result['status'] == 'healthy'


# ============================================================================
# TEST SUITE 7: Cross-Module Integration
# ============================================================================

@pytest.mark.asyncio
async def test_pro_user_full_workflow(pro_user):
    """Pro User kann kompletten Workflow ausführen"""
    from app.services.trace_service import trace_service
    from app.services.case_service import case_service
    from app.api.v1.investigator import get_relationship_graph
    
    # 1. Trace Transaction
    trace_result = await trace_service.trace_forward(
        chain="ethereum",
        address="0x123",
        max_depth=5,
        user=pro_user
    )
    assert trace_result['status'] == 'success'
    
    # 2. Create Case
    case_result = await case_service.create_case(
        user=pro_user,
        title="Investigation",
        description="Trace results"
    )
    assert case_result['status'] == 'created'
    
    # 3. Use Investigator
    with patch('app.services.graph_service.build_relationship_graph') as mock_graph:
        mock_graph.return_value = {'nodes': [], 'edges': []}
        
        graph_result = await get_relationship_graph(
            address="0x123",
            chain="ethereum",
            depth=2,
            current_user=pro_user
        )
        assert 'nodes' in graph_result


@pytest.mark.asyncio
async def test_community_user_partial_workflow(community_user):
    """Community User kann nur Basic-Workflow"""
    from app.services.trace_service import trace_service
    from app.services.case_service import case_service
    from app.api.v1.investigator import get_relationship_graph
    
    # 1. Basic Trace (OK)
    trace_result = await trace_service.trace_forward(
        chain="ethereum",
        address="0x123",
        max_depth=2,
        user=community_user
    )
    assert trace_result['status'] == 'success'
    
    # 2. Create Case (OK)
    case_result = await case_service.create_case(
        user=community_user,
        title="Basic Investigation",
        description="Community trace"
    )
    assert case_result['status'] == 'created'
    
    # 3. Investigator (BLOCKED)
    with pytest.raises(HTTPException) as exc_info:
        await get_relationship_graph(
            address="0x123",
            chain="ethereum",
            depth=2,
            current_user=community_user
        )
    assert exc_info.value.status_code == 403


# ============================================================================
# TEST SUITE 8: Plan Hierarchy Validation
# ============================================================================

def test_plan_hierarchy():
    """Test Plan-Hierarchie ist korrekt"""
    from app.auth.plan_gates import is_plan_sufficient
    
    # Community < Pro
    assert is_plan_sufficient(
        required=SubscriptionPlan.COMMUNITY,
        user_plan=SubscriptionPlan.PRO
    )
    
    # Pro < Plus
    assert is_plan_sufficient(
        required=SubscriptionPlan.PRO,
        user_plan=SubscriptionPlan.PLUS
    )
    
    # Plus > Pro (FAIL)
    assert not is_plan_sufficient(
        required=SubscriptionPlan.PLUS,
        user_plan=SubscriptionPlan.PRO
    )
    
    # Enterprise >= alle
    assert is_plan_sufficient(
        required=SubscriptionPlan.PRO,
        user_plan=SubscriptionPlan.ENTERPRISE
    )


# ============================================================================
# SUMMARY
# ============================================================================
"""
Test Coverage:
✅ Transaction Tracing (Community: depth 2, Pro: depth 5)
✅ Case Management (Community: limited, Pro: more)
✅ Investigator (Pro+)
✅ Correlation (Pro+)
✅ AI Agent (Plus+)
✅ Analytics (Admin only)
✅ Monitoring (Admin only)
✅ Cross-Module Workflows (Pro full, Community partial)
✅ Plan Hierarchy Validation

Total: 20 Tests für Feature Access E2E
Status: KRITISCH für SaaS-Verifikation ✅
"""
