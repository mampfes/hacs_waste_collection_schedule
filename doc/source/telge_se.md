# Telge Återvinning

Source for Telge Återvinning, household waste collection in Södertälje
municipality, Sweden. Telge Återvinning has operated since 1998 and serves
Södertälje and surrounding areas (Järna, Hölö, Mörkö, Enhörna, Mölnbo).

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: telge_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*

The address in uppercase format as used by Telge's system, e.g.
`BERGSGATAN 22, SÖDERTÄLJE`.

### How to find your `address`

1. Visit the Telge waste collection schedule page:
   https://www.telge.se/atervinning/kundservice/nar-kommer-sopbilen/

2. Enter your address in the search field.

3. Use the address exactly as shown in the autocomplete dropdown, including
   the locality after the comma (e.g. `BERGSGATAN 22, SÖDERTÄLJE` or
   `BERGA 1, JÄRNA`).

Alternatively, query the autocomplete API directly:

```
GET https://www.telge.se/api/thorweb/garbagecollection/autocomplete/{query}
```

### Example YAML Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: telge_se
      args:
        address: "BERGSGATAN 22, SÖDERTÄLJE"
```
