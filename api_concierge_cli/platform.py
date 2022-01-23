from typing import Callable, Dict, List, Mapping, Optional, Any, Sequence, Union, cast, Type, Iterable

import click

from .types import SchemaRequest, SchemaResponse, InvocationRequest, ErrorResponse

class RequestError(Exception):
    pass

class Target:
    def get_name(self) -> str:
        raise NotImplementedError

    def get_description(self) -> Optional[str]:
        raise NotImplementedError

    def search_for_schema(self) -> Optional[SchemaResponse]:
        raise NotImplementedError

    def request_schema(self, request: SchemaRequest, *, search: bool=False) -> SchemaResponse:
        raise NotImplementedError

    def invoke(
        self, request: InvocationRequest
    ) -> Union[SchemaResponse, ErrorResponse, Any]:
        raise NotImplementedError

    def invoke_request_to_str(self, request: InvocationRequest, json_dump_func: Callable[[Any], str]) -> str:
        raise NotImplementedError

    def invoke_response_to_str(self, response: Any, json_dump_func: Callable[[Any], str]) -> str:
        raise NotImplementedError

class Platform:

    @classmethod
    def get_name(cls) -> str:
        raise NotImplementedError

    @classmethod
    def get_list_command(cls, handler: Callable[[Iterable[Target]], None]) -> click.Command:
        raise NotImplementedError

    @classmethod
    def get_invoke_command(cls, handler: Callable[[Type["Platform"], Target], None]) -> click.Command:
        raise NotImplementedError

    @classmethod
    def get_get_schema_command(cls, handler: Callable[[Type["Platform"], Target], None]) -> click.Command:
        raise NotImplementedError
