import json
import sys
import copy
import itertools
import textwrap
from typing import Mapping, Type, Any

import click

from jsonschema_prompt import prompt

import jsonpointer

from .types import (
    SchemaRequest,
    SchemaResponse,
    InvocationRequest,
    ErrorResponse,
    InvalidSchemaError,
    InvalidStateError,
    InvalidErrorResponseError,
    InvalidSchemaResponseError,
)

from .platform import Target, Platform, RequestError

from . import __version__

CLIENT = f"api-concierge-cli {__version__}"

def _json_dump(v: Any) -> str:
    return json.dumps(v, indent=2)

def _validate_set(ctx, param, value):
    set_values = {}
    for key, value in value:
        try:
            jsonpointer.JsonPointer(key)
        except jsonpointer.JsonPointerException as e:
            raise click.BadParameter(f"Path {key} is invalid: {e}")
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
        set_values[key] = value
    return set_values

def add_global_invoke_options(invoke_command: click.Command):
    invoke_command.params.append(click.Option(["--set"], multiple=True, nargs=2,
        metavar="JSON_POINTER VALUE",
        callback=_validate_set))
    invoke_command.params.append(click.Option(["--show-schema/--no-show-schema"]))
    invoke_command.params.append(click.Option(["--show-event/--no-show-event"]))

def invoke_handler(platform: Type[Platform], target: Target, kwargs: Mapping):
    set_values = kwargs.get("set", {})

    schema_request = SchemaRequest(client=CLIENT)
    try:
        schema_response = target.request_schema(schema_request)
    except InvalidSchemaResponseError:
        print("Invalid schema response", file=sys.stderr)
        sys.exit(1)
    except InvalidSchemaError:
        print("Invalid schema", file=sys.stderr)
        sys.exit(1)
    except RequestError as e:
        print(f"Error requesting schema: {e}", file=sys.stderr)
        sys.exit(1)

    for step in itertools.count(start=1):
        if step > 1:
            print("\n----")
        if kwargs.get("show_schema"):
            print("Schema:")
            print(_json_dump(schema_response.schema))
            print()
        if schema_response.instructions:
            print(textwrap.fill(schema_response.instructions.rstrip()))
        prompt_kwargs = {}
        if step == 1:
            prompt_kwargs["set_values"] = set_values
        value = prompt(schema_response.schema, set_values=set_values)
        # print(f"prompt result: {json.dumps(value, indent=2)}")
        # print("base", schema_response.base, "path", schema_response.path)
        payload = combine(schema_response.base, schema_response.path, value)
        invoke_request = InvocationRequest(
            payload=payload, client=CLIENT, state=schema_response.state
        )
        if kwargs.get("show_event"):
            print()
            print("Invocation request:")
            print(target.invoke_request_to_str(invoke_request, _json_dump))
        try:
            invoke_response = target.invoke(invoke_request)
            if isinstance(invoke_response, ErrorResponse):
                print(f"Error: {invoke_response.error_message}")
                if invoke_response.schema:
                    schema_response = invoke_response.to_schema_response()
                    continue
                else:
                    sys.exit(2)
            elif isinstance(invoke_response, SchemaResponse):
                schema_response = invoke_response
                continue
            else:
                print()
                print("Invocation response:")
                print(target.invoke_response_to_str(invoke_response, _json_dump))
                sys.exit(0)
        except RequestError as e:
            print(f"Error during invoke: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception:
            raise

def _merge(o1, o2):
    if not (isinstance(o1, dict) and isinstance(o2, dict)):
        return o2
    for key, value in o2.items():
        if key not in o1:
            o1[key] = value
        else:
            o1[key] = _merge(o1[key], value)
    return o1

def combine(base, path, payload):
    if base is None:
        return payload
    if path is None:
        path = ""
    path = jsonpointer.JsonPointer(path)
    try:
        value = path.get(base)
    except jsonpointer.JsonPointerException:
        return path.set(base, payload, inplace=False)
    else:
        return path.set(base, _merge(value, payload), inplace=False)
