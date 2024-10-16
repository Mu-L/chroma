from typing import Optional, Sequence, TypeVar, Type
from abc import abstractmethod
from chromadb.types import (
    Collection,
    Operation,
    RequestVersionContext,
    Segment,
    SeqId,
    Metadata,
)
from chromadb.config import Component, System
from uuid import UUID
from enum import Enum


class SegmentType(Enum):
    SQLITE = "urn:chroma:segment/metadata/sqlite"
    HNSW_LOCAL_MEMORY = "urn:chroma:segment/vector/hnsw-local-memory"
    HNSW_LOCAL_PERSISTED = "urn:chroma:segment/vector/hnsw-local-persisted"
    HNSW_DISTRIBUTED = "urn:chroma:segment/vector/hnsw-distributed"
    BLOCKFILE_RECORD = "urn:chroma:segment/record/blockfile"
    BLOCKFILE_METADATA = "urn:chroma:segment/metadata/blockfile"


class SegmentImplementation(Component):
    @abstractmethod
    def __init__(self, sytstem: System, segment: Segment):
        pass

    @abstractmethod
    def count(self, request_version_context: RequestVersionContext) -> int:
        """Get the number of embeddings in this segment"""
        pass

    @abstractmethod
    def max_seqid(self) -> SeqId:
        """Get the maximum SeqID currently indexed by this segment"""
        pass

    @staticmethod
    def propagate_collection_metadata(metadata: Metadata) -> Optional[Metadata]:
        """Given an arbitrary metadata map (e.g, from a collection), validate it and
        return metadata (if any) that is applicable and should be applied to the
        segment. Validation errors will be reported to the user."""
        return None

    @abstractmethod
    def delete(self) -> None:
        """Delete the segment and all its data"""
        ...


S = TypeVar("S", bound=SegmentImplementation)


class SegmentManager(Component):
    """Interface for a pluggable strategy for creating, retrieving and instantiating
    segments as required"""

    @abstractmethod
    def create_segments(self, collection: Collection) -> Sequence[Segment]:
        """Return the segments required for a new collection. Returns only segment data,
        does not persist to the SysDB"""
        pass

    @abstractmethod
    def delete_segments(self, collection_id: UUID) -> Sequence[UUID]:
        """Delete any local state for all the segments associated with a collection, and
        returns a sequence of their IDs. Does not update the SysDB."""
        pass

    # Future Note: To support time travel, add optional parameters to this method to
    # retrieve Segment instances that are bounded to events from a specific range of
    # time
    @abstractmethod
    def get_segment(self, collection_id: UUID, type: Type[S]) -> S:
        """Return the segment that should be used for servicing queries to a collection.
        Implementations should cache appropriately; clients are intended to call this
        method repeatedly rather than storing the result (thereby giving this
        implementation full control over which segment impls are in or out of memory at
        a given time.)"""
        pass

    @abstractmethod
    def hint_use_collection(self, collection_id: UUID, hint_type: Operation) -> None:
        """Signal to the segment manager that a collection is about to be used, so that
        it can preload segments as needed. This is only a hint, and implementations are
        free to ignore it."""
        pass
