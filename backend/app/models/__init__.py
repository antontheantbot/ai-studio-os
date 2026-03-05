# Import all models here so SQLAlchemy registers them with Base.metadata
from app.models.opportunity import Opportunity
from app.models.architecture import ArchitectureLocation
from app.models.collector import Collector
from app.models.curator import Curator
from app.models.press import PressItem
from app.models.proposal import Proposal
from app.models.knowledge import KnowledgeItem

__all__ = [
    "Opportunity",
    "ArchitectureLocation",
    "Collector",
    "Curator",
    "PressItem",
    "Proposal",
    "KnowledgeItem",
]
