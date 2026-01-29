from __future__ import annotations

import argparse
import keyword
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect
from sqlalchemy.engine import Engine


# ============================================================
# Naming helpers
# ============================================================

def split_words(name: str) -> list[str]:
    """
    Split identifiers into word parts for snake_case, kebab-case,
    camelCase, PascalCase, acronyms, etc.
    """
    s = re.sub(r"[\W_]+", " ", name).strip()
    if not s:
        return []

    parts: list[str] = []
    for token in s.split():
        chunks = re.findall(
            r"[A-Z]+(?=[A-Z][a-z]|[0-9]|\b)|[A-Z]?[a-z]+|[0-9]+",
            token,
        )
        parts.extend(chunks if chunks else [token])
    return parts


def to_pascal_case(name: str) -> str:
    words = split_words(name)
    if not words:
        return "Model"
    return "".join(w if w.isupper() else w.capitalize() for w in words)


def safe_classname(table_name: str) -> str:
    cname = to_pascal_case(table_name)
    if keyword.iskeyword(cname.lower()):
        cname += "Model"
    return cname


def safe_identifier(name: str) -> str:
    name = re.sub(r"\W+", "_", name)
    if not name:
        name = "field"
    if name[0].isdigit():
        name = f"f_{name}"
    if keyword.iskeyword(name):
        name = f"{name}_"
    return name


# ============================================================
# SQLAlchemy type rendering
# ============================================================

def render_sqla_type(coltype: Any) -> str:
    """
    Render a SQLAlchemy column type expression as source code.
    Conservative on purpose.
    """
    t = coltype.__class__.__name__

    mapping: Dict[str, str] = {
        "INTEGER": "Integer",
        "Integer": "Integer",
        "BIGINT": "BigInteger",
        "BigInteger": "BigInteger",
        "SMALLINT": "SmallInteger",
        "SmallInteger": "SmallInteger",
        "TINYINT": "SmallInteger",
        "VARCHAR": "String",
        "String": "String",
        "CHAR": "String",
        "TEXT": "Text",
        "Text": "Text",
        "MEDIUMTEXT": "Text",
        "LONGTEXT": "Text",
        "BOOLEAN": "Boolean",
        "Boolean": "Boolean",
        "DATE": "Date",
        "Date": "Date",
        "DATETIME": "DateTime",
        "DateTime": "DateTime",
        "TIMESTAMP": "DateTime",
        "TIME": "Time",
        "Time": "Time",
        "DECIMAL": "Numeric",
        "Numeric": "Numeric",
        "FLOAT": "Float",
        "Float": "Float",
        "DOUBLE": "Float",
        "JSON": "JSON",
        "ENUM": "Enum",
        "Enum": "Enum",
        "BLOB": "LargeBinary",
        "TINYBLOB": "LargeBinary",
        "MEDIUMBLOB": "LargeBinary",
        "LONGBLOB": "LargeBinary",
        "LargeBinary": "LargeBinary",
    }

    base = mapping.get(t)
    if base is None:
        base = t

    if base == "String":
        length = getattr(coltype, "length", None)
        return f"{base}({length})" if length else base

    if base == "Numeric":
        p = getattr(coltype, "precision", None)
        s = getattr(coltype, "scale", None)
        if p is not None and s is not None:
            return f"{base}({p}, {s})"
        if p is not None:
            return f"{base}({p})"
        return base

    if base == "Enum":
        enums = getattr(coltype, "enums", None)
        if enums:
            values = ", ".join(repr(v) for v in enums)
            return f"Enum({values})"
        return "Enum"

    return base


# ============================================================
# Schema models
# ============================================================

class ColumnInfo:
    def __init__(
        self,
        *,
        name: str,
        attr_name: str,
        type_expr: str,
        nullable: bool,
        primary_key: bool,
        autoincrement: Optional[bool],
        unique: bool,
        foreign_keys: List[Tuple[str, str]],
    ):
        self.name = name
        self.attr_name = attr_name
        self.type_expr = type_expr
        self.nullable = nullable
        self.primary_key = primary_key
        self.autoincrement = autoincrement
        self.unique = unique
        self.foreign_keys = foreign_keys


