from contextlib import suppress
from functools import wraps
from typing import Callable, Type, TypeVar

from pydantic import BaseModel, ValidationError
from typing_extensions import ParamSpec

from .exceptions import ModelValidateError

ModelT = TypeVar("ModelT", bound=BaseModel)
P = ParamSpec("P")


def model_dispatch(*models: Type[ModelT]) -> Callable[[Callable[P, BaseModel]], Callable[P, ModelT]]:
    def _model_dispatcher(func: Callable[P, BaseModel]) -> Callable[P, ModelT]:
        @wraps(func)
        def _wrapped_model_dispatch(*args: P.args, **kwargs: P.kwargs) -> ModelT:
            ret = func(*args, **kwargs)
            for model in models:
                with suppress(ValidationError):
                    return model.validate(ret)
            raise ModelValidateError(f"Failed to validate {ret!r} as any of {models!r}")
        return _wrapped_model_dispatch
    return _model_dispatcher
