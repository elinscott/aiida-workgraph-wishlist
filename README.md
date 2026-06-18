# aiida-workgraph-wishlist

Minimal, **executable** MWEs of `aiida-workgraph` behaviours — both the ones
that already work (regression guards) and the ones we *wish* worked (tracked as
`xfail`). Built to bring concrete, runnable pain points to the aiida-workgraph
dev week.

Pinned versions these observations were made against:

| package | version |
|---|---|
| aiida-workgraph | 0.8.1 |
| node-graph | 0.6.5 |

## The mechanism, in one table

Where a value comes from determines what you can do with it. Everything below is
asserted by the tests (aiida-workgraph 0.8.1):

| Context | Your variable is | `x["k"]` | `==` / branch | `is None` | `is <enum>` | `x * 2`, `x // 2` |
|---|---|---|---|---|---|---|
| **Deferred `@task.graph` body** (runs at runtime via `materialize_graph`) | `TaggedValue` (concrete value + provenance tag) | works | works | works | **silently False** | works |
| **Raw future socket** (`task.outputs`, `z.item.value` in a zone body) | `TaskSocket` (a *future*) | **raises** `GraphDeferredIllegalOperationError` | — | — | — | works (builds an operator task) |

Two findings worth stressing, because they contradict common "always wrap it in
a `@task`" folklore:

1. **Inside a deferred `@task.graph` body almost everything just works** —
   subscript, `==` (incl. against an Enum), structural `if`/branching, and even
   `is None`. The values are real.
2. **Arithmetic on a raw future works** — `socket * 2` builds a deferred
   `op_mul` task. So `socket // 2` is fine.

The genuine gaps (the `xfail`s) are narrow:

- **`is <non-None object>` is silently wrong.** A non-None graph input is a
  `wrapt.ObjectProxy`; Python's `is` compares the *proxy's* identity, which
  wrapt cannot intercept, so `value is Enum.MEMBER` is silently `False` even
  though `==` is `True`. (`is None` escapes this — None arrives unwrapped.) No
  runtime detection is possible, hence "wish it errored or matched."
- **Subscripting a raw future raises**, so indexing a `Map` item inline
  (`z.item.value["k"]`) needs a wrapper `@task` — even though arithmetic on the
  same future is allowed. That asymmetry is the ergonomic wish.

## How this repo tracks progress

- A test that **passes** documents behaviour that *currently works* — a
  regression guard.
- A test marked `@pytest.mark.xfail(strict=True, reason=...)` documents a
  behaviour we **wish** worked. It `xfail`s today. The day aiida-workgraph
  grants the wish, the test starts passing -> `strict=True` turns that into a
  loud `XPASS` **failure**, prompting us to promote it to a normal test. So
  `pytest` going green-except-for-XPASS is exactly the signal "a wish came
  true."

```
pytest -q          # xfailed = still-open wishes; xpassed = wish granted (flip it!)
pytest -rX         # list which wishes are still open
```

## Running

Any environment with `aiida-workgraph` + a working AiiDA profile. The suite uses
AiiDA's `aiida_profile` pytest fixture (a throwaway profile); `WorkGraph.run()`
executes in-process, no daemon needed.

```
pip install -e .          # or: use an env that already has aiida-workgraph
pytest
```

## Layout

- `tests/test_graph_body_values.py` — what a *deferred* `@task.graph` body sees
  (subscript / `==` / branch work; `is` does not).
- `tests/test_zone_ergonomics.py` — *eager* zone-body ergonomics we wish we had
  (inline subscript / arithmetic on a socket without a wrapper `@task`).

Each test's docstring states: **what** it does, the **ideal**, and the
**current** behaviour.
