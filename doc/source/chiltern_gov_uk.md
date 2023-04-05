# Chiltern Area - Buckinghamshire Council

Support for schedules provided by former Chiltern, SouthBucks or Wycombe area,  Council](https://chiltern.gov.uk/collection-dates) that covers High Wycombe.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: chiltern_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: chiltern_gov_uk
      args:
        uprn: 200000811701
```

## How to get the source argument

Search for your address on the [FindMyAddress service](https://www.findmyaddress.co.uk/) which displays the UPRN in the result.