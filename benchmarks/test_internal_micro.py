from zodiac_core.response import Response
from zodiac_core.routing import ZodiacRoute

from .conftest import BenchmarkUser


class TestInternalMicroBenchmarks:
    """Micro-benchmarks for internal Zodiac logic."""

    def test_internal_wrap_check(self, benchmark):
        """Measure _should_wrap decision logic overhead."""
        benchmark(ZodiacRoute._should_wrap, BenchmarkUser)

    def test_internal_response_creation(self, benchmark):
        """Measure Response model instantiation cost."""

        def run():
            return Response(code=0, data={"id": 1}, message="Success")

        benchmark(run)

    def test_internal_generic_response_creation(self, benchmark):
        """Measure Response[T] generic instantiation cost."""

        def run():
            return Response[BenchmarkUser](
                code=0,
                data=BenchmarkUser(id=1, name="Test", email="t@t.com"),
            )

        benchmark(run)

    def test_internal_response_serialization(self, benchmark):
        """Measure Response.model_dump(mode='json') serialization cost."""
        resp = Response(code=0, data={"id": 1, "name": "Test"}, message="Success")
        benchmark(lambda: resp.model_dump(mode="json"))

    def test_internal_generic_response_serialization(self, benchmark):
        """Measure Response[T].model_dump(mode='json') serialization cost."""
        resp = Response[BenchmarkUser](
            code=0,
            data=BenchmarkUser(id=1, name="Test", email="t@t.com"),
        )
        benchmark(lambda: resp.model_dump(mode="json"))
