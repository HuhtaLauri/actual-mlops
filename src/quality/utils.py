from great_expectations.checkpoint import Checkpoint
from great_expectations.core.validation_definition import ValidationDefinition
from great_expectations.data_context.data_context import FileDataContext


def add_or_update_validation_definition(
    context: FileDataContext, vd: ValidationDefinition
) -> ValidationDefinition:
    validation_definition_names = [v.name for v in context.validation_definitions.all()]
    if vd.name in validation_definition_names:
        context.validation_definitions.delete(vd.name)
    return context.validation_definitions.add(vd)


def add_or_update_checkpoint(
    context: FileDataContext, checkpoint: Checkpoint
) -> Checkpoint:
    checkpoint_names = [c.name for c in context.checkpoints.all()]
    if checkpoint.name in checkpoint_names:
        context.checkpoints.delete(checkpoint.name)
    return context.checkpoints.add(checkpoint)
