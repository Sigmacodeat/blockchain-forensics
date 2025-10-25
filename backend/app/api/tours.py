"""
Guided Tours API Endpunkte für Blockchain-Forensik-Anwendung

Bietet REST-API für Tour-Management und Analytics.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
import asyncio

from app.services.tour_service import tour_service, TourStatus, TourType
from app.auth.dependencies import get_current_user

router = APIRouter(prefix="/api/v1/tours", tags=["tours"])

# Pydantic Models
class TourStepRequest(BaseModel):
    step_id: str = Field(..., description="Eindeutige Schritt-ID")
    title: str = Field(..., description="Titel des Schritts")
    content: str = Field(..., description="Inhalt des Schritts")
    target: str = Field(..., description="CSS-Selektor für das Ziel-Element")
    placement: str = Field("bottom", description="Positionierung des Tooltips")
    disable_beacon: bool = Field(False, description="Beacon deaktivieren")
    show_skip_button: bool = Field(True, description="Skip-Button anzeigen")

class CreateTourRequest(BaseModel):
    tour_id: str = Field(..., description="Eindeutige Tour-ID")
    name: str = Field(..., description="Name der Tour")
    description: str = Field(..., description="Beschreibung der Tour")
    type: str = Field("feature_introduction", description="Typ der Tour")
    steps: List[TourStepRequest] = Field(..., description="Liste der Tour-Schritte")

class UpdateProgressRequest(BaseModel):
    tour_id: str = Field(..., description="Tour-ID")
    step_index: int = Field(..., description="Aktueller Schritt-Index")
    action: str = Field("next", description="Aktion (next, previous, skip)")

# API Endpunkte

@router.get("/available", response_model=List[Dict[str, Any]])
async def get_available_tours(
    current_user = Depends(get_current_user)
):
    """Holt verfügbare Touren für den aktuellen Benutzer"""
    try:
        # Benutzer-ID aus Token extrahieren (vereinfacht)
        user_id = current_user.get("sub", "anonymous")

        tours = await tour_service.get_available_tours(user_id)

        return tours

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Touren Laden fehlgeschlagen: {str(e)}")

@router.get("/{tour_id}", response_model=Dict[str, Any])
async def get_tour_details(
    tour_id: str,
    current_user = Depends(get_current_user)
):
    """Holt Details einer spezifischen Tour"""
    try:
        tour = await tour_service.get_tour_details(tour_id)

        if not tour:
            raise HTTPException(status_code=404, detail="Tour nicht gefunden")

        return tour

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tour-Details Laden fehlgeschlagen: {str(e)}")

@router.post("/{tour_id}/start", response_model=Dict[str, str])
async def start_tour(
    tour_id: str,
    current_user = Depends(get_current_user)
):
    """Startet eine Tour für den aktuellen Benutzer"""
    try:
        # Benutzer-ID aus Token extrahieren (vereinfacht)
        user_id = current_user.get("sub", "anonymous")

        success = await tour_service.start_tour(user_id, tour_id)

        if success:
            return {"message": "Tour erfolgreich gestartet", "status": "started"}
        else:
            raise HTTPException(status_code=400, detail="Tour konnte nicht gestartet werden")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tour Starten fehlgeschlagen: {str(e)}")

@router.post("/progress", response_model=Dict[str, str])
async def update_tour_progress(
    request: UpdateProgressRequest,
    current_user = Depends(get_current_user)
):
    """Aktualisiert den Fortschritt einer Tour"""
    try:
        # Benutzer-ID aus Token extrahieren (vereinfacht)
        user_id = current_user.get("sub", "anonymous")

        success = await tour_service.update_tour_progress(
            user_id=user_id,
            tour_id=request.tour_id,
            step_index=request.step_index,
            action=request.action
        )

        if success:
            return {"message": "Fortschritt aktualisiert", "status": "updated"}
        else:
            raise HTTPException(status_code=400, detail="Fortschritt konnte nicht aktualisiert werden")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Fortschritt Aktualisieren fehlgeschlagen: {str(e)}")

@router.post("/{tour_id}/skip", response_model=Dict[str, str])
async def skip_tour(
    tour_id: str,
    current_user = Depends(get_current_user)
):
    """Überspringt eine Tour"""
    try:
        # Benutzer-ID aus Token extrahieren (vereinfacht)
        user_id = current_user.get("sub", "anonymous")

        success = await tour_service.skip_tour(user_id, tour_id)

        if success:
            return {"message": "Tour übersprungen", "status": "skipped"}
        else:
            raise HTTPException(status_code=400, detail="Tour konnte nicht übersprungen werden")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tour Überspringen fehlgeschlagen: {str(e)}")

@router.get("/progress/{tour_id}", response_model=Dict[str, Any])
async def get_tour_progress(
    tour_id: str,
    current_user = Depends(get_current_user)
):
    """Holt den Fortschritt einer Tour für den aktuellen Benutzer"""
    try:
        # Benutzer-ID aus Token extrahieren (vereinfacht)
        user_id = current_user.get("sub", "anonymous")

        progress = await tour_service.get_user_tour_progress(user_id, tour_id)

        if progress:
            return {
                "tour_id": progress.tour_id,
                "current_step": progress.current_step,
                "status": progress.status.value,
                "started_at": progress.started_at.isoformat() if progress.started_at else None,
                "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
                "step_times": progress.step_times
            }
        else:
            return {"message": "Kein Fortschritt gefunden", "status": "not_started"}

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tour-Fortschritt Laden fehlgeschlagen: {str(e)}")

@router.get("/analytics", response_model=Dict[str, Any])
async def get_tour_analytics(
    tour_id: str = None,
    current_user = Depends(get_current_user)
):
    """Holt Analytics für Touren (nur für Admins)"""
    try:
        # Vereinfachte Admin-Prüfung
        # In echter Anwendung würde hier eine echte Berechtigungsprüfung stehen

        analytics = await tour_service.get_tour_analytics(tour_id)

        return analytics

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tour-Analytics Laden fehlgeschlagen: {str(e)}")

@router.post("/create", response_model=Dict[str, str])
async def create_tour(
    request: CreateTourRequest,
    current_user = Depends(get_current_user)
):
    """Erstellt eine neue Tour (nur für Admins)"""
    try:
        # Vereinfachte Admin-Prüfung
        # In echter Anwendung würde hier eine echte Berechtigungsprüfung stehen

        tour_id = await tour_service.create_custom_tour(
            tour_data=request.dict(),
            admin_user_id=current_user.get("sub", "admin")
        )

        if tour_id:
            return {"message": "Tour erfolgreich erstellt", "tour_id": tour_id}
        else:
            raise HTTPException(status_code=400, detail="Tour konnte nicht erstellt werden")

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tour Erstellen fehlgeschlagen: {str(e)}")

@router.get("/types", response_model=List[str])
async def get_tour_types(current_user = Depends(get_current_user)):
    """Holt verfügbare Tour-Typen"""
    return [tour_type.value for tour_type in TourType]

@router.get("/status", response_model=List[str])
async def get_tour_statuses(current_user = Depends(get_current_user)):
    """Holt verfügbare Tour-Status"""
    return [status.value for status in TourStatus]

@router.get("/stats", response_model=Dict[str, Any])
async def get_tour_stats(current_user = Depends(get_current_user)):
    """Holt grundlegende Tour-Statistiken"""
    try:
        total_tours = len(tour_service.tours)
        active_tours = sum(1 for tour in tour_service.tours.values() if tour.is_active)
        total_users = len(tour_service.user_progress)

        return {
            "total_tours": total_tours,
            "active_tours": active_tours,
            "total_users": total_users,
            "tour_types": {tour.tour_id: tour.type.value for tour in tour_service.tours.values()},
            "last_updated": datetime.utcnow().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Tour-Statistiken Laden fehlgeschlagen: {str(e)}")

# Import für datetime
from datetime import datetime
