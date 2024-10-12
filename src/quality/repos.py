import great_expectations as gx
import great_expectations.expectations as gxe
from great_expectations.data_context.data_context import FileDataContext
from great_expectations.checkpoint import Checkpoint
from argparse import ArgumentParser
from typing import Dict, Callable, List
import sys
from src.paths import GITHUB_REPOSITORIES_RAW_DIR_PATH
from src.quality.utils import (
    add_or_update_checkpoint,
    add_or_update_validation_definition,
)
from great_expectations.exceptions.exceptions import ValidationError


def build(context: FileDataContext):
    datasource = context.data_sources.add_or_update_pandas_filesystem(
        name="repos-fs-datasource", base_directory=GITHUB_REPOSITORIES_RAW_DIR_PATH
    )

    asset = datasource.add_json_asset(name="repos-asset", lines=True)

    batch_definition = asset.add_batch_definition_path(
        name="repos-daily-bd", path="data.json"
    )

    suite_name = "repos-suite"
    if suite_name in [s.name for s in context.suites.all()]:
        context.suites.delete(suite_name)

    suite = context.suites.add(gx.ExpectationSuite(name="repos-suite"))

    suite.expectations.append(gxe.ExpectColumnToExist(column="id"))
    suite.expectations.append(gxe.ExpectColumnToExist(column="name"))
    suite.expectations.append(gxe.ExpectColumnToExist(column="full_name"))
    suite.expectations.append(gxe.ExpectColumnToExist(column="private"))
    suite.expectations.append(gxe.ExpectColumnToExist(column="owner"))
    suite.save()

    validation_definition = add_or_update_validation_definition(
        context=context,
        vd=gx.ValidationDefinition(
            name="repos-vd", data=batch_definition, suite=suite
        ),
    )

    action_list = [
        gx.checkpoint.UpdateDataDocsAction(
            name="update_all_data_docs",
        ),
    ]

    checkpoint = add_or_update_checkpoint(
        context=context,
        checkpoint=Checkpoint(
            name="repos-default-checkpoint",
            validation_definitions=[validation_definition],
            actions=action_list,
            result_format={
                "result_format": "COMPLETE",
                "include_unexpected_rows": False,
                "partial_unexpected_count": 20,
            },
        ),
    )


def validate(context: FileDataContext):
    print("Validating", GITHUB_REPOSITORIES_RAW_DIR_PATH)

    checkpoint = context.checkpoints.get("repos-default-checkpoint")
    batch_identifier_list = checkpoint.validation_definitions[
        0
    ].batch_definition.get_batch_identifiers_list()
    results = []

    res = checkpoint.run()
    results.append(res.success)

    batch_success = all(results)
    if not batch_success:
        raise ValidationError("All validations did not pass")


if __name__ == "__main__":
    action_map: Dict[str, Callable] = {
        "build": build,
        "validate": validate,
    }
    parser = ArgumentParser()

    parser.add_argument("action")
    parser.add_argument(
        "--files",
        "-f",
        nargs="+",
    )

    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit()

    args = parser.parse_args()

    context = gx.get_context(mode="file")

    func = action_map[args.action]

    if args.action == "validate-files":
        if not args.files:
            print("Error: --files argument is required for 'validate-files'.")
            sys.exit(1)
        func(context=context, files=args.files)
    else:
        func(context=context)
