# Heinz-Entsorgung (Landkreis Freising) - ICS (Deprecated)

> ⚠️ **DEPRECATED**: The ICS-based method is no longer available. The website has been completely redesigned and now uses a Blazor WebAssembly application with encrypted API parameters.

## Migration to new source

Please use the new [Heinz-Entsorgung](/doc/source/heinz_entsorgung_de.md) source instead.

The new method requires extracting an encrypted `param` value from the website using browser Developer Tools. See the [source documentation](/doc/source/heinz_entsorgung_de.md) for detailed instructions.

## Why the change?

The old website (`https://heinz-entsorgung.de/abfallkalender/`) with direct ICS downloads has been replaced by a new Blazor-based application (`https://abfallkalender.heinz-entsorgung.de/`) that uses:
- Client-side calendar rendering
- Encrypted API parameters
- No direct ICS file downloads

## Old Configuration (No longer working)

The following configuration format is **no longer supported**:

```yaml
# OLD FORMAT - DO NOT USE
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://heinz-entsorgung.de/abfallkalender/query.php?ORT=...&STRASSE=...&FRAKTIONEN=...
```

Please update to the new [heinz_entsorgung_de](/doc/source/heinz_entsorgung_de.md) source.
