# Dundee City Council

Support for schedules provided by [Dundee City Council](https://www.dundeecity.gov.uk/services/bins-%26-recycling), serving Dundee City, Scotland (UK).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dundeecity_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**UPRN**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: dundeecity_gov_uk
      args:
        uprn: "9059060343"
```

## How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
