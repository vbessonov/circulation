from nose.tools import assert_raises, eq_
from parameterized import parameterized

from api.saml.metadata.filter import SAMLSubjectFilter, SAMLSubjectFilterError
from api.saml.metadata.model import (
    SAMLAttribute,
    SAMLAttributeStatement,
    SAMLAttributeType,
    SAMLSubject,
)


class TestSAMLSubjectFilter(object):
    @parameterized.expand(
        [
            (
                "fails_in_the_case_of_syntax_error",
                'subject.attribute_statement.attributes["eduPersonEntitlement"].values[0 == "urn:mace:nyu.edu:entl:lib:eresources"',
                SAMLSubject(
                    None,
                    SAMLAttributeStatement(
                        [
                            SAMLAttribute(
                                name=SAMLAttributeType.eduPersonEntitlement.name,
                                values=["urn:mace:nyu.edu:entl:lib:eresources"],
                            )
                        ]
                    ),
                ),
                None,
                SAMLSubjectFilterError,
            ),
            (
                "fails_in_the_case_of_unknown_attribute",
                'subject.attribute_statement.attributes["mail"].values[0] == "urn:mace:nyu.edu:entl:lib:eresources"',
                SAMLSubject(
                    None,
                    SAMLAttributeStatement(
                        [
                            SAMLAttribute(
                                name=SAMLAttributeType.eduPersonEntitlement.name,
                                values=["urn:mace:nyu.edu:entl:lib:eresources"],
                            )
                        ]
                    ),
                ),
                None,
                SAMLSubjectFilterError,
            ),
            (
                "fails_when_subject_is_not_used",
                'attributes["eduPersonEntitlement"].values[0] == "urn:mace:nyu.edu:entl:lib:eresources"',
                SAMLSubject(
                    None,
                    SAMLAttributeStatement(
                        [
                            SAMLAttribute(
                                name=SAMLAttributeType.eduPersonEntitlement.name,
                                values=["urn:mace:nyu.edu:entl:lib:eresources"],
                            )
                        ]
                    ),
                ),
                None,
                SAMLSubjectFilterError,
            ),
            (
                "can_filter_when_attribute_has_one_value",
                'subject.attribute_statement.attributes["eduPersonEntitlement"].values[0] == "urn:mace:nyu.edu:entl:lib:eresources"',
                SAMLSubject(
                    None,
                    SAMLAttributeStatement(
                        [
                            SAMLAttribute(
                                name=SAMLAttributeType.eduPersonEntitlement.name,
                                values=["urn:mace:nyu.edu:entl:lib:eresources"],
                            )
                        ]
                    ),
                ),
                True,
            ),
            (
                "can_filter_when_attribute_has_multiple_values",
                """any([
                        value 
                        for value in subject.attribute_statement.attributes["eduPersonEntitlement"].values 
                        if value == "urn:mace:nyu.edu:entl:lib:eresources"
                    ]
                )
""",
                SAMLSubject(
                    None,
                    SAMLAttributeStatement(
                        [
                            SAMLAttribute(
                                name=SAMLAttributeType.eduPersonEntitlement.name,
                                values=[
                                    "urn:mace:nyu.edu:entl:lib:eresources",
                                    "urn:mace:nyu.edu:entl:lib:books",
                                ],
                            )
                        ]
                    ),
                ),
                True,
            ),
        ]
    )
    def test_execute(
        self, _, expression, subject, expected_result, expected_exception=None
    ):
        # Arrange
        subject_filter = SAMLSubjectFilter()

        # Act
        if expected_exception:
            with assert_raises(expected_exception):
                subject_filter.execute(expression, subject)
        else:
            result = subject_filter.execute(expression, subject)

            # Assert
            eq_(expected_result, result)

    @parameterized.expand(
        [
            (
                "fails_in_the_case_of_syntax_error",
                'subject.attribute_statement.attributes["eduPersonEntitlement"].values[0 == "urn:mace:nyu.edu:entl:lib:eresources"',
                SAMLSubjectFilterError,
            ),
            (
                "fails_when_subject_is_not_used",
                'attributes["eduPersonEntitlement"].values[0] == "urn:mace:nyu.edu:entl:lib:eresources"',
                SAMLSubjectFilterError,
            ),
            (
                "can_filter_by_attribute_oid",
                'subject.attribute_statement.attributes["urn:oid:1.3.6.1.4.1.5923.1.8"].values[0] == "urn:mace:nyu.edu:entl:lib:eresources"',
                None,
            ),
            (
                "can_filter_when_attribute_has_one_value",
                'subject.attribute_statement.attributes["eduPersonEntitlement"].values[0] == "urn:mace:nyu.edu:entl:lib:eresources"',
                None,
            ),
            (
                "can_filter_when_attribute_has_multiple_values",
                """any([
                        value 
                        for value in subject.attribute_statement.attributes["eduPersonEntitlement"].values 
                        if value == "urn:mace:nyu.edu:entl:lib:eresources"
                    ]
                )
""",
                None,
            ),
        ]
    )
    def test_validate(self, _, expression, expected_exception):
        # Arrange
        subject_filter = SAMLSubjectFilter()

        # Act
        if expected_exception:
            with assert_raises(expected_exception):
                subject_filter.validate(expression)
        else:
            result = subject_filter.validate(expression)

            # Assert
            eq_(True, result)
