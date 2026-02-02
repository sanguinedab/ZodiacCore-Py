class TestRoutingPerformance:
    """Benchmark tests comparing Native vs Zodiac routing performance."""

    # --- Small Response (Single Object) ---

    def test_latency_native_small(self, benchmark, benchmark_clients):
        """Benchmark: Native FastAPI (small response)."""
        native, _, _ = benchmark_clients
        benchmark(native.get, "/native/small")

    def test_latency_zodiac_small(self, benchmark, benchmark_clients):
        """Benchmark: Zodiac wrapping only (small response)."""
        _, zodiac, _ = benchmark_clients
        benchmark(zodiac.get, "/zodiac/small")

    def test_latency_full_small(self, benchmark, benchmark_clients):
        """Benchmark: Zodiac + Middleware full stack (small response)."""
        _, _, full = benchmark_clients
        benchmark(full.get, "/full/small")

    # --- Large Response (100 Objects) ---

    def test_latency_native_large(self, benchmark, benchmark_clients):
        """Benchmark: Native FastAPI (large response)."""
        native, _, _ = benchmark_clients
        benchmark(native.get, "/native/large")

    def test_latency_zodiac_large(self, benchmark, benchmark_clients):
        """Benchmark: Zodiac wrapping only (large response)."""
        _, zodiac, _ = benchmark_clients
        benchmark(zodiac.get, "/zodiac/large")

    def test_latency_full_large(self, benchmark, benchmark_clients):
        """Benchmark: Zodiac + Middleware full stack (large response)."""
        _, _, full = benchmark_clients
        benchmark(full.get, "/full/large")
