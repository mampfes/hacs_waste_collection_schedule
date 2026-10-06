# Dacorum Borough Council

Support for schedules provided by [Dacorum Borough Council](https://www.dacorum.gov.uk/).

Source for Dacorum Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dacorum_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: dacorum_gov_uk
      args:
        postcode: HP1 1AB
        uprn: 200004054631
```

## How to get the source arguments

Enter your postcode and your UPRN. Find your UPRN at https://www.findmyaddress.co.uk/ or by searching for your address on the council's [bin collections page](https://webapps.dacorum.gov.uk/bincollections/).
