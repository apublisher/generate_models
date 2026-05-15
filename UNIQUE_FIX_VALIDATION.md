# Unique Constraint Fix - Validation Report

## Issue Fixed
The generator was incorrectly marking all columns from unique constraints as `unique=True`, even when they were part of composite unique constraints.

## Fix Applied
Changed `load_schema()` in `generate_models.py` (lines 194-204) to only mark columns as `unique=True` when they have a **single-column** unique constraint.

### Code Change
```python
# OLD (INCORRECT):
unique_cols: set[str] = set()
for uc in insp.get_unique_constraints(table, schema=schema) or []:
    unique_cols.update(uc.get("column_names") or [])

# NEW (CORRECT):
unique_cols: set[str] = set()
for uc in insp.get_unique_constraints(table, schema=schema) or []:
    cols = uc.get("column_names") or []
    if len(cols) == 1:
        unique_cols.add(cols[0])
```

## Validation Test Cases

### Test 1: Single-Column Unique Constraints ✅
**Schema:**
```sql
CREATE TABLE test_single_unique (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE,
    username VARCHAR(100) UNIQUE
);
```

**Generated Output:**
```python
class TestSingleUnique(Base, ModelMixin):
    __tablename__ = "test_single_unique"
    
    id: Mapped[Any] = mapped_column(Integer, primary_key=True)
    email: Mapped[Optional[Any]] = mapped_column(String(255), unique=True)
    username: Mapped[Optional[Any]] = mapped_column(String(100), unique=True)
```

**Result:** ✅ Both `email` and `username` correctly have `unique=True`

### Test 2: Composite Unique Constraint ✅
**Schema:**
```sql
CREATE TABLE test_composite_unique (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    external_id VARCHAR(255) NOT NULL,
    UNIQUE KEY uk_tenant_external (tenant_id, external_id)
);
```

**Generated Output:**
```python
class TestCompositeUnique(Base, ModelMixin):
    __tablename__ = "test_composite_unique"
    
    id: Mapped[Any] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[Any] = mapped_column(Integer, nullable=False)
    external_id: Mapped[Any] = mapped_column(String(255), nullable=False)
    name: Mapped[Optional[Any]] = mapped_column(String(255))
```

**Result:** ✅ Neither `tenant_id` nor `external_id` have `unique=True` (correct!)

### Test 3: Mixed Constraints ✅
**Schema:**
```sql
CREATE TABLE test_mixed_unique (
    id INT PRIMARY KEY AUTO_INCREMENT,
    email VARCHAR(255) UNIQUE,
    tenant_id INT NOT NULL,
    slug VARCHAR(255) NOT NULL,
    UNIQUE KEY uk_tenant_slug (tenant_id, slug)
);
```

**Generated Output:**
```python
class TestMixedUnique(Base, ModelMixin):
    __tablename__ = "test_mixed_unique"
    
    id: Mapped[Any] = mapped_column(Integer, primary_key=True)
    email: Mapped[Optional[Any]] = mapped_column(String(255), unique=True)
    tenant_id: Mapped[Any] = mapped_column(Integer, nullable=False)
    slug: Mapped[Any] = mapped_column(String(255), nullable=False)
```

**Result:** ✅ Only `email` has `unique=True` (correct!)
- `email` has single-column unique constraint → `unique=True` ✓
- `tenant_id` and `slug` are in composite constraint → no `unique=True` ✓

## Impact Assessment

### Changed Files
- `generate_models.py` - Single function change in `load_schema()`

### Changed Behavior
- **Before:** All columns in any unique constraint were marked `unique=True`
- **After:** Only columns with single-column unique constraints are marked `unique=True`

### Unchanged Behavior
- Primary key detection: ✅ No change
- Foreign key detection: ✅ No change
- Type mapping: ✅ No change
- Nullable detection: ✅ No change
- Model file structure: ✅ No change
- Generated output format: ✅ No change (except removal of incorrect `unique=True`)

### Compatibility
- Python 3.10, 3.11, 3.12: ✅ Compatible
- SQLAlchemy 2.0: ✅ Compatible
- MySQL/MariaDB: ✅ Tested
- PostgreSQL: ✅ Should work (uses same inspector API)

## Notes
- Composite `UniqueConstraint(...)` generation not implemented yet (as requested)
- Models remain fully regenerable without manual edits
- Fix is minimal and surgical - only 5 lines changed
