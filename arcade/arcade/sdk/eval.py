import functools
import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable

from openai.resources.chat.completions import ChatCompletion
from pydantic import ValidationError

from arcade.client import Arcade
from arcade.core.catalog import ToolCatalog
from arcade.core.config import config


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

    # a little bit much on the casts, but it's fine
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


@dataclass
class EvalRubric:
    fail_threshold: float
    """The threshold for failing the evaluation (0.0-1.0)."""
    warn_threshold: float
    """The threshold for issuing a warning (0.0-1.0)."""


@dataclass
class EvalCase:
    """
    Represents a single evaluation case within an EvalSuite.

    An EvalCase defines a specific scenario to test, including the user input,
    expected tool usage, and criteria for evaluation.

    Example:
        case = EvalCase(
            name="Check stock price",
            user_message="What's the current stock price of Apple?",
            expected_tool="get_stock_price",
            expected_tool_args={"symbol": "AAPL"},
            rubric=EvalRubric(fail_threshold=0.6, warn_threshold=0.9),
            critics=[
                BinaryCritic(critic_field="symbol", weight=1.0),
                NumericCritic(critic_field="price", weight=1.0, value_range=(0, 1000))
            ]
        )

    Attributes:
        name: A descriptive name for this evaluation case.
        user_message: The user input to be sent to the AI model.
        expected_tool: The name of the tool expected to be called by the model.
        expected_tool_args: A dictionary of expected arguments for the tool call.
        rubric: An EvalRubric object defining pass/fail criteria.
        critics: A list of Critic objects used to evaluate tool arguments.
        additional_messages: Optional list of additional context messages.
    """

    name: str
    user_message: str
    expected_tool: str
    expected_tool_args: dict[str, Any]
    rubric: EvalRubric
    critics: list[Critic] = field(default_factory=list)
    additional_messages: list[dict[str, str]] = field(default_factory=list)

    def evaluate(
        self,
        actual_tool: str,
        actual_tool_args: dict[str, Any],
    ) -> dict[str, Any]:
        total_score = 0.0
        total_weight = 0.0
        results = []

        # Evaluate tool selection
        tool_match = actual_tool == self.expected_tool
        total_score += 1.0 if tool_match else 0.0
        total_weight += 1.0
        results.append(
            {
                "field": "tool_selection",
                "match": tool_match,
                "score": 1.0 if tool_match else 0.0,
                "weight": 1.0,  # weight is always 1.0 for tool selection
            }
        )

        # Evaluate arguments using critics
        for critic in self.critics:
            expected_value = self.expected_tool_args.get(critic.critic_field)
            actual_value = actual_tool_args.get(critic.critic_field)
            if expected_value is not None and actual_value is not None:
                result = critic.evaluate(expected_value, actual_value)
                total_score += result["score"]
                total_weight += critic.weight
                results.append(
                    {
                        "field": critic.critic_field,
                        **result,
                        "weight": critic.weight,
                        "max_score": critic.max_score,
                    }
                )

        normalized_score = total_score / total_weight if total_weight > 0 else 0.0
        return {
            "score": normalized_score,
            "pass": normalized_score >= self.rubric.warn_threshold,
            "warning": self.rubric.fail_threshold <= normalized_score < self.rubric.warn_threshold,
            "fail": normalized_score < self.rubric.fail_threshold,
            "critic_results": results,
        }


