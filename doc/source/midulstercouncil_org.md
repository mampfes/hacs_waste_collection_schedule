# Mid Ulster District Council

Support for schedules provided by [Mid Ulster District Council](https://www.midulstercouncil.org).

Source for Mid Ulster District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midulstercouncil_org
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: midulstercouncil_org
      args:
        uprn: 185653615
```

## How to get the source arguments

You can find your UPRN by visiting https://www.findmyaddress.co.uk/ and entering your address details.
