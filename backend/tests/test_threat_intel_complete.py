"""
Comprehensive Tests for Threat Intelligence System
==================================================

Tests for the complete threat intelligence system including:
- Dark web monitoring
- Intel sharing network
- Threat intelligence service
- Community reports
"""
import pytest
import asyncio
from datetime import datetime
from app.intel.service import ThreatIntelService, get_threat_intel_service
from app.intel.darkweb import DarkWebMonitor, DarkWebIntelStore
from app.intel.sharing import IntelSharingNetwork
from app.intel.models import (
    ThreatIntelItem,
    ThreatLevel,
    IntelCategory,
    IntelSource,
    IntelStatus,
    IntelQuery
)


class TestThreatIntelService:
    """Tests for ThreatIntelService"""
    
    @pytest.fixture
    def service(self):
        return ThreatIntelService()
    
    @pytest.mark.asyncio
    async def test_initialize(self, service):
        """Test service initialization"""
        await service.initialize()
        
        assert len(service.threat_feeds) > 0
        assert "cryptoscamdb" in service.threat_feeds
        assert "chainabuse" in service.threat_feeds
    
    @pytest.mark.asyncio
    async def test_store_intel_items(self, service):
        """Test storing intelligence items with deduplication"""
        items = [
            ThreatIntelItem(
                chain="ethereum",
                address="0x1234567890abcdef1234567890abcdef12345678",
                threat_level=ThreatLevel.HIGH,
                category=IntelCategory.SCAM,
                source=IntelSource.OSINT,
                confidence=0.9,
                title="Scam address"
            ),
            # Duplicate
            ThreatIntelItem(
                chain="ethereum",
                address="0x1234567890abcdef1234567890abcdef12345678",
                threat_level=ThreatLevel.HIGH,
                category=IntelCategory.SCAM,
                source=IntelSource.OSINT,
                confidence=0.9,
                title="Scam address"
            ),
            # Different address
            ThreatIntelItem(
                chain="ethereum",
                address="0xabcdefabcdefabcdefabcdefabcdefabcdefabcd",
                threat_level=ThreatLevel.MEDIUM,
                category=IntelCategory.PHISHING,
                source=IntelSource.COMMUNITY,
                confidence=0.7,
                title="Phishing address"
            )
        ]
        
        stored = await service._store_intel_items(items)
        
        assert stored == 2  # Only 2 unique items
        assert len(service.intel_items) == 2
    
    @pytest.mark.asyncio
    async def test_enrich_address_no_matches(self, service):
        """Test enriching address with no intelligence"""
        result = await service.enrich_address(
            chain="ethereum",
            address="0x0000000000000000000000000000000000000000"
        )
        
        assert result.threat_score == 0.0
        assert result.confidence == 0.0
        assert result.recommended_action == "allow"
        assert len(result.matches) == 0
    
    @pytest.mark.asyncio
    async def test_enrich_address_with_matches(self, service):
        """Test enriching address with intelligence matches"""
        # Store test intel
        test_item = ThreatIntelItem(
            chain="ethereum",
            address="0x1234567890abcdef1234567890abcdef12345678",
            threat_level=ThreatLevel.CRITICAL,
            category=IntelCategory.RANSOMWARE,
            source=IntelSource.LAW_ENFORCEMENT,
            confidence=0.95,
            title="Known ransomware address",
            status=IntelStatus.ACTIVE
        )
        
        await service._store_intel_items([test_item])
        
        # Enrich the address
        result = await service.enrich_address(
            chain="ethereum",
            address="0x1234567890abcdef1234567890abcdef12345678"
        )
        
        assert result.threat_score > 0.8  # High threat
        assert result.confidence == 0.95
        assert result.recommended_action == "block"
        assert len(result.matches) == 1
        assert result.highest_threat_level == ThreatLevel.CRITICAL
        assert "ransomware" in [cat.lower() for cat in result.risk_factors[0].lower().split()]
    
    @pytest.mark.asyncio
    async def test_submit_community_report(self, service):
        """Test submitting community intelligence report"""
        report = await service.submit_community_report(
            reporter_id="user_123",
            chain="ethereum",
            address="0xabcdef1234567890abcdef1234567890abcdef12",
            category=IntelCategory.SCAM,
            threat_level=ThreatLevel.HIGH,
            title="Ponzi scheme",
            description="This address is running a ponzi scheme",
            evidence={"transactions": ["0xtxhash"]}
        )
        
        assert report.reporter_id == "user_123"
        assert report.status == IntelStatus.PENDING
        assert report.chain == "ethereum"
        assert len(service.community_reports) == 1
    
    @pytest.mark.asyncio
    async def test_query_intelligence(self, service):
        """Test querying intelligence"""
        # Store test data
        items = [
            ThreatIntelItem(
                chain="ethereum",
                address="0x1111111111111111111111111111111111111111",
                threat_level=ThreatLevel.HIGH,
                category=IntelCategory.SCAM,
                source=IntelSource.OSINT,
                confidence=0.9,
                title="Scam 1"
            ),
            ThreatIntelItem(
                chain="bitcoin",
                address="bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh",
                threat_level=ThreatLevel.CRITICAL,
                category=IntelCategory.RANSOMWARE,
                source=IntelSource.DARK_WEB,
                confidence=0.95,
                title="Ransomware payment"
            )
        ]
        
        await service._store_intel_items(items)
        
        # Query by chain
        query = IntelQuery(chains=["ethereum"])
        results = await service.query_intelligence(query)
        
        assert len(results) == 1
        assert results[0].chain == "ethereum"
        
        # Query by category
        query = IntelQuery(categories=[IntelCategory.RANSOMWARE])
        results = await service.query_intelligence(query)
        
        assert len(results) == 1
        assert results[0].category == IntelCategory.RANSOMWARE
        
        # Query by threat level
        query = IntelQuery(threat_levels=[ThreatLevel.CRITICAL])
        results = await service.query_intelligence(query)
        
        assert len(results) == 1
        assert results[0].threat_level == ThreatLevel.CRITICAL
    
    @pytest.mark.asyncio
    async def test_get_statistics(self, service):
        """Test getting statistics"""
        # Store test data
        items = [
            ThreatIntelItem(
                chain="ethereum",
                address=f"0x{i:040x}",
                threat_level=ThreatLevel.HIGH,
                category=IntelCategory.SCAM,
                source=IntelSource.OSINT,
                confidence=0.8,
                title=f"Scam {i}",
                status=IntelStatus.ACTIVE
            )
            for i in range(5)
        ]
        
        await service._store_intel_items(items)
        
        stats = await service.get_statistics()
        
        assert stats.total_items == 5
        assert stats.by_category[IntelCategory.SCAM] == 5
        assert stats.by_source[IntelSource.OSINT] == 5
        assert stats.avg_confidence == 0.8


