class TestRoutingPerformance:
    """Benchmark tests comparing Native vs Zodiac routing performance."""

    def test_latency_native_small(self, benchmark, benchmark_clients):
        """Benchmark: Native FastAPI latency (Small response)."""
        native, _, _ = benchmark_clients
        benchmark(native.get, "/native/small")

    def test_latency_zodiac_small(self, benchmark, benchmark_clients):
        """Benchmark: Zodiac wrapping overhead (Small response)."""
        _, zodiac, _ = benchmark_clients
        benchmark(zodiac.get, "/zodiac/small")

    def test_latency_zodiac_full_stack(self, benchmark, benchmark_clients):
        """Benchmark: Total overhead (Zodiac wrapping + Middleware)."""
        _, _, full = benchmark_clients
        benchmark(full.get, "/full/small")

    def test_latency_native_large(self, benchmark, benchmark_clients):
        """Benchmark: Native FastAPI latency (Large list)."""
        native, _, _ = benchmark_clients
        benchmark(native.get, "/native/large")

    def test_latency_zodiac_large(self, benchmark, benchmark_clients):
        """Benchmark: Zodiac wrapping overhead (Large list)."""
        _, zodiac, _ = benchmark_clients
        benchmark(zodiac.get, "/zodiac/large")
