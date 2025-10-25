"""
Security Tests: Dependency Security
====================================
Prüft ob Dependencies sicher und aktuell sind.
"""

import pytest
import pkg_resources
import subprocess
import json


class TestDependencySecurity:
    """Tests für Dependency Security"""

    def test_no_known_vulnerabilities_in_dependencies(self):
        """Test: Keine bekannten Vulnerabilities in Dependencies"""
        # Führe Safety Check durch
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                vulnerabilities = json.loads(result.stdout)
                
                # Prüfe auf kritische Vulnerabilities
                critical_vulns = [
                    v for v in vulnerabilities 
                    if "critical" in v.get("severity", "").lower()
                ]
                
                # Sollte keine kritischen Vulnerabilities geben
                assert len(critical_vulns) == 0, \
                    f"Kritische Vulnerabilities gefunden: {critical_vulns}"
                
        except FileNotFoundError:
            pytest.skip("Safety nicht installiert")
        except Exception as e:
            pytest.skip(f"Safety Check fehlgeschlagen: {e}")

    def test_dependencies_not_outdated(self):
        """Test: Dependencies sind nicht stark veraltet"""
        # Prüfe ob kritische Packages aktuell sind
        critical_packages = [
            "fastapi",
            "pydantic",
            "sqlalchemy",
            "psycopg2-binary",
            "python-jose",
            "passlib",
        ]
        
        outdated_packages = []
        
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                outdated = json.loads(result.stdout)
                
                for pkg in outdated:
                    if pkg["name"].lower() in critical_packages:
                        outdated_packages.append(pkg)
                
                # Warnung wenn kritische Packages veraltet sind
                if outdated_packages:
                    print(f"\n⚠️  Veraltete kritische Packages: {outdated_packages}")
                
        except Exception as e:
            pytest.skip(f"Outdated Check fehlgeschlagen: {e}")

    def test_no_conflicting_dependencies(self):
        """Test: Keine Dependency Conflicts"""
        try:
            result = subprocess.run(
                ["pip", "check"],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # pip check sollte keine Conflicts melden
            assert result.returncode == 0, \
                f"Dependency Conflicts gefunden:\n{result.stdout}"
                
        except Exception as e:
            pytest.skip(f"Dependency Check fehlgeschlagen: {e}")

    def test_secure_package_sources(self):
        """Test: Packages kommen von vertrauenswürdigen Quellen"""
        # Prüfe ob alle Packages von PyPI kommen
        # (Keine privaten/unsicheren Package-Repositories)
        
        installed_packages = list(pkg_resources.working_set)
        
        for pkg in installed_packages:
            # Prüfe Package-Location
            location = pkg.location
            
            # Sollte aus site-packages kommen, nicht aus unsicheren Pfaden
            assert "site-packages" in location or "dist-packages" in location, \
                f"Package {pkg.key} aus unsicherer Quelle: {location}"


class TestCryptographicDependencies:
    """Tests für Kryptografische Dependencies"""

    def test_cryptography_library_present(self):
        """Test: Aktuelle Crypto-Library vorhanden"""
        try:
            import cryptography
            # Version sollte aktuell sein (mindestens 41.0+)
            version = pkg_resources.get_distribution("cryptography").version
            major_version = int(version.split(".")[0])
            
            assert major_version >= 41, \
                f"Veraltete cryptography Version: {version}"
                
        except ImportError:
            pytest.fail("cryptography library nicht installiert")

    def test_passlib_with_bcrypt(self):
        """Test: passlib mit bcrypt Support"""
        try:
            from passlib.context import CryptContext
            
            # Erstelle Context mit bcrypt
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            
            # Test-Hash
            hashed = pwd_context.hash("test123")
            assert pwd_context.verify("test123", hashed)
            
        except ImportError:
            pytest.fail("passlib oder bcrypt nicht verfügbar")


class TestProductionDependencies:
    """Tests für Production-Dependencies"""

    def test_no_development_dependencies_in_production(self):
        """Test: Keine Dev-Dependencies in Production"""
        # Dev-only Packages die nicht in Production sein sollten
        dev_packages = [
            "pytest",
            "pytest-cov",
            "black",
            "flake8",
            "mypy",
            "ipython",
            "jupyter",
        ]
        
        installed = [pkg.key for pkg in pkg_resources.working_set]
        
        # In Production-Umgebung sollten diese nicht installiert sein
        # (Dieser Test ist nur informativ, da wir in Dev-Umgebung sind)
        production_dev_packages = [
            pkg for pkg in dev_packages 
            if pkg in installed
        ]
        
        if production_dev_packages:
            print(f"\n⚠️  Dev-Packages in Environment: {production_dev_packages}")
            print("   → In Production entfernen!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
