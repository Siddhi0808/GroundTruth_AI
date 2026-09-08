"""Backward-compatible root entry point forwarding to tests/test_benchmark_1000.py"""
from tests.test_benchmark_1000 import run_1000_benchmark

if __name__ == "__main__":
    run_1000_benchmark()
