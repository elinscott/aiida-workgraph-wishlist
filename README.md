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
```
See the test contents for concrete examples and explanations.

One common theme is that the `TaggedValue`/socket proxy leaks into user Python with surprising, usually **silent** edges (`is`, `None`, scalar-as-node). The loud `GraphDeferredIllegalOperationError` on eager subscript is the model to extend.