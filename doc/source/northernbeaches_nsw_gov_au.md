# Northern Beaches Council (NSW)

Support for schedules provided by [Northern Beaches Council](https://www.northernbeaches.nsw.gov.au), serving the Northern Beaches area of Sydney, NSW, Australia.

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
Your street address including suburb, as shown on the [Northern Beaches Council bin collection days](https://www.northernbeaches.nsw.gov.au/services/rubbish-and-recycling/bins/bin-collection-days) page. The suburb should be in uppercase.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: northernbeaches_nsw_gov_au
      args:
        address: "25 Pittwater Road MANLY"
```

## How to get the arguments

1. Go to the [Northern Beaches Council bin collection days](https://www.northernbeaches.nsw.gov.au/services/rubbish-and-recycling/bins/bin-collection-days) page.
2. Type your address in the search box.
3. Use the full address as shown in the dropdown (e.g. `25 Pittwater Road MANLY`).
