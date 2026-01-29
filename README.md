# Flask-SQLAlchemy Model Generator

Generate Flask-SQLAlchemy ORM model files from existing database schemas.

## Features

- 🚀 Generate models from existing MySQL/MariaDB/PostgreSQL databases
- 🎯 Smart type mapping (handles datetime, Decimal, JSON, etc.)
- 🔧 Rich utility methods (to_dict, to_json, update, clone, etc.)
- ✅ Type-safe with full type hints
- 📦 Use as CLI tool or Python library
- 🔍 Check for tables without primary keys
- 🎨 Generate only specific tables or all at once

## Installation

### From GitHub
```bash
# Basic installation
pip install git+https://github.com/apublisher/generate_models.git

# With MySQL/MariaDB support
pip install "git+https://github.com/apublisher/generate_models.git#egg=flask-sqlalchemy-model-generator[mysql]"

# With PostgreSQL support
pip install "git+https://github.com/apublisher/generate_models.git#egg=flask-sqlalchemy-model-generator[postgresql]"

# For development
pip install "git+https://github.com/apublisher/generate_models.git#egg=flask-sqlalchemy-model-generator[dev]"
```

### From source (for local development)
```bash
git clone https://github.com/apublisher/generate_models.git
cd generate_models
pip install -e .
```

## Quick Start

### 1. Set up database connection

Create a `.env` file:
```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/database_name
```

### 2. Generate models

```bash
# Generate all models
generate-models

# Generate specific tables
generate-models users products orders

# Check for tables without primary keys
generate-models --check-pk

# Custom output directory
generate-models --out my_models

# Override database URL
generate-models --db-url mysql+pymysql://user:pass@host/db
```

## Usage as Library

```python
from generate_models import main

# Generate all models
result = main(
    db_url="mysql+pymysql://user:pass@localhost/db",
    out_dir="models",
)

# Generate specific tables
result = main(
    db_url="mysql+pymysql://user:pass@localhost/db",
    table_names=["users", "products"],
)

# Check for tables without PKs
result = main(
    db_url="mysql+pymysql://user:pass@localhost/db",
    check_pk_only=True,
)

print(f"Generated {result['tables_generated']} models")
print(f"Skipped {len(result['tables_skipped'])} tables without PKs")
```

## Generated Model Features

### Utility Methods

Every generated model includes:

```python
from models import User

user = session.get(User, 1)

# Convert to dictionary
data = user.to_dict()
data = user.to_dict(exclude=['password'])  # Exclude sensitive fields

# Convert to JSON
json_str = user.to_json(indent=2)

# Update from dictionary
user.from_dict({'name': 'John', 'email': 'john@example.com'})

# Quick updates
user.update(name='Jane', status='active')  # Strict by default
user.update(strict=False, name='Jane', unknown_field='ignored')

# Get primary key
user_id = user.get_pk()

# Clone record (excludes PK by default)
new_user = user.clone()
session.add(new_user)
session.commit()
```

### SQLAlchemy 2.0 Style

Generated models work with modern SQLAlchemy 2.0 syntax:

```python
from sqlalchemy import select
from models import User

# Query examples
stmt = select(User).where(User.email == 'test@example.com')
user = session.execute(stmt).scalar()

# Multiple conditions
stmt = select(User).where(
    User.active == 1,
    User.email.like('%@gmail.com')
)
users = session.execute(stmt).scalars().all()
```

## Configuration

### Environment Variables

- `DATABASE_URL`: Database connection string

### Command Line Options

```
--db-url TEXT       Database URL (overrides .env)
--out TEXT         Output directory (default: models)
--schema TEXT      Database schema name
--check-pk         Only check for missing primary keys
tables            Specific table names (optional)
```

## Requirements

- Python 3.10+
- SQLAlchemy 2.0+
- python-dotenv
- Database driver (pymysql, psycopg2, etc.)

## Examples

See the included examples:
- `example_select.py` - Query examples with WHERE clauses
- `demo.py` - Interactive demo tool
- `check_tables.py` - Check database tables

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run type checking
mypy generate_models.py

# Format code
black generate_models.py
```

## License

MIT License - see LICENSE file for details

## Contributing

Contributions welcome! Please feel free to submit a Pull Request.
