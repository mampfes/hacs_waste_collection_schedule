# East Cambridgeshire District Council

Support for schedules provided by [East Cambridgeshire District Council](https://www.eastcambs.gov.uk/), serving East Cambridgeshire district, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastcambs_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

#### How to find your `UPRN`

Visit the [East Cambridgeshire bin collection checker](https://eastcambs-self.achieveservice.com/service/Check_your_waste_collection_day) and search for your address. Your UPRN will appear as part of the address lookup.

Alternatively, go to <https://www.findmyaddress.co.uk/> and enter your address details.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: eastcambs_gov_uk
      args:
        uprn: 10002601730
```