class TableInfo:
    def __init__(self, *, name: str, class_name: str, columns: List[ColumnInfo]):
        self.name = name
        self.class_name = class_name
        self.columns = columns


# ============================================================
# Introspection
# ============================================================

def load_schema(
    engine: Engine,
    schema: Optional[str] = None,
    table_names: Optional[List[str]] = None,
) -> List[TableInfo]:
    insp = inspect(engine)
    all_tables = insp.get_table_names(schema=schema)
    
    # Filter by table_names if provided, otherwise use all tables
    tables = [t for t in all_tables if t in table_names] if table_names else all_tables
    
    result: List[TableInfo] = []

    for table in tables:
        cols_raw = insp.get_columns(table, schema=schema)
        pk_cols = set(
            insp.get_pk_constraint(table, schema=schema)
            .get("constrained_columns", [])
        )

        unique_cols: set[str] = set()
        for uc in insp.get_unique_constraints(table, schema=schema) or []:
            unique_cols.update(uc.get("column_names") or [])

        fk_map: Dict[str, List[Tuple[str, str]]] = {}
        for fk in insp.get_foreign_keys(table, schema=schema) or []:
            rt = fk.get("referred_table")
            for cc, rc in zip(
                fk.get("constrained_columns") or [],
                fk.get("referred_columns") or [],
            ):
                fk_map.setdefault(cc, []).append((rt or "", rc))

        columns: List[ColumnInfo] = []
        for c in cols_raw:
            name = c["name"]
            columns.append(
                ColumnInfo(
                    name=name,
                    attr_name=safe_identifier(name),
                    type_expr=render_sqla_type(c["type"]),
                    nullable=bool(c.get("nullable", True)),
                    primary_key=name in pk_cols,
                    autoincrement=c.get("autoincrement"),
                    unique=name in unique_cols,
                    foreign_keys=fk_map.get(name, []),
                )
            )

        # Skip tables without primary keys (SQLAlchemy requires them)
        if not pk_cols:
            print(f"Warning: Skipping table '{table}' (no primary key defined)")
            continue

        result.append(
            TableInfo(
                name=table,
                class_name=safe_classname(table),
                columns=columns,
            )
        )

    return result


# ============================================================
# Code generation
# ============================================================

