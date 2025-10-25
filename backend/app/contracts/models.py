from pydantic import BaseModel
from typing import Optional, List

class ContractProfile(BaseModel):
    address: str
    chain: Optional[str] = None
    bytecode_hash: Optional[str] = None
    proxy: Optional[bool] = None
    implementation: Optional[str] = None

class ContractRiskIssue(BaseModel):
    id: str
    address: str
    kind: str
    severity: str
    evidence: Optional[str] = None

class ContractAnalysis(BaseModel):
    score: float
    findings: List[ContractRiskIssue] = []
