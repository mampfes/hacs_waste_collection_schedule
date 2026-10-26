# Wieliczka Kiedy Odpady (deprecated)

```yaml
waste_collection_schedule:
  sources:
    - name: wieliczka_kiedyodpady_pl
      args:
        city: "Wieliczka (miasto)"
        street: "ul. Adama Asnyka"
        number: "pozostałe"
```

This source remains **deprecated**. Prefer `kiedyodpady_pl` with `municipality: wieliczka` for new configurations.

The source uses the shared Kiedy Odpady address lookup and schedule parser. `city`, optional `street` and optional `number` remain unchanged. An optional `lookahead_days` defaults to **35**, preserving the legacy window. Copy address values from the [public Wieliczka selector](https://wieliczka.kiedyodpady.pl).

Waste names now use the canonical platform vocabulary. Combined metals/plastics collections produce both canonical categories on the same date. Update filters and customisations that use the former labels. The provider is fixed internally to Wieliczka, without an unused municipality field in the form.
