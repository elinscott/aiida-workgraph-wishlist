"""``While`` zone ergonomics -- the heaviest tax we pay.

A "do this, then loop until the result converges" algorithm (kcp.x alpha
refinement in aiida-koopmans2 `ComputeScreeningParameters`) has to be written
with a startling amount of ceremony, all of which the framework should hide:

1. **The first iteration is fully duplicated** *before* the loop, because the
   ``While`` condition reads a value the loop body produces, and there is no
   do-while / repeat-until -- the condition is checked *before* the body, so it
   needs a seeded value to look at.
2. **Loop-carried state is plumbed by hand through ``wg.ctx``** -- and because
   ``ctx`` stores per-socket, a namespace result (``filled`` + ``empty``) must
   be split into separate ``ctx`` slots and reassembled inside the loop.
3. **A manual ``<<`` wait edge** is needed (``cond << first.result``) because
   ``ctx`` assignments do not create dataflow edges, so the condition would
   otherwise be evaluated before the first iteration has produced a value.
4. A **special-case to skip the whole loop** when only one iteration is wanted.

The test below runs the minimal version of exactly that pattern (a counter that
increments until it reaches 3). It PASSES -- the ceremony works -- but every line
marked ``# tax:`` is overhead we wish we did not have to write. The wish: a
``repeat ... until`` that runs the body, threads its output as state
automatically, and checks the condition *after* each pass -- no unrolled first
iteration, no ``wg.ctx``, no manual wait edge.

(The "natural" formulation -- ``with While(x < 3): x = inc(x=x)`` -- is NOT run
here: without ``ctx`` the condition never updates and the loop ignores
``max_iterations`` and hangs, which is itself a wart.)

The docs steer to **recursion** instead (``test_..._via_recursion`` below). That
is provenance-correct -- each iteration is a process whose loop variable is a
real immutable input node, so the condition reads a resolved value and the value
flows iteration-to-iteration as data links, native to a dataflow DAG. But it is
not free: it is harder to conceptualise (most people think in loops), it has a
``max_depth`` ceiling (default 100), and each layer is a nested process. The wish
is therefore NOT "use recursion" -- it is that the ``While`` zone (a shipped,
public construct the docs barely use) be **lowered to that recursive dataflow
form internally**, so users write the intuitive loop and still get correct
provenance: no ``ctx``, no ``<<``, no unrolled first iteration, do-while support.
"""

from __future__ import annotations

from aiida_workgraph import While, get_current_graph, task


# mwe: while-zone
@task
def inc(x: int) -> int:
    return x + 1


def test_do_while_today_needs_unroll_ctx_and_wait_edges(aiida_profile):
    @task.graph
    def top():
        first = inc(x=0)  # tax: first iteration unrolled before the loop
        wg = get_current_graph()
        wg.ctx.x = first.result  # tax: loop state hand-plumbed through ctx
        cond = wg.ctx.x < 3
        cond << first.result  # tax: manual wait edge (ctx writes are not dataflow)
        with While(cond, max_iterations=5):
            nxt = inc(x=wg.ctx.x)
            wg.ctx.x = nxt.result  # tax: re-store state every pass
        return wg.ctx.x

    graph = top.build()
    graph.run()
    assert graph.outputs.result.value == 3


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
