### Exa Models and Enums ###
from enum import Enum


class SearchType(str, Enum):
    """
    Search type for Exa API.
    """

    NEURAL = "neural"  # Uses embeddings
    KEYWORD = "keyword"  # Uses traditional search
    AUTO = "auto"  # Decides betwee neural and keyword, based on the query
