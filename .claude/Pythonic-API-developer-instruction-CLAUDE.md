# Pythonic API Library Developer Guide

This guide teaches developers how to build Pythonic API wrapper libraries using a three-pattern architecture: Raw Data Storage, Property-Based Access, and Core Data Extraction. While examples use AWS Redshift Serverless, these patterns apply to any REST API.

## Overview

The architecture consists of three key design patterns that work together to create resilient, maintainable, and Pythonic API wrappers:

1. **Raw Data Storage Pattern**: Store original API responses unchanged
2. **Property-Based Access Pattern**: Expose data through lazy-loaded properties  
3. **Core Data Extraction Pattern**: Provide standardized minimal representations

## Architecture Patterns

### Pattern 1: Raw Data Storage

Store the complete API response in a `raw_data` attribute without modification. This preserves the original data structure and provides resilience against API schema changes.

**Implementation:**

```python
import typing as T
import dataclasses
from func_args.api import T_KWARGS, REQ, BaseModel

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_redshift_serverless.type_defs import (
        NamespaceTypeDef,
        NamespaceStatusType,
    )

@dataclasses.dataclass
class Base(BaseModel):
    raw_data: T_KWARGS = dataclasses.field(default=REQ)

@dataclasses.dataclass  
class RedshiftServerlessNamespace(Base):
    raw_data: "NamespaceTypeDef" = dataclasses.field(default=REQ)
```

**Key Benefits:**

- Preserves complete API response data
- Provides foundation for property-based access
- Enables debugging and troubleshooting with original data

### Pattern 2: Property-Based Access (Lazy Loading)

Expose all data attributes through properties instead of direct instance attributes. This enables lazy loading, data validation, and type conversion.

**Implementation:**

```python
@dataclasses.dataclass
class RedshiftServerlessNamespace(Base):
    raw_data: "NamespaceTypeDef" = dataclasses.field(default=REQ)
    
    @property
    def admin_username(self) -> T.Optional[str]:
        return self.raw_data.get("adminUsername")
        
    @property
    def status(self) -> "NamespaceStatusType":
        return self.raw_data["status"]  # Required field
        
    @property
    def is_available(self) -> bool:
        return self.status == "AVAILABLE"
```

**Property Guidelines:**

- Use `raw_data.get(key)` for optional fields (returns `None` if missing)
- Use `raw_data[key]` for required fields (raises `KeyError` if missing)  
- Add computed properties for common state checks
- Use proper type hints for all properties

### Pattern 3: Core Data Extraction

Implement a `core_data` property that returns essential information in a standardized dictionary format.

**Implementation:**

```python
@property
def core_data(self) -> T_KWARGS:
    return {
        "namespace_name": self.namespace_name,
        "namespace_id": self.namespace_id, 
        "namespace_arn": self.namespace_arn,
        "status": self.status,
        "creation_date": self.creation_date,
    }
```

**Usage Benefits:**

- Consistent interface across different model types
- Easy serialization for logging and caching
- Simplified testing and debugging

## Implementation Guide

### Step 1: Define Base Model

Create a base class that all models inherit from:

```python
# model.py
import dataclasses
from func_args.api import T_KWARGS, REQ, BaseModel

@dataclasses.dataclass
class Base(BaseModel):
    raw_data: T_KWARGS = dataclasses.field(default=REQ)

    @property
    def core_data(self) -> T_KWARGS:
        raise NotImplementedError
```

### Step 2: Implement Specific Models

Create model classes for each API resource:

```python
# model_redshift_serverless.py
import typing as T
import dataclasses
import datetime

@dataclasses.dataclass
class RedshiftServerlessNamespace(Base):
    raw_data: "NamespaceTypeDef" = dataclasses.field(default=REQ)

    # Direct API field access
    @property
    def admin_username(self) -> T.Optional[str]:
        return self.raw_data.get("adminUsername")

    @property  
    def status(self) -> "NamespaceStatusType":
        return self.raw_data["status"]

    # Computed properties
    @property
    def is_available(self) -> bool:
        return self.status == "AVAILABLE"

    # Core data extraction
    @property
    def core_data(self) -> T_KWARGS:
        return {
            "namespace_name": self.namespace_name,
            "status": self.status,
            "creation_date": self.creation_date,
        }
```

