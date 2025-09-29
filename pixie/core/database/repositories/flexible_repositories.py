"""Generic repository for flexible product system that works with any table structure."""

from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session


class DynamicRepository:
    """Dynamic repository that works with any table structure discovered at runtime."""

    def __init__(self, session: Session, table_name: str):
        self.session = session
        self.table_name = table_name
        self._columns = None
        self._primary_key = None

    def _get_columns(self) -> List[Dict[str, Any]]:
        """Get column information for the table."""
        if self._columns is None:
            # Use SQLAlchemy inspector to get column info
            from sqlalchemy import inspect

            inspector = inspect(self.session.bind)
            if inspector is not None:
                self._columns = inspector.get_columns(self.table_name)
            else:
                raise RuntimeError("Could not create database inspector")

        return self._columns

    def _get_primary_key(self) -> str:
        """Get primary key column name."""
        if self._primary_key is None:
            from sqlalchemy import inspect

            inspector = inspect(self.session.bind)
            if inspector is not None:
                pk_constraint = inspector.get_pk_constraint(self.table_name)
                if pk_constraint and pk_constraint["constrained_columns"]:
                    self._primary_key = pk_constraint["constrained_columns"][0]
                else:
                    # Fallback to 'id' if no primary key found
                    self._primary_key = "id"
            else:
                raise RuntimeError("Could not create database inspector")

        return self._primary_key

    def get_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get all records from the table."""
        query = f"SELECT * FROM {self.table_name}"
        if limit:
            query += f" LIMIT {limit}"

        result = self.session.execute(text(query))
        columns = [col["name"] for col in self._get_columns()]

        return [dict(zip(columns, row)) for row in result.fetchall()]

    def get_by_id(self, id_value: Any) -> Optional[Dict[str, Any]]:
        """Get record by ID."""
        pk_column = self._get_primary_key()
        query = f"SELECT * FROM {self.table_name} WHERE {pk_column} = :id"

        result = self.session.execute(text(query), {"id": id_value})
        columns = [col["name"] for col in self._get_columns()]
        row = result.fetchone()

        return dict(zip(columns, row)) if row else None

    def find_by_column(
        self, column: str, value: Any, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Find records by column value."""
        # Validate column exists
        columns = [col["name"] for col in self._get_columns()]
        if column not in columns:
            raise ValueError(
                f"Column '{column}' does not exist in table '{self.table_name}'"
            )

        query = f"SELECT * FROM {self.table_name} WHERE {column} = :value"
        if limit:
            query += f" LIMIT {limit}"

        result = self.session.execute(text(query), {"value": value})
        return [dict(zip(columns, row)) for row in result.fetchall()]

    def search_text(
        self, search_term: str, columns: List[str], limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for text in specified columns."""
        # Validate columns exist
        all_columns = [col["name"] for col in self._get_columns()]
        invalid_columns = [col for col in columns if col not in all_columns]
        if invalid_columns:
            raise ValueError(
                f"Columns {invalid_columns} do not exist in table '{self.table_name}'"
            )

        # Build search conditions
        conditions = [f"{col} ILIKE :search_term" for col in columns]
        where_clause = " OR ".join(conditions)

        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        if limit:
            query += f" LIMIT {limit}"

        result = self.session.execute(text(query), {"search_term": f"%{search_term}%"})
        return [dict(zip(all_columns, row)) for row in result.fetchall()]

    def filter_by_attributes(
        self, filters: Dict[str, Any], limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Filter records by multiple attributes."""
        # Validate columns exist
        all_columns = [col["name"] for col in self._get_columns()]
        invalid_columns = [col for col in filters.keys() if col not in all_columns]
        if invalid_columns:
            raise ValueError(
                f"Columns {invalid_columns} do not exist in table '{self.table_name}'"
            )

        # Build WHERE conditions
        conditions = []
        params = {}

        for i, (column, value) in enumerate(filters.items()):
            param_name = f"param_{i}"
            conditions.append(f"{column} = :{param_name}")
            params[param_name] = value

        where_clause = " AND ".join(conditions)
        query = f"SELECT * FROM {self.table_name} WHERE {where_clause}"
        if limit:
            query += f" LIMIT {limit}"

        result = self.session.execute(text(query), params)
        return [dict(zip(all_columns, row)) for row in result.fetchall()]

    def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new record."""
        from datetime import datetime, timezone

        # Validate columns exist
        all_columns = [col["name"] for col in self._get_columns()]
        invalid_columns = [col for col in data.keys() if col not in all_columns]
        if invalid_columns:
            raise ValueError(
                f"Columns {invalid_columns} do not exist in table '{self.table_name}'"
            )

        # Add timestamps if columns exist and not provided
        data_with_timestamps = data.copy()
        current_time = datetime.now(timezone.utc)

        if "created_at" in all_columns and "created_at" not in data_with_timestamps:
            data_with_timestamps["created_at"] = current_time
        if "updated_at" in all_columns and "updated_at" not in data_with_timestamps:
            data_with_timestamps["updated_at"] = current_time

        # Build INSERT query
        columns = list(data_with_timestamps.keys())
        placeholders = [f":{col}" for col in columns]

        query = f"""
            INSERT INTO {self.table_name} ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
            RETURNING *
        """

        query_params = self._adapt_outbound_data(data_with_timestamps)

        result = self.session.execute(text(query), query_params)
        self.session.commit()

        row = result.fetchone()
        return dict(zip(all_columns, row)) if row else {}

    def update(self, id_value: Any, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Update a record."""
        from datetime import datetime, timezone

        # Validate columns exist
        all_columns = [col["name"] for col in self._get_columns()]
        invalid_columns = [col for col in data.keys() if col not in all_columns]
        if invalid_columns:
            raise ValueError(
                f"Columns {invalid_columns} do not exist in table '{self.table_name}'"
            )

        pk_column = self._get_primary_key()

        # Add updated_at timestamp if column exists and not provided
        data_with_timestamps = data.copy()
        if "updated_at" in all_columns and "updated_at" not in data_with_timestamps:
            data_with_timestamps["updated_at"] = datetime.now(timezone.utc)

        # Build UPDATE query
        set_parts = [f"{col} = :{col}" for col in data_with_timestamps.keys()]
        query = f"""
            UPDATE {self.table_name}
            SET {', '.join(set_parts)}
            WHERE {pk_column} = :id
            RETURNING *
        """

        params = self._adapt_outbound_data(data_with_timestamps)
        params["id"] = id_value

        result = self.session.execute(text(query), params)
        self.session.commit()

        row = result.fetchone()
        return dict(zip(all_columns, row)) if row else None

    def delete(self, id_value: Any) -> bool:
        """Delete a record."""
        pk_column = self._get_primary_key()
        query = f"DELETE FROM {self.table_name} WHERE {pk_column} = :id"

        self.session.execute(text(query), {"id": id_value})
        self.session.commit()

        # Check if any rows were affected
        return True  # Assume success if no exception was raised

    def get_table_info(self) -> Dict[str, Any]:
        """Get information about the table structure."""
        return {
            "table_name": self.table_name,
            "columns": self._get_columns(),
            "primary_key": self._get_primary_key(),
            "row_count": self._get_row_count(),
        }

    def _get_row_count(self) -> int:
        """Get total number of rows in the table."""
        query = f"SELECT COUNT(*) FROM {self.table_name}"
        result = self.session.execute(text(query))
        count = result.scalar()
        return count if count is not None else 0

    def _adapt_outbound_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare data payloads for dialect-specific requirements (e.g. JSON adaptation)."""
        if not data:
            return data

        bind = getattr(self.session, "bind", None)
        dialect_name = getattr(getattr(bind, "dialect", None), "name", "")
        if dialect_name != "postgresql":
            return data

        try:
            from psycopg2.extras import Json  # type: ignore
        except (
            ImportError
        ):  # pragma: no cover - defensive guard for alternative drivers
            return data

        adapted = data.copy()
        for column in self._get_columns():
            column_name = column["name"]
            if column_name not in adapted:
                continue

            value = adapted[column_name]
            if value is None or isinstance(value, Json):
                continue

            if self._is_json_type(column["type"]):
                adapted[column_name] = Json(value)

        return adapted

    @staticmethod
    def _is_json_type(column_type: Any) -> bool:
        """Return True when the SQLAlchemy column type represents JSON/JSONB."""
        try:
            from sqlalchemy.types import JSON as SQLAlchemyJSON  # type: ignore
        except (
            ImportError
        ):  # pragma: no cover - SQLAlchemy always provides JSON, but guard anyway
            SQLAlchemyJSON = ()  # type: ignore

        if isinstance(column_type, SQLAlchemyJSON):
            return True

        # Fallback: inspect the SQLAlchemy type name to cover dialect-specific subclasses
        type_name = column_type.__class__.__name__.lower()
        return type_name in {"json", "jsonb"}


class TableDiscovery:
    """Utility class to discover and work with all available tables."""

    def __init__(self, session: Session):
        self.session = session

    def get_all_tables(self) -> List[str]:
        """Get all table names in the database."""
        from sqlalchemy import inspect

        inspector = inspect(self.session.bind)
        if inspector is not None:
            return inspector.get_table_names()
        else:
            raise RuntimeError("Could not create database inspector")

    def get_product_tables(self) -> List[str]:
        """Get tables that appear to be product tables (excluding system tables)."""
        all_tables = self.get_all_tables()

        # Exclude system tables and known non-product tables
        exclude_patterns = [
            "alembic_version",
            "spatial_ref_sys",
            "geography_columns",
            "geometry_columns",
            "raster_columns",
            "raster_overviews",
        ]

        product_tables = []
        for table in all_tables:
            if not any(pattern in table for pattern in exclude_patterns):
                product_tables.append(table)

        return product_tables

    def create_repository_for_table(self, table_name: str) -> DynamicRepository:
        """Create a repository instance for a specific table."""
        return DynamicRepository(self.session, table_name)

    def get_table_summary(self) -> List[Dict[str, Any]]:
        """Get summary information for all product tables."""
        summaries = []
        for table_name in self.get_product_tables():
            try:
                repo = self.create_repository_for_table(table_name)
                info = repo.get_table_info()
                summaries.append(info)
            except Exception as e:
                summaries.append({"table_name": table_name, "error": str(e)})

        return summaries


# Factory functions for easy access
def get_dynamic_repository(session: Session, table_name: str) -> DynamicRepository:
    """Create a dynamic repository for any table."""
    return DynamicRepository(session, table_name)


def get_table_discovery(session: Session) -> TableDiscovery:
    """Create a table discovery instance."""
    return TableDiscovery(session)


def discover_product_tables(session: Session) -> List[str]:
    """Discover all product tables in the database."""
    discovery = TableDiscovery(session)
    return discovery.get_product_tables()


# Legacy compatibility functions
def get_product_repository(session: Session):
    """Legacy function - now returns dynamic repository for products table."""
    return get_dynamic_repository(session, "products")


def get_product_type_repository(session: Session):
    """Legacy function - now returns dynamic repository for product_types table."""
    return get_dynamic_repository(session, "product_types")
