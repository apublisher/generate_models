# TODO

## Safe incremental model generation

### 1. Preserve `__init__.py` during partial generation

- [ ] When generating all database tables, rebuild `models/__init__.py` from scratch so it exactly represents the complete generated model set.
- [ ] When generating one table or an explicit list of tables, add or update imports for those models without removing existing imports.
- [ ] Keep the `Base` and `ModelMixin` imports.
- [ ] Avoid duplicate imports and keep model imports in a deterministic order.
- [ ] Preserve unrelated, valid content where practical during partial generation.
- [ ] Write files atomically so a failed generation cannot leave a truncated `__init__.py`.

### 2. Protect and validate `base.py`

- [ ] Do not overwrite an existing `base.py` during normal generation.
- [ ] Define the code/API that generated models require from `base.py`, including `Base` and `ModelMixin`.
- [ ] Validate that the required definitions and compatible behavior are present. Additional user code is allowed and must not by itself trigger regeneration.
- [ ] If `base.py` is missing, generate it from the current template.
- [ ] If required code is missing or incompatible, regenerate `base.py` from the current template and clearly warn that the generated file was replaced.
- [ ] Prefer a structural validation strategy (for example AST/API checks or a generator-owned version marker) rather than requiring the entire file to match byte-for-byte.
- [ ] Document that editing generated files, including `base.py`, is discouraged because incompatible changes may be replaced.

### 3. Tests and documentation

- [ ] Test full generation followed by partial generation of one table.
- [ ] Test partial generation with multiple tables.
- [ ] Verify that existing model imports survive partial generation.
- [ ] Verify that duplicate imports are not created.
- [ ] Verify that full generation removes imports for tables that no longer exist.
- [ ] Verify that a valid existing `base.py` is preserved, including additional user code.
- [ ] Verify that missing or incompatible required base code triggers regeneration.
- [ ] Update the README with the full-versus-partial generation behavior and the generated-file policy.

## Reproducible SQLAlchemy schema

### Goal and scope

The generated model package should contain enough schema metadata for
`Base.metadata.create_all(engine)` to create a functionally equivalent set of
tables in an existing empty database. Exact physical DDL reproduction is not
required.

- [ ] Document that the target database/schema itself must exist before
      `create_all()` is called.
- [ ] Ensure that importing the generated package registers every generated
      model in `Base.metadata`.
- [ ] Preserve column types and relevant dialect-specific attributes, including
      MySQL `UNSIGNED` where supported.
- [ ] Preserve primary keys, including composite primary keys.
- [ ] Generate single-column and composite unique constraints.
- [ ] Generate single-column and composite foreign-key constraints without
      reducing composite constraints to unrelated column-level foreign keys.
- [ ] Generate non-unique and unique indexes, including composite indexes.
- [ ] Preserve server-side defaults and supported `ON UPDATE` behavior.
- [ ] Generate supported check constraints.
- [ ] Preserve relevant table options such as MySQL engine, charset, and
      collation where SQLAlchemy reflection exposes them.
- [ ] Preserve constraint and index names where available.
- [ ] Define and document behavior for database features that cannot be
      represented portably by SQLAlchemy models.

### Round-trip verification

- [ ] Create an integration fixture containing representative MySQL schema
      features.
- [ ] Reflect the source schema and generate models.
- [ ] Import all generated models and run `Base.metadata.create_all()` against
      an empty target database.
- [ ] Reflect the target schema and compare it structurally with the source.
- [ ] Test nullable columns, defaults, auto-increment, enums, unsigned numeric
      types, composite keys, foreign keys, unique constraints, checks, and
      indexes.
- [ ] Make expected dialect limitations explicit in the comparison rather than
      silently ignoring them.

### Explicitly out of scope for this version

- Views and materialized views
- Triggers and stored procedures/functions
- Users, grants, and permissions
- Table data
- Exact byte-for-byte or text-for-text DDL reproduction
- Advanced physical database features such as partitioning unless they become
  necessary for functional schema equivalence
