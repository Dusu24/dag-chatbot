# core/models.py
# These are the data structures used throughout the pipeline.
# Think of them as containers that hold your data at each stage.

from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uuid


class RawSegment(BaseModel):
    """
    One chapter from one book — straight out of the file, not yet cleaned.
    """
    segment_id: str = ""  # unique ID, assigned automatically
    book_title: str       # e.g. "daughter-you-can-make-it"
    chapter_number: Optional[int] = None   # e.g. 33
    chapter_title: Optional[str] = None   # e.g. "Daughter of Destiny"
    raw_text: str         # the full chapter text, uncleaned

    def __init__(self, **data):
        super().__init__(**data)
        if not self.segment_id:
            self.segment_id = str(uuid.uuid4())


class Chunk(BaseModel):
    """
    A small piece of a chapter — this is what gets stored
    in the database and searched when users ask questions.
    """
    chunk_id: str = ""
    source_segment_id: str   # which segment this came from
    book_title: str
    chapter_number: Optional[int] = None
    chapter_title: Optional[str] = None
    text: str                # the actual text of this chunk
    char_count: int          # how many characters
    chunk_index: int         # position within its chapter (0, 1, 2...)
    ingestion_run_id: str    # which pipeline run created this
    created_at: str = ""

    def __init__(self, **data):
        super().__init__(**data)
        if not self.chunk_id:
            self.chunk_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.utcnow().isoformat()


class EmbeddedChunk(Chunk):
    """
    A chunk that has been converted into a vector (list of numbers).
    This is what actually gets stored in Qdrant.
    """
    embedding: list[float]        # the vector — typically 1536 numbers
    embedding_model: str          # which model created it