BASE_PY = """from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class ModelMixin:
    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        \"\"\"Convert model instance to dictionary.
        
        Serializes all mapped column attributes to a dictionary. Handles special
        types like datetime (ISO format), Decimal (string), and dataclasses.
        
        Args:
            exclude: Column names to exclude from output
            
        Returns:
            Dictionary of column names to values
        \"\"\"
        mapper = getattr(self, "__mapper__", None)
        if mapper is None:
            return {}

        exclude_set: Set[str] = set(exclude) if exclude else set()
        out: Dict[str, Any] = {}
        
        for attr in mapper.column_attrs:
            key = attr.key
            if key in exclude_set:
                continue
            
            val = getattr(self, key)

            if isinstance(val, (datetime, date)):
                out[key] = val.isoformat()
            elif isinstance(val, Decimal):
                out[key] = str(val)
            elif is_dataclass(val):
                out[key] = asdict(val)  # type: ignore[arg-type]
            else:
                out[key] = val

        return out

    def to_json(self, exclude: Optional[List[str]] = None, **kwargs: Any) -> str:
        \"\"\"Convert model instance to JSON string.
        
        Args:
            exclude: Column names to exclude from output
            **kwargs: Additional arguments passed to json.dumps (e.g., indent=2)
            
        Returns:
            JSON string representation
        \"\"\"
        return json.dumps(self.to_dict(exclude=exclude), **kwargs)

    def from_dict(
        self,
        data: Dict[str, Any],
        exclude: Optional[List[str]] = None,
        strict: bool = False
    ) -> None:
        \"\"\"Update model instance from dictionary.
        
        Sets mapped column attributes from the provided dictionary. Only processes
        keys that correspond to actual database columns.
        
        Args:
            data: Dictionary of column names to values
            exclude: Column names to skip (even if present in data)
            strict: If True, raises ValueError for keys in data that are not mapped columns
            
        Raises:
            ValueError: When strict=True and data contains unknown column names
        \"\"\"
        mapper = getattr(self, "__mapper__", None)
        if mapper is None:
            return

        exclude_set: Set[str] = set(exclude) if exclude else set()
        valid_keys: Set[str] = {attr.key for attr in mapper.column_attrs}
        
        if strict:
            data_keys = set(data.keys()) - exclude_set
            unknown_keys = data_keys - valid_keys
            if unknown_keys:
                unknown_sorted = sorted(unknown_keys)
                valid_sorted = sorted(valid_keys)
                raise ValueError(
                    f"Unknown column keys for {self.__class__.__name__}: {unknown_sorted}. "
                    f"Valid keys are: {valid_sorted}"
                )
        
        for attr in mapper.column_attrs:
            key = attr.key
            if key in exclude_set or key not in data:
                continue
            setattr(self, key, data[key])

    def update(self, strict: bool = True, **kwargs: Any) -> None:
        \"\"\"Update model instance attributes.
        
        Convenience method to update multiple column attributes at once. Only sets
        attributes that correspond to mapped database columns.
        
        Args:
            strict: If True (default), raises ValueError for unknown column names
            **kwargs: Column names and values to update
            
        Raises:
            ValueError: When strict=True and kwargs contains unknown column names
            
        Example:
            user.update(firstname='John', surname='Doe')
            user.update(strict=False, firstname='John', unknown_field='ignored')
        \"\"\"
        mapper = getattr(self, "__mapper__", None)
        if mapper is None:
            return
        
        valid_keys: Set[str] = {attr.key for attr in mapper.column_attrs}
        
        if strict:
            unknown_keys = set(kwargs.keys()) - valid_keys
            if unknown_keys:
                unknown_sorted = sorted(unknown_keys)
                valid_sorted = sorted(valid_keys)
                raise ValueError(
                    f"Unknown column keys for {self.__class__.__name__}: {unknown_sorted}. "
                    f"Valid keys are: {valid_sorted}"
                )
        
        for key, value in kwargs.items():
            if key in valid_keys:
                setattr(self, key, value)

    def get_pk(self) -> Any:
        \"\"\"Get primary key value(s).
        
        Returns:
            Single value for single-column primary keys, or tuple for composite keys.
            Returns None if mapper is not available.
        \"\"\"
        mapper = getattr(self, "__mapper__", None)
        if mapper is None:
            return None

        pk_cols = [col.key for col in mapper.primary_key]
        pk_values = [getattr(self, col) for col in pk_cols]
        
        if len(pk_values) == 1:
            return pk_values[0]
        return tuple(pk_values)

    def clone(self, exclude_pk: bool = True) -> ModelMixin:
        \"\"\"Create a copy of the model instance.
        
        Creates a new instance with the same column values. Does NOT copy:
        - Primary key (by default)
        - Relationships
        - Session state / identity
        
        Args:
            exclude_pk: If True (default), excludes primary key columns from copy
            
        Returns:
            New instance of the same model class with copied column values
            
        Example:
            original = session.get(User, 1)
            duplicate = original.clone()  # New user with same data, no PK
            session.add(duplicate)
            session.commit()  # Creates new record in database
        \"\"\"
        mapper = getattr(self, "__mapper__", None)
        if mapper is None:
            return self.__class__()

        exclude_cols: List[str] = []
        if exclude_pk:
            exclude_cols = [col.key for col in mapper.primary_key]

        data = self.to_dict(exclude=exclude_cols)
        new_instance = self.__class__()
        new_instance.from_dict(data, strict=False)
        return new_instance

    def __repr__(self) -> str:
        \"\"\"String representation showing class name and primary key.\"\"\"
        pk = self.get_pk()
        if pk is not None:
            return f"<{self.__class__.__name__}(pk={pk})>"
        return f"<{self.__class__.__name__}(unsaved)>"
"""


