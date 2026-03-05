"""
Celery tasks — thin wrappers that call the async agents via asyncio.run().
Agents live in backend/app/agents/ and use SQLAlchemy async sessions.
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../backend"))

from workers.celery_app import celery_app


def _run(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.get_event_loop().run_until_complete(coro)


@celery_app.task(name="tasks.scan_opportunities", bind=True, max_retries=3)
def scan_opportunities(self):
    try:
        from app.agents.opportunity_scanner import OpportunityScanner
        scanner = OpportunityScanner()
        result = _run(scanner.run())
        return {"status": "ok", "saved": result}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.scout_architecture", bind=True, max_retries=3)
def scout_architecture(self):
    try:
        from app.agents.architecture_scout import ArchitectureScout
        scout = ArchitectureScout()
        result = _run(scout.run())
        return {"status": "ok", "saved": result}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.monitor_press", bind=True, max_retries=3)
def monitor_press(self):
    try:
        from app.agents.press_monitor import PressMonitor
        monitor = PressMonitor()
        result = _run(monitor.run())
        return {"status": "ok", "saved": result}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(name="tasks.ingest_knowledge", bind=True, max_retries=3)
def ingest_knowledge(self, url: str):
    try:
        from app.agents.knowledge_ingestor import KnowledgeIngestor
        ingestor = KnowledgeIngestor()
        result = _run(ingestor.ingest_url(url))
        return {"status": "ok", "item_id": result}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
