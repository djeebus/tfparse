import os.path
import shutil
from pathlib import Path
from unittest.mock import ANY

import pytest
from pytest_terraform.tf import TerraformRunner

from tfparse import ParseError, load_from_path


def init_module(module_name, tmp_path):
    tf_bin = shutil.which("terraform")
    if tf_bin is None:
        raise RuntimeError("Terraform binary required on path")

    src_mod_path = Path(__file__).parent / "terraform" / module_name
    mod_path = tmp_path / module_name
    shutil.copytree(src_mod_path, mod_path)

    plugin_cache = Path(__file__).parent.parent / ".tfcache"
    if not plugin_cache.exists():
        plugin_cache.mkdir()

    runner = TerraformRunner(mod_path, tf_bin=tf_bin, plugin_cache=plugin_cache)
    runner.init()
    return mod_path


def test_parse_no_dir(tmp_path):
    result = load_from_path(tmp_path)
    assert result == {}

    with pytest.raises(ParseError) as e_info:
        load_from_path(tmp_path / "xyz")

    assert "no such file or directory" in str(e_info)


def test_parse_vpc_module(tmp_path):
    mod_path = init_module("vpc_module", tmp_path)
    parsed = load_from_path(mod_path)
    summary = {resource_type: len(items) for resource_type, items in parsed.items()}

    assert summary == {
        "aws_eip": 3,
        "aws_internet_gateway": 1,
        "aws_nat_gateway": 3,
        "aws_route": 4,
        "aws_route_table": 4,
        "aws_route_table_association": 6,
        "aws_subnet": 6,
        "aws_vpc": 1,
        "aws_vpn_gateway": 1,
        "module": 1,
    }


def test_parse_eks(tmp_path):
    mod_path = init_module("eks", tmp_path)
    parsed = load_from_path(mod_path)
    assert set(parsed) == {
        "aws_default_route_table",
        "aws_eks_node_group",
        "aws_subnet",
        "aws_vpc",
        "aws_iam_role_policy_attachment",
        "aws_iam_role",
        "aws_eks_cluster",
        "aws_internet_gateway",
    }
    assert {item["__tfmeta"]["path"] for item in parsed["aws_subnet"]} == {
        "aws_subnet.cluster_example[0]",
        "aws_subnet.cluster_example[1]",
        "aws_subnet.node_group_example[0]",
        "aws_subnet.node_group_example[1]",
    }

    assert parsed["aws_eks_cluster"][0]["__tfmeta"] == {
        "filename": "main.tf",
        "label": "aws_eks_cluster",
        "line_start": 1,
        "line_end": 15,
        "path": "aws_eks_cluster.example",
    }


def test_parse_apprunner(tmp_path):
    mod_path = init_module("apprunner", tmp_path)
    parsed = load_from_path(mod_path)

    image_id = "public.ecr.aws/aws-containers/hello-app-runner:latest"

    assert parsed == {
        "aws_apprunner_service": [
            {
                "__tfmeta": {
                    "filename": "main.tf",
                    "label": "aws_apprunner_service",
                    "line_end": 18,
                    "line_start": 1,
                    "path": "aws_apprunner_service.example",
                },
                "id": ANY,
                "service_name": "example",
                "source_configuration": {
                    "__tfmeta": {
                        "filename": "main.tf",
                        "line_end": 13,
                        "line_start": 4,
                    },
                    "auto_deployments_enabled": False,
                    "id": ANY,
                    "image_repository": {
                        "__tfmeta": {
                            "filename": "main.tf",
                            "line_end": 11,
                            "line_start": 5,
                        },
                        "id": ANY,
                        "image_configuration": {
                            "__tfmeta": {
                                "filename": "main.tf",
                                "line_end": 8,
                                "line_start": 6,
                            },
                            "id": ANY,
                            "port": "8000",
                        },
                        "image_identifier": image_id,
                        "image_repository_type": "ECR_PUBLIC",
                    },
                },
                "tags": {"Name": "example-apprunner-service"},
            }
        ]
    }


def test_parse_notify_slack(tmp_path):
    mod_path = init_module("notify_slack", tmp_path)
    parsed = load_from_path(mod_path)

    assert {resource_type: len(items) for resource_type, items in parsed.items()} == {
        "aws_cloudwatch_log_group": 2,
        "aws_iam_policy": 2,
        "aws_iam_role": 2,
        "aws_iam_role_policy_attachment": 2,
        "aws_lambda_function": 2,
        "aws_lambda_permission": 4,
        "aws_sns_topic": 2,
        "aws_sns_topic_subscription": 2,
        "local_file": 2,
        "module": 4,
        "null_resource": 2,
    }

    assert [m["__tfmeta"]["label"] for m in parsed["module"]] == [
        "notify_slack_qa",
        "notify_slack_saas",
        "lambda",
        "lambda",
    ]


def test_parse_dynamic_content(tmp_path):
    here = os.path.dirname(__file__)
    mod_path = os.path.join(here, "terraform", "dynamic-stuff")

    # mod_path = init_module("dynamic-stuff", tmp_path)
    parsed = load_from_path(mod_path)

    resource = {
        "__tfmeta": {
            "filename": "main.tf",
            "label": "some_resource",
            "line_end": 41,
            "line_start": 1,
            "path": ANY,
        },
        "count": 2,
        "id": ANY,
        "prop1": "one",
        "prop2": "two",
        "prop3": "end",
        "loop_one": [
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 11, "line_start": 9},
                "id": ANY,
                "other": True,
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 11, "line_start": 9},
                "id": ANY,
                "other": False,
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 11, "line_start": 9},
                "id": ANY,
                "other": None,
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 37, "line_start": 35},
                "id": ANY,
                "other": "aaa",
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 37, "line_start": 35},
                "id": ANY,
                "other": "bbb",
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 37, "line_start": 35},
                "id": ANY,
                "other": "ccc",
            },
        ],
        "loop_two": [
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 25, "line_start": 23},
                "id": ANY,
                "other": 1,
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 25, "line_start": 23},
                "id": ANY,
                "other": 2,
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 25, "line_start": 23},
                "id": ANY,
                "other": 3,
            },
        ],
        "static": [
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 16, "line_start": 14},
                "id": ANY,
                "name": "first",
            },
            {
                "__tfmeta": {"filename": "main.tf", "line_end": 30, "line_start": 28},
                "id": ANY,
                "name": "second",
            },
        ],
    }

    assert parsed == {
        "some_resource": [
            resource,
            resource,
        ],
    }