@dataclass
class EvalSuite:
    """
    A suite for evaluating AI model performance on specific tasks or scenarios.

    EvalSuite manages a collection of EvalCases, each representing a specific test scenario.
    It provides methods to add cases, register tools, and run evaluations against specified models.

    Example usage:
        suite = EvalSuite(
            name="Weather Inquiry Suite",
            system="You are a helpful weather assistant.",
            exact_tool_selection=True,
            tool_choice="auto"
        )
        suite.add_case(
            name="Simple temperature query",
            user_message="What's the temperature in New York?",
            expected_tool="get_temperature",
            expected_tool_args={"city": "New York"},
            rubric=EvalRubric(fail_threshold=0.5, warn_threshold=0.8),
            critics=[
                BinaryCritic(critic_field="city", weight=1.0),
                NumericCritic(critic_field="temperature", weight=1.0, value_range=(0, 100))
            ]
        )
        suite.register_tool(get_temperature)
        results = suite.run("gpt-3.5-turbo", arcade_client)

    Attributes:
        name: The name of the evaluation suite.
        system: The system message to be used for all cases in this suite.
        cases: A list of EvalCase objects representing individual test scenarios.
        exact_tool_selection: Whether to require exact tool name matches (default True).
        exact_tool_args: Whether to require exact argument matches (default False).
        tool_choice: The tool choice mode for the AI model ("auto" or "function").
        catalog: A ToolCatalog object containing registered tools.
    """

    name: str
    system: str
    cases: list[EvalCase] = field(default_factory=list)
    exact_tool_selection: bool = True
    exact_tool_args: bool = False
    tool_choice: str = "auto"
    catalog: ToolCatalog = field(default_factory=ToolCatalog)

    def add_case(
        self,
        name: str,
        user_message: str,
        expected_tool: str,
        expected_tool_args: dict[str, Any],
        rubric: EvalRubric,
        critics: list[Critic],
        additional_messages: list[dict[str, str]] | None = None,
    ) -> None:
        """
        Add a new evaluation case to the suite.

        Args:
            name: The name of the evaluation case.
            user_message: The user's input message.
            expected_tool: The name of the expected tool to be called.
            expected_tool_args: The expected arguments for the tool.
            rubric: The evaluation rubric for this case.
            critics: List of critics to evaluate the tool arguments.
            additional_messages: Optional list of additional messages for context.
        """
        case = EvalCase(
            name=name,
            user_message=user_message,
            expected_tool=expected_tool,
            expected_tool_args=expected_tool_args,
            rubric=rubric,
            critics=critics,
            additional_messages=additional_messages or [],
        )
        self.cases.append(case)

    def extend_case(
        self,
        name: str,
        user_message: str,
        expected_tool: str | None = None,
        expected_tool_args: dict[str, Any] | None = None,
        rubric: EvalRubric | None = None,
        critics: list[Critic] | None = None,
    ) -> None:
        """
        Extend the last added case with new information.

        Args:
            name: The name of the extended case.
            user_message: The new user message for this extended case.
            expected_tool: The new expected tool (if different from the last case).
            expected_tool_args: New or updated expected tool arguments.
            rubric: A new rubric (if different from the last case).
            critics: New critics (if different from the last case).
        """
        if not self.cases:
            raise ValueError("No cases to extend. Add a case first.")

        last_case = self.cases[-1]

        # Create a new message list with the previous case's messages and user message
        new_additional_messages = [
            *last_case.additional_messages,
            {"role": "user", "content": last_case.user_message},
        ]

        # Create a new case, copying from the last one and updating fields
        new_case = EvalCase(
            name=name,
            user_message=user_message,
            expected_tool=expected_tool or last_case.expected_tool,
            expected_tool_args=last_case.expected_tool_args.copy(),
            rubric=rubric or last_case.rubric,
            critics=critics or last_case.critics.copy(),
            additional_messages=new_additional_messages,
        )

        # Update expected_tool_args if provided
        if expected_tool_args:
            new_case.expected_tool_args.update(expected_tool_args)

        self.cases.append(new_case)

    def register_tool(self, tool_func: Callable):
        self.catalog.add_tool(tool_func)

    def register_toolkit(self, toolkit):
        self.catalog.add_toolkit(toolkit)

    def run(self, model: str, arcade_client: Arcade) -> dict[str, Any]:
        results = {"model": model, "cases": []}

        for case in self.cases:
            messages = [{"role": "system", "content": self.system}]
            messages.extend(list(case.additional_messages))
            messages.append({"role": "user", "content": case.user_message})

            response = arcade_client.chat.completions.create(
                model=model,
                messages=messages,
                tool_choice=self.tool_choice,
                tools=list(self.catalog.tools.keys()),
            )

            predicted_args = get_tool_args(response)

            for tool_name, args in predicted_args:
                try:
                    # Validate input against the tool's input model
                    materialized_tool = self.catalog[tool_name]
                    materialized_tool.input_model(**args)
                except KeyError:
                    evaluation = {
                        "score": 0,
                        "pass": False,
                        "warning": False,
                        "fail": True,
                        "error": f"Tool '{tool_name}' not found in catalog.",
                    }
                except ValidationError as e:
                    evaluation = {
                        "score": 0,
                        "pass": False,
                        "warning": False,
                        "fail": True,
                        "error": f"Input validation failed: {e!s}",
                    }
                else:
                    evaluation = case.evaluate(
                        tool_name,
                        args,
                    )

                result = {
                    "name": case.name,
                    "input": case.user_message,
                    "expected_tool": case.expected_tool,
                    "expected_args": case.expected_tool_args,
                    "predicted_tool": tool_name,
                    "predicted_args": args,
                    "evaluation": evaluation,
                }

                results["cases"].append(result)

        return results


def get_tool_args(chat_completion: ChatCompletion) -> list[tuple[str, dict[str, Any]]]:
    """
    Returns the tool arguments from the chat completion object.
    """
    tool_args_list = []
    message = chat_completion.choices[0].message
    if message.tool_calls:
        for tool_call in message.tool_calls:
            tool_args_list.append(
                (
                    tool_call.function.name,
                    json.loads(tool_call.function.arguments),
                )
            )
    return tool_args_list


def tool_eval(*models: str):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper():
            client = Arcade(
                api_key=config.api.key,
                base_url=config.engine_url,
            )
            suite = func()
            if not isinstance(suite, EvalSuite):
                raise TypeError("Eval function must return an EvalSuite")
            results = []
            for model in models:
                results.append(suite.run(model, client))
            return results

        wrapper.__tool_eval__ = True
        return wrapper

    return decorator
