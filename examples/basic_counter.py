#!/usr/bin/env python3
"""
Basic Counter Example for Alethic ISM Python Processor

This example demonstrates how to:
1. Configure the secure environment
2. Create a simple counter runnable
3. Process multiple queries
"""

from ismcore.compiler.secure_runnable import SecurityConfig, SecureRunnableBuilder
import json

# Define a simple counter runnable
counter_code = """
from typing import Any, Dict, List
import json

class Runnable(BaseSecureRunnable):
    def init(self):
        # Initialize counter in context
        self.context['counter'] = 0
    
    def process(self, queries: List[Any]) -> List[Any]:
        # Increment the counter for each batch of queries
        c = self.context['counter']
        self.context['counter'] = c + 1
        
        # Add counter to each query result
        results = []
        for i, query in enumerate(queries):
            results.append({
                'query_index': i,
                'batch_number': self.context['counter'],
                'previous_count': c,
                **query
            })
        
        # Log for debugging
        self.logger.info(f"Processed batch #{self.context['counter']} with {len(queries)} queries")
        
        return results
    
    def process_stream(self, query: Dict) -> Any:
        # Stream processing
        yield json.dumps({
            'streaming': True,
            'counter': self.context['counter'],
            **query
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
        runnable = builder.compile(counter_code)
        
        # Process multiple batches of queries
        print("\n=== Processing Batch Queries ===")
        for i in range(3):
            queries = [
                {'message': f'Query A in batch {i+1}'},
                {'message': f'Query B in batch {i+1}'}
            ]
            results = runnable.process(queries=queries)
            print(f"\nBatch {i+1} Results:")
            print(json.dumps(results, indent=2))
        
        # Demonstrate streaming
        print("\n=== Processing Stream Query ===")
        stream_query = {'stream_message': 'Testing stream processing'}
        for result in runnable.process_stream(stream_query):
            print(result)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    main()