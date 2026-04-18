from __future__ import annotations

from enum import Enum


class ChangeType(str, Enum):
    ADD_COLUMN = "ADD_COLUMN"
    DROP_COLUMN = "DROP_COLUMN"
    RENAME_COLUMN = "RENAME_COLUMN"
    ALTER_TYPE = "ALTER_TYPE"
    ALTER_NULLABILITY = "ALTER_NULLABILITY"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class Confidence(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class AssetType(str, Enum):
    TABLE = "TABLE"
    VIEW = "VIEW"
    DASHBOARD = "DASHBOARD"
    PIPELINE = "PIPELINE"
    MODEL = "MODEL"
    FEATURE_STORE = "FEATURE_STORE"
