"""
Pagination-Service für große Datensätze

Implementiert effiziente Pagination für Transaktionslisten und andere Daten.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Generic, TypeVar
from dataclasses import dataclass
from math import ceil

logger = logging.getLogger(__name__)

T = TypeVar('T')

@dataclass
class PaginationParams:
    """Parameter für Pagination"""
    page: int = 1
    page_size: int = 50
    sort_by: Optional[str] = None
    sort_order: str = "desc"  # "asc" or "desc"
    total_count: Optional[int] = None

@dataclass
class PaginatedResult(Generic[T]):
    """Ergebnis einer paginierten Abfrage"""
    items: List[T]
    pagination: PaginationParams
    total_pages: int
    has_next: bool
    has_prev: bool

class PaginationService:
    """Service für effiziente Pagination"""

    @staticmethod
    def calculate_pagination(total_items: int, page: int, page_size: int) -> Dict[str, Any]:
        """Berechnet Pagination-Metadaten"""
        total_pages = ceil(total_items / page_size) if page_size > 0 else 0

        return {
            "current_page": page,
            "page_size": page_size,
            "total_items": total_items,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_page": page + 1 if page < total_pages else None,
            "prev_page": page - 1 if page > 1 else None
        }

    @staticmethod
    def validate_pagination_params(params: PaginationParams) -> PaginationParams:
        """Validiert und korrigiert Pagination-Parameter"""
        # Page muss mindestens 1 sein
        page = max(1, params.page)

        # Page Size muss zwischen 1 und 1000 sein
        page_size = max(1, min(1000, params.page))

        # Sort Order validieren
        sort_order = params.sort_order.lower() if params.sort_order else "desc"
        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"

        return PaginationParams(
            page=page,
            page_size=page_size,
            sort_by=params.sort_by,
            sort_order=sort_order,
            total_count=params.total_count
        )

    @staticmethod
    async def paginate_list(
        items: List[T],
        params: PaginationParams
    ) -> PaginatedResult[T]:
        """Paginiert eine Liste von Elementen"""

        # Parameter validieren
        params = PaginationService.validate_pagination_params(params)

        # Sortierung anwenden (falls sort_by angegeben)
        if params.sort_by:
            try:
                # Einfache Sortierung nach Attribut
                sorted_items = sorted(
                    items,
                    key=lambda x: getattr(x, params.sort_by, ""),
                    reverse=(params.sort_order == "desc")
                )
            except (AttributeError, TypeError):
                # Fallback: keine Sortierung
                sorted_items = items
        else:
            sorted_items = items

        # Pagination anwenden
        start_index = (params.page - 1) * params.page_size
        end_index = start_index + params.page_size

        paginated_items = sorted_items[start_index:end_index]

        # Metadaten berechnen
        total_items = len(items)
        pagination_meta = PaginationService.calculate_pagination(
            total_items, params.page, params.page_size
        )

        return PaginatedResult(
            items=paginated_items,
            pagination=PaginationParams(
                page=params.page,
                page_size=params.page_size,
                sort_by=params.sort_by,
                sort_order=params.sort_order,
                total_count=total_items
            ),
            total_pages=pagination_meta["total_pages"],
            has_next=pagination_meta["has_next"],
            has_prev=pagination_meta["has_prev"]
        )

    @staticmethod
    async def paginate_database_query(
        query_func,
        params: PaginationParams,
        **query_kwargs
    ) -> PaginatedResult[Dict[str, Any]]:
        """Paginiert eine Datenbankabfrage"""

        # Parameter validieren
        params = PaginationService.validate_pagination_params(params)

        # Offset und Limit für Datenbank
        offset = (params.page - 1) * params.page_size
        limit = params.page_size

        try:
            # Datenbankabfrage mit Pagination
            if asyncio.iscoroutinefunction(query_func):
                # Asynchrone Abfrage
                items, total_count = await query_func(
                    offset=offset,
                    limit=limit,
                    sort_by=params.sort_by,
                    sort_order=params.sort_order,
                    **query_kwargs
                )
            else:
                # Synchrone Abfrage (mit asyncio.to_thread)
                items, total_count = await asyncio.to_thread(
                    query_func,
                    offset=offset,
                    limit=limit,
                    sort_by=params.sort_by,
                    sort_order=params.sort_order,
                    **query_kwargs
                )

            # Metadaten berechnen
            pagination_meta = PaginationService.calculate_pagination(
                total_count, params.page, params.page_size
            )

            return PaginatedResult(
                items=items,
                pagination=params,
                total_pages=pagination_meta["total_pages"],
                has_next=pagination_meta["has_next"],
                has_prev=pagination_meta["has_prev"]
            )

        except Exception as e:
            logger.error(f"Pagination-Fehler: {e}")
            # Fallback: Leeres Ergebnis
            return PaginatedResult(
                items=[],
                pagination=params,
                total_pages=0,
                has_next=False,
                has_prev=False
            )

# Convenience-Funktionen für häufige Anwendungsfälle

def create_pagination_params(
    page: int = 1,
    page_size: int = 50,
    sort_by: Optional[str] = None,
    sort_order: str = "desc"
) -> PaginationParams:
    """Erstellt Pagination-Parameter aus einfachen Werten"""
    return PaginationParams(
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order
    )

def parse_pagination_from_request(
    page: int = 1,
    page_size: int = 50,
    sort_by: Optional[str] = None,
    sort_order: str = "desc"
) -> PaginationParams:
    """Parst Pagination-Parameter aus HTTP-Request"""
    return create_pagination_params(page, page_size, sort_by, sort_order)

# Singleton-Instance
pagination_service = PaginationService()
