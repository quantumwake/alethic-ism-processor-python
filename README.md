# Alethic Instruction-Based State Machine (Python Processor)

Executes python code in a semi-secure environment using RestrictedPython. This allows for input streams and or events to process inbound messages using python and produce output stream and or events.

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

#### Example of a runnable that uses the `process` method to process queries add a counter and return the result:

```python
class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:

        c = self.context['counter']
        self.context['counter'] = c + 1
        self.context['other'] = f"other_{c}"

        return [{
            'index': self.context['counter'],
            **query
        } for query in queries]

    def process_stream(self, queries: List[Any]) -> Any:
        # yield from (self.process(query) for query in queries)
        pass
```

#### Example of a runnable that uses the `get_stock_data` method to get stock data:
```python
class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:
        self.logger.info("test message")
        ticker = "AAPL"
        stock_data = self.get_stock_data(ticker)
        if stock_data:
            stock_data = stock_data['Time Series (5min)']
            stock_data = list(stock_data.items())[0]
            stock_data = stock_data[1]

        return [{
            'ticker': ticker,
            **stock_data,
            **query
        } for query in queries]

    def process_stream(self, query: Dict) -> Any:
        yield json.dumps(query, indent=2)
    
```

#### Basic input -> output direct feed
```python
class Runnable(BaseSecureRunnable):
    def init(self):
        self.context['counter'] = 0

    def process(self, queries: List[Any]) -> List[Any]:
        return [{
            **self.query_stock(query),
            **query
        } for query in queries]

    def process_stream(self, query: Dict) -> Any:
        yield json.dumps({
            **query,
            **self.query_stock(query)
        }, indent=2)
```

#### Example of a runnable that uses the `query_stock` method to get stock data:
```python

config = SecurityConfig(
    max_memory_mb=100,
    max_cpu_time_seconds=5,
    max_requests=50,
    allowed_domains=["*"],
    execution_timeout=10,
    enable_resource_limits=False
)

try:
    # Create builder
    builder = SecureRunnableBuilder(config)

    # Compile and instantiate the runnable
    runnable = builder.compile(user_code3)

    # Use the runnable
    # for i in range(5):
    #   result = runnable.process(queries=[{'test': 'data'}])
    #   print(f"Query result: {result}")

    result = runnable.process(queries=[{'is_stock_question': 'true', 'ticker': 'AAPL'}])
    print(f"Query result: {result}")

    # batch_result = runnable.process_async([
    #     {'test': 'data1'},
    #     {'test': 'data2'}
    # ])
    # print(f"Batch result: {batch_result}")
except Exception as e:
    print(f"Error: {str(e)}")

```