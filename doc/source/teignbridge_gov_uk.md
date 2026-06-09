# Teignbridge District Council

Support for schedules provided by [Teignbridge District Council](https://www.teignbridge.gov.uk/recycling-and-waste/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: teignbridge_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)* Postcode

**uprn**  
*(string) (required)* Unique Property Reference Number

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: teignbridge_gov_uk
      args:
        postcode: EX4 2JR
        uprn: "010032968474"
```

## How to get the source arguments

Visit the [Teignbridge collection calendar](https://www.teignbridge.gov.uk/recycling-and-waste/forms/download-your-collection-calendar/) page, enter your postcode and select your address. Your UPRN can be found at [Find My Address](https://www.findmyaddress.co.uk).

Collection types:

- **Food waste container**
- **Black box** (recycling)
- **Green box** (glass)
- **Sack for paper**
- **Refuse - black bin**
