# Northern Beaches Council (NSW)

Support for schedules provided by [Northern Beaches Council (NSW)](https://www.northernbeaches.nsw.gov.au).

Source for Northern Beaches Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northernbeaches_nsw_gov_au
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
    - name: northernbeaches_nsw_gov_au
      args:
        address: 25 Pittwater Road MANLY
```

## How to get the source arguments

Enter your address as shown on the Northern Beaches Council website, including the suburb in uppercase, e.g. '25 Pittwater Road MANLY'.
