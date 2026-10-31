# Preston City Council

Support for schedules provided by [Preston City Council](https://preston.gov.uk).

Source for preston.gov.uk services for Preston City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: preston_gov_uk
      args:
        street: STREET
        uprn: UPRN
```

### Configuration Variables

**street**  
*(string) (required)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: preston_gov_uk
      args:
        street: town hall, lancaster road
```

## How to get the source arguments

Enter your street name or postcode as you would on https://selfservice.preston.gov.uk/service/Forms/FindMyNearest.aspx?Service=bins. If it matches more than one property, also enter your Unique Property Reference Number (UPRN), which you can find at https://www.findmyaddress.co.uk/. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