MODEL_IMPORTS = """from __future__ import annotations

from typing import Any, Optional

from sqlalchemy import (
    Boolean,  # type: ignore
    Date,  # type: ignore
    DateTime,  # type: ignore
    Enum,  # type: ignore
    Float,  # type: ignore
    Integer,  # type: ignore
    BigInteger,  # type: ignore
    SmallInteger,  # type: ignore
    LargeBinary,  # type: ignore
    Numeric,  # type: ignore
    String,  # type: ignore
    Text,  # type: ignore
    Time,  # type: ignore
    JSON,  # type: ignore
    ForeignKey,  # type: ignore
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, ModelMixin
"""


def render_column(col: ColumnInfo) -> str:
    args = [col.type_expr]

    if col.foreign_keys:
        rt, rc = col.foreign_keys[0]
        if rt and rc:
            args.append(f'ForeignKey("{rt}.{rc}")')

    kwargs: List[str] = []
    if col.primary_key:
        kwargs.append("primary_key=True")
    if col.unique and not col.primary_key:
        kwargs.append("unique=True")
    if not col.nullable and not col.primary_key:
        kwargs.append("nullable=False")
    if col.primary_key and col.autoincrement is False:
        kwargs.append("autoincrement=False")

    arg_str = ", ".join(args + kwargs)
    hint = "Optional[Any]" if col.nullable and not col.primary_key else "Any"

    return f"{col.attr_name}: Mapped[{hint}] = mapped_column({arg_str})"


def render_model(table: TableInfo) -> str:
    lines: List[str] = [MODEL_IMPORTS, ""]
    lines.append(f"class {table.class_name}(Base, ModelMixin):")
    lines.append(f'    __tablename__ = "{table.name}"')
    lines.append("")
    for col in table.columns:
        lines.append(f"    {render_column(col)}")
    lines.append("")
    return "\n".join(lines)


def write_models(out_dir: Path, tables: List[TableInfo]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "base.py").write_text(BASE_PY, encoding="utf-8")

    init_lines = ["from .base import Base, ModelMixin", ""]
    for t in tables:
        mod = safe_identifier(t.name).lower()
        init_lines.append(f"from .{mod} import {t.class_name}")
    init_lines.append("")
    (out_dir / "__init__.py").write_text("\n".join(init_lines), encoding="utf-8")

    for t in tables:
        mod = safe_identifier(t.name).lower()
        (out_dir / f"{mod}.py").write_text(render_model(t), encoding="utf-8")


# ============================================================
# CLI
# ============================================================

def check_tables_without_pk(engine: Engine, schema: Optional[str] = None) -> List[str]:
    """Check which tables are missing primary keys.
    
    Args:
        engine: SQLAlchemy engine
        schema: Optional schema name
        
    Returns:
        List of table names without primary keys
    """
    insp = inspect(engine)
    all_tables = insp.get_table_names(schema=schema)
    tables_without_pk: List[str] = []
    
    for table in all_tables:
        pk_constraint = insp.get_pk_constraint(table, schema=schema)
        pk_cols = pk_constraint.get("constrained_columns", [])
        if not pk_cols:
            tables_without_pk.append(table)
    
    return tables_without_pk


