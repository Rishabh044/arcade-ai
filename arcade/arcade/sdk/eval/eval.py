import functools
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from openai.resources.chat.completions import ChatCompletion
from scipy.optimize import linear_sum_assignment

from arcade.client import Arcade
from arcade.core.config import config

if TYPE_CHECKING:
    from arcade.core.catalog import ToolCatalog
    from arcade.sdk.eval.critic import Critic


@dataclass
class EvalRubric:
    fail_threshold: float
    """The threshold for failing the evaluation (0.0-1.0)."""
    warn_threshold: float
    """The threshold for issuing a warning (0.0-1.0)."""


@dataclass
class ExpectedToolCall:
    name: str
    args: dict[str, Any]


@dataclass
class EvalCase:
    """
    Represents a single evaluation case within an EvalSuite.

    An EvalCase defines a specific scenario to test, including the user input,
    expected tool usage, and criteria for evaluation.

    Attributes:
        name: A descriptive name for this evaluation case.
        user_message: The user input to be sent to the AI model.
        expected_tool_calls: A list of ExpectedToolCall objects representing the expected tool calls.
        rubric: An EvalRubric object defining pass/fail criteria.
        critics: A list of Critic objects used to evaluate tool arguments.
        additional_messages: Optional list of additional context messages.
    """

    name: str
    user_message: str
    expected_tool_calls: list[ExpectedToolCall]
    rubric: EvalRubric
    critics: list["Critic"]
    additional_messages: list[dict[str, str]] = field(default_factory=list)

    def evaluate(
        self,
        actual_tool_calls: list[tuple[str, dict[str, Any]]],
    ) -> dict[str, Any]:
        # Create a cost matrix for the assignment problem
        cost_matrix = self._create_cost_matrix(actual_tool_calls)

        # Use lsa algorithm to find the optimal assignment
        row_ind, col_ind = linear_sum_assignment(cost_matrix, maximize=True)

        total_score = 0.0
        total_weight = 0.0
        results = []

        for i, j in zip(row_ind, col_ind):
            if i < len(self.expected_tool_calls) and j < len(actual_tool_calls):
                expected = self.expected_tool_calls[i]
                actual_tool, actual_args = actual_tool_calls[j]

                # Evaluate tool selection
                tool_match = actual_tool == expected.name
                tool_score = 1.0 if tool_match else 0.0
                total_score += tool_score
                total_weight += 1.0
                results.append({
                    "field": "tool_selection",
                    "match": tool_match,
                    "score": tool_score,
                    "weight": 1.0,
                    "expected": expected.name,
                    "actual": actual_tool,
                })

                # Evaluate arguments using critics
                for critic in self.critics:
                    expected_value = expected.args.get(critic.critic_field)
                    actual_value = actual_args.get(critic.critic_field)
                    if expected_value is not None and actual_value is not None:
                        result = critic.evaluate(expected_value, actual_value)
                        total_score += result["score"]
                        total_weight += critic.weight
                        results.append({
                            "field": critic.critic_field,
                            **result,
                            "weight": critic.weight,
                            "max_score": critic.max_score,
                            "expected": expected_value,
                            "actual": actual_value,
                        })

        # Penalize for missing or extra tool calls
        missing_calls = len(self.expected_tool_calls) - len(actual_tool_calls)
        if missing_calls > 0:
            total_weight += missing_calls
            results.append({
                "field": "missing_tool_calls",
                "match": False,
                "score": 0.0,
                "weight": missing_calls,
                "expected": len(self.expected_tool_calls),
                "actual": len(actual_tool_calls),
            })
        elif missing_calls < 0:
            extra_calls = abs(missing_calls)
            total_weight += extra_calls
            results.append({
                "field": "extra_tool_calls",
                "match": False,
                "score": 0.0,
                "weight": extra_calls,
                "expected": len(self.expected_tool_calls),
                "actual": len(actual_tool_calls),
            })

        normalized_score = total_score / total_weight if total_weight > 0 else 0.0
        return {
            "score": normalized_score,
            "pass": normalized_score >= self.rubric.warn_threshold,
            "warning": self.rubric.fail_threshold <= normalized_score < self.rubric.warn_threshold,
            "fail": normalized_score < self.rubric.fail_threshold,
            "critic_results": results,
        }

    def _create_cost_matrix(
        self, actual_tool_calls: list[tuple[str, dict[str, Any]]]
    ) -> np.ndarray:
        """
        Create a cost matrix for the Hungarian algorithm.

        This method computes the score for each possible pairing of expected and actual tool calls.
        The resulting matrix is used by the Hungarian algorithm to find the optimal assignment.

        Args:
            actual_tool_calls: A list of tuples containing the actual tool calls and their arguments.

        Returns:
            A numpy array representing the cost matrix.
        """
        n = max(len(self.expected_tool_calls), len(actual_tool_calls))
        cost_matrix = np.zeros((n, n))

        for i, expected in enumerate(self.expected_tool_calls):
            for j, (actual_tool, actual_args) in enumerate(actual_tool_calls):
                score = 1.0 if expected.name == actual_tool else 0.0
                for critic in self.critics:
                    expected_value = expected.args.get(critic.critic_field)
                    actual_value = actual_args.get(critic.critic_field)
                    if expected_value is not None and actual_value is not None:
                        result = critic.evaluate(expected_value, actual_value)
                        score += result["score"]
                cost_matrix[i, j] = score

        return cost_matrix


