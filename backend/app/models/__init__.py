# Import all models here so SQLAlchemy registers them with Base.metadata
from app.models.opportunity import Opportunity
from app.models.architecture import ArchitectureLocation
from app.models.collector import Collector
from app.models.curator import Curator
from app.models.press import PressItem
from app.models.proposal import Proposal
from app.models.knowledge import KnowledgeItem
from app.models.artist import Artist
from app.models.artwork import Artwork
from app.models.institution import Institution
from app.models.exhibition import Exhibition
from app.models.relationships import (
    CollectorArtistRelation,
    ArtistInstitutionRelation,
    ArtistGalleryRelation,
)

__all__ = [
    "Opportunity",
    "ArchitectureLocation",
    "Collector",
    "Curator",
    "PressItem",
    "Proposal",
    "KnowledgeItem",
    "Artist",
    "Artwork",
    "Institution",
    "Exhibition",
    "CollectorArtistRelation",
    "ArtistInstitutionRelation",
    "ArtistGalleryRelation",
]
