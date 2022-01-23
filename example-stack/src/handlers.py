import textwrap
import json
import functools
import dataclasses

from api_concierge_lib import *
from api_concierge_lib.aws.awslambda import api_concierge_handler

SCHEMA = {
    "$comment": textwrap.dedent("""\
        bar is a number and required.
        foo is a string but not required.
        other properties may be entered.
        """),
    "type": "object",
    "properties": {
        "foo": {
            "$comment": "This is the foo string",
            "type": "string"
        },
        "bar": {
            "type": "array",
            "items": {
                "type": "number"
            }
        }
    },
    "required": ["bar"]
}

INSTRUCTIONS = textwrap.dedent("""\
    Instructions from outside the schema.
    """)

def handler1(event, context):
    print(json.dumps(event))
    if SchemaRequest.is_schema_request(event):
        return SchemaResponse(SCHEMA, instructions=INSTRUCTIONS).get_payload()
    if InvocationRequest.is_invocation_request(event):
        return {"request_type": "invoke", "event": event}
    raise Exception(f"invalid event {json.dumps(event)}")

@api_concierge_handler(SCHEMA, instructions=INSTRUCTIONS)
def handler2(event, context):
    return {"event": event}

SCHEMA1 = {
    "type": "object",
    "properties": {
        "custom_greeting": {"type": "boolean"}
    },
    "additionalProperties": False
}

SCHEMA2 = {
    "type": "object",
    "properties": {
        "greeting": {"type": "string"}
    },
    "additionalProperties": False
}

SCHEMA3 = {
    "type": "object",
    "properties": {
        "name": {"type": "string"}
    },
    "additionalProperties": False
}

def handler3(event, context):
    if SchemaRequest.is_schema_request(event):
        return SchemaResponse(SCHEMA1, state="step1",
            instructions="First, do you want a custom greeting?").get_payload()
    if InvocationRequest.is_invocation_request(event):
        request = InvocationRequest.load_from_payload(event)
        print(json.dumps(dataclasses.asdict(request)))
        if request.state == "step1":
            if request.payload["custom_greeting"]:
                return SchemaResponse(
                    schema=SCHEMA2,
                    state="step2",
                    instructions="Enter the greeting:"
                ).get_payload()
            else:
                base = {
                    "greeting": "Hello"
                }
                return SchemaResponse(
                    schema=SCHEMA3,
                    state="step3",
                    instructions="Enter your name:",
                    base=base,
                ).get_payload()
        if request.state == "step2":
            return SchemaResponse(
                schema=SCHEMA3,
                state="step3",
                instructions="Enter your name:",
                base=request.payload,
            ).get_payload()
        if request.state == "step3":
            result = request.payload["greeting"] + " " + request.payload["name"]
            return {"result": result}
        raise Exception(f"invalid invocation request {json.dumps(event)}")
    raise Exception(f"invalid event {json.dumps(event)}")