### Step 3: Create Client Functions

Implement client functions that return model instances:

```python
# client_redshift_serverless.py
def list_namespaces(
    redshift_serverless_client,
) -> RedshiftServerlessNamespaceIterProxy:
    res = redshift_serverless_client.list_namespaces()
    namespaces = [
        RedshiftServerlessNamespace(raw_data=data)
        for data in res.get("namespaces", [])
    ]
    return RedshiftServerlessNamespaceIterProxy(namespaces)
```

### Step 4: Create Public API

Expose public APIs through a centralized module:

```python
# api.py
from . import redshift_serverless_api as redshift_serverless

# redshift_serverless_api.py
from .model_redshift_serverless import RedshiftServerlessNamespace
from .client_redshift_serverless import list_namespaces
```

## Testing Patterns

### Property Testing

Use automated property testing to ensure all properties are accessible:

```python
# tests/test_property_helpers.py
def verify_all_properties(klass: T.Type[BaseModel], instance: BaseModel):
    for name, member in inspect.getmembers(klass):
        if name.startswith("_"):
            continue
        if isinstance(member, (property, cached_property)):
            try:
                getattr(instance, name)
            except Exception as e:
                raise RuntimeError(f"Property '{name}' failed: {e}") from e
```

### Manual Testing

Create manual tests for integration testing:

```python
# tests/test_model_redshift_serverless.py
class TestRedshiftServerlessNamespace:
    def test(self):
        res = bsm.redshiftserverless_client.list_namespaces()
        namespaces = [
            RedshiftServerlessNamespace(raw_data=dct)
            for dct in res.get("namespaces", [])
        ]
        namespace = namespaces[0]
        
        # Automated property testing
        verify_all_properties(RedshiftServerlessNamespace, namespace)
        
        # Manual verification of key properties
        print(f"{namespace.is_available = }")
        print(f"{namespace.core_data = }")
```

## Type Hints Best Practices

### Property Return Types

Use appropriate type hints for different scenarios:

```python
# Optional fields that may be missing from API response
@property
def admin_username(self) -> T.Optional[str]:
    return self.raw_data.get("adminUsername")

# Required fields that must exist
@property  
def status(self) -> "NamespaceStatusType":
    return self.raw_data["status"]
    
# Computed boolean properties
@property
def is_available(self) -> bool:
    return self.status == "AVAILABLE"
```

### Import Organization

Organize imports with proper conditional typing:

```python
import typing as T
import dataclasses

if T.TYPE_CHECKING:  # pragma: no cover
    from mypy_boto3_redshift_serverless.type_defs import (
        NamespaceTypeDef,
        NamespaceStatusType,
    )
```

## Project Structure

Recommended directory structure:

```
project_root/
├── your_library/
│   ├── __init__.py
│   ├── api.py                    # Public API exports
│   ├── model.py                  # Base model classes
│   ├── model_service.py          # Service-specific models
│   ├── client_service.py         # Client functions
│   └── service_api.py            # Service API module
├── tests/
│   ├── test_property_helpers.py  # Property testing utilities
│   └── test_*.py                 # Unit tests
└── tests_manual/
    └── test_*.py                 # Integration tests
```

## Summary

This architecture provides:

- **Resilience**: Raw data storage protects against API changes
- **Performance**: Lazy loading through properties  
- **Maintainability**: Clear separation of concerns
- **Type Safety**: Comprehensive type hints
- **Testability**: Automated property testing
- **Consistency**: Standardized core data interface

Follow these patterns when building Pythonic API libraries for any REST API provider. The three-pattern architecture ensures your library remains stable, performant, and easy to maintain as the underlying API evolves.