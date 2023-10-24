# Dudley Metropolitan Borough Council

Support for schedules provided by [Dudley Metropolitan Borough Council](https://www.dudley.gov.uk/residents/bins-and-recycling/rubbish-collection/), serving the city of Dudley, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dudley_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables
**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: dudley_gov_uk
      args:
        uprn: "90092621"
```

## How to find your `UPRN`

Your Unique Property Reference Number (UPRN) is displayed in the Property Details panel when you search for your address on the [My Council](https://maps.dudley.gov.uk/mycouncil.aspx) web page.
Alternatively, you can your UPRN  by going to <https://www.findmyaddress.co.uk/> and entering your address details.