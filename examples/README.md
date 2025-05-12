# Alethic ISM Python Processor Examples

This directory contains examples demonstrating how to use the Alethic Instruction-Based State Machine (ISM) Python Processor.

## Available Examples

### 1. Basic Counter (`basic_counter.py`)

A simple example that demonstrates:
- Setting up the security configuration
- Creating a runnable that maintains state using a counter
- Processing multiple batches of queries
- Using the streaming API

Run with:
```bash
python3 basic_counter.py
```

### 2. Stock Data Processor (`stock_data_processor.py`)

An example showing how to:
- Query stock data using the built-in API
- Process multiple stock queries in a batch
- Track state between requests
- Stream stock data results

Run with:
```bash
python3 stock_data_processor.py
```

## Usage Notes

- These examples assume you have the `ismcore` package installed
- The security configuration is set to be permissive for demonstration purposes
- In production environments, you should enable resource limits and set appropriate restrictions

## Key Concepts

1. **Secure Environment**: All code runs in a restricted Python environment with configurable resource limits
2. **State Management**: The `self.context` dictionary allows maintaining state between requests
3. **Batch Processing**: The `process` method handles multiple queries at once
4. **Streaming**: The `process_stream` method yields results incrementally
5. **Built-in Helpers**: Methods like `get_stock_data` provide access to external data in a controlled manner