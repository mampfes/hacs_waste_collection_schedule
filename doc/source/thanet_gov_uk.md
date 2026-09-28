# Thanet District Council

Support for schedules provided by [Thanet District Council](https://thanet.gov.uk).

Source for thanet.gov.uk services for Thanet District Council

## Configuration via configuration.yaml

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: thanet_gov_uk
      args:
        uprn: UPRN
```

### Using postcode and street_address

```yaml
waste_collection_schedule:
  sources:
    - name: thanet_gov_uk
      args:
        postcode: POSTCODE
        street_address: STREET_ADDRESS
```

### Configuration Variables

**uprn**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**street_address**  
*(string) (alternative)*

Provide one of: `uprn` or `postcode` + `street_address`.

## Example

### Using uprn

```yaml
waste_collection_schedule:
  sources:
    - name: thanet_gov_uk
      args:
        uprn: '100061108233'
```

### Using postcode and street_address

```yaml
waste_collection_schedule:
  sources:
    - name: thanet_gov_uk
      args:
        postcode: CT7 9SL
        street_address: Forus
```

## How to get the source arguments

Enter either your UPRN (available from [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/)) OR your postcode and the first line of your address, e.g. '2 London Road' (anything before the first comma of the address on the council's site). UPRNs work every time; a postcode and street address work when a match can be found.
