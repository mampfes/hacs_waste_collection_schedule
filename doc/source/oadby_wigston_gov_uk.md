# Charnwood

Support for schedules provided by [Oadby and Wigston Council](https://www.oadby-wigston.gov.uk), serving Charnwood, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: oadby_wigston_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: oadby_wigston_gov_uk
      args:
        address: 89, Leicester Road, Leicester, Leicestershire
```

## How to get the source argument

You can check [https://my.oadby-wigston.gov.uk/](https://my.oadby-wigston.gov.uk/). The address should exactly match the autocomplete suggestion.
