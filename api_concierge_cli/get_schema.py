import json
import sys
import textwrap
from typing import Mapping, Type, Any

import click

from jsonschema_prompt import prompt


from .types import (
    SchemaRequest,
    InvalidSchemaError,
    InvalidSchemaResponseError,
)

from .platform import Target, Platform, RequestError

from . import __version__

CLIENT = f"api-concierge-cli {__version__}"

def _json_dump(v: Any) -> str:
    return json.dumps(v, indent=2)

def add_global_get_schema_options(invoke_command: click.Command):
    invoke_command.params.append(click.Option(["--show-all/--schema-only"]))

def get_schema_handler(platform: Type[Platform], target: Target, kwargs: Mapping):
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

    if not kwargs["show_all"]:
        print(_json_dump(schema_response.schema))
        return

    if schema_response.instructions:
        print(textwrap.fill(f"Instructions: {schema_response.instructions}"))
    if schema_response.state:
        print(f"State: {schema_response.state}")
    if schema_response.base is not None:
        print(f"Base:")
        print(_json_dump(schema_response.base))
        if schema_response.path is not None:
            print(f"Path: {schema_response.path!r}")
    print("Schema:")
    print(_json_dump(schema_response.schema))
    #TODO: state, base, etc.

