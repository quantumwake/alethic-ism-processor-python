#!/usr/bin/env python3
"""
Stock Data Processor Example for Alethic ISM Python Processor

This example demonstrates how to:
1. Configure the secure environment
2. Create a runnable that processes stock data
3. Query for specific stock information
"""

from ismcore.compiler.secure_runnable import SecurityConfig, SecureRunnableBuilder
import json

# Define a stock data processor runnable
stock_processor_code = """
from typing import Any, Dict, List
import json

class Runnable(BaseSecureRunnable):
    def init(self):
        # Initialize tracking in context
        self.context['processed_tickers'] = []
    
    def process(self, queries: List[Any]) -> List[Any]:
        results = []
        
        for query in queries:
            # Extract ticker if present, otherwise use default
            ticker = query.get('ticker', 'AAPL')
            
            # Track the processed ticker
            self.context['processed_tickers'].append(ticker)
            
            # Get stock data using the helper method
            stock_data = self.get_stock_data(ticker)
            
            # Process stock data if available
            if stock_data and 'Time Series (5min)' in stock_data:
                # Get the most recent data point
                time_series = stock_data['Time Series (5min)']
                latest_data = list(time_series.items())[0]
                timestamp, data = latest_data
                
                # Add processed data to result
                results.append({
                    'ticker': ticker,
                    'timestamp': timestamp,
                    'data': data,
                    'history_count': len(self.context['processed_tickers']),
                    **query
                })
            else:
                # Handle case where stock data isn't available
                results.append({
                    'ticker': ticker,
                    'error': 'No stock data available',
                    'history_count': len(self.context['processed_tickers']),
                    **query
                })
        
        # Log for debugging
        self.logger.info(f"Processed {len(queries)} stock queries")
        return results
    
    def process_stream(self, query: Dict) -> Any:
        # Extract ticker if present
        ticker = query.get('ticker', 'AAPL')
        
        # Get stock data
        stock_data = self.get_stock_data(ticker)
        
        # Stream the result
        yield json.dumps({
            'ticker': ticker,
            'streaming': True,
            'data_available': stock_data is not None,
            **query
        }, indent=2)
        
        # If data is available, stream each time point
        if stock_data and 'Time Series (5min)' in stock_data:
            time_series = stock_data['Time Series (5min)']
            for timestamp, data in list(time_series.items())[:5]:  # Limit to 5 points
                yield json.dumps({
                    'ticker': ticker,
                    'timestamp': timestamp,
                    'data': data
                }, indent=2)
"""

def main():
    # Set up security configuration
    config = SecurityConfig(
        max_memory_mb=100,
        max_cpu_time_seconds=5,
        max_requests=10,
        allowed_domains=["*"],
        execution_timeout=10,
        enable_resource_limits=False  # Set to True in production
    )
    
    try:
        # Create the secure runnable builder
        builder = SecureRunnableBuilder(config)
        
        # Compile the runnable code
        runnable = builder.compile(stock_processor_code)
        
        # Process multiple stock queries
        print("\n=== Processing Stock Queries ===")
        queries = [
            {'ticker': 'AAPL', 'request_type': 'price_check'},
            {'ticker': 'MSFT', 'request_type': 'price_check'},
            {'ticker': 'GOOGL', 'request_type': 'price_check'}
        ]
        
        results = runnable.process(queries=queries)
        print(f"\nStock Query Results:")
        print(json.dumps(results, indent=2))
        
        # Demonstrate streaming
        print("\n=== Processing Stream Stock Query ===")
        stream_query = {'ticker': 'AMZN', 'stream_type': 'time_series'}
        for result in runnable.process_stream(stream_query):
            print(result)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()