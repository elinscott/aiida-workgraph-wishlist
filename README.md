# aiida-workgraph-wishlist

Runnable MWEs of `aiida-workgraph` behaviours we rely on, work around, or wish
we had. Built to bring concrete pain points to the dev week.

## How it tracks progress

- **Passing test** = behaviour that works today (a guard, often documenting a
  gotcha + its workaround in the assertion).
- **`xfail` test** = a wish. `xfail_strict` is on, so the day it's granted the
  test XPASSes → the suite fails loudly → promote it to a guard.

```
pytest          # green except XPASS
pytest -rX      # list the still-open wishes
uv run --group docs sphinx-build -W -b html docs docs/_build/html   # build the meeting page
```
See the test contents for concrete examples and explanations. The meeting notes, with every example included from its test, are in `docs/index.rst`.

One common theme is that the `TaggedValue`/socket proxy leaks into user Python with surprising, usually **silent** edges (`is`, `None`, scalar-as-node). The loud `GraphDeferredIllegalOperationError` on eager subscript is the model to extend.

A second theme, which the 2026-09 examples sharpen: the *same* body behaves differently depending on whether a caller invoked its graph at top level or as a node inside another graph — a choice the body's author does not make. An `Enum`, a `dict`, and a returned input each cross that line with a different answer.

## The examples

Each module opens with a docstring stating the mechanism and which of its cases are guards and which are wishes. Counts are against aiida-workgraph 0.9.0 (upstream main @ 502c1b5b) with node-graph 0.6.5, aiida-pythonjob 0.5.2 and aiida-core 2.7.3.

| module | theme | guards | wishes |
|---|---|---|---|
| `test_enum_coercion.py` | an `Enum` member never arrives as itself — unserializable bare, a node proxy in a graph body, a bare `str` in a task body; and the socket's Enum type is never a membership rule | 3 | 5 |
| `test_plain_python_in_bodies.py` | a body does not get the types its signature declares: `orm.Int` for an `int` field, `orm.Dict` or `dict` for a `dict` depending on the call site, a vanished `None` field, a defaulted field reported missing, a file node only a calcfunction can hold | 2 | 5 |
| `test_graph_echoes_input.py` | returning a graph input as a graph output is refused eagerly and accepted deferred | 3 | 1 |
| `test_two_serialization_paths.py` | `to_dict()` hands back live objects, so a `from_dict(to_dict())` guard can be green on a graph that dies at run; plus the undocumented recipe for driving the daemon's own checkpoint path | 3 | 1 |
| `test_graph_body_values.py` | what a deferred body sees: subscript, `==` and `is None` work, `is <enum>` is silently False | 4 | 1 |
| `test_node_and_serialization.py` | node-vs-value surprises at task boundaries | 5 | — |
| `test_none_handling.py` | `None` as a task argument is dropped; `None` inside an opaque dict survives | 1 | 1 |
| `test_dynamic_namespace_typing.py` | a `TypedDict` return is not at parity with an explicit namespace, and a gathered namespace cannot be re-scattered | 1 | 2 |
| `test_zone_ergonomics.py` | arithmetic on a future builds an operator task while subscript refuses; the `Map` entry is now `z.value` | 4 | 1 |
| `test_while_zone.py` | the do-while tax: unrolled first iteration, `ctx` plumbing, manual wait edges | 2 | — |
| `test_future_annotations.py` | PEP 563 and dynamic namespaces — granted by #788 | 1 | — |
| `test_link_labels.py` | a leading-underscore task name — granted by #787 | 1 | — |

`proposed-issues/NN-<repo>-<slug>.md` holds a paste-ready draft per wish that is not yet filed upstream, each with `## Description`, `## MWE` and `## Wish`, and each claim graded reproduced or not.