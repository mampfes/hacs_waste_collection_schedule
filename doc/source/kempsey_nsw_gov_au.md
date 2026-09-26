# Kempsey Shire Council

Support for schedules provided by [Kempsey Shire Council](https://www.kempsey.nsw.gov.au).

Source script for kempsey.nsw.gov.au waste collection services.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kempsey_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kempsey_nsw_gov_au
      args:
        address: 10-12 Smith Street Kempsey
```

## How to get the source arguments

Enter your full street address as it appears on the Kempsey Shire Council website, e.g. '10-12 Smith Street Kempsey'.
