from zodiac_core.response import Response
from zodiac_core.routing import ZodiacRoute

from .conftest import BenchmarkUser


class TestInternalMicroBenchmarks:
    """Micro-benchmarks for internal Zodiac logic."""

    def test_internal_wrap_check(self, benchmark):
        """Measure decision logic overhead."""
        benchmark(ZodiacRoute._should_wrap, BenchmarkUser)

    def test_internal_response_creation(self, benchmark):
        """Measure cost of creating standard Response model instance."""

        def run():
            return Response(code=0, data={"id": 1}, message="Success")

        benchmark(run)
