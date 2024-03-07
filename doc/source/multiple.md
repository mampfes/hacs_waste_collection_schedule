# Multiple Source Wrapper

Wrapper Source to include multiple sources in one calendar.

This wrapper is meant for configurations where you want to include multiple sources in one calendar entity. If you want to have multiple calendars, you should simply pass multiple sources to the `sources` parameter in the configuration.

This is just a wrapper class for other sources for further information see the documentation of the sources you want to include.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: multiple
      args:
        SOURCE_NAME: SOURCE_ARGS
        SOURCE_NAME: SOURCE_ARGS
        ...
        # or (can be mixed)
        SOURCE_NAME: 
          - SOURCE_ARGS
          - SOURCE_ARGS
            ...
```

### Configuration Variables

**SOURCE_NAME**  
*(string) (required)*

The name of the source to include. **Note:** You cannot use the same source name multiple times (use the second syntax instead).

**SOURCE_ARGS**  
*(dict) (required)*

A dictionary of arguments for the source.

## Examples

### Two static sources

```yaml
waste_collection_schedule:
  sources:
    - name: multiple
      args:
        static:
          - type: "Dates only"
            dates:
              - "2022-01-01"
              - "2022-01-01"
          - type: "First day of month"
            frequency: "MONTHLY"
            interval: 1
            start: "2022-01-01"
            until: "2022-12-31"
```

### Two ics sources

```yaml
waste_collection_schedule:
  sources:
    - name: multiple
      args:
        ics:
          - url: "https://servicebetrieb.koblenz.de/abfallwirtschaft/entsorgungstermine-digital/entsorgungstermine-2023-digital/altstadt-2023.ics?cid=2ui7"
          - url: "https://recollect.a.ssl.fastly.net/api/places/BCCDF30E-578B-11E4-AD38-5839C200407A/services/208/events.en.ics"
            split_at: "\\, (?:and )?|(?: and )"
```

### One Static and ics source each

```yaml
waste_collection_schedule:
  sources:
    - name: multiple
      args:
        static:
          type: "Dates only"
          dates:
            - "2022-01-01"
            - "2022-01-01"
        ics:
          url: "https://sperrmuell.erlensee.de/?type=reminder"
          method: "POST"
          params:
            street: 8
            eventType[]:
              - 27
              - 23
              - 19
              - 20
              - 21
              - 24
              - 22
              - 25
              - 26
            timeframe: 23
            download: "ical"
```

### Three "normal" sources

```yaml
waste_collection_schedule:
  sources:
    - name: multiple
      args:
        lund_se:
          street_address: "Lokföraregatan 7, LUND (19120)"
        meinawb_de:
          city: "Oberzissen"
          street: "Lindenstrasse"
          house_number: "1"
        jumomind_de:
          service_id: "mymuell"
          city: "Bad Wünnenberg-Bleiwäsche"
```

### Two "normal" sources with two static sources

```yaml
waste_collection_schedule:
  sources:
    - name: multiple
      args:
        lund_se:
          street_address: "Lokföraregatan 7, LUND (19120)"
        nawma_sa_gov_au:
          street_number: "128"
          street_name: "Bridge Road"
          suburb: "Pooraka"
        static:
          - type: "Dates only"
            dates:
              - "2024-01-01"
              - "2024-01-24"
          - type: "First day of month"
            frequency: "MONTHLY"
            interval: 1
            start: "2022-01-01"
            until: "2022-12-31"
```
