# Design Patterns and Architecture

This document describes the design patterns and architectural decisions implemented in the Notion Task Runner project.

## Core Architectural Patterns

### 1. Abstract Factory Pattern - Task Creation

**Location**: `src/notion_task_runner/container.py`

The application uses dependency injection to create different types of tasks through an ApplicationContainer:

```python
from dependency_injector import containers, providers

class ApplicationContainer(containers.DeclarativeContainer):
    # Database and client providers
    notion_client = providers.Singleton(AsyncNotionClient)
    notion_database = providers.Factory(NotionDatabase, client=notion_client)
    
    # Task providers
    pas_page_task = providers.Factory(
        PASPageTask,
        client=notion_client,
        db=notion_database,
        config=config,
        calculator=sum_calculator
    )
```

**Benefits**:
- Centralized object creation and configuration
- Easy dependency management and testing
- Loose coupling between components

### 2. Template Method Pattern - Base Page Tasks

**Location**: `src/notion_task_runner/tasks/base_page_task.py`

The `NotionPageUpdateTask` defines the skeleton of an algorithm for updating Notion pages:

```python
class NotionPageUpdateTask(Task, HTTPClientMixin):
    async def run(self) -> None:
        """Template method defining the algorithm steps."""
        database_id = self.get_database_id()      # Step 1: Get data source
        column_name = self.get_column_name()      # Step 2: Define calculation
        
        rows = await self.db.fetch_rows(database_id)                    # Step 3: Fetch data
        total_value = self.calculator.calculate_total_for_column(...)   # Step 4: Calculate
        await self._update_callout_block(total_value)                   # Step 5: Update page
    
    @abstractmethod
    def get_database_id(self) -> str: pass
    
    @abstractmethod
    def get_column_name(self) -> str: pass
    
    @abstractmethod 
    def get_display_text(self, total_value: float) -> str: pass
```

**Benefits**:
- Code reuse across different page update tasks
- Consistent algorithm structure
- Easy to add new page update tasks

### 3. Mixin Pattern - HTTP Client Functionality  

**Location**: `src/notion_task_runner/utils/http_client.py`

The `HTTPClientMixin` provides common HTTP functionality to multiple classes:

```python
class HTTPClientMixin:
    async def _make_notion_request(self, method: str, url: str, headers: dict, data: dict | None = None):
        """Common HTTP request logic with retries and error handling."""
        # Retry logic, error handling, logging
        
    async def _make_parallel_requests(self, requests: list, max_concurrent: int = 5):
        """Parallel request execution with concurrency control."""
        # Semaphore-based concurrency control
```

**Usage**:
```python
class StatsTask(Task, HTTPClientMixin):
    async def _update_row_property(self, page_id: str, new_value: Any):
        await self._make_notion_request("PATCH", url, headers, data)
```

**Benefits**:
- Shared HTTP functionality without inheritance restrictions
- Consistent error handling and retry logic
- Testable with mock compatibility

### 4. Strategy Pattern - Sum Calculation

**Location**: `src/notion_task_runner/tasks/pas/sum_calculator.py`

Different calculation strategies can be implemented and injected:

```python
class SumCalculator:
    def calculate_total_for_column(self, rows: list, column_name: str) -> float:
        """Strategy for calculating column totals."""
        return sum(row["properties"][column_name]["number"] for row in rows)
```

**Benefits**:
- Pluggable calculation algorithms
- Easy to add new calculation strategies
- Testable in isolation

### 5. Singleton Pattern - Async Notion Client

**Location**: `src/notion_task_runner/notion/async_notion_client.py`

The AsyncNotionClient uses a singleton pattern to manage shared resources:

```python
class AsyncNotionClient:
    _instance: Optional['AsyncNotionClient'] = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    async def reset_singleton(cls) -> None:
        """Clean up singleton instance and resources."""
        if cls._instance and hasattr(cls._instance, "_session") and cls._instance._session:
            await cls._instance.close()
        cls._instance = None
```

**Benefits**:
- Shared HTTP session management
- Resource efficiency
- Centralized connection handling

### 6. Domain Model Pattern - Statistics Entities

**Location**: `src/notion_task_runner/tasks/statistics/models.py`

Rich domain models with validation and behavior:

