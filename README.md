# API Concierge

> :warning: This is a prototype in progress.

The purpose of API Concierge is to provide a single CLI tool that can act as an interactive interface for arbitrary JSON API endpoints, leveraging JSON Schema as the description language for the required input.
It consists of two pieces: an in-band protocol for requesting the schema for the API, and a CLI prompter that interactively builds a JSON object using JSON Schema.

In its basic form, the service simply returns the schema for an invocation and expects to be invoked with an object fitting that schema.
This is useful for services with simple schemas, and for a simple retrofit onto existing services.

For advanced use cases, when the CLI invokes the service with the object built from the schema, the service can respond with *another* schema, allowing for dynamic prompting and more interactivity.
The protocol provides for statefulness and the ability to build an object in multiple steps.

The CLI is partitioned into *platforms*, which are the different kinds of endpoints that can be used.
Platforms include AWS Lambda, TODO: AWS API Gateway, and generic HTTP endpoints.
Additional platforms can be added.

Some platforms support service discovery, and may additionally support referencing a fixed schema to skip the API Concierge protocol interaction.

See [api-concierge-lib](https://github.com/benkehoe/api-concierge-lib-python) for service-side helpers.

# Usage

```
pipx install git+https://github.com/benkehoe/api-concierge-cli.git
or
python -m pip install --user git+https://github.com/benkehoe/api-concierge-cli.git
```

```bash

# PLATFORM is lambda, TODO: aws-api-gateway, http

# find names that can be used with invoke
api-concierge PLATFORM list

# get the schema and build an invocation
api-concierge PLATFORM invoke NAME [--show-event] [--show-schema] [--set JSON_POINTER VALUE]

# just retrieve the schema
api-concierge PLATFORM get-schema NAME [--show-all/--schema-only]
```

You can set values in the invocation with `--set` using [JSON Pointer](https://www.rfc-editor.org/rfc/rfc6901.html).

TODO: for Lambda at least, there should be `--schema-search` and `--schema-arn` options that let the schema be defined outside the function and have the CLI skip the API Concierge protocol entirely.

# Example

A Lambda function could look like the following (see [api-concierge-lib](https://github.com/benkehoe/api-concierge-lib-python)):

```python
from api_concierge_lib.aws.awslambda import api_concierge_handler

SCHEMA = {
    "$comment": "General instructions",
    "type": "object",
    "properties": {
        "field1": {
            "type": "string",
            "$comment": "Instructions for field1"
        },
        "field2": {"type": "number"}
    },
    "required": ["field1"],
    "additionalProperties": False
}

@api_concierge_handler(SCHEMA)
def handler(event, context):
    return {"result": "success", "event": event}
```

The [protocol](docs/protocol.md) is intentionally simple; basic support can be accomplished without a library in any language. For Python:

```python
SCHEMA = { ... }

def handler(event, context):
    if event.get("x-api-concierge-request") == "schema":
        return {
            "x-api-concierge-response": "schema",
            "x-api-concierge-schema": SCHEMA
        }
    # function code...
```

Invoking looks like:
```
$ api-concierge lambda invoke MyFunction
General instructions
  Instructions for field1
  field1 [string] [REQUIRED]: foo
  field2 [number] (CTRL-D to skip): 1

Invocation response:
{
  "result": "success",
  "event": {
    "field1": "foo",
    "field2": 1
  }
}
```

You can see the schema and the invocation payload with `--show-schema` and `--show-event`.

# Protocol
Read the [protocol docs](docs/protocol.md).

# Example stack
See the [example stack](example-stack/README.md).

# Platforms

## AWS Lambda
To be listable, Lambda functions need to have either a tag or an environment variable named `api-concierge`, with the value `true` or a description of the function.
