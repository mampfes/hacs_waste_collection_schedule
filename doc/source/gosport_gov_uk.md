# Gosport Borough Council

Support for schedules provided by [Gosport Borough Council](https://www.gosport.gov.uk), serving Gosport, Hampshire, UK.

## Local Government Reorganisation note
During the ongoing local government reorganisation (LGR) in Hampshire, please continue to use the source for your current area as long as it's still working. New sources for the new South East Hampshire Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: gosport_gov_uk
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
    - name: gosport_gov_uk
      args:
        postcode: "PO12 4RL"
        uprn: "37020212"
```

## How to get the source arguments

1. Go to <https://www.gosport.gov.uk/refuserecyclingdays> and enter your postcode.
2. Your postcode is the first argument.
3. Select your address from the dropdown. The number shown at the end of the address text is your UPRN (e.g. `37020212`).
