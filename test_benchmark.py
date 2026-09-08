"""Backward-compatible root entry point forwarding to tests/test_benchmark.py"""
from tests.test_benchmark import run_benchmark

if __name__ == "__main__":
    run_benchmark()
