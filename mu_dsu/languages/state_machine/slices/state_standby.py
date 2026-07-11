"""Stand-by variant of the state slice — seamless adaptation (Sect. 3.2).

Paper: "the turn-on operation will not only turn on the appliance but
also store the timestamp of when it is turned on" and two internal
events — activity and time_elapsed — appear as "a sort of a side effect
of the changes to the language semantics" (Fig. 2(c), dashed edges).

Replacing sm.state with this slice (same syntax, new semantics) and
re-running the UNCHANGED default program (Listing 2(a)) yields the
merged-nodes behaviour of Fig. 2(c):

  on --activity-->  on   (re-entering on resets the stored time)
  on --elapsed-->   off  (inactivity for more than 10 steps)

The internal events are callables in __sm_events__, the extra
transitions are appended to __sm_transitions__["on"], and the timer
reset is an on-enter hook — all installed by an 'after' action on the
program root, so the wiring survives every redo.
"""

from mu_dsu.core.slice import LanguageSlice, SemanticAction, SyntaxDefinition

# Paper Sect. 3.2: "if it is not in motion for 10 seconds, it is
# considered not in use"; Listing 2(b): elapsed = t > 10
INACTIVITY_LIMIT = 10

_INTERNAL_TRANSITIONS = [("__activity__", "on"), ("__elapsed__", "off")]


def state_standby_slice() -> LanguageSlice:
    """Replacement state slice: turn-on also tracks inactivity time."""
    return LanguageSlice(
        name="sm.state",
        syntax=SyntaxDefinition(
            rules='state_def: IDENT "=" action_list',
        ),
        dependencies=["sm.action"],
        actions=[
            SemanticAction(
                node_type="state_def", role="execution", phase="replace",
                handler=_exec_state_def_standby,
                id="sm.state_def.exec",
            ),
            SemanticAction(
                node_type="start", role="execution", phase="after",
                handler=_wire_standby_semantics,
                id="sm.state_def.standby_wiring",
            ),
        ],
    )


def _exec_state_def_standby(node, ctx, visit):
    """Register a state — same as the default slice."""
    name = str(node.children[0])
    states = ctx.env.get("__sm_states__")
    states[name] = node.children[1]
    return name


def _wire_standby_semantics(node, ctx, visit, result):
    """Install the Fig. 2(c) side effects after the program (re-)runs."""
    env = ctx.env
    env.set("__sm_standby_enabled__", True)
    env.set("__sm_t__", 0)

    events = env.get("__sm_events__")
    events["__activity__"] = _activity_event
    events["__elapsed__"] = _elapsed_event

    transitions = env.get("__sm_transitions__")
    on_transitions = transitions.setdefault("on", [])
    for rule in _INTERNAL_TRANSITIONS:
        if rule not in on_transitions:
            on_transitions.append(rule)

    hooks = env.get("__sm_on_enter__") if env.has("__sm_on_enter__") else {}
    hooks["on"] = _store_timestamp
    env.set("__sm_on_enter__", hooks)
    return result


def _store_timestamp(env):
    """Turn-on now also stores 'the timestamp of when it is turned on'."""
    env.set("__sm_t__", 0)


def _is_active(env):
    probe = env.get("get.activity") if env.has("get.activity") else None
    return bool(probe()) if callable(probe) else False


def _activity_event(env):
    """Internal activity event: re-enter on (which resets the stored time)."""
    return _is_active(env)


def _elapsed_event(env):
    """Internal time_elapsed event: fires after prolonged inactivity.

    Each evaluation while inactive advances the stored time by one step;
    the appliance turns off once it exceeds INACTIVITY_LIMIT.
    """
    if _is_active(env):
        return False
    t = env.get("__sm_t__") + 1
    env.set("__sm_t__", t)
    return t > INACTIVITY_LIMIT
