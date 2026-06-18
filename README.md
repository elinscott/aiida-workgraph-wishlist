# aiida-workgraph-wishlist

Runnable MWEs of `aiida-workgraph` behaviours we rely on, work around, or wish
we had — distilled from the contortions in `aiida-koopmans2`. Built to bring
concrete pain points to the dev week.

Observed against **aiida-workgraph 0.8.1 / node-graph 0.6.5**.

## How it tracks progress

- **Passing test** = behaviour that works today (a guard, often documenting a
  gotcha + its workaround in the assertion).
- **`xfail` test** = a wish. `xfail_strict` is on, so the day it's granted the
  test XPASSes → the suite fails loudly → promote it to a guard.

```
pytest          # green except XPASS
pytest -rX      # list the still-open wishes
```

## The wishes (`xfail`)

| Wish | Today |
|---|---|
| `value is <enum>` in a graph body | silently `False` (wrapt proxy identity); `==` works, `is None` works |
| `None` as a task input arg | silently dropped → "missing arg" / default |
| index a `Map` item inline (`z.item.value["k"]`) | raises; needs a wrapper `@task` (yet `socket * 2` is fine) |
| bad link-label name (`_foo`, `dft_n-1`) | task **silently skipped**, workgraph "succeeds" — should fail at build |

## Gotchas that already work (guards)

| In a *deferred* `@task.graph` body | Outside (raw futures / nodes) |
|---|---|
| subscript, `==`, branching, `is None`, arithmetic — all see real values | `socket * 2` / `// 2` build operator tasks |
| `None` inside an opaque dict survives | subscripting a raw future raises (loud, good) |
| | `str(node)` is a repr → use `.value` |
| | a scalar input is a proxy/node → use `.value` |
| | a `@task` body gets the *deserialized* payload (ase.Atoms), not the node |
| | plain Enum → `EnumData` (want `orm.Str`? pass `.value`) |
| | emit an existing node only from a `@task.workfunction`, not a `@task` |

## The one-line theme for the devs

The `TaggedValue`/socket proxy leaks into user Python with surprising, usually
**silent** edges (`is`, `None`, scalar-as-node). The loud
`GraphDeferredIllegalOperationError` on eager subscript is the model to extend.

## Running

Any env with `aiida-workgraph`; the suite uses AiiDA's `aiida_profile` fixture
and runs each graph in-process (no daemon). Layout:

- `test_graph_body_values.py` — what a deferred `@task.graph` body sees
- `test_zone_ergonomics.py` — raw future sockets (arithmetic vs subscript)
- `test_none_handling.py` — where `None` survives or vanishes
- `test_node_and_serialization.py` — node↔value boundary surprises
- `test_link_labels.py` — silent link-label rejection
