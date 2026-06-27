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
