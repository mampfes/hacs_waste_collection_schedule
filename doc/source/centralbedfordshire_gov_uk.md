# Central Bedfordshire Council

Support for schedules provided by [Central Bedfordshire Council](https://www.centralbedfordshire.gov.uk/waste-and-recycling/waste-collection-schedule), serving Central Bedfordshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: centralbedfordshire_gov_uk
      args:
        postcode: POSTCODE
        house_name: HOUSE_NAME
        uprn: UPRN
```

### Configuration Variables

**POSTCODE**  
*(string) (optional if `uprn` is provided)*

**HOUSE_NAME**  
*(string) (optional if `uprn` is provided)*

This must be a prefix of your address as shown on [Central Bedfordshire Council's postcode lookup](https://www.centralbedfordshire.gov.uk/waste-and-recycling/waste-collection-schedule). E.g. for `"10 Old School Walk, Arlesey, SG15 6YF"` use `"10 Old School Walk"`.

**UPRN**  
*(string) (optional)*

Your property's Unique Property Reference Number. If provided, `postcode` and `house_name` are not required and the postcode-form scrape is skipped, giving a more robust configuration. To find your UPRN: use the [council's lookup](https://www.centralbedfordshire.gov.uk/waste-and-recycling/waste-collection-schedule), select your address, and read the number at the end of the URL (e.g. `.../view/10000863589`).

## Example

Using postcode and house name:

```yaml
waste_collection_schedule:
    sources:
    - name: centralbedfordshire_gov_uk
      args:
        postcode: "SG15 6YF"
        house_name: "10 Old School Walk"
```

Using UPRN (recommended — more robust):

```yaml
waste_collection_schedule:
    sources:
    - name: centralbedfordshire_gov_uk
      args:
        uprn: "10000863589"
```
