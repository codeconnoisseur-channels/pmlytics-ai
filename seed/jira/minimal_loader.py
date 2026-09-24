"""Minimal deterministic loader for Jira expectations in MockServer 7.6.0.

Loads scenario expectations (PAY-117, CORE-82, PAY-134, background tasks) into MockServer
via its official REST control endpoint PUT /mockserver/expectation.
Ground truth evaluation metadata is strictly excluded.
"""

from mocks.jira.expectations import get_jira_mock_expectations
from mocks.jira.mockserver_controller import MockServerController


async def load_minimal_jira_expectations(controller: MockServerController) -> int:
    """Load minimal scenario Jira expectations into MockServer 7.6.0.

    Returns the count of expectations successfully registered.
    """
    expectations = get_jira_mock_expectations()
    return await controller.load_expectations(expectations)
