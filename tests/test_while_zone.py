"""``While`` zone ergonomics.

A "do this, then loop until the result converges" algorithm (kcp.x alpha
refinement in aiida-koopmans2 `ComputeScreeningParameters`) is written today with
ceremony the framework should hide. Empirically (aiida-workgraph 0.9.0, upstream
main @ 502c1b5b; node-graph 0.6.5):

* the natural spelling -- rebind the loop variable inside ``with While(...)`` --
  builds, runs to ``max_iterations`` on a frozen value, and returns the wrong
  answer with exit status 0. No error, no warning;
* the loop works only with its state hand-plumbed through ``wg.ctx``, re-stored
  on every pass -> PASS (the guard, every ``# tax:`` line is overhead).

The unrolled first iteration and the manual ``cond << first.result`` wait edge
that aiida-koopmans2 also writes are NOT needed on this version: a literal seed in
``ctx`` and no wait edge give the same result and the same number of ``inc``
runs, starting below or above the target.

The docs steer to **recursion** instead (``test_..._via_recursion`` below). That
is provenance-correct -- each iteration is a process whose loop variable is a
real immutable input node, so the condition reads a resolved value and the value
flows iteration-to-iteration as data links, native to a dataflow DAG. But it is
not free: it is harder to conceptualise (most people think in loops), it has a
``max_depth`` ceiling (default 100), and each layer is a nested process. The wish
is therefore NOT "use recursion" -- it is that the ``While`` zone (a shipped,
public construct the docs barely use) be **lowered to that recursive dataflow
form internally**, so users write the intuitive loop and still get correct
provenance, with no ``ctx`` and the condition checked after the body.
"""

from __future__ import annotations

from aiida_workgraph import While, get_current_graph, task


# mwe: while-zone
@task
def inc(x: int) -> int:
    return x + 1


def test_while_loop_state_needs_ctx(aiida_profile):
    @task.graph
    def natural():
        x = inc(x=0).result
        with While(x < 3, max_iterations=5):
            x = inc(x=x).result  # rebinds a Python name; the loop never sees it
        return x

    @task.graph
    def with_ctx():
        wg = get_current_graph()
        wg.ctx.x = 0  # tax: loop state hand-plumbed through ctx
        with While(wg.ctx.x < 3, max_iterations=5):
            wg.ctx.x = inc(x=wg.ctx.x).result  # tax: re-store state every pass
        return wg.ctx.x

    wrong = natural.build()
    wrong.run()
    assert wrong.outputs.result.value == 2  # silently wrong: should be 3
    assert wrong.process.exit_status == 0  # and reported as a success
    right = with_ctx.build()
    right.run()
    assert right.outputs.result.value == 3


# Module level: the body runs again at run time and finds `Loop` as a global.
@task.graph
def Loop(x, target):
    if x >= target:  # condition on an INPUT -> concrete value in the body
        return x
    return Loop(x=inc(x=x).result, target=target)


def test_same_loop_via_recursion_is_clean_but_has_costs(aiida_profile):
    graph = Loop.build(x=0, target=3)
    graph.run()
    assert graph.outputs.result.value == 3


# end mwe: while-zone
