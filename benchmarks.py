#!/usr/bin/env python3
"""
Performance benchmarks for the noexcept package.
"""

import time
import threading
from multiprocessing import Process, Queue
from typing import List
import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from noexcept import no

def timeit(func, iterations: int = 1000):
    """Time a function execution"""
    start = time.perf_counter()
    for _ in range(iterations):
        func()
    end = time.perf_counter()
    return (end - start) / iterations * 1000  # Return ms per iteration

def benchmark_code_registration():
    """Benchmark registering error codes"""
    def register_codes():
        for i in range(100):
            no.likey(1000 + i, f"Test error {i}")
    
    no.dice()  # Clear state
    avg_time = timeit(register_codes, 100)
    print(f"Code registration: {avg_time:.4f} ms per 100 codes")

def benchmark_simple_exception_raising():
    """Benchmark raising simple exceptions"""
    no.likey(2000, "Benchmark error")
    
    def raise_exception():
        try:
            no(2000)
        except no.way:
            pass
    
    avg_time = timeit(raise_exception, 1000)
    print(f"Simple exception raising: {avg_time:.4f} ms per exception")

def benchmark_soft_exceptions():
    """Benchmark soft exception accumulation"""
    no.likey(3000, "Soft error", soft=True)
    
    def soft_exception():
        no(3000)
    
    no.dice()  # Clear state
    avg_time = timeit(soft_exception, 1000)
    print(f"Soft exception accumulation: {avg_time:.4f} ms per exception")

def benchmark_exception_linking():
    """Benchmark linking existing exceptions"""
    no.likey(4000, "Linked error")
    
    def link_exception():
        try:
            raise ValueError("Original error")
        except ValueError as ve:
            try:
                no(4000, ve)
            except no.way:
                pass
    
    avg_time = timeit(link_exception, 1000)
    print(f"Exception linking: {avg_time:.4f} ms per linked exception")

def benchmark_exception_groups():
    """Benchmark creating exception groups"""
    no.likey(5000, "Group error 1")
    no.likey(5001, "Group error 2")
    no.likey(5002, "Group error 3")
    
    def create_group():
        try:
            no([5000, 5001, 5002])
        except ExceptionGroup:
            pass
    
    avg_time = timeit(create_group, 1000)
    print(f"Exception groups (3 codes): {avg_time:.4f} ms per group")

def benchmark_builder_pattern():
    """Benchmark the builder pattern"""
    no.likey(6000, "Builder error 1")
    no.likey(6001, "Builder error 2")
    
    def use_builder():
        try:
            exc = (no.build()
                   .withCode(6000, "Custom message 1")
                   .withCode(6001, "Custom message 2")
                   .asSoft(6000)
                   .build())
        except Exception:
            pass
    
    avg_time = timeit(use_builder, 1000)
    print(f"Builder pattern (2 codes): {avg_time:.4f} ms per build")

def benchmark_threading_safety():
    """Benchmark thread safety"""
    def worker(thread_id: int, results: List[float]):
        no.likey(7000 + thread_id, f"Thread error {thread_id}")
        
        def thread_work():
            try:
                no(7000 + thread_id)
            except no.way:
                pass
        
        start = time.perf_counter()
        for _ in range(100):
            thread_work()
        end = time.perf_counter()
        results.append((end - start) / 100 * 1000)
    
    # Test with multiple threads
    num_threads = 4
    results = []
    threads = []
    
    for i in range(num_threads):
        thread = threading.Thread(target=worker, args=(i, results))
        threads.append(thread)
        thread.start()
    
    for thread in threads:
        thread.join()
    
    avg_time = sum(results) / len(results)
    print(f"Threading safety ({num_threads} threads): {avg_time:.4f} ms per exception")

def benchmark_memory_usage():
    """Benchmark memory usage with many exceptions"""
    import tracemalloc
    
    no.likey(8000, "Memory test", soft=True)
    
    tracemalloc.start()
    
    # Create many soft exceptions
    for _ in range(1000):
        no(8000, f"Memory test {_}")
    
    current, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    
    print(f"Memory usage (1000 soft exceptions): {current / 1024 / 1024:.2f} MB current, {peak / 1024 / 1024:.2f} MB peak")
    
    no.dice()  # Clean up

def run_all_benchmarks():
    """Run all performance benchmarks"""
    print("NoExcept Performance Benchmarks")
    print("=" * 40)
    
    benchmark_code_registration()
    benchmark_simple_exception_raising()
    benchmark_soft_exceptions()
    benchmark_exception_linking()
    benchmark_exception_groups()
    benchmark_builder_pattern()
    benchmark_threading_safety()
    benchmark_memory_usage()
    
    print("\nBenchmarks completed!")

if __name__ == "__main__":
    run_all_benchmarks()
