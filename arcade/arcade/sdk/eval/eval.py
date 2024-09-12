import functools
import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable

import numpy as np
from openai.resources.chat.completions import ChatCompletion
from scipy.optimize import linear_sum_assignment

from arcade.client import Arcade
from arcade.core.config import config
from arcade.sdk.error import WeightError

if TYPE_CHECKING:
    from arcade.core.catalog import ToolCatalog
    from arcade.sdk.eval.critic import Critic


@dataclass
class ExpectedToolCall:
    """
    Represents an expected tool call with its name and arguments.

    Attributes:
        name: The name of the tool.
        args: A dictionary containing the expected arguments for the tool.
    """

    name: str
    args: dict[str, Any]


@dataclass
class EvalRubric:
    """
    Defines the pass/fail criteria and tool selection behavior for an evaluation case.

    Args:
        fail_threshold: The threshold for failing the evaluation (0.0-1.0).
        warn_threshold: The threshold for issuing a warning (0.0-1.0).
        fail_on_tool_selection: Whether to fail the evaluation if the tool selection is incorrect.
        tool_selection_weight: The weight of the tool selection score (0.0-1.0).
        missing_tool_calls_weight: The weight for penalizing missing tool calls (0.0-1.0).
        extra_tool_calls_weight: The weight for penalizing extra tool calls (0.0-1.0).

    Examples:
        # Strict rubric with high thresholds and strict tool selection
        rubric = EvalRubric(
            fail_threshold=0.9,
            warn_threshold=0.95,
            fail_on_tool_selection=True,
            tool_selection_weight=1.0,
            missing_tool_calls_weight=0.0,
            extra_tool_calls_weight=0.0,
        )

        # Lenient rubric with lower thresholds and lenient tool selection
        rubric = EvalRubric(
            fail_threshold=0.7,
            warn_threshold=0.8,
            fail_on_tool_selection=False,
            tool_selection_weight=0.3,
            missing_tool_calls_weight=0.35,
            extra_tool_calls_weight=0.35,
        )
    """

    fail_threshold: float = 0.8
    warn_threshold: float = 0.9
    fail_on_tool_selection: bool = True
    tool_selection_weight: float = 1.0
    missing_tool_calls_weight: float = 0.0
    extra_tool_calls_weight: float = 0.0

    def __post_init__(self):
        """Validate the rubric weights."""
        self._validate_weights()

    def _validate_weights(self):
        """Validate the rubric weights."""
        total_weight = (
            self.tool_selection_weight
            + self.missing_tool_calls_weight
            + self.extra_tool_calls_weight
        )
        if total_weight > 1.0:
            raise WeightError(f"Sum of rubric weights must not exceed 1.0, got {total_weight}")

        for weight in (
            self.tool_selection_weight,
            self.missing_tool_calls_weight,
            self.extra_tool_calls_weight,
        ):
            if weight < 0.0 or weight > 1.0:
                raise WeightError(f"Rubric weights must be between 0.0 and 1.0, got {weight}")

    def get_tool_selection_score(self, expected: str, actual: str) -> float:
        """
        Calculate the tool selection score based on the rubric's tool_selection_weight.

        Args:
            expected: The expected tool name.
            actual: The actual tool name.

        Returns:
            The tool selection score (0.0 if the tool names don't match, tool_selection_weight if they match).
        """
        return self.tool_selection_weight if expected == actual else 0.0

    def get_missing_tool_calls_score(self, expected_count: int, actual_count: int) -> float:
        """
        Calculate the score for missing tool calls based on the rubric's missing_tool_calls_weight.

        Args:
            expected_count: The expected number of tool calls.
            actual_count: The actual number of tool calls.

        Returns:
            The missing tool calls score (0.0 if there are missing calls, missing_tool_calls_weight if not).
        """
        missing_calls = max(expected_count - actual_count, 0)
        return self.missing_tool_calls_weight if missing_calls == 0 else 0.0

    def get_extra_tool_calls_score(self, expected_count: int, actual_count: int) -> float:
        """
        Calculate the score for extra tool calls based on the rubric's extra_tool_calls_weight.

        Args:
            expected_count: The expected number of tool calls.
            actual_count: The actual number of tool calls.

        Returns:
            The extra tool calls score (0.0 if there are extra calls, extra_tool_calls_weight if not).
        """
        extra_calls = max(actual_count - expected_count, 0)
        return self.extra_tool_calls_weight if extra_calls == 0 else 0.0


