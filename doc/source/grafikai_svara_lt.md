# Kauno švara

Support for schedules provided by [Kauno švara](https://svara.lt).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grafikai_svara_lt
      args:
        region: REGION
        street: STREET_NAME
        house_number: HOUSE_NUMBER
        district: DISTRICT
```

### Configuration Variables

**region**
*(string) (required)*

**street**
*(string) (required)*

**house_number**
*(string) (required)*

**district**
*(string) (optional)*

**waste_object_ids**
*(list of int) (optional)* — see [Filtering by wasteObjectId](#filtering-by-wasteobjectid) below.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grafikai_svara_lt
      args:
        region: Kauno m. sav.
        street: Demokratų g.
        house_number: 7
```

## How to get the source arguments

Visit the [Grafikai](https://grafikai.svara.lt) page and search for your address. The dropdown labels on the page map to YAML arguments as follows:

| Page field            | YAML argument |
|-----------------------|---------------|
| Regionas              | region        |
| Seniūnija             | district      |
| Gatvė                 | street        |
| Namo numeris          | house_number  |

## Filtering by wasteObjectId

By default the source returns every collection scheduled for the address. If multiple containers are registered there (e.g. mixed waste, paper/plastic, glass) and you want only some of them, set `waste_object_ids` to a list of numeric IDs.

Find the IDs by searching for your address on [grafikai.svara.lt](https://grafikai.svara.lt) with your browser's DevTools open: in the Network tab, locate the `getcontracts` server-function request and inspect its response. Each row contains a `wasteObjectId` integer field — pick the ones you want.

Note: numeric `wasteObjectId` values from before the April 2026 grafikai.svara.lt rebuild are no longer valid; if your config carries old IDs, look them up again.
