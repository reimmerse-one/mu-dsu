"""State machine step-execution runner.

Two-phase execution:
1. Load phase: interpreter parses the program, semantic actions populate
   state/event/transition tables in the environment.
2. Step phase: runner evaluates events, takes transitions, executes
   state initialization actions by re-visiting stored AST nodes.
"""

from __future__ import annotations

from typing import Any

from mu_dsu.core.interpreter import Interpreter


class StateMachineRunner:
    """Step-driven state machine executor."""

    def __init__(self, interpreter: Interpreter) -> None:
        self._interp = interpreter
        self._current_state: str | None = None

    def load(self, source: str) -> dict[str, Any]:
        """Parse and execute the declaration phase. Returns SM tables."""
        result = self._interp.run(source)
        # Enter the first declared state
        states = self._interp.env.get("__sm_states__")
        if states:
            first_state = next(iter(states))
            self._enter_state(first_state)
        return result

    @property
    def current_state(self) -> str | None:
        return self._current_state

    @property
    def states(self) -> dict:
        return self._interp.env.get("__sm_states__")

    @property
    def events(self) -> dict:
        return self._interp.env.get("__sm_events__")

    @property
    def transitions(self) -> dict:
        return self._interp.env.get("__sm_transitions__")

    def inject_event(self, name: str, value: Any) -> None:
        """Set an external event's value for the next step.

        For func_call events (e.g., get.click), register a callable.
        For bool_expr events, set the underlying variable.
        """
        if callable(value):
            self._interp.env.set_global(name, value)
        else:
            self._interp.env.set(name, value)

    def step(self) -> str | None:
        """Evaluate events for current state, take first matching transition.

        Returns the new state name if a transition fired, None otherwise.
        """
        if self._current_state is None:
            return None

        transitions = self._interp.env.get("__sm_transitions__")
        state_transitions = transitions.get(self._current_state, [])

        for event_name, target_state in state_transitions:
            if self._evaluate_event(event_name):
                self._enter_state(target_state)
                return target_state

        return None

    def run_steps(self, max_steps: int = 100) -> list[str]:
        """Run steps until no transition fires or max reached.

        Returns list of states entered (not including the initial state).
        """
        visited: list[str] = []
        for _ in range(max_steps):
            result = self.step()
            if result is None:
                break
            visited.append(result)
        return visited

    def _enter_state(self, state_name: str) -> None:
        """Enter a state: execute its initialization actions.

        Adapted language semantics may register extra entry behaviour in
        __sm_on_enter__ (e.g., the seamless stand-by slice makes turn-on
        also store the inactivity timestamp — Sect. 3.2 of the paper).
        """
        self._current_state = state_name
        env = self._interp.env
        states = env.get("__sm_states__")
        action_node = states.get(state_name)
        if action_node is not None:
            self._interp._visit(action_node)
        if env.has("__sm_on_enter__"):
            hook = env.get("__sm_on_enter__").get(state_name)
            if hook is not None:
                hook(env)

    def _evaluate_event(self, event_name: str) -> bool:
        """Evaluate an event condition.

        Events declared in the program are stored as AST nodes and
        re-visited; internal events introduced by adapted semantics
        (Fig. 2(c) dashed transitions) are stored as callables.
        """
        events = self._interp.env.get("__sm_events__")
        condition = events.get(event_name)
        if condition is None:
            return False
        if callable(condition):
            return bool(condition(self._interp.env))
        return bool(self._interp._visit(condition))