@dataclass
class EvaluationResult:
    """
    Represents the result of an evaluation case.

    Attributes:
        score: The normalized evaluation score (0.0-1.0).
        passed: Whether the evaluation passed based on the fail_threshold.
        warning: Whether the evaluation issued a warning based on the warn_threshold.
        results: A list of dictionaries containing the results for each critic.

    """

    score: float = 0.0
    passed: bool = False
    warning: bool = False
    results: list[dict[str, Any]] = field(default_factory=list)

    @property
    def fail(self) -> bool:
        return not self.passed and not self.warning

    def add(
        self,
        field: str,
        result: dict[str, Any],
        weight: float,
        expected: Any,
        actual: Any,
    ) -> None:
        """
        Add a critic result to the list of critic results.

        Args:
            field: The field name for the critic result.
            result: A dictionary containing the critic result.
            weight: The weight of the critic.
            expected: The expected value for the critic.
            actual: The actual value for the critic.
        """
        self.results.append({
            "field": field,
            **result,
            "weight": weight,
            "expected": expected,
            "actual": actual,
        })


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
        rubric: An EvalRubric object defining pass/fail criteria and tool selection behavior.
        critics: A list of Critic objects used to evaluate tool arguments.
        additional_messages: Optional list of additional context messages.

    Methods:
        _validate_critics: Validate the sum of critic weights.
        evaluate: Evaluate the actual tool calls against the expected tool calls and critics.
    """

    name: str
    user_message: str
    expected_tool_calls: list[ExpectedToolCall]
    rubric: EvalRubric
    critics: list["Critic"]
    additional_messages: list[dict[str, str]] = field(default_factory=list)

    def __post_init__(self):
        self._validate_critics()

    def _validate_critics(self):
        """
        Validate the sum of critic weights.

        Raises:
            WeightError: If the sum of critic weights exceeds 1.0.
        """
        total_weight = sum(critic.weight for critic in self.critics)
        if total_weight > 1.0:
            raise WeightError(f"Sum of critic weights must not exceed 1.0, got {total_weight}")

        for critic in self.critics:
            if critic.weight < 0.1:
                raise WeightError(f"Critic weights should be at least 0.1, got {critic.weight}")

    def evaluate(
        self,
        actual_tool_calls: list[tuple[str, dict[str, Any]]],
    ) -> EvaluationResult:
        """
        Evaluate the actual tool calls against the expected tool calls and critics.

        This method uses the Linear Sum Assignment (LSA) algorithm, also known as the Hungarian algorithm,
        to find the optimal assignment between the expected and actual tool calls. The algorithm minimizes
        the cost of assigning each expected tool call to an actual tool call, based on a cost matrix.

        The cost matrix is created by comparing the expected tool name and arguments with the actual tool
        name and arguments. The cost is calculated as 1 - similarity, where similarity is determined by
        the ToolSelectionCritic for tool names and other critics for tool arguments.

        After finding the optimal assignment, the method calculates the total score by summing the scores
        from the assigned critics. It also penalizes for missing or extra tool calls by adding a weight
        for each missing or extra call.

        Finally, the method normalizes the total score by dividing it by the total weight and creates an
        EvaluationResult object with the normalized score, pass/fail status, warning status, and detailed
        critic results.

        Args:
            actual_tool_calls: A list of tuples containing the actual tool name and arguments.

        Returns:
            An EvaluationResult object containing the evaluation results.
        """
        # Create a cost matrix for the assignment problem
        cost_matrix = self._create_cost_matrix(actual_tool_calls)

        # Use the Linear Sum Assignment (LSA) algorithm to find the optimal assignment
        # The algorithm minimizes the cost of assigning each expected tool call to an actual tool call
        row_ind, col_ind = linear_sum_assignment(cost_matrix, maximize=True)

        total_score = 0.0
        total_weight = 0.0
        evaluation_result = EvaluationResult()

        for i, j in zip(row_ind, col_ind):
            if i < len(self.expected_tool_calls) and j < len(actual_tool_calls):
                expected = self.expected_tool_calls[i]
                actual_tool, actual_args = actual_tool_calls[j]

                # Evaluate tool selection
                tool_selection_score = self.rubric.get_tool_selection_score(
                    expected.name, actual_tool
                )
                total_score += tool_selection_score
                total_weight += self.rubric.tool_selection_weight
                evaluation_result.add(
                    "tool_selection",
                    {"match": expected.name == actual_tool, "score": tool_selection_score},
                    self.rubric.tool_selection_weight,
                    expected.name,
                    actual_tool,
                )

                # If tool selection is incorrect and fail_on_tool_selection_error is True, skip argument evaluation
                if not tool_selection_score and self.rubric.fail_on_tool_selection:
                    continue

                # Evaluate arguments using critics
                for critic in self.critics:
                    expected_value = expected.args.get(critic.critic_field)
                    actual_value = actual_args.get(critic.critic_field)
                    if expected_value is not None and actual_value is not None:
                        result = critic.evaluate(expected_value, actual_value)
                        total_score += result["score"]
                        total_weight += critic.weight
                        evaluation_result.add(
                            critic.critic_field, result, critic.weight, expected_value, actual_value
                        )

        # Penalize for missing or extra tool calls
        expected_count = len(self.expected_tool_calls)
        actual_count = len(actual_tool_calls)

        # Calculate the score for missing tool calls
        missing_tool_calls_score = self.rubric.get_missing_tool_calls_score(
            expected_count, actual_count
        )
        total_score += missing_tool_calls_score
        total_weight += self.rubric.missing_tool_calls_weight
        evaluation_result.add(
            "missing_tool_calls",
            {"match": missing_tool_calls_score > 0, "score": missing_tool_calls_score},
            self.rubric.missing_tool_calls_weight,
            expected_count,
            actual_count,
        )

        # Calculate the score for extra tool calls
        extra_tool_calls_score = self.rubric.get_extra_tool_calls_score(
            expected_count, actual_count
        )
        total_score += extra_tool_calls_score
        total_weight += self.rubric.extra_tool_calls_weight
        evaluation_result.add(
            "extra_tool_calls",
            {"match": extra_tool_calls_score > 0, "score": extra_tool_calls_score},
            self.rubric.extra_tool_calls_weight,
            expected_count,
            actual_count,
        )

        # Normalize the total score by dividing it by the total weight
        normalized_score = total_score / total_weight if total_weight > 0 else 0.0
        evaluation_result.score = normalized_score

        # Set the pass/fail status based on the fail_threshold
        evaluation_result.passed = normalized_score >= self.rubric.fail_threshold

        # Set the warning status based on the warn_threshold
        evaluation_result.warning = (
            not evaluation_result.passed and normalized_score >= self.rubric.warn_threshold
        )

        return evaluation_result

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
                score = self.rubric.get_tool_selection_score(expected.name, actual_tool)
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
