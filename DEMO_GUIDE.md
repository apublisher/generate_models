# Demo.py Quick Reference

## Starting the Demo

```bash
.venv/bin/python demo.py
```

## Commands

- `list` - Show all available models
- `info MODEL_NAME` - Inspect a specific model (columns, types, record count)
- `demos` - Run all demo functions
- `help` - Show help
- `exit` - Exit the demo

## Basic SQLAlchemy Operations

### Query Examples (to use in the demo or your code)

```python
from sqlalchemy import select
from models import Apv3User

# Get one record by primary key
user = session.get(Apv3User, 1)

# Get first record
user = session.query(Apv3User).first()

# Get all records
users = session.query(Apv3User).all()

# Filter with WHERE clause
stmt = select(Apv3User).where(Apv3User.email == 'test@example.com')
user = session.execute(stmt).scalar()

# Filter with LIKE
from sqlalchemy import or_
stmt = select(Apv3User).where(Apv3User.name.like('%John%'))
users = session.execute(stmt).scalars().all()

# Multiple conditions (AND)
stmt = select(Apv3User).where(
    Apv3User.status == 'active',
    Apv3User.email.like('%@example.com')
)
users = session.execute(stmt).scalars().all()

# Multiple conditions (OR)
stmt = select(Apv3User).where(
    or_(
        Apv3User.status == 'active',
        Apv3User.status == 'pending'
    )
)
users = session.execute(stmt).scalars().all()

# Ordering
stmt = select(Apv3User).order_by(Apv3User.name)
users = session.execute(stmt).scalars().all()

# Limit and offset
stmt = select(Apv3User).limit(10).offset(20)
users = session.execute(stmt).scalars().all()

# Count records
from sqlalchemy import func
count = session.query(func.count(Apv3User.id)).scalar()
```

### Create (INSERT)

```python
# Method 1: Create and set attributes
new_user = Apv3User()
new_user.name = 'John Doe'
new_user.email = 'john@example.com'
session.add(new_user)
session.commit()

# Method 2: Use from_dict()
new_user = Apv3User()
new_user.from_dict({'name': 'Jane Doe', 'email': 'jane@example.com'})
session.add(new_user)
session.commit()

# Method 3: Constructor (if columns match)
new_user = Apv3User(name='Bob Smith', email='bob@example.com')
session.add(new_user)
session.commit()
```

### Update (UPDATE)

```python
# Get the record
user = session.get(Apv3User, 1)

# Method 1: Direct assignment
user.name = 'Updated Name'
session.commit()

# Method 2: Use update()
user.update(name='Updated Name', status='active')
session.commit()

# Method 3: Use from_dict()
user.from_dict({'name': 'New Name', 'email': 'new@example.com'})
session.commit()
```

### Delete (DELETE)

```python
user = session.get(Apv3User, 1)
session.delete(user)
session.commit()
```

## Using the Utility Methods

```python
user = session.get(Apv3User, 1)

# Convert to dictionary
data = user.to_dict()
print(data)

# Convert to dictionary (exclude fields)
data = user.to_dict(exclude=['password', 'secret_token'])

# Convert to JSON string
json_str = user.to_json()
json_str = user.to_json(indent=2)  # Pretty print

# Get primary key value
pk = user.get_pk()
print(f"User ID: {pk}")

# Clone a record (useful for duplicating)
new_user = user.clone()  # Excludes primary key
session.add(new_user)
session.commit()

# String representation
print(user)  # <Apv3User(pk=1)>
```

## Working with Relationships (if foreign keys exist)

```python
# If you have a foreign key relationship
order = session.get(InternalOrder, 1)

# Access related records (you may need to configure relationships manually)
# lines = order.lines  # This would work if relationships are set up
```

## Transaction Management

```python
try:
    # Multiple operations
    new_user = Apv3User(name='Test', email='test@example.com')
    session.add(new_user)
    
    another_user = Apv3User(name='Test2', email='test2@example.com')
    session.add(another_user)
    
    # Commit all at once
    session.commit()
except Exception as e:
    # Rollback on error
    session.rollback()
    print(f"Error: {e}")
finally:
    session.close()
```

## Tips for PHP/Laminas Developers

| PHP/Laminas | SQLAlchemy |
|-------------|------------|
| `$table->select()->where(['id' => 1])` | `session.query(Model).where(Model.id == 1)` |
| `$row->toArray()` | `model.to_dict()` |
| `$row->save()` | `session.commit()` |
| `$table->insert($data)` | `session.add(Model(**data))` + `session.commit()` |
| `$row->delete()` | `session.delete(row)` + `session.commit()` |

## Common Gotchas

1. **Always commit**: Changes aren't saved until you call `session.commit()`
2. **Session management**: Close sessions when done (`session.close()`)
3. **Query vs Select**: Both work, but `select()` is the modern 2.0 style
4. **Relationships**: Auto-generated models don't include relationships - add manually if needed