@dataclass
class EvalSuite:
    """
    A suite for evaluating AI model performance on specific tasks or scenarios.

    EvalSuite manages a collection of EvalCases, each representing a specific test scenario.
    It provides methods to add cases, register tools, and run evaluations against specified models.

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
    catalog: "ToolCatalog"
    cases: list[EvalCase] = field(default_factory=list)
    exact_tool_selection: bool = True
    exact_tool_args: bool = False
    tool_choice: str = "auto"

    def add_case(
        self,
        name: str,
        user_message: str,
        expected_tool_calls: list[ExpectedToolCall],
        rubric: EvalRubric,
        critics: list["Critic"],
        additional_messages: list[dict[str, str]] | None = None,
    ) -> None:
        """
        Add a new evaluation case to the suite.

        Args:
            name: The name of the evaluation case.
            user_message: The user's input message.
            expected_tool_calls: A list of expected tool calls.
            rubric: The evaluation rubric for this case.
            critics: list of critics to evaluate the tool arguments.
            additional_messages: Optional list of additional messages for context.
        """
        case = EvalCase(
            name=name,
            user_message=user_message,
            expected_tool_calls=expected_tool_calls,
            rubric=rubric,
            critics=critics,
            additional_messages=additional_messages or [],
        )
        self.cases.append(case)

    def extend_case(
        self,
        name: str,
        user_message: str,
        expected_tool_calls: list[ExpectedToolCall] | None = None,
        rubric: EvalRubric | None = None,
        critics: list["Critic"] | None = None,
    ) -> None:
        """
        Extend the last added case with new information.

        Args:
            name: The name of the extended case.
            user_message: The new user message for this extended case.
            expected_tool_calls: New or updated expected tool calls.
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
            expected_tool_calls=expected_tool_calls or last_case.expected_tool_calls,
            rubric=rubric or last_case.rubric,
            critics=critics or last_case.critics.copy(),
            additional_messages=new_additional_messages,
        )

        self.cases.append(new_case)

    def run(self, model: str, arcade_client: Arcade) -> dict[str, Any]:
        results = {"model": model, "cases": []}

        for case in self.cases:
            print(f"Running case: {case.name}")
            messages = [{"role": "system", "content": self.system}]
            messages.extend(list(case.additional_messages))
            messages.append({"role": "user", "content": case.user_message})

            response = arcade_client.chat.completions.create(  # type: ignore[call-overload]
                model=model,
                messages=messages,
                tool_choice=self.tool_choice,
                tools=list(self.catalog.tools.keys()),
            )

            predicted_args = get_tool_args(response)

            evaluation = case.evaluate(predicted_args)

            result = {
                "name": case.name,
                "input": case.user_message,
                "expected_tool_calls": [
                    {"name": tc.name, "args": tc.args} for tc in case.expected_tool_calls
                ],
                "predicted_tool_calls": [
                    {"name": tool, "args": args} for tool, args in predicted_args
                ],
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
                print(f"\nRunning evaluation suite for model: {model}\n")
                results.append(suite.run(model, client))
            return results

        wrapper.__tool_eval__ = True
        return wrapper

    return decorator
