"""Backward-compatible root entry point forwarding to tests/test_benchmark_500.py"""
from tests.test_benchmark_500 import run_500_benchmark

if __name__ == "__main__":
    run_500_benchmark()
