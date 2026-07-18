"""MVP `dwh` persistence — H19 schema + H20 import + H08 read adapter."""

from app.dwh.models import Base, DWH_TABLE_NAMES

__all__ = ["Base", "DWH_TABLE_NAMES"]
