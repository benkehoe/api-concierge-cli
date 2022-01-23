import itertools
import json
from typing import Callable, Iterable, Mapping, Sequence, Type, Union, Any, Optional

from ..types import (
    InvocationRequest,
    SchemaRequest,
    SchemaResponse,
    ErrorResponse,
)

from ..platform import RequestError, Target, Platform

import click

try:
    import boto3

    class LambdaTarget(Target):
        def __init__(
            self,
            *,
            session: boto3.Session,
            function_arn: str,
            description: Optional[str] = None,
            schema_arn: Optional[str] = None,
            schema_search: Optional[bool] = None
        ) -> None:
            self.session = session
            self.lambda_client = session.client("lambda")
            self.arn = function_arn
            self._description = description
            self.schema_arn = schema_arn
            self.schema_search = schema_search

        def get_name(self) -> str:
            return self.arn.split(":", 6)[-1]

        def get_description(self) -> Optional[str]:
            return self._description

        def search_for_schema(self) -> Optional[SchemaResponse]:
            #TODO: check Parameter Store
            #TODO: check tags
            #TODO: check env var
            return None

        def request_schema(self, request: SchemaRequest) -> SchemaResponse:
            if self.schema_arn:
                raise NotImplementedError
            if self.schema_search:
                raise NotImplementedError
            response = self.lambda_client.invoke(
                FunctionName=self.arn, Payload=json.dumps(request.get_payload())
            )
            response_payload = json.load(response["Payload"])
            if "FunctionError" in response:
                message = f"Error {response['FunctionError']}"
                try:
                    message += f" {response_payload['errorType']}: {response_payload['errorMessage']}"
                except:
                    pass
                raise RequestError(message)
            return SchemaResponse.load_from_payload(response_payload)

        def invoke(
            self, request: InvocationRequest
        ) -> Union[SchemaResponse, ErrorResponse, Any]:
            response = self.lambda_client.invoke(
                FunctionName=self.arn, Payload=json.dumps(request.get_payload())
            )
            response_payload = json.load(response["Payload"])
            if "FunctionError" in response:
                message = f"Error {response['FunctionError']}"
                try:
                    message += f" {response_payload['errorType']}: {response_payload['errorMessage']}"
                except:
                    pass
                raise RequestError(message)
            if SchemaResponse.is_schema_response(response_payload):
                return SchemaResponse.load_from_payload(response_payload)
            if ErrorResponse.is_error_response(response_payload):
                return ErrorResponse.load_from_payload(response_payload)
            return response_payload

        def invoke_request_to_str(self, request: InvocationRequest, json_dump_func: Callable[[Any], str]) -> str:
            return json_dump_func(request.get_payload())

        def invoke_response_to_str(self, response: Any, json_dump_func: Callable[[Any], str]) -> str:
            return json_dump_func(response)


    class LambdaPlatform(Platform):
        TAG_KEY = "api-concierge"

        @classmethod
        def get_name(cls) -> str:
            return "lambda"

        @classmethod
        def get_list_command(cls, handler: Callable[[Iterable[Target], Mapping], None]) -> click.Command:
            @click.command()
            @click.option("--profile", metavar="PROFILE")
            @click.option("--tags/--no-tags", default=None)
            @click.option("--env/--no-env", default=None)
            @click.option("--ssm/--no-ssm", default=None)
            def command(profile, tags, env, ssm, **kwargs):
                session = boto3.Session(profile_name=profile)
                iters = []
                already_returned = set()
                if tags is None and env is None and ssm is None:
                    iters = [
                        cls._iter_tags(session, already_returned),
                        cls._iter_env(session, already_returned),
                        cls._iter_ssm(session, already_returned),
                    ]
                else:
                    if tags:
                        iters.append(cls._iter_tags(session, already_returned))
                    if env:
                        iters.append(cls._iter_env(session, already_returned))
                    if ssm:
                        iters.append(cls._iter_ssm(session, already_returned))
                handler(itertools.chain(*iters), kwargs)

            return command

        @classmethod
        def get_invoke_command(cls, handler: Callable[[Type["Platform"], Target, Mapping], None]) -> click.Command:
            @click.command()
            @click.argument("function")
            @click.option("--profile", metavar="PROFILE")
            @click.option("--schema-search", is_flag=True)
            @click.option("--schema-arn", metavar="ARN")
            def command(function, profile, schema_search, schema_arn, **kwargs):
                if schema_search and schema_arn:
                    raise click.UsageError("Cannot use --schema-search and --schema-arn")
                session = boto3.Session(profile_name=profile)
                if not function.startswith("arn:"):
                    account = session.client("sts").get_caller_identity()["Account"]
                    function = f"arn:aws:lambda:{session.region_name}:{account}:function:{function}"
                target = LambdaTarget(
                    session=session, function_arn=function, schema_search=schema_search, schema_arn=schema_arn
                )
                handler(cls, target, kwargs)

            return command

        @classmethod
        def get_get_schema_command(cls, handler: Callable[[Type["Platform"], Target, Mapping], None]) -> click.Command:
            @click.command()
            @click.argument("function")
            @click.option("--profile", metavar="PROFILE")
            def command(function, profile, **kwargs):
                session = boto3.Session(profile_name=profile)
                if not function.startswith("arn:"):
                    account = session.client("sts").get_caller_identity()["Account"]
                    function = f"arn:aws:lambda:{session.region_name}:{account}:function:{function}"
                target = LambdaTarget(
                    session=session, function_arn=function
                )
                handler(cls, target, kwargs)

            return command


        @classmethod
        def _iter_tags(cls, session: boto3.Session, already_returned: set):
            resource_client = session.client("resourcegroupstaggingapi")
            paginator = resource_client.get_paginator("get_resources")

            tag_filters = []
            tag_filters.append({"Key": cls.TAG_KEY})

            args = {"TagFilters": tag_filters, "ResourceTypeFilters": ["lambda:function"]}

            class Skip(Exception):
                pass

            for response in paginator.paginate(**args):
                for resource in response["ResourceTagMappingList"]:
                    function_arn = resource["ResourceARN"]
                    if function_arn in already_returned:
                        continue
                    already_returned.add(function_arn)
                    try:
                        description = None
                        for tag in resource["Tags"]:
                            if tag["Key"] == cls.TAG_KEY:
                                value = tag["Value"]
                                if value.lower() == "false":
                                    raise Skip
                                if value.lower() != "true":
                                    description = value
                                break
                        yield LambdaTarget(
                            session=session, function_arn=function_arn, description=description
                        )
                    except Skip:
                        continue

        @classmethod
        def _iter_env(cls, session: boto3.Session, already_returned: set):
            lambda_client = session.client("lambda")
            paginator = lambda_client.get_paginator("list_functions")
            class Skip(Exception):
                pass
            for response in paginator.paginate():
                for function in response.get("Functions", []):
                    function_arn = function["FunctionArn"]
                    if function_arn in already_returned:
                        continue
                    already_returned.add(function_arn)
                    try:
                        for env_key, env_value in (
                            function.get("Environment", {}).get("Variables", {}).items()
                        ):
                            if env_key == cls.TAG_KEY:
                                description = None
                                if env_value.lower() == "false":
                                    raise Skip
                                if env_value.lower() != "true":
                                    description = env_value
                                yield LambdaTarget(
                                    session=session, function_arn=function_arn, description=description
                                )
                                break
                    except Skip:
                        continue


        @classmethod
        def _iter_ssm(cls, session: boto3.Session, already_returned: set):
            return []

    PLATFORMS = [LambdaPlatform]
except ModuleNotFoundError:
    PLATFORMS = []
