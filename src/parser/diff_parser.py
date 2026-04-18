from __future__ import annotations

import re

from src.domain.enums import ChangeType
from src.domain.models import SchemaChange


_IDENT = r'(?:"[^"]+"|[A-Za-z_][A-Za-z0-9_]*)(?:\.(?:"[^"]+"|[A-Za-z_][A-Za-z0-9_]*))*'
_COL = r'(?:"[^"]+"|[A-Za-z_][A-Za-z0-9_]*)'


def _strip_quotes(token: str) -> str:
    token = token.strip()
    if len(token) >= 2 and token[0] == '"' and token[-1] == '"':
        return token[1:-1]
    return token


class DiffParser:
    _drop_column = re.compile(
        rf"\bALTER\s+TABLE\s+(?P<entity>{_IDENT})\s+DROP\s+COLUMN\s+(?:IF\s+EXISTS\s+)?(?P<column>{_COL})\b",
        re.IGNORECASE,
    )
    _add_column = re.compile(
        rf"\bALTER\s+TABLE\s+(?P<entity>{_IDENT})\s+ADD\s+COLUMN\s+(?:IF\s+NOT\s+EXISTS\s+)?(?P<column>{_COL})\s+(?P<coltype>[^;]+?)\b",
        re.IGNORECASE,
    )
    _rename_column = re.compile(
        rf"\bALTER\s+TABLE\s+(?P<entity>{_IDENT})\s+RENAME\s+COLUMN\s+(?P<old>{_COL})\s+TO\s+(?P<new>{_COL})\b",
        re.IGNORECASE,
    )
    _alter_type = re.compile(
        rf"\bALTER\s+TABLE\s+(?P<entity>{_IDENT})\s+ALTER\s+COLUMN\s+(?P<column>{_COL})\s+TYPE\s+(?P<newtype>[^;]+?)\b",
        re.IGNORECASE,
    )

    @classmethod
    def parse(cls, raw_sql: str) -> list[SchemaChange]:
        changes: list[SchemaChange] = []

        for m in cls._drop_column.finditer(raw_sql):
            changes.append(
                SchemaChange(
                    entity=_strip_quotes(m.group("entity")),
                    change_type=ChangeType.DROP_COLUMN,
                    column=_strip_quotes(m.group("column")),
                )
            )

        for m in cls._add_column.finditer(raw_sql):
            changes.append(
                SchemaChange(
                    entity=_strip_quotes(m.group("entity")),
                    change_type=ChangeType.ADD_COLUMN,
                    column=_strip_quotes(m.group("column")),
                )
            )

        for m in cls._rename_column.finditer(raw_sql):
            changes.append(
                SchemaChange(
                    entity=_strip_quotes(m.group("entity")),
                    change_type=ChangeType.RENAME_COLUMN,
                    column=_strip_quotes(m.group("old")),
                    new_type=_strip_quotes(m.group("new")),
                )
            )

        for m in cls._alter_type.finditer(raw_sql):
            new_type = m.group("newtype").strip()
            changes.append(
                SchemaChange(
                    entity=_strip_quotes(m.group("entity")),
                    change_type=ChangeType.ALTER_TYPE,
                    column=_strip_quotes(m.group("column")),
                    new_type=new_type,
                )
            )

        return changes
