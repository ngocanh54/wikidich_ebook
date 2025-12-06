"""
Data models for wikidich ebook creator.
"""
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class BookInfo:
    """Data class to hold book metadata."""
    title: str
    author: str
    status: str
    url_pattern: str
    output_folder: str
    image_url: str
    main_page_url: str
    bookcover_filename: str
    latest_chapter: str
    updated_time: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> 'BookInfo':
        """Create BookInfo from dictionary."""
        return cls(**data)


@dataclass
class Chapter:
    """Data class to hold chapter information."""
    chapter_number: int
    chapter_name: str
    url: str
    volume_name: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
