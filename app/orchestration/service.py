"""Production application service orchestrating PMLytics AI investigations."""

import logging
import uuid
from typing import Any

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from psycopg.rows import dict_row
from psycopg_pool import AsyncConnectionPool

from app.agents.analytics import AnalyticsAgent
from app.agents.engineering import EngineeringAgent
from app.agents.research import ResearchAgent
from app.config.settings import Settings, get_model_for_role, get_settings
from app.domain.investigation_scope import InvestigationScope
from app.integrations.jira import JiraAdapter, JiraClient
from app.integrations.llm.client import LLMClient, OpenRouterClient
from app.integrations.observability.tracer import InvestigationTracer, trace_investigation
from app.integrations.posthog import PostHogAdapter, PostHogClient
from app.integrations.zendesk import ZendeskAdapter, ZendeskClient
from app.orchestration.graph import create_investigation_graph
from app.orchestration.state import InvestigationState
from app.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class InvestigationService:
    """Authoritative production investigation service.

    Orchestrates the multi-agent graph across Zendesk, PostHog, and Jira,
    instruments distributed LangSmith tracing with strict fail-open resilience,
    and returns the completed investigation state with verified provenance.
    """

    def __init__(
        self,
        llm_client: LLMClient,
        research_agent: ResearchAgent,
        analytics_agent: AnalyticsAgent,
        engineering_agent: EngineeringAgent,
        settings: Settings | None = None,
    ) -> None:
        self.llm_client = llm_client
        self.research_agent = research_agent
        self.analytics_agent = analytics_agent
        self.engineering_agent = engineering_agent
        self.settings = settings or get_settings()
        self.checkpointer: AsyncPostgresSaver | None = None
        self._checkpoint_pool: AsyncConnectionPool[Any] | None = None

        # Build compiled investigation graph
        self.graph = create_investigation_graph(
            llm_client=self.llm_client,
            research_agent=self.research_agent,
            analytics_agent=self.analytics_agent,
            engineering_agent=self.engineering_agent,
            planner_model=get_model_for_role("planner"),
            assessment_model=get_model_for_role("assessment"),
            pm_model=get_model_for_role("pm"),
            pm_revision_model=get_model_for_role("pm_revision"),
            critic_model=get_model_for_role("critic"),
        )

    async def start(self) -> None:
        """Open durable workflow storage and recompile the graph against it."""
        if self.checkpointer is not None or not self.settings.database_url:
            return
        database_url = self.settings.database_url.replace(
            "postgresql+asyncpg://", "postgresql://", 1
        ).replace("postgresql+psycopg://", "postgresql://", 1)
        pool: AsyncConnectionPool[Any] = AsyncConnectionPool(
            conninfo=database_url,
            min_size=1,
            max_size=4,
            open=False,
            check=AsyncConnectionPool.check_connection,
            kwargs={
                "autocommit": True,
                "prepare_threshold": 0,
                "row_factory": dict_row,
            },
            max_idle=60.0,
            max_lifetime=300.0,
            reconnect_timeout=30.0,
        )
        await pool.open(wait=True)
        checkpointer = AsyncPostgresSaver(pool)
        try:
            await checkpointer.setup()
        except Exception:
            await pool.close()
            raise
        self._checkpoint_pool = pool
        self.checkpointer = checkpointer
        self.graph = create_investigation_graph(
            llm_client=self.llm_client,
            research_agent=self.research_agent,
            analytics_agent=self.analytics_agent,
            engineering_agent=self.engineering_agent,
            planner_model=get_model_for_role("planner"),
            assessment_model=get_model_for_role("assessment"),
            pm_model=get_model_for_role("pm"),
            pm_revision_model=get_model_for_role("pm_revision"),
            critic_model=get_model_for_role("critic"),
            checkpointer=checkpointer,
        )

    async def close(self) -> None:
        """Release the checkpoint connection owned by this service."""
        if self._checkpoint_pool:
            await self._checkpoint_pool.close()
        self._checkpoint_pool = None
        self.checkpointer = None

    @classmethod
    def create_default(cls, settings: Settings | None = None) -> "InvestigationService":
        """Factory creating the production service with configured adapters and clients."""
        cfg = settings or get_settings()

        llm_client = OpenRouterClient(
            api_key=cfg.openrouter_api_key,
            base_url=cfg.openrouter_base_url,
        )
        zendesk_client = ZendeskClient(
            base_url=cfg.zendesk_base_url,
            username=cfg.zendesk_username,
            api_key=cfg.zendesk_api_key,
            timeout_seconds=cfg.zendesk_timeout_seconds,
        )
        posthog_client = PostHogClient(
            host=cfg.posthog_host,
            project_id=cfg.posthog_project_id,
            api_key=cfg.posthog_api_key,
            timeout_seconds=cfg.posthog_timeout_seconds,
        )
        jira_client = JiraClient(
            base_url=cfg.jira_base_url,
            username=cfg.jira_username,
            api_token=cfg.jira_api_token,
            timeout_seconds=cfg.jira_timeout_seconds,
        )

        zendesk_adapter = ZendeskAdapter(zendesk_client)
        posthog_adapter = PostHogAdapter(posthog_client)
        jira_adapter = JiraAdapter(jira_client)

        registry = ToolRegistry.create_default(
            zendesk_adapter=zendesk_adapter,
            posthog_adapter=posthog_adapter,
            jira_adapter=jira_adapter,
        )

        research_agent = ResearchAgent(
            llm_client=llm_client,
            toolset=registry.get_toolset_for_role("research"),
        )
        analytics_agent = AnalyticsAgent(
            llm_client=llm_client,
            toolset=registry.get_toolset_for_role("analytics"),
        )
        engineering_agent = EngineeringAgent(
            llm_client=llm_client,
            toolset=registry.get_toolset_for_role("engineering"),
        )

        return cls(
            llm_client=llm_client,
            research_agent=research_agent,
            analytics_agent=analytics_agent,
            engineering_agent=engineering_agent,
            settings=cfg,
        )

    async def investigate(
        self,
        user_query: str,
        investigation_id: str | None = None,
        context: dict[str, Any] | None = None,
        tracer: InvestigationTracer | None = None,
        resume: bool = False,
    ) -> InvestigationState:
        """Execute an investigation workflow from user query to recommendation with distributed tracing."""
        inv_id = investigation_id or f"inv_{uuid.uuid4().hex[:12]}"
        active_tracer = tracer or InvestigationTracer(
            investigation_id=inv_id,
            enabled=bool(self.settings.langsmith_tracing and self.settings.langsmith_api_key),
            environment=self.settings.environment,
        )

        max_revisions = 1 if self.settings.investigation_profile == "standard" else 2
        scope_payload = (context or {}).get("scope")
        scope = InvestigationScope.model_validate(scope_payload or {})
        initial_state = (
            None
            if resume
            else InvestigationState(
                investigation_id=inv_id,
                user_query=user_query,
                scope=scope,
                max_revisions=max_revisions,
            )
        )
        graph_config = {
            "configurable": {"thread_id": inv_id},
            "metadata": {"investigation_id": inv_id},
        }

        with trace_investigation(active_tracer):
            try:
                raw_output = await self.graph.ainvoke(
                    initial_state,
                    config=graph_config,
                    durability="sync" if self.checkpointer else None,
                )
                final_state = InvestigationState.model_validate(raw_output)
                final_status = "completed" if final_state.recommendation else "incomplete"
                active_tracer.close(final_status=final_status)
                return final_state
            except Exception as exc:
                logger.error(
                    "Investigation '%s' encountered unhandled error: %s",
                    inv_id,
                    exc,
                    exc_info=True,
                )
                active_tracer.close(final_status="error", error=str(exc))
                raise


async def run_investigation(
    user_query: str,
    investigation_id: str | None = None,
    settings: Settings | None = None,
) -> InvestigationState:
    """Convenience top-level function executing a production investigation."""
    service = InvestigationService.create_default(settings=settings)
    return await service.investigate(user_query=user_query, investigation_id=investigation_id)
