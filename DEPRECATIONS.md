# Deprecations

Tracks deprecated sources and configuration and their target removal version, so
compatibility shims do not silently accumulate. See the policy in
[`doc/versioning.md`](doc/versioning.md).

Rules in brief: a deprecation ships in a minor release and is kept for at least
two minor releases; removal is batched into the next major release and never
happens in the same release as the deprecation.

| Item | Kind | Deprecated in | Replacement | Target removal | Ref |
|---|---|---|---|---|---|
| `newcastle_gov_uk` | source | 2.30.0 | shared ReCollect ICS source (area `NewcastleUponTyneUK`) | next major | [#6753](https://github.com/mampfes/hacs_waste_collection_schedule/pull/6753) |

When you deprecate something, add a row here, log a one-time runtime warning in
the source, add a `Deprecated` entry to `CHANGELOG.md`, and point the source's
doc at the replacement.