```python
@dataclass(frozen=True)
class Watch:
    name: str
    cost: int
    purchased_date: str

    def __post_init__(self) -> None:
        if self.cost < 0:
            raise ValueError("Watch cost cannot be negative")
        if not self.name.strip():
            raise ValueError("Watch name cannot be empty")

@dataclass(frozen=True) 
class WorkspaceStats:
    total_watches: int
    total_watch_cost: int
    # ... more fields
    
    @property
    def total_items(self) -> int:
        """Business logic as property."""
        return self.total_watches + self.total_cables + ...
    
    @property 
    def total_cost(self) -> int:
        """Calculated property for total cost."""
        return self.total_watch_cost + self.total_vinyl_cost
```

**Benefits**:
- Encapsulated business logic
- Data validation at creation time
- Immutable value objects
- Self-documenting code

### 7. Repository Pattern - Data Access

**Location**: `src/notion_task_runner/notion/notion_database.py`

Abstraction layer for data access:

```python
class NotionDatabase:
    async def fetch_rows(self, database_id: str) -> list[dict]:
        """Abstract data access method."""
        # Implementation details hidden from business logic
```

**Benefits**:
- Separation of data access from business logic
- Easy to mock for testing
- Can be replaced with different data sources

## Error Handling Patterns

### 1. Retry Pattern with Exponential Backoff

**Location**: `src/notion_task_runner/utils/http_client.py`

```python
@retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_exponential(multiplier=1, min=DEFAULT_RETRY_WAIT_SECONDS, max=10),
    reraise=True,
)
async def _make_notion_request(self, ...):
    # Request implementation with automatic retries
```

### 2. Custom Exception Hierarchy

**Location**: `src/notion_task_runner/utils/http_client.py`

```python
class NotionHTTPError(Exception):
    """Domain-specific exception with structured data."""
    def __init__(self, status_code: int, message: str, response_data: dict | None = None):
        self.status_code = status_code
        self.response_data = response_data
        super().__init__(f"Notion API error {status_code}: {message}")
```

## Testing Patterns

### 1. Dependency Injection for Testing

Mocks are easily injected through the container pattern:

```python
# In tests
mock_client = AsyncMock()
task = PASPageTask(client=mock_client, db=mock_db, ...)
await task.run()
mock_client.patch.assert_called_once()
```

### 2. HTTPClientMixin Test Compatibility

The mixin automatically detects mock clients:

```python
# Production: Creates real aiohttp session
# Testing: Uses injected mock client
if hasattr(self, 'client') and self.client:
    response = await self.client.patch(url, headers=headers, json=data)
else:
    async with aiohttp.ClientSession() as session:
        # Real HTTP calls
```

## Performance Patterns

### 1. Concurrent Execution

**Location**: `src/notion_task_runner/tasks/statistics/stats_fetcher.py`

```python
# Fetch all data concurrently
rows_watches, rows_cables, rows_prylar, rows_vinyls = await asyncio.gather(
    self.db.fetch_rows(self.WATCHES_DB_ID),
    self.db.fetch_rows(self.CABLES_DB_ID),
    self.db.fetch_rows(self.PRYLAR_DB_ID), 
    self.db.fetch_rows(self.VINYLS_DB_ID),
)
```

### 2. Parallel Request Processing

**Location**: `src/notion_task_runner/utils/http_client.py`

```python
async def _make_parallel_requests(self, requests: list, max_concurrent: int = 5):
    semaphore = asyncio.Semaphore(max_concurrent)
    # Process requests with controlled concurrency
```

## Best Practices Implemented

1. **Separation of Concerns**: Each class has a single responsibility
2. **Dependency Inversion**: High-level modules don't depend on low-level modules
3. **Open/Closed Principle**: Open for extension, closed for modification
4. **Interface Segregation**: Small, focused interfaces
5. **DRY (Don't Repeat Yourself)**: Common patterns extracted to mixins and utilities
6. **Fail Fast**: Early validation in domain models
7. **Immutable Data**: Use of frozen dataclasses for value objects
8. **Async/Await**: Proper async patterns throughout
9. **Type Safety**: Comprehensive type annotations
10. **Error Handling**: Structured exceptions and retry logic

This architecture supports maintainability, testability, and extensibility while following established design patterns and Python best practices.