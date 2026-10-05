# Rochford District Council

Support for schedules provided by [Rochford District Council](https://www.rochford.gov.uk).

Source for Rochford District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rochford_gov_uk
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
    - name: rochford_gov_uk
      args:
        postcode: SS4 1AS
        uprn: E05010853-10014203194
```

## How to get the source arguments

Go to https://www.rochford.gov.uk/bins-and-collections and enter your postcode, then press 'Find'. Open the address dropdown that appears and select your address. The 'uprn' is the value of the selected option in that dropdown: a composite of the ward code and UPRN separated by a hyphen, e.g. 'E05010853-10014203194'. You can read it from the page's HTML source (the <option value> attribute).
