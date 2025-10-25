"""
Guided Tours Service für Blockchain-Forensik-Anwendung

Implementiert interaktive Touren für neue Benutzer zur Einführung in die Plattform.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class TourStatus(Enum):
    """Status einer Tour"""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    SKIPPED = "skipped"

class TourType(Enum):
    """Typ einer Tour"""
    ONBOARDING = "onboarding"
    FEATURE_INTRODUCTION = "feature_introduction"
    ADVANCED_FEATURES = "advanced_features"

@dataclass
class TourStep:
    """Ein Schritt in einer Tour"""
    step_id: str
    title: str
    content: str
    target: str  # CSS-Selektor oder Element-ID
    placement: str = "bottom"  # top, bottom, left, right, center
    disable_beacon: bool = False
    show_skip_button: bool = True
    spotlight_clicks: bool = False

@dataclass
class Tour:
    """Eine komplette Tour"""
    tour_id: str
    name: str
    description: str
    type: TourType
    steps: List[TourStep]
    is_active: bool = True
    created_at: datetime = None
    updated_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()

@dataclass
class UserTourProgress:
    """Fortschritt eines Benutzers bei einer Tour"""
    user_id: str
    tour_id: str
    current_step: int = 0
    status: TourStatus = TourStatus.NOT_STARTED
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None
    step_times: Dict[int, int] = None  # Zeit pro Schritt in Sekunden

    def __post_init__(self):
        if self.step_times is None:
            self.step_times = {}
        if self.last_activity is None:
            self.last_activity = datetime.utcnow()

class TourService:
    """Haupt-Service für Guided Tours"""

    def __init__(self):
        self.tours: Dict[str, Tour] = {}
        self.user_progress: Dict[str, Dict[str, UserTourProgress]] = {}  # user_id -> tour_id -> progress
        self._load_default_tours()

    def _load_default_tours(self):
        """Lädt Standard-Touren"""
        try:
            # Onboarding Tour für neue Benutzer
            onboarding_tour = Tour(
                tour_id="onboarding_main",
                name="Plattform-Einführung",
                description="Lernen Sie die wichtigsten Features der Blockchain-Forensik-Plattform kennen",
                type=TourType.ONBOARDING,
                steps=[
                    TourStep(
                        step_id="welcome",
                        title="Willkommen!",
                        content="Willkommen bei der ultimativen Blockchain-Forensik-Plattform. Diese Tour führt Sie durch die wichtigsten Features.",
                        target=".main-header",
                        placement="center"
                    ),
                    TourStep(
                        step_id="dashboard_overview",
                        title="Dashboard Übersicht",
                        content="Ihr Dashboard zeigt eine Übersicht aller wichtigen Metriken und Aktivitäten.",
                        target=".dashboard-overview",
                        placement="bottom"
                    ),
                    TourStep(
                        step_id="wallet_management",
                        title="Wallet-Verwaltung",
                        content="Hier können Sie Ihre Wallets verwalten, Transaktionen analysieren und Multi-Chain-Operationen durchführen.",
                        target=".wallet-section",
                        placement="right"
                    ),
                    TourStep(
                        step_id="defi_features",
                        title="DeFi-Integration",
                        content="Nutzen Sie unsere DeFi-Tools für Liquidity Pools, Staking und Yield Farming Analyse.",
                        target=".defi-section",
                        placement="left"
                    ),
                    TourStep(
                        step_id="nft_portfolio",
                        title="NFT-Portfolio",
                        content="Verwalten und analysieren Sie Ihr NFT-Portfolio mit Rarity-Scoring und Marktanalysen.",
                        target=".nft-section",
                        placement="top"
                    ),
                    TourStep(
                        step_id="cross_chain",
                        title="Cross-Chain Swaps",
                        content="Führen Sie Swaps zwischen verschiedenen Blockchains durch mit intelligenten Bridge-Empfehlungen.",
                        target=".crosschain-section",
                        placement="bottom"
                    ),
                    TourStep(
                        step_id="analytics_tools",
                        title="Analytics & Tools",
                        content="Nutzen Sie unsere KI-gestützten Analytics für tiefgehende Blockchain-Analysen.",
                        target=".analytics-section",
                        placement="right"
                    ),
                    TourStep(
                        step_id="tour_complete",
                        title="Tour abgeschlossen!",
                        content="Sie haben erfolgreich die Plattform-Einführung abgeschlossen. Viel Erfolg bei Ihrer Arbeit!",
                        target=".main-content",
                        placement="center"
                    )
                ]
            )

            # Wallet Management Tour
            wallet_tour = Tour(
                tour_id="wallet_management",
                name="Wallet-Features",
                description="Detaillierte Einführung in alle Wallet-Management-Features",
                type=TourType.FEATURE_INTRODUCTION,
                steps=[
                    TourStep(
                        step_id="wallet_overview",
                        title="Wallet Übersicht",
                        content="Hier sehen Sie alle Ihre verbundenen Wallets und deren Balances.",
                        target=".wallet-overview"
                    ),
                    TourStep(
                        step_id="transaction_history",
                        title="Transaktionsverlauf",
                        content="Analysieren Sie alle Transaktionen mit KI-gestützter Risikobewertung.",
                        target=".transaction-history"
                    ),
                    TourStep(
                        step_id="export_import",
                        title="Export/Import",
                        content="Sichern Sie Ihre Wallets oder importieren Sie bestehende Wallets sicher.",
                        target=".export-import"
                    ),
                    TourStep(
                        step_id="multisig_setup",
                        title="Multi-Signature",
                        content="Richten Sie Multi-Sig-Wallets für erhöhte Sicherheit ein.",
                        target=".multisig-setup"
                    )
                ]
            )

            # DeFi Tour
            defi_tour = Tour(
                tour_id="defi_features",
                name="DeFi-Features",
                description="Einführung in alle DeFi-Analyse- und Management-Tools",
                type=TourType.FEATURE_INTRODUCTION,
                steps=[
                    TourStep(
                        step_id="liquidity_pools",
                        title="Liquidity Pools",
                        content="Überwachen Sie Liquidity Pools mit Echtzeit-APY und Risikoanalyse.",
                        target=".liquidity-pools"
                    ),
                    TourStep(
                        step_id="staking_positions",
                        title="Staking-Positionen",
                        content="Verfolgen Sie Ihre Staking-Positionen und verdiente Rewards.",
                        target=".staking-positions"
                    ),
                    TourStep(
                        step_id="yield_farming",
                        title="Yield Farming",
                        content="Entdecken Sie die besten Yield Farming Möglichkeiten mit KI-Empfehlungen.",
                        target=".yield-farming"
                    )
                ]
            )

            self.tours = {
                onboarding_tour.tour_id: onboarding_tour,
                wallet_tour.tour_id: wallet_tour,
                defi_tour.tour_id: defi_tour
            }

            logger.info(f"✅ {len(self.tours)} Standard-Touren geladen")

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Standard-Touren: {e}")

    async def get_available_tours(self, user_id: str) -> List[Dict[str, Any]]:
        """Holt verfügbare Touren für einen Benutzer"""
        try:
            available_tours = []

            for tour in self.tours.values():
                if not tour.is_active:
                    continue

                # Prüfen ob Benutzer Tour bereits abgeschlossen hat
                progress = await self.get_user_tour_progress(user_id, tour.tour_id)

                tour_data = {
                    "tour_id": tour.tour_id,
                    "name": tour.name,
                    "description": tour.description,
                    "type": tour.type.value,
                    "step_count": len(tour.steps),
                    "status": progress.status.value if progress else "not_started",
                    "progress": progress.current_step if progress else 0,
                    "is_completed": progress.status == TourStatus.COMPLETED if progress else False
                }

                available_tours.append(tour_data)

            return available_tours

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden verfügbarer Touren: {e}")
            return []

    async def get_tour_details(self, tour_id: str) -> Optional[Dict[str, Any]]:
        """Holt Details einer spezifischen Tour"""
        try:
            tour = self.tours.get(tour_id)
            if not tour:
                return None

            return {
                "tour_id": tour.tour_id,
                "name": tour.name,
                "description": tour.description,
                "type": tour.type.value,
                "steps": [
                    {
                        "step_id": step.step_id,
                        "title": step.title,
                        "content": step.content,
                        "target": step.target,
                        "placement": step.placement
                    }
                    for step in tour.steps
                ],
                "is_active": tour.is_active
            }

        except Exception as e:
            logger.error(f"❌ Fehler beim Laden der Tour-Details: {e}")
            return None

    async def start_tour(self, user_id: str, tour_id: str) -> bool:
        """Startet eine Tour für einen Benutzer"""
        try:
            tour = self.tours.get(tour_id)
            if not tour or not tour.is_active:
                return False

            # Initialisiere oder aktualisiere Progress
            if user_id not in self.user_progress:
                self.user_progress[user_id] = {}

            progress = UserTourProgress(
                user_id=user_id,
                tour_id=tour_id,
                status=TourStatus.IN_PROGRESS,
                started_at=datetime.utcnow()
            )

            self.user_progress[user_id][tour_id] = progress

            logger.info(f"✅ Tour {tour_id} für Benutzer {user_id} gestartet")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Starten der Tour: {e}")
            return False

    async def update_tour_progress(self, user_id: str, tour_id: str, step_index: int, action: str = "next") -> bool:
        """Aktualisiert den Fortschritt einer Tour"""
        try:
            progress = await self.get_user_tour_progress(user_id, tour_id)
            if not progress:
                return False

            tour = self.tours.get(tour_id)
            if not tour:
                return False

            # Schritt aktualisieren
            progress.current_step = step_index
            progress.last_activity = datetime.utcnow()

            # Schritt-Zeit tracken
            if step_index not in progress.step_times:
                progress.step_times[step_index] = 0
            progress.step_times[step_index] += 1  # Vereinfacht: Sekunden seit letzter Aktualisierung

            # Prüfen ob Tour abgeschlossen ist
            if step_index >= len(tour.steps):
                progress.status = TourStatus.COMPLETED
                progress.completed_at = datetime.utcnow()
                logger.info(f"✅ Tour {tour_id} für Benutzer {user_id} abgeschlossen")

            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Aktualisieren des Tour-Fortschritts: {e}")
            return False

    async def skip_tour(self, user_id: str, tour_id: str) -> bool:
        """Überspringt eine Tour"""
        try:
            progress = await self.get_user_tour_progress(user_id, tour_id)
            if not progress:
                return False

            progress.status = TourStatus.SKIPPED
            progress.last_activity = datetime.utcnow()

            logger.info(f"⏭️ Tour {tour_id} für Benutzer {user_id} übersprungen")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Überspringen der Tour: {e}")
            return False

    async def get_user_tour_progress(self, user_id: str, tour_id: str) -> Optional[UserTourProgress]:
        """Holt den Fortschritt eines Benutzers bei einer Tour"""
        return self.user_progress.get(user_id, {}).get(tour_id)

    async def get_tour_analytics(self, tour_id: str = None) -> Dict[str, Any]:
        """Holt Analytics für Touren"""
        try:
            analytics = {
                "total_users": len(self.user_progress),
                "tours_by_status": {},
                "popular_tours": [],
                "completion_rates": {},
                "average_step_times": {}
            }

            # Status zählen
            status_counts = {}
            tour_stats = {}

            for user_progress in self.user_progress.values():
                for progress in user_progress.values():
                    # Gesamt-Status
                    status = progress.status.value
                    status_counts[status] = status_counts.get(status, 0) + 1

                    # Tour-spezifische Stats
                    if progress.tour_id not in tour_stats:
                        tour_stats[progress.tour_id] = {
                            "started": 0,
                            "completed": 0,
                            "skipped": 0,
                            "total_time": 0,
                            "step_times": {}
                        }

                    tour_stats[progress.tour_id]["started"] += 1

                    if progress.status == TourStatus.COMPLETED:
                        tour_stats[progress.tour_id]["completed"] += 1
                        tour_stats[progress.tour_id]["total_time"] += sum(progress.step_times.values())

                    elif progress.status == TourStatus.SKIPPED:
                        tour_stats[progress.tour_id]["skipped"] += 1

                    # Schritt-Zeiten aggregieren
                    for step_idx, step_time in progress.step_times.items():
                        if step_idx not in tour_stats[progress.tour_id]["step_times"]:
                            tour_stats[progress.tour_id]["step_times"][step_idx] = []
                        tour_stats[progress.tour_id]["step_times"][step_idx].append(step_time)

            analytics["tours_by_status"] = status_counts

            # Completion Rates berechnen
            for tour_id, stats in tour_stats.items():
                if stats["started"] > 0:
                    completion_rate = (stats["completed"] / stats["started"]) * 100
                    analytics["completion_rates"][tour_id] = round(completion_rate, 2)

                    # Durchschnittliche Schritt-Zeiten
                    avg_step_times = {}
                    for step_idx, times in stats["step_times"].items():
                        avg_step_times[step_idx] = round(sum(times) / len(times), 2)
                    analytics["average_step_times"][tour_id] = avg_step_times

            # Beliebteste Touren
            sorted_tours = sorted(tour_stats.items(), key=lambda x: x[1]["started"], reverse=True)
            analytics["popular_tours"] = [
                {"tour_id": tour_id, "stats": stats}
                for tour_id, stats in sorted_tours[:5]
            ]

            return analytics

        except Exception as e:
            logger.error(f"❌ Fehler bei Tour-Analytics: {e}")
            return {"error": str(e)}

    async def create_custom_tour(self, tour_data: Dict[str, Any], admin_user_id: str) -> Optional[str]:
        """Erstellt eine benutzerdefinierte Tour (nur für Admins)"""
        try:
            # Vereinfachte Validierung - in echter Anwendung würde hier eine echte Admin-Prüfung stehen

            tour = Tour(
                tour_id=tour_data["tour_id"],
                name=tour_data["name"],
                description=tour_data["description"],
                type=TourType(tour_data.get("type", "feature_introduction")),
                steps=[
                    TourStep(**step_data)
                    for step_data in tour_data.get("steps", [])
                ]
            )

            self.tours[tour.tour_id] = tour

            logger.info(f"✅ Benutzerdefinierte Tour {tour.tour_id} erstellt")
            return tour.tour_id

        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen der Tour: {e}")
            return None

# Singleton-Instance
tour_service = TourService()
