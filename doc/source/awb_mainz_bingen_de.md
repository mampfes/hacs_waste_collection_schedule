# Abfallwirtschaftsbetrieb LK Mainz-Bingen (deprecated)

```yaml
waste_collection_schedule:
  sources:
    - name: awb_mainz_bingen_de
      args:
        bezirk: "Stadt Ingelheim"
        ort: "Ingelheim Süd"
```

This compatibility source remains **deprecated**. Prefer `kaw_mainz_bingen_de` for new configurations.

The source now directly composes the current KAW pipeline components. `bezirk` and `ort` keep their existing meaning and matching rules. Saved legacy `strasse` values remain accepted; the current API does not use them, so there is no unused street field in the config form. Existing dates, metadata and canonical waste types are preserved. The deprecation warning is logged once.
