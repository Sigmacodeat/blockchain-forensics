from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any

class SanctionedEntity(BaseModel):
    id: str
    canonical_name: str
    type: Optional[str] = None
    risk_level: Optional[Literal["LOW","MEDIUM","HIGH","CRITICAL"]] = None
    # Multi-Liste-Felder
    sources: List[str] = Field(default_factory=list)  # Liste der Quellen (e.g., ["ofac", "un"])
    aliases: List[Dict[str, Any]] = Field(default_factory=list)  # Vereinfacht für Flexibilität
    addresses: List[str] = Field(default_factory=list)  # Blockchain-Adressen
    countries: List[str] = Field(default_factory=list)  # Länder-Codes
    programs: List[str] = Field(default_factory=list)  # Sanktionsprogramme (e.g., ["SDN", "UNSC"])
    remarks: Optional[str] = None
    last_updated: Optional[str] = None

class SanctionsListSource(BaseModel):
    id: str
    code: Literal["ofac","un","eu","uk","canada","australia","other"]
    version: str
    url: Optional[str] = None  # Für Feed-Integration
    last_fetched: Optional[str] = None

class EntityAlias(BaseModel):
    id: str
    entity_id: str
    value: str
    kind: Literal["name","aka","ens","address"]
    source_code: str
    confidence: float = Field(ge=0.0, le=1.0, default=0.9)

# OFAC-spezifische Felder
class OFACSpecific(BaseModel):
    sdn_type: Optional[str] = None  # z.B. "Individual", "Entity"
    programs: List[str] = Field(default_factory=list)  # SDN-Programme
    aka_list: List[str] = Field(default_factory=list)  # AKAs
    addresses: List[str] = Field(default_factory=list)  # Physische Adressen
    nationalities: List[str] = Field(default_factory=list)  # Nationalitäten
    citizenships: List[str] = Field(default_factory=list)  # Staatsbürgerschaften
    dates_of_birth: List[str] = Field(default_factory=list)  # Geburtsdaten
    places_of_birth: List[str] = Field(default_factory=list)  # Geburtsorte
    passport_numbers: List[str] = Field(default_factory=list)  # Passnummern
    id_numbers: List[str] = Field(default_factory=list)  # ID-Nummern
    vessel_info: Optional[Dict[str, Any]] = None  # Für Schiffe/Flugzeuge

# UN-spezifische Felder
class UNSpecific(BaseModel):
    unsc_programs: List[str] = Field(default_factory=list)  # UNSC-Programme
    committee: Optional[str] = None  # Sanktionskomitee
    reference_numbers: List[str] = Field(default_factory=list)  # Referenznummern
    listed_on: Optional[str] = None  # Listungsdatum
    amended_on: Optional[str] = None  # Änderungsdatum
    narrative_summaries: List[str] = Field(default_factory=list)  # Beschreibungen

# EU-spezifische Felder
class EUSpecific(BaseModel):
    regulation_number: Optional[str] = None  # EU-Verordnung
    consolidated_version: Optional[str] = None  # Konsolidierte Version
    entry_date: Optional[str] = None  # Eintragsdatum
    amendment_date: Optional[str] = None  # Änderungsdatum
    subject_type: Optional[str] = None  # Subjekttyp
    remark: Optional[str] = None  # Bemerkungen

# UK-spezifische Felder (ähnlich EU)
class UKSpecific(BaseModel):
    designation: Optional[str] = None  # Bezeichnung
    regime: Optional[str] = None  # Regime
    listed_on: Optional[str] = None  # Listungsdatum
    last_updated: Optional[str] = None  # Letzte Aktualisierung
    additional_information: Optional[str] = None  # Zusätzliche Infos

# Erweiterte Entität mit spezifischen Feldern
class DetailedSanctionedEntity(SanctionedEntity):
    ofac_details: Optional[OFACSpecific] = None
    un_details: Optional[UNSpecific] = None
    eu_details: Optional[EUSpecific] = None
    uk_details: Optional[UKSpecific] = None

# Screening-Resultat für Multi-Liste-Prüfung
class SanctionsScreeningResult(BaseModel):
    address: str
    is_sanctioned: bool
    matches: List[Dict[str, Any]] = Field(default_factory=list)  # Details zu Matches pro Liste
    overall_risk: Literal["LOW","MEDIUM","HIGH","CRITICAL"] = "LOW"
    recommendations: List[str] = Field(default_factory=list)
    screened_at: str

# Screening-Query für Multi-Liste
class MultiSanctionsQuery(BaseModel):
    addresses: List[str]
    sources: List[Literal["ofac","un","eu","uk","canada","australia"]] = Field(default_factory=lambda: ["ofac", "un", "eu", "uk"])
    include_aliases: bool = True
    confidence_threshold: float = Field(ge=0.0, le=1.0, default=0.8)
