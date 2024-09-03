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
    def evaluate(self, expected: Any, actual: Any) -> dict[str, float | bool]:
        match = expected == actual
        return {"match": match, "score": self.weight if match else 0.0}


@dataclass
class NumericCritic(Critic):
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
    name: str
    fail_threshold: float
    warn_threshold: float


@dataclass
class EvalCase:
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
        results.append({
            "field": "tool_selection",
            "match": tool_match,
            "score": 1.0 if tool_match else 0.0,
            "weight": 1.0,  # weight is always 1.0 for tool selection
        })

        # Evaluate arguments using critics
        for critic in self.critics:
            expected_value = self.expected_tool_args.get(critic.critic_field)
            actual_value = actual_tool_args.get(critic.critic_field)
            if expected_value is not None and actual_value is not None:
                result = critic.evaluate(expected_value, actual_value)
                total_score += result["score"]
                total_weight += critic.weight
                results.append({
                    "field": critic.critic_field,
                    **result,
                    "weight": critic.weight,
                    "max_score": critic.max_score,
                })

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
    name: str
    system: str
    cases: list[EvalCase] = field(default_factory=list)
    exact_tool_selection: bool = True
    exact_tool_args: bool = False
    tool_choice: str = "auto"
    catalog: ToolCatalog = field(default_factory=ToolCatalog)

    def add_case(
        self,
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
            user_message: The user's input message.
            expected_tool: The name of the expected tool to be called.
            expected_tool_args: The expected arguments for the tool.
            rubric: The evaluation rubric for this case.
            critics: List of critics to evaluate the tool arguments.
            additional_messages: Optional list of additional messages for context.
        """
        case = EvalCase(
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
        user_message: str,
        expected_tool: str | None = None,
        expected_tool_args: dict[str, Any] | None = None,
        rubric: EvalRubric | None = None,
        critics: list[Critic] | None = None,
    ) -> None:
        """
        Extend the last added case with new information.

        Args:
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
            tool_args_list.append((
                tool_call.function.name,
                json.loads(tool_call.function.arguments),
            ))
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
