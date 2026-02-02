import inspect
from functools import wraps
from typing import Any, Callable, Dict, Optional, Union, get_origin

from fastapi import APIRouter as FastAPIRouter
from fastapi import Response as FastAPIResponse
from fastapi.datastructures import DefaultPlaceholder  # FastAPI internal, requires >=0.128.0
from fastapi.routing import APIRoute

from zodiac_core.response import Response


class ZodiacRoute(APIRoute):
    """
    Custom APIRoute that automatically wraps response models and endpoint returns
    with the standard Response[T] structure.
    """

    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        response_model: Any = None,
        responses: Optional[Dict[Union[int, str], Dict[str, Any]]] = None,
        **kwargs,
    ) -> None:
        # Resolve FastAPI's DefaultPlaceholder
        if isinstance(response_model, DefaultPlaceholder):
            response_model = response_model.value

        # 1. Wrap main response model (default to Any if missing)
        if self._should_wrap(response_model):
            response_model = self._wrap_response_model(response_model or Any)

        # 2. Wrap additional responses (e.g. 400, 404 models)
        # Copy to avoid mutating caller's dict
        if responses:
            responses = {code: {**res_dict} for code, res_dict in responses.items()}
            for res in responses.values():
                if "model" in res and self._should_wrap(res["model"]):
                    res["model"] = self._wrap_response_model(res["model"])

        # 3. Wrap endpoint to auto-wrap return values
        endpoint = self._wrap_endpoint(endpoint)

        super().__init__(
            path,
            endpoint,
            response_model=response_model,
            responses=responses,
            **kwargs,
        )

    @staticmethod
    def _should_wrap(model: Any) -> bool:
        """Check if a model needs to be wrapped with Response[T]."""
        if model is Any or model is None:
            return True
        origin = get_origin(model)
        if origin is Response:
            return False
        try:
            if isinstance(model, type) and issubclass(model, Response):
                return False
        except TypeError:
            pass
        return True

    @staticmethod
    def _wrap_response_model(model: Any) -> type[Response]:
        """Wrap a model type with Response[T] using Pydantic's native generics."""
        return Response[model]

    @staticmethod
    def _maybe_wrap_result(result: Any) -> Any:
        """Wrap result in Response if not already a Response type."""
        if isinstance(result, (Response, FastAPIResponse)):
            return result
        return Response(data=result)

    @staticmethod
    def _wrap_endpoint(endpoint: Callable) -> Callable:
        """Wrap endpoint to automatically wrap return values in Response."""

        @wraps(endpoint)
        async def async_wrapper(*args, **kwargs):
            result = await endpoint(*args, **kwargs)
            return ZodiacRoute._maybe_wrap_result(result)

        @wraps(endpoint)
        def sync_wrapper(*args, **kwargs):
            result = endpoint(*args, **kwargs)
            return ZodiacRoute._maybe_wrap_result(result)

        return async_wrapper if inspect.iscoroutinefunction(endpoint) else sync_wrapper


class APIRouter(FastAPIRouter):
    """
    Zodiac-enhanced APIRouter that uses ZodiacRoute by default.

    All routes registered via this router will automatically:
    - Wrap response_model with Response[T] for OpenAPI docs
    - Wrap endpoint return values with Response structure
    """

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("route_class", ZodiacRoute)
        super().__init__(*args, **kwargs)
