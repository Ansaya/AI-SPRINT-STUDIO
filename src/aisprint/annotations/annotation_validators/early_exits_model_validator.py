from .annotation_validator import AnnotationValidator

class EarlyExitsModelValidator(AnnotationValidator):

    def _check_arguments_validity(self):
        # TODO
        pass

    def check_annotation_validity(self):
        super().check_annotation_validity()