class TestDarkWebMonitor:
    """Tests for Dark Web Monitoring"""
    
    @pytest.fixture
    def monitor(self):
        return DarkWebMonitor()
    
    @pytest.fixture
    def store(self):
        return DarkWebIntelStore()
    
    @pytest.mark.asyncio
    async def test_monitor_marketplaces(self, monitor):
        """Test marketplace monitoring"""
        intel = await monitor.monitor_marketplaces()
        
        # Should return simulated results
        assert isinstance(intel, list)
    
    @pytest.mark.asyncio
    async def test_monitor_forums(self, monitor):
        """Test forum monitoring"""
        intel = await monitor.monitor_forums()
        
        assert isinstance(intel, list)
    
    @pytest.mark.asyncio
    async def test_extract_iocs(self, monitor):
        """Test IOC extraction"""
        text = """
        Send payment to bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh
        Contact: attacker@evil.onion
        Visit: http://darkmarket.onion
        Ethereum: 0x742d35Cc6634C0532925a3b844Bc454e4438f44e
        IP: 192.168.1.1
        """
        
        iocs = await monitor.extract_iocs(text)
        
        assert len(iocs["bitcoin_addresses"]) > 0
        assert len(iocs["ethereum_addresses"]) > 0
        assert len(iocs["domains"]) > 0
        assert len(iocs["emails"]) > 0
        assert len(iocs["ipv4_addresses"]) > 0
    
    @pytest.mark.asyncio
    async def test_run_full_scan(self, monitor):
        """Test full monitoring scan"""
        results = await monitor.run_full_scan()
        
        assert "total_items" in results
        assert "marketplaces_monitored" in results
        assert "forums_monitored" in results
        assert "unique_addresses" in results
    
    @pytest.mark.asyncio
    async def test_store_and_search(self, monitor, store):
        """Test storing and searching dark web intel"""
        # Run scan
        results = await monitor.run_full_scan()
        items = results.get("items", [])
        
        # Store items
        stored = await store.store(items)
        assert stored >= 0
        
        # Search by category
        search_results = await store.search(category=IntelCategory.RANSOMWARE)
        assert isinstance(search_results, list)


