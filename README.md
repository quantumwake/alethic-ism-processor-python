# Alethic Instruction-Based State Machine (Python Processor)

A component of the Alethic ISM framework that executes Python code in a semi-secure environment using RestrictedPython. This processor allows for input streams and events to process inbound messages using Python and produce output streams and/or events.

## Overview

The Python Processor:
- Creates a secure execution environment with configurable resource limitations
- Processes input queries through user-defined Python code
- Supports both batch processing and streaming operations
- Provides built-in state management capabilities
- Integrates with the broader ISM messaging system

## Usage

To use the Python Processor, you create a `Runnable` class that defines how your input data should be processed:

```python
## Template to customize a python state
class Runnable(BaseSecureRunnable):
    ## any initialization parameters you want to save (on a per event basis)
    def init(self):
        self.context['counter'] = 0

    ## if the state is using a python state type
    def process(self, queries: List[Any]) -> List[Any]:
        logger.info(queries)
        return [{
            **self.query_stock(query),
            **query
        } for query in queries]

    ## if the state is using a stream state type
    def process_stream(self, query: Dict) -> Any:
        yield json.dumps({
            **query,
            **self.query_stock(query)
        }, indent=2)
```

## Examples

### Example 1: State Counter

This example demonstrates maintaining state between requests by incrementing a counter and adding it to each query result:

```python
class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:
        # Get current counter value
        c = self.context['counter']

        # Increment counter and store additional state
        self.context['counter'] = c + 1
        self.context['other'] = f"other_{c}"

        # Return processed queries with counter added
        return [{
            'index': self.context['counter'],
            **query
        } for query in queries]

    def process_stream(self, queries: List[Any]) -> Any:
        # Stream processing implementation
        # yield from (self.process(query) for query in queries)
        pass
```

### Example 2: Stock Data Retrieval

This example shows how to use the built-in `get_stock_data` method to fetch and process stock information:

```python
class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:
        # Log message for debugging
        self.logger.info("Processing stock data request")

        # Get stock data for Apple
        ticker = "AAPL"
        stock_data = self.get_stock_data(ticker)

        # Process the stock data if available
        if stock_data:
            stock_data = stock_data['Time Series (5min)']
            stock_data = list(stock_data.items())[0]
            stock_data = stock_data[1]

        # Return processed results
        return [{
            'ticker': ticker,
            **stock_data,
            **query
        } for query in queries]

    def process_stream(self, query: Dict) -> Any:
        # Stream JSON response
        yield json.dumps(query, indent=2)
```

### Example 3: Basic Input-Output Processing

A simple example that passes through input queries with optional stock data:

```python
class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:
        # Process each query and add stock data if applicable
        return [{
            **self.query_stock(query),
            **query
        } for query in queries]

    def process_stream(self, query: Dict) -> Any:
        # Stream result as formatted JSON with query and stock data
        yield json.dumps({
            **query,
            **self.query_stock(query)
        }, indent=2)
```

### Example 4: Using the Python Processor with the SecureRunnableBuilder

This example demonstrates how to set up and use the Python Processor with security configurations:

```python
from ismcore.compiler.secure_runnable import SecurityConfig, SecureRunnableBuilder

# Define security configuration
config = SecurityConfig(
    max_memory_mb=100,              # Limit memory usage to 100MB
    max_cpu_time_seconds=5,         # Limit CPU time to 5 seconds
    max_requests=50,                # Limit to 50 external requests
    allowed_domains=["*"],          # Allow all domains for HTTP requests
    execution_timeout=10,           # Timeout after 10 seconds
    enable_resource_limits=False    # Disable resource limiting for testing
)

# Your Runnable class code
user_code = """
class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:
        return [{
            **self.query_stock(query),
            **query
        } for query in queries]
"""

try:
    # Create builder with security config
    builder = SecureRunnableBuilder(config)

    # Compile and instantiate the runnable
    runnable = builder.compile(user_code)

    # Process a single query
    result = runnable.process(queries=[{'is_stock_question': 'true', 'ticker': 'AAPL'}])
    print(f"Query result: {result}")

    # Process multiple queries asynchronously
    # batch_result = runnable.process_async([
    #     {'test': 'data1'},
    #     {'test': 'data2'}
    # ])
    # print(f"Batch result: {batch_result}")
except Exception as e:
    print(f"Error: {str(e)}")
```

## Security Considerations

The Python Processor uses RestrictedPython to create a controlled execution environment with:

- Memory usage limitations
- CPU time restrictions
- Network access controls
- Execution timeouts
- Resource limiting capabilities

These security features help prevent malicious code execution while allowing for flexible Python processing within the ISM framework.