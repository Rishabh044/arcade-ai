from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass
class Critic(ABC):
    critic_field: str
    weight: float

    @property
    def max_score(self) -> float:
        return self.weight

    @abstractmethod
    def evaluate(self, expected: Any, actual: Any) -> dict[str, Any]:
        pass


@dataclass
class BinaryCritic(Critic):
    """A critic for performing exact equality comparisons between expected and actual values.

    This critic evaluates whether the expected and actual values are exactly equal.
    It's useful for scenarios where only an exact match is acceptable.

    Returns a dict with:
        - "match": True if expected == actual, otherwise False.
        - "score": The full weight if there's a match, otherwise 0.0.
    """

    def evaluate(self, expected: Any, actual: Any) -> dict[str, float | bool]:
        match = expected == actual
        return {"match": match, "score": self.weight if match else 0.0}


@dataclass
class NumericCritic(Critic):
    """A critic for evaluating numeric values within a specified range.

    This critic performs a "fuzzy" comparison of numeric values, where values closer
    to each other (relative to the specified range) result in higher scores. It's
    useful for scenarios where exact matches aren't necessary, but closeness within
    a certain tolerance is rewarded.

    Attributes:
        value_range (tuple[float, float]): The min and max values of the expected range.
        match_threshold (float): The threshold for considering a match (default 0.8).

    The evaluation process:
    1. Normalizes both expected and actual values to a 0-1 scale based on value_range.
    2. Calculates the absolute difference between these normalized values.
    3. Subtracts this difference from 1 to get a similarity score (closer to 1 is more similar).
    4. Multiplies the similarity by the critic's weight for the final score.

    Returns a dict with:
        - "match": True if the score >= match_threshold, otherwise False.
        - "score": The calculated score (similarity * weight).
    """

    value_range: tuple[float, float]
    match_threshold: float = 0.8

    def evaluate(self, expected: Any, actual: Any) -> dict[str, Any]:
        min_val, max_val = self.value_range
        normalized_expected = float((float(expected) - min_val) / (max_val - min_val))
        normalized_actual = float((float(actual) - min_val) / (max_val - min_val))
        score = float(1 - abs(normalized_expected - normalized_actual))
        return {"match": bool(score >= self.match_threshold), "score": float(score * self.weight)}


@dataclass
class SimilarityCritic(Critic):
    """A critic for evaluating the similarity between two strings.

    This critic uses a specified similarity metric to compare the expected and actual
    string values. Currently, it supports cosine similarity using TF-IDF vectorization.

    Args:
        metric: The similarity metric to use (default is "cosine").
        similarity_threshold: The threshold for considering a match (default 0.8).

    The evaluation process:
    1. Converts both expected and actual values to strings.
    2. Calculates the similarity score using the specified metric.
    3. Determines a match based on the similarity_threshold.
    4. Calculates the final score by multiplying the similarity by the critic's weight.

    Returns a dict with:
        - "match": True if similarity >= similarity_threshold, otherwise False.
        - "score": The calculated score (similarity * weight).

    Raises:
        ImportError: If scikit-learn is not installed (required for cosine similarity).
        ValueError: If an unsupported similarity metric is specified.
    """

    metric: str = "cosine"
    similarity_threshold: float = 0.8

    def evaluate(self, expected: str, actual: str) -> dict[str, Any]:
        if self.metric == "cosine":
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity
            except ImportError:
                raise ImportError(
                    "Please install scikit-learn to use the cosine similarity metric."
                )
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform([str(expected), str(actual)])
            similarity = float(cosine_similarity(tfidf_matrix[0], tfidf_matrix[1])[0][0])
        else:
            raise ValueError(f"Unsupported similarity metric: {self.metric}")
        return {
            "match": bool(similarity >= self.similarity_threshold),
            "score": float(similarity * self.weight),
        }
