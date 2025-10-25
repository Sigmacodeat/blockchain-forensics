"""
Security Audit Report Generator
================================
Generiert automatische Security Audit Reports basierend auf Scanning-Ergebnissen.
"""

import json
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List
from pydantic import BaseModel


class SecurityIssue(BaseModel):
    """Security Issue Model"""
    severity: str  # critical, high, medium, low
    category: str  # sql-injection, xss, auth, crypto, etc.
    title: str
    description: str
    file: str | None = None
    line: int | None = None
    cwe: str | None = None
    owasp: str | None = None
    recommendation: str | None = None


class SecurityAuditReport(BaseModel):
    """Security Audit Report Model"""
    timestamp: datetime
    scan_duration_seconds: float
    total_files_scanned: int
    total_issues: int
    critical_issues: int
    high_issues: int
    medium_issues: int
    low_issues: int
    issues: List[SecurityIssue]
    tools_used: List[str]
    summary: str


class SecurityAuditor:
    """Security Audit Orchestrator"""

    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.reports_dir = self.project_root / "security-reports"
        self.reports_dir.mkdir(exist_ok=True)

    async def run_full_audit(self) -> SecurityAuditReport:
        """Führt vollständiges Security Audit durch"""
        start_time = datetime.now()
        
        # Sammle alle Issues
        all_issues: List[SecurityIssue] = []
        tools_used = []

        # 1. Bandit Scan (Python Security)
        try:
            bandit_issues = await self._run_bandit_scan()
            all_issues.extend(bandit_issues)
            tools_used.append("Bandit")
        except Exception as e:
            print(f"Bandit Scan fehlgeschlagen: {e}")

        # 2. Safety Scan (Dependency Vulnerabilities)
        try:
            safety_issues = await self._run_safety_scan()
            all_issues.extend(safety_issues)
            tools_used.append("Safety")
        except Exception as e:
            print(f"Safety Scan fehlgeschlagen: {e}")

        # 3. Semgrep Scan (SAST)
        try:
            semgrep_issues = await self._run_semgrep_scan()
            all_issues.extend(semgrep_issues)
            tools_used.append("Semgrep")
        except Exception as e:
            print(f"Semgrep Scan fehlgeschlagen: {e}")

        # 4. Secrets Detection
        try:
            secrets_issues = await self._run_secrets_scan()
            all_issues.extend(secrets_issues)
            tools_used.append("detect-secrets")
        except Exception as e:
            print(f"Secrets Scan fehlgeschlagen: {e}")

        # Berechne Statistiken
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        critical = sum(1 for i in all_issues if i.severity == "critical")
        high = sum(1 for i in all_issues if i.severity == "high")
        medium = sum(1 for i in all_issues if i.severity == "medium")
        low = sum(1 for i in all_issues if i.severity == "low")

        summary = self._generate_summary(critical, high, medium, low)

        report = SecurityAuditReport(
            timestamp=start_time,
            scan_duration_seconds=duration,
            total_files_scanned=self._count_python_files(),
            total_issues=len(all_issues),
            critical_issues=critical,
            high_issues=high,
            medium_issues=medium,
            low_issues=low,
            issues=all_issues,
            tools_used=tools_used,
            summary=summary
        )

        # Speichere Report
        await self._save_report(report)

        return report

    async def _run_bandit_scan(self) -> List[SecurityIssue]:
        """Führt Bandit Security Scan durch"""
        issues = []
        
        try:
            result = subprocess.run(
                ["bandit", "-r", "app/", "-f", "json", "-o", str(self.reports_dir / "bandit.json")],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            # Parse Bandit JSON Output
            report_file = self.reports_dir / "bandit.json"
            if report_file.exists():
                with open(report_file) as f:
                    data = json.load(f)
                    
                for result_item in data.get("results", []):
                    issue = SecurityIssue(
                        severity=self._map_bandit_severity(result_item.get("issue_severity")),
                        category="bandit-" + result_item.get("test_id", "unknown"),
                        title=result_item.get("issue_text", ""),
                        description=result_item.get("issue_text", ""),
                        file=result_item.get("filename"),
                        line=result_item.get("line_number"),
                        cwe=result_item.get("issue_cwe", {}).get("id") if isinstance(result_item.get("issue_cwe"), dict) else None,
                        recommendation=result_item.get("more_info")
                    )
                    issues.append(issue)

        except subprocess.TimeoutExpired:
            print("Bandit Scan Timeout")
        except FileNotFoundError:
            print("Bandit nicht installiert. Führe aus: pip install bandit")
        except Exception as e:
            print(f"Bandit Scan Error: {e}")

        return issues

    async def _run_safety_scan(self) -> List[SecurityIssue]:
        """Führt Safety Dependency Scan durch"""
        issues = []
        
        try:
            result = subprocess.run(
                ["safety", "check", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout:
                data = json.loads(result.stdout)
                
                for vuln in data:
                    issue = SecurityIssue(
                        severity=self._map_safety_severity(vuln.get("severity", "unknown")),
                        category="dependency-vulnerability",
                        title=f"Vulnerable dependency: {vuln.get('package', 'unknown')}",
                        description=vuln.get("vulnerability", ""),
                        cwe=vuln.get("cve"),
                        recommendation=f"Upgrade to {vuln.get('package')} >= {vuln.get('fixed_version', 'latest')}"
                    )
                    issues.append(issue)

        except FileNotFoundError:
            print("Safety nicht installiert. Führe aus: pip install safety")
        except Exception as e:
            print(f"Safety Scan Error: {e}")

        return issues

    async def _run_semgrep_scan(self) -> List[SecurityIssue]:
        """Führt Semgrep SAST Scan durch"""
        issues = []
        
        try:
            result = subprocess.run(
                ["semgrep", "--config=.semgrep.yml", "--json", "app/"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )

            if result.stdout:
                data = json.loads(result.stdout)
                
                for finding in data.get("results", []):
                    issue = SecurityIssue(
                        severity=finding.get("extra", {}).get("severity", "medium").lower(),
                        category=finding.get("check_id", "unknown"),
                        title=finding.get("extra", {}).get("message", ""),
                        description=finding.get("extra", {}).get("message", ""),
                        file=finding.get("path"),
                        line=finding.get("start", {}).get("line"),
                        cwe=finding.get("extra", {}).get("metadata", {}).get("cwe"),
                        owasp=finding.get("extra", {}).get("metadata", {}).get("owasp")
                    )
                    issues.append(issue)

        except FileNotFoundError:
            print("Semgrep nicht installiert. Führe aus: pip install semgrep")
        except Exception as e:
            print(f"Semgrep Scan Error: {e}")

        return issues

    async def _run_secrets_scan(self) -> List[SecurityIssue]:
        """Führt Secrets Detection durch"""
        issues = []
        
        try:
            result = subprocess.run(
                ["detect-secrets", "scan", "--all-files", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.stdout:
                data = json.loads(result.stdout)
                
                for file_path, secrets in data.get("results", {}).items():
                    for secret in secrets:
                        issue = SecurityIssue(
                            severity="high",
                            category="hardcoded-secret",
                            title=f"Potential secret found: {secret.get('type', 'unknown')}",
                            description=f"Secret detected in {file_path}",
                            file=file_path,
                            line=secret.get("line_number"),
                            cwe="CWE-798",
                            owasp="A07:2021",
                            recommendation="Move secret to environment variables or secure vault"
                        )
                        issues.append(issue)

        except FileNotFoundError:
            print("detect-secrets nicht installiert. Führe aus: pip install detect-secrets")
        except Exception as e:
            print(f"Secrets Scan Error: {e}")

        return issues

    def _map_bandit_severity(self, severity: str) -> str:
        """Mappt Bandit Severity zu Standard-Levels"""
        mapping = {
            "HIGH": "high",
            "MEDIUM": "medium",
            "LOW": "low",
        }
        return mapping.get(severity.upper(), "low")

    def _map_safety_severity(self, severity: str) -> str:
        """Mappt Safety Severity zu Standard-Levels"""
        if "critical" in severity.lower():
            return "critical"
        elif "high" in severity.lower():
            return "high"
        elif "medium" in severity.lower():
            return "medium"
        return "low"

    def _count_python_files(self) -> int:
        """Zählt Python-Dateien im Projekt"""
        return len(list(self.project_root.glob("**/*.py")))

    def _generate_summary(self, critical: int, high: int, medium: int, low: int) -> str:
        """Generiert Summary Text"""
        total = critical + high + medium + low
        
        if total == 0:
            return "✅ Keine Sicherheitsprobleme gefunden! Exzellent!"
        
        summary = f"📊 Insgesamt {total} Sicherheitsprobleme gefunden:\n"
        if critical > 0:
            summary += f"🚨 {critical} CRITICAL Issues (sofortige Behebung erforderlich)\n"
        if high > 0:
            summary += f"⚠️ {high} HIGH Issues (zeitnahe Behebung empfohlen)\n"
        if medium > 0:
            summary += f"⚡ {medium} MEDIUM Issues (geplante Behebung)\n"
        if low > 0:
            summary += f"ℹ️ {low} LOW Issues (optional)\n"
        
        return summary

    async def _save_report(self, report: SecurityAuditReport):
        """Speichert Security Report"""
        timestamp_str = report.timestamp.strftime("%Y%m%d_%H%M%S")
        
        # JSON Report
        json_file = self.reports_dir / f"security-audit_{timestamp_str}.json"
        with open(json_file, "w") as f:
            f.write(report.model_dump_json(indent=2))
        
        # Markdown Report
        md_file = self.reports_dir / f"security-audit_{timestamp_str}.md"
        with open(md_file, "w") as f:
            f.write(self._generate_markdown_report(report))
        
        print(f"✅ Security Report gespeichert: {json_file}")
        print(f"✅ Markdown Report: {md_file}")

    def _generate_markdown_report(self, report: SecurityAuditReport) -> str:
        """Generiert Markdown-Report"""
        md = f"""# 🔒 Security Audit Report

**Timestamp**: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}  
**Scan Duration**: {report.scan_duration_seconds:.2f}s  
**Files Scanned**: {report.total_files_scanned}  
**Tools Used**: {', '.join(report.tools_used)}

---

## 📊 Summary

{report.summary}

**Issue Breakdown:**
- 🚨 Critical: {report.critical_issues}
- ⚠️ High: {report.high_issues}
- ⚡ Medium: {report.medium_issues}
- ℹ️ Low: {report.low_issues}
- **Total**: {report.total_issues}

---

## 🔍 Detailed Issues

"""
        # Gruppiere Issues nach Severity
        for severity in ["critical", "high", "medium", "low"]:
            severity_issues = [i for i in report.issues if i.severity == severity]
            if severity_issues:
                md += f"\n### {severity.upper()} Severity ({len(severity_issues)} issues)\n\n"
                
                for issue in severity_issues:
                    md += f"#### {issue.title}\n\n"
                    md += f"- **Category**: {issue.category}\n"
                    if issue.file:
                        md += f"- **File**: `{issue.file}`"
                        if issue.line:
                            md += f" (Line {issue.line})"
                        md += "\n"
                    if issue.cwe:
                        md += f"- **CWE**: {issue.cwe}\n"
                    if issue.owasp:
                        md += f"- **OWASP**: {issue.owasp}\n"
                    md += f"- **Description**: {issue.description}\n"
                    if issue.recommendation:
                        md += f"- **Recommendation**: {issue.recommendation}\n"
                    md += "\n---\n\n"

        return md


# CLI Interface
if __name__ == "__main__":
    import asyncio
    
    auditor = SecurityAuditor(".")
    report = asyncio.run(auditor.run_full_audit())
    print("\n" + report.summary)