class TestIntelSharingNetwork:
    """Tests for Intelligence Sharing Network"""
    
    @pytest.fixture
    def network(self):
        return IntelSharingNetwork("test_network")
    
    def test_register_organization(self, network):
        """Test registering organization"""
        org = network.register_organization(
            org_id="org_test",
            name="Test Organization",
            org_type="private"
        )
        
        assert org.org_id == "org_test"
        assert org.name == "Test Organization"
        assert org.trust_score == 0.5  # Initial score
    
    @pytest.mark.asyncio
    async def test_share_intelligence_broadcast(self, network):
        """Test broadcasting intelligence"""
        # Register org
        network.register_organization("org_sender", "Sender Org", "private")
        
        # Share intel
        message = await network.share_intelligence(
            sender_org="org_sender",
            threat_level=ThreatLevel.HIGH,
            category=IntelCategory.SCAM,
            title="New scam detected",
            description="Large-scale scam operation",
            indicators={"ethereum_addresses": ["0x1234..."]},
            recipient_orgs=None  # Broadcast
        )
        
        assert message is not None
        assert message.sender_org == "org_sender"
        assert message.threat_level == ThreatLevel.HIGH
        assert len(message.recipient_orgs) == 0  # Broadcast
    
    @pytest.mark.asyncio
    async def test_share_intelligence_targeted(self, network):
        """Test targeted intelligence sharing"""
        # Register orgs
        network.register_organization("org_sender", "Sender", "private")
        network.register_organization("org_recipient", "Recipient", "private")
        
        # Share to specific recipient
        message = await network.share_intelligence(
            sender_org="org_sender",
            threat_level=ThreatLevel.CRITICAL,
            category=IntelCategory.RANSOMWARE,
            title="Ransomware alert",
            description="Active ransomware campaign",
            indicators={"bitcoin_addresses": ["bc1q..."]},
            recipient_orgs=["org_recipient"]
        )
        
        assert message is not None
        assert "org_recipient" in message.recipient_orgs
    
    @pytest.mark.asyncio
    async def test_get_messages_for_org(self, network):
        """Test retrieving messages for organization"""
        # Register and share
        network.register_organization("org_sender", "Sender", "private")
        network.register_organization("org_receiver", "Receiver", "private")
        
        await network.share_intelligence(
            sender_org="org_sender",
            threat_level=ThreatLevel.HIGH,
            category=IntelCategory.SCAM,
            title="Test alert",
            description="Test",
            indicators={"addresses": ["0x123"]},
            recipient_orgs=["org_receiver"]
        )
        
        # Get messages
        messages = await network.get_messages_for_org("org_receiver")
        
        assert len(messages) > 0
        assert messages[0].title == "Test alert"
    
    @pytest.mark.asyncio
    async def test_verify_intelligence(self, network):
        """Test intelligence verification"""
        # Share intel
        network.register_organization("org_sender", "Sender", "private")
        network.register_organization("org_verifier", "Verifier", "private")
        
        message = await network.share_intelligence(
            sender_org="org_sender",
            threat_level=ThreatLevel.MEDIUM,
            category=IntelCategory.PHISHING,
            title="Phishing site",
            description="Fake exchange",
            indicators={"domains": ["fake-exchange.com"]},
            recipient_orgs=None
        )
        
        # Verify
        success = await network.verify_intelligence(
            message_id=message.id,
            verifier_org="org_verifier",
            is_verified=True,
            notes="Confirmed phishing site"
        )
        
        assert success is True
        assert message.verified is True
        
        # Check reputation update
        sender = network.organizations["org_sender"]
        assert sender.trust_score > 0.5  # Should increase
    
    def test_rate_limiting(self, network):
        """Test rate limiting"""
        network.register_organization("org_test", "Test", "private")
        
        # Check rate limit
        allowed = network._check_rate_limit("org_test", "hourly")
        assert allowed is True
    
    def test_network_statistics(self, network):
        """Test network statistics"""
        # Register some orgs
        network.register_organization("org_1", "Org 1", "private")
        network.register_organization("org_2", "Org 2", "exchange")
        
        stats = network.get_network_statistics()
        
        assert stats["total_organizations"] == 2
        assert stats["network_name"] == "test_network"
        assert "avg_trust_score" in stats


class TestIntegration:
    """Integration tests for complete threat intel system"""
    
    @pytest.mark.asyncio
    async def test_end_to_end_workflow(self):
        """Test complete workflow from feed update to enrichment"""
        service = ThreatIntelService()
        
        # 1. Initialize service
        await service.initialize()
        
        # 2. Update feeds (will be simulated)
        # In real scenario, this would fetch from external APIs
        
        # 3. Submit community report
        report = await service.submit_community_report(
            reporter_id="analyst_1",
            chain="ethereum",
            address="0x1234567890abcdef1234567890abcdef12345678",
            category=IntelCategory.SCAM,
            threat_level=ThreatLevel.HIGH,
            title="Ponzi scheme detected",
            description="Investment scam",
            evidence={}
        )
        
        assert report.status == IntelStatus.PENDING
        
        # 4. Query intelligence
        query = IntelQuery(chains=["ethereum"])
        results = await service.query_intelligence(query)
        
        # Results depend on what was stored
        assert isinstance(results, list)
        
        # 5. Get statistics
        stats = await service.get_statistics()
        assert stats.community_reports >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
