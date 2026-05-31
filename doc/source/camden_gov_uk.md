# London Borough of Camden

Support for schedules provided by [London Borough of Camden](https://www.camden.gov.uk/), serving Camden, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: camden_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: camden_gov_uk
      args:
        uprn: 5061647
        
```

## How to get the source argument

Camden now expects the property's Unique Property Reference Number (UPRN) directly.

You can look up the UPRN via a public address service such as <https://www.findmyaddress.co.uk/>.
