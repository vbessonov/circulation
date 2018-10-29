from nose.tools import (
    set_trace,
    eq_,
    assert_raises
)
import flask
from werkzeug import MultiDict
from core.model import (
    AdminRole,
)
from api.adobe_vendor_id import (
    AdobeVendorIDModel,
    AuthdataUtility,
)
from api.admin.controller.patrons import PatronController
from api.admin.exceptions import *
from api.authenticator import PatronData
from test_controller import AdminControllerTest

class TestPatronController(AdminControllerTest):
    def setup(self):
        super(TestPatronController, self).setup()
        self.admin.add_role(AdminRole.LIBRARIAN, self._default_library)

    def test__load_patrondata(self):
        """Test the _load_patrondata helper method."""
        class MockAuthenticator(object):
            def __init__(self, providers):
                self.providers = providers

        class MockAuthenticationProvider(object):
            def __init__(self, patron_dict):
                self.patron_dict = patron_dict

            def remote_patron_lookup(self, patrondata):
                return self.patron_dict.get(patrondata.authorization_identifier)

        authenticator = MockAuthenticator([])
        auth_provider = MockAuthenticationProvider({})
        identifier = "Patron"

        form = MultiDict([("identifier", identifier)])
        m = self.manager.admin_patron_controller._load_patrondata

        # User doesn't have admin permission
        with self.request_context_with_library("/"):
            assert_raises(AdminNotAuthorized, m, authenticator)

        # No form data specified
        with self.request_context_with_library_and_admin("/"):
            response = m(authenticator)
            eq_(404, response.status_code)
            eq_(NO_SUCH_PATRON.uri, response.uri)
            eq_("Please enter a patron identifier", response.detail)

        # AuthenticationProvider has no Authenticators.
        with self.request_context_with_library_and_admin("/"):
            flask.request.form = form
            response = m(authenticator)

            eq_(404, response.status_code)
            eq_(NO_SUCH_PATRON.uri, response.uri)
            eq_("This library has no authentication providers, so it has no patrons.",
                response.detail
            )

        # Authenticator can't find patron with this identifier
        authenticator.providers.append(auth_provider)
        with self.request_context_with_library_and_admin("/"):
            flask.request.form = form
            response = m(authenticator)

            eq_(404, response.status_code)
            eq_(NO_SUCH_PATRON.uri, response.uri)
            eq_("No patron with identifier %s was found at your library" % identifier,
            response.detail)

    def test_lookup_patron(self):

        # Here's a patron.
        patron = self._patron()
        patron.authorization_identifier = self._str

        # This PatronController will always return information about that
        # patron, no matter what it's asked for.
        class MockPatronController(PatronController):
            def _load_patrondata(self, authenticator):
                self.called_with = authenticator
                return PatronData(
                    authorization_identifier="An Identifier",
                    personal_name="A Patron",
                )

        controller = MockPatronController(self.manager)

        authenticator = object()
        with self.request_context_with_library_and_admin("/"):
            flask.request.form = MultiDict([("identifier", object())])
            response = controller.lookup_patron(authenticator)
            # The authenticator was passed into _load_patrondata()
            eq_(authenticator, controller.called_with)

            # _load_patrondata() returned a PatronData object. We
            # converted it to a dictionary, which will be dumped to
            # JSON on the way out.
            eq_("An Identifier", response['authorization_identifier'])
            eq_("A Patron", response['personal_name'])

    def test_reset_adobe_id(self):
        # Here's a patron with two Adobe-relevant credentials.
        patron = self._patron()
        patron.authorization_identifier = self._str

        self._credential(
            patron=patron, type=AdobeVendorIDModel.VENDOR_ID_UUID_TOKEN_TYPE
        )
        self._credential(
            patron=patron, type=AuthdataUtility.ADOBE_ACCOUNT_ID_PATRON_IDENTIFIER
        )

        # This PatronController will always return a specific
        # PatronData object, no matter what is asked for.
        class MockPatronController(PatronController):
            mock_patrondata = None
            def _load_patrondata(self, authenticator):
                self.called_with = authenticator
                return self.mock_patrondata

        controller = MockPatronController(self.manager)
        controller.mock_patrondata = PatronData(
            authorization_identifier=patron.authorization_identifier
        )

        # We reset their Adobe ID.
        authenticator = object()
        with self.request_context_with_library_and_admin("/"):
            form = MultiDict([("identifier", patron.authorization_identifier)])
            flask.request.form = form

            response = controller.reset_adobe_id(authenticator)
            eq_(200, response.status_code)

            # _load_patrondata was called and gave us information about
            # which Patron to modify.
            controller.called_with = authenticator

        # Both of the Patron's credentials are gone.
        eq_(patron.credentials, [])

        # Here, the AuthenticationProvider finds a PatronData, but the
        # controller can't turn it into a Patron because it's too vague.
        controller.mock_patrondata = PatronData()
        with self.request_context_with_library_and_admin("/"):
            flask.request.form = form
            response = controller.reset_adobe_id(authenticator)

            eq_(404, response.status_code)
            eq_(NO_SUCH_PATRON.uri, response.uri)
            assert "Could not create local patron object" in response.detail
