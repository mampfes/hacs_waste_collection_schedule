# Charnwood

Support for schedules provided by [Charnwood](https://www.charnwood.gov.uk/).

Source for Charnwood Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: charnwood_gov_uk
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
    - name: charnwood_gov_uk
      args:
        address: 111, Main Street, Swithland
```

## How to get the source arguments

Enter your address exactly as the council's address search lists it, for example `111, Main Street, Swithland`.
