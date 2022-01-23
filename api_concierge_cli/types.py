from dataclasses import dataclass, field as dataclass_field
from typing import Callable, Dict, List, Mapping, Optional, Any, Sequence, Union, cast, Type, Iterable
import json
import base64

PREFIX = "x-api-concierge-"
REQUEST_FIELD = PREFIX + "request"
RESPONSE_FIELD = PREFIX + "response"
SCHEMA_FIELD = PREFIX + "schema"
INSTRUCTIONS_FIELD = PREFIX + "instructions"
CLIENT_FIELD = PREFIX + "client"
ERROR_FIELD = PREFIX + "error"
STATE_FIELD = PREFIX + "state"
BASE_FIELD = PREFIX + "base"
PATH_FIELD = PREFIX + "path"


class InvalidSchemaError(Exception):
    pass


class InvalidStateError(Exception):
    pass


class InvalidSchemaResponseError(Exception):
    pass


class InvalidErrorResponseError(Exception):
    pass


def _serialize(data: Any) -> str:
    return str(base64.urlsafe_b64encode(json.dumps(data).encode("ascii")))


def _deserialize_schema(schema_data: Any) -> Any:
    if not isinstance(schema_data, str):
        return schema_data
    try:
        return json.loads(base64.urlsafe_b64decode(schema_data))
    except:
        raise InvalidSchemaError

def _deserialize_base(base_data: Any) -> Any:
    if not isinstance(base_data, str):
        return base_data
    try:
        return json.loads(base64.urlsafe_b64decode(base_data))
    except:
        raise InvalidSchemaError

@dataclass(frozen=True)
class SchemaRequest:
    client: str

    def get_headers(self) -> Mapping[str, str]:
        return {REQUEST_FIELD: "schema", CLIENT_FIELD: self.client}

    def get_payload(self) -> Mapping[str, Any]:
        return {REQUEST_FIELD: "schema", CLIENT_FIELD: self.client}


@dataclass(frozen=True)
class SchemaResponse:
    schema: Any
    instructions: Optional[str] = None
    state: Optional[str] = None
    base: Optional[Any] = None
    path: Optional[str] = None

    @classmethod
    def is_schema_response(cls, data: Mapping[str, Any]) -> bool:
        for data_field, data_value in data.items():
            if data_field.lower() == RESPONSE_FIELD.lower():
                return data_value == "schema"
        return False

    @classmethod
    def load_from_headers(cls, headers: Mapping[str, str]) -> "SchemaResponse":
        if not cls.is_schema_response(headers):
            raise ValueError("Input is not a schema response.")
        kwargs = {}
        for header_name, header_value in headers.items():
            if header_name.lower() == SCHEMA_FIELD.lower():
                kwargs["schema"] = _deserialize_schema(header_value)
            elif header_name.lower() == INSTRUCTIONS_FIELD.lower():
                kwargs["instructions"] == header_value
            elif header_name.lower() == STATE_FIELD.lower():
                kwargs["state"] = header_value
            elif header_name.lower() == BASE_FIELD.lower():
                kwargs["base"] = _deserialize_base(header_value)
            elif header_name.lower() == PATH_FIELD.lower():
                kwargs["path"] = header_value
        if "schema" not in kwargs:
            raise InvalidSchemaResponseError
        return cls(**kwargs)

    @classmethod
    def load_from_payload(cls, payload: Mapping[str, Any]) -> "SchemaResponse":
        if not cls.is_schema_response(payload):
            raise ValueError("Input is not a schema response.")
        kwargs = {}
        for key, value in payload.items():
            if key.lower() == SCHEMA_FIELD.lower():
                kwargs["schema"] = _deserialize_schema(value)
            elif key.lower() == INSTRUCTIONS_FIELD.lower():
                kwargs["instructions"] = value
            elif key.lower() == STATE_FIELD.lower():
                kwargs["state"] = value
            elif key.lower() == BASE_FIELD.lower():
                kwargs["base"] = _deserialize_base(value)
            elif key.lower() == PATH_FIELD.lower():
                kwargs["path"] = value
        if "schema" not in kwargs:
            raise InvalidSchemaResponseError
        return cls(**kwargs)


@dataclass(frozen=True)
class InvocationRequest:
    payload: Any
    client: str
    state: Optional[str] = None

    def __post_init__(self):
        if self.state is not None and not isinstance(self.payload, dict):
            raise TypeError(f"Payload is of type {type(self.payload)}, must be dict when a state is set")

    def get_headers(self) -> Mapping[str, str]:
        headers = {REQUEST_FIELD: "invoke", CLIENT_FIELD: self.client}
        if self.state:
            headers[STATE_FIELD] = self.state

    def _update_payload(self, payload: Dict[str, Any]):
        payload[REQUEST_FIELD] = "invoke"
        payload[CLIENT_FIELD] = self.client
        if self.state:
            payload[STATE_FIELD] = self.state

    def get_payload(self) -> Any:
        if not isinstance(self.payload, dict):
            return self.payload
        payload = self.payload.copy()
        self._update_payload(payload)
        return payload


@dataclass(frozen=True)
class ErrorResponse:
    error_message: str
    schema: Optional[Any] = None
    state: Optional[str] = None
    base: Optional[Any] = None
    path: Optional[str] = None

    def to_schema_response(self):
        if not self.schema:
            raise ValueError("This ErrorResponse has no schema")
        return SchemaResponse(
            schema=self.schema,
            state=self.state,
            base=self.base,
            path=self.path
        )

    @classmethod
    def is_error_response(self, data: Mapping[str, Any]) -> bool:
        for data_field, data_value in data.items():
            if data_field.lower() == RESPONSE_FIELD.lower():
                return data_value == "error"
        return False

    @classmethod
    def load_from_headers(cls, headers: Mapping[str, str]) -> "SchemaResponse":
        if not cls.is_error_response(headers):
            raise ValueError("Input is not an error response.")
        kwargs = {}
        for header_name, header_value in headers.items():
            if header_name.lower() == ERROR_FIELD.lower():
                kwargs["error_message"] = header_value
            elif header_name.lower() == SCHEMA_FIELD.lower():
                kwargs["schema"] == _deserialize_schema(header_value)
            elif header_name.lower() == STATE_FIELD.lower():
                kwargs["state"] = header_value
            elif header_name.lower() == BASE_FIELD.lower():
                kwargs["base"] = _deserialize_base(header_value)
            elif header_name.lower() == PATH_FIELD.lower():
                kwargs["path"] = header_value
        if "error_message" not in kwargs:
            raise InvalidErrorResponseError
        return cls(**kwargs)

    @classmethod
    def load_from_payload(cls, payload: Mapping[str, Any]) -> "SchemaResponse":
        if not cls.is_error_response(payload):
            raise ValueError("Input is not an error response.")
        kwargs = {}
        for key, value in payload.items():
            if key.lower() == ERROR_FIELD.lower():
                kwargs["error_message"] = value
            elif key.lower() == SCHEMA_FIELD.lower():
                kwargs["schema"] = _deserialize_schema(value)
            elif key.lower() == STATE_FIELD.lower():
                kwargs["state"] = value
            elif key.lower() == BASE_FIELD.lower():
                kwargs["base"] = _deserialize_base(value)
            elif key.lower() == PATH_FIELD.lower():
                kwargs["path"] = value
        if "error_message" not in kwargs:
            raise InvalidErrorResponseError
        return cls(**kwargs)

