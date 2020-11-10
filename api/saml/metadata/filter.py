import logging

from api.saml.metadata.model import SAMLAttribute, SAMLAttributeStatement, SAMLSubject
from core.exceptions import BaseError
from core.util.string_helpers import is_string


class SAMLSubjectFilterError(BaseError):
    """Raised in the case of any errors during execution of a filter expression."""

    def __init__(self, inner_exception):
        """Initialize a new instance of SAMLSubjectFilterError class.

        :param inner_exception: Inner exception
        :type inner_exception: Exception
        """
        message = "Incorrect filter expression: {0}".format(str(inner_exception))

        super(SAMLSubjectFilterError, self).__init__(message, inner_exception)


class SAMLDummyAttributesDict(dict):
    """Dummy class used for validating SAML filtration expressions.

    This class always returns a SAML attribute with the same name as requested and signle "dummy" value.
    """

    def __init__(self):
        """Initialize a new instance of SAMLDummyAttributesDict."""
        super(SAMLDummyAttributesDict, self).__init__()

    def __getitem__(self, attribute_name):
        """Return a SAMLAttribute object by its name.

        :param attribute_name: SAML attribute's name
        :type attribute_name: str

        :return: Dummy SAML attribute name with the same name as requested and single "dummy" value
        :rtype: SAMLAttribute
        """
        return SAMLAttribute(attribute_name, ["dummy"])


class SAMLDummyAttributeStatement(SAMLAttributeStatement):
    """Dummy class used for validating SAML filtration expressions.

    This attribute statement contains a SAMLDummyAttributesDict instance returning dummy SAML attributes.
    """

    def __init__(self):
        """Initialize a new instance of SAMLDummyAttributeStatement class."""
        super(SAMLDummyAttributeStatement, self).__init__([])

        self._attributes = SAMLDummyAttributesDict()

    @property
    def attributes(self):
        """Return a SAMLDummyAttributesDict object.

        :return: SAMLDummyAttributesDict object
        :rtype: SAMLDummyAttributesDict
        """
        return self._attributes


class SAMLSubjectFilter(object):
    """Executes filter expressions."""

    def __init__(self):
        """Initialize a new instance of SAMLSubjectFilter class."""
        self._logger = logging.getLogger(__name__)

    def execute(self, expression, subject):
        """Apply the expression to the subject and return a boolean value indicating whether it's a valid subject.

        :param expression: String containing the filter expression
        :type expression: str

        :param subject: SAML subject
        :type subject: api.saml.metadata.model.SAMLSubject

        :return: Boolean value indicating whether it's a valid subject
        :rtype: bool

        :raise SAMLSubjectFilterError: in the case of any errors occurred during expression evaluation
        """
        if not expression or not is_string(expression):
            raise ValueError("Argument 'expression' must be a non-empty string")
        if not isinstance(subject, SAMLSubject):
            raise ValueError("Argument 'subject' must an instance of Subject class")

        self._logger.info(
            "Started applying expression '{0}' to {1}".format(expression, subject)
        )

        try:
            result = eval(expression)
        except Exception as exception:
            raise SAMLSubjectFilterError(exception)

        self._logger.info(
            "Finished applying expression '{0}' to {1}: {2}".format(
                expression, subject, result
            )
        )

        result = bool(result)

        return result

    def validate(self, expression):
        """Validate the filter expression.

        Try to apply the expression to a dummy Subject object containing all the known SAML attributes.

        :param expression: String containing the filter expression
        :type expression: str

        :return: True when the expression is valid otherwise raises SAMLSubjectFilterError
        :rtype: bool

        :raise: SAMLSubjectFilterError
        """
        if not expression or not is_string(expression):
            raise ValueError("Argument 'expression' must be a non-empty string")

        dummy_subject = SAMLSubject(None, SAMLDummyAttributeStatement())

        self.execute(expression, dummy_subject)

        return True
