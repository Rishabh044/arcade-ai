from arcade.sdk.eval import EvalRubric, tool_eval, BinaryCritic

rubric = EvalRubric(
    name="Hello Eval",
    grader="gpt-4",
    fail=0.8,
    warn=0.9,
    critics=[
        BinaryCritic(
            criteria="Does the tool output the expected greeting?",
            weight=1.0,
        )
    ],
    fail_on_parse_error=True,
    fail_on_tool_choice=True,
    fail_on_tool_error=False,
    fail_on_tool_timeout=True,
    retries=2,
)


@tool_eval(models=["gpt-3.5-turbo"], rubric=rubric, tool="Hello")
def eval_hello(evaluator):
    evaluator.set_context(messages=[{"system": "You are a chatbot that greets users."}])
    evaluator.score(
        {
            "input": "Hello",
            "expected_tool": "greet",
            "expected_tool_args": {"greeting": "Hello"},
            "output": "Hello",
        }
    )