def main(
    db_url: Optional[str] = None,
    out_dir: str = "models",
    schema: Optional[str] = None,
    table_names: Optional[List[str]] = None,
    check_pk_only: bool = False,
) -> Dict[str, Any]:
    """Generate SQLAlchemy ORM models from database schema.
    
    Can be used as a library function or via CLI.
    
    Args:
        db_url: Database URL (overrides .env and CLI)
        out_dir: Output directory for generated models
        schema: Database schema name
        table_names: Specific tables to generate (None = all tables)
        check_pk_only: Only check for tables without PKs, don't generate
        
    Returns:
        Dictionary with generation results:
        - success: bool
        - tables_generated: int
        - tables_skipped: List[str] (tables without PK)
        - output_dir: str (if models were generated)
    """
    # Load .env file
    load_dotenv()
    
    # Priority: function arg > CLI arg > .env
    # When called as library, db_url is passed directly
    # When called from CLI, we'll handle it there
    if db_url is None:
        db_url = os.getenv("DATABASE_URL")
    
    if not db_url:
        raise ValueError("db_url is required or DATABASE_URL must be set in .env")

    engine = create_engine(db_url)
    
    # Check for tables without primary keys
    tables_without_pk = check_tables_without_pk(engine, schema=schema)
    
    if check_pk_only:
        # Just report and exit
        all_tables = inspect(engine).get_table_names(schema=schema)
        print(f"Total tables in database: {len(all_tables)}")
        if tables_without_pk:
            print(f"\n⚠️  Tables WITHOUT primary keys ({len(tables_without_pk)}):")
            for table in tables_without_pk:
                print(f"   - {table}")
        else:
            print("\n✓ All tables have primary keys")
        
        print(f"\n✓ Tables WITH primary keys: {len(all_tables) - len(tables_without_pk)}")
        
        return {
            "success": True,
            "tables_generated": 0,
            "tables_skipped": tables_without_pk,
            "total_tables": len(all_tables),
        }
    
    # Generate models
    tables = load_schema(engine, schema=schema, table_names=table_names)
    
    if not tables:
        msg = ""
        if table_names:
            msg = f"No matching tables found for: {', '.join(table_names)}"
        else:
            msg = "No tables found in database"
        print(f"Warning: {msg}")
        return {
            "success": False,
            "tables_generated": 0,
            "tables_skipped": tables_without_pk,
            "message": msg,
        }

    write_models(Path(out_dir), tables)

    # Report results
    if table_names:
        msg = f"Generated {len(tables)} model file(s) for tables: {', '.join([t.name for t in tables])}"
    else:
        msg = f"Generated {len(tables)} model files for all tables in {Path(out_dir).resolve()}"
    
    if tables_without_pk:
        print(f"\nNote: Skipped {len(tables_without_pk)} table(s) without primary keys")
    
    print(msg)
    
    return {
        "success": True,
        "tables_generated": len(tables),
        "tables_skipped": tables_without_pk,
        "output_dir": str(Path(out_dir).resolve()),
    }


def cli() -> None:
    """CLI entry point for the generator."""
    parser = argparse.ArgumentParser(
        description="Generate SQLAlchemy ORM models from an existing MariaDB/MySQL database"
    )
    parser.add_argument(
        "--db-url",
        help="Database URL (overrides DATABASE_URL from .env)"
    )
    parser.add_argument("--out", default="models", help="Output directory for models")
    parser.add_argument("--schema", default=None, help="Database schema name")
    parser.add_argument(
        "--check-pk",
        action="store_true",
        help="Only check which tables are missing primary keys (don't generate models)"
    )
    parser.add_argument(
        "tables",
        nargs="*",
        help="Specific table names to generate (if none provided, all tables will be generated)"
    )
    args = parser.parse_args()
    
    try:
        result = main(
            db_url=args.db_url,
            out_dir=args.out,
            schema=args.schema,
            table_names=args.tables if args.tables else None,
            check_pk_only=args.check_pk,
        )
        
        # Exit with appropriate code
        if not result["success"]:
            exit(1)
            
    except ValueError as e:
        parser.error(str(e))
    except Exception as e:
        print(f"Error: {e}")
        exit(1)


if __name__ == "__main__":
    cli()
