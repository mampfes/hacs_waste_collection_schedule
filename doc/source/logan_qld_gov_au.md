# Logan City Council

Support for schedules provided by [Logan City Council](https://www.logan.qld.gov.au/MyLogan), Queensland, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: logan_qld_gov_au
      args:
        property_location: PROPERTY_LOCATION
```

### Configuration Variables

**property_location**  
*(string) (required)*

Your street address. The closest match returned by the MyLogan address search is used, so the exact council formatting is not required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: logan_qld_gov_au
      args:
        property_location: 12 Ashton Street Kingston
```

## How to get the source arguments

Visit the [MyLogan](https://www.logan.qld.gov.au/MyLogan) tool and search for your address. Any address string that the search box accepts and resolves to your property will work — for example `12 Ashton Street Kingston`.
