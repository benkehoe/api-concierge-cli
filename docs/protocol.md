# API Concierge Protocol

# Overview

A client, invoked by a user, communicates with a service that accepts JSON or a format that can be descibed with JSON schema.
The service has some acceptable range of input.
The API Concierge protocol allows in-band communication with the service in order allow the client provide interative construction of acceptable input for the user.
The client initiates a *session* with the service, which ends with an *invocation* that is accepted by the service.

The purpose of the protocol is specifically for interactive prompting.
It is not a general-purpose service definition in the vein of WSDL or OpenAPI.

# Format

The protocol consists of a set of metadata defined for client requests and server responses.
This metadata consists of string-valued keys and values that may be either plain strings, or structured data in the form of a JSON object.

Communication with the service is assumed to have a *payload* and potentially metadata.
For HTTP services, the payload is usually the body and the metadata is the headers.

The metadata specified by the service can either be included in the payload, or in the metadata.

The payload may be JSON, or it may be a format that JSON can be mapped into (e.g., protobuf).

There is no provision in the protocol for negotiation of the location of the metadata.
Whether the metadata should be put in the payload or not must be known to the client when communicating with the service.

# Sessions

The client initiates a session by sending a [*schema request*](#schema-request).
The service MUST respond with a [*schema response*](#schema-response).

The schema response contains a schema.
The client uses the schema to interactively build a schema-compliant payload.
The client then sends an [*invocation request*](#invocation-request).

The service replies with one of three responses.
* If the invocation request forms acceptable input for the service, it MUST treat the invocation request payload as a normal invocation of the service, and responds accordingly.
* If the invocation is invalid, it SHOULD respond with an [*error response*](#error-response).
* The service MAY continue the session with a new schema response; usually this is part of a multi-step session.

# Single- and multi-step sessions

For simple service inputs, the schema provided by the service in the initial schema response may suffice for constructing a valid service invocation.
For more complex inputs, or for a better user experience, it may be useful to construct the service invocation over multiple steps.
In this case, the response to the first invocation request is another schema response.
In multi-step sessions, there is no indication to the client whether an invocation request will be the final step or not, allowing for dynamic sessions.

# Schema request

A schema request MUST have the field `x-api-concierge-request` set to the value `schema`.

The client MAY set the field `x-api-concierge-client` to a string value identifying the client.
The value SHOULD NOT include the identity of the user.

The client SHOULD NOT include any additional content in the schema request.

```json5
{
    // required fields
    "x-api-concierge-request": "schema",

    // optional fields
    "x-api-concierge-client": "client identifier" // any string value is acceptable
}
```

# Schema response

A schema response MUST have the field `x-api-concierge-response` set to the value `schema`.
It MUST have the field `x-api-concierge-schema` set to a JSON schema, either as a JSON object or as url-safe base64-encoded stringified JSON.
The client MUST accept either format.
The schema SHOULD use schema version draft-07.
If `$schema` is not included in the schema, it MUST use draft-07.

The response MAY include the field `x-api-concierge-base`, which is a JSON object that the client MUST use for constructing the invocation request payload.
If `x-api-concierge-base` is present, the response MAY additionally include the field `x-api-concierge-path`, which MUST be a [JSON pointer](https://datatracker.ietf.org/doc/html/rfc6901).
If these fields are present, the client MUST construct the invocation payload by using the base object and merging the constructed payload from the schema at the given path (or at the root if no path is given).
The merge MUST be performed by **TODO**.

The response MAY include the field `x-api-concierge-instructions` set to a string value that will presented to the user for guidance.

The response MAY include the field `x-api-concierge-state` set to a string value.
The value MUST contain only the ASCII characters `A-Za-z0-9,;-_=`.
If the value is structured or dynamic data, it SHOULD be base64-encoded with the URL-safe alphabet.
This value MAY be opaque to the client; the client MUST NOT interpret the state in any way.
If a non-empty state is included in a schema response, it MUST be included in the subsequent invocation request.
Clients MUST not allow state values for invocation requests to be provided by the user (that is, there should not be replay support).

```json5
{
    // required fields
    "x-api-concierge-response": "schema",

    "x-api-concierge-schema": { "type": "string" }, // as JSON
    // or url-safe base64-encoded JSON:
    "x-api-concierge-schema": "eyJ0eXBlIjogInN0cmluZyJ9",

    // optional fields
    "x-api-concierge-instructions": "Instructions for the user",
    "x-api-concierge-state": "state",

    "x-api-concierge-base": { "other_field": "value" },
    "x-api-concierge-path": "/some_field"
}
```

# Invocation request

An invocation request is a standard payload for the service, with the following additional content:

An invocation request MUST have the field `x-api-concierge-request` set to the value `invoke`,

The client MAY set the field `"x-api-concierge-client"` to a string value identifying the client.
The value SHOULD NOT include the identity of the user.

If the invocation request was created based on a schema response or an error response and that response contained an `x-api-concierge-state` field, the client MUST set that field in the invocation request with the same value.

```json5
{
    // required fields
    "x-api-concierge-request": "invoke",

    // optional fields
    "x-api-concierge-client": "client identifier" // any string value is acceptable

    // other payload fields if the metadata is being included in the payload
}
```

# Invocation response

An invocation response SHOULD NOT include any additional content particular to being invoked with an invocation request.

# Error response

An error response MUST have the field `x-api-concierge-response` set to the value `error`.

The response MUST have the field `x-api-concierge-error` set to a string value describing the error.

If the error is recoverable, the service MAY include the field `x-api-concierge-schema` with the same semantics as in a schema response.
The client SHOULD re-prompt the user using this schema for another invocation request, unless the user has specifically directed the client to abort.

If `x-api-concierge-schema` is present, the response MAY include the fields `x-api-concierge-instructions` and/or `x-api-concierge-state` with the same semantics as in a schema response.

```json5
{
    // required fields
    "x-api-concierge-response": "error",
    "x-api-concierge-error": "An error message",

    // optional fields
    "x-api-concierge-schema": { "type": "string" }, // as JSON
    // or url-safe base64-encoded JSON
    "x-api-concierge-schema": "eyJ0eXBlIjogInN0cmluZyJ9",

    "x-api-concierge-instructions": "Instructions for the user",
    "x-api-concierge-state": "state",
}
```

# Discovery

TODO: flesh out

This section is non-normative; the API Concierge protocol does not define a standard mechanism for making API Concierge-compliant services discoverable.
However, the `api-concierge` CLI contains an implementation for it, and the guidelines it follows are documented here.

Discoverability is platform dependent, but relies on the ability to list services and for each service to have a

* marker
    * signal value
    * description
* schema
    * inline
    * reference
