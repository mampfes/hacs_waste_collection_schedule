# Nottingham City Council

Support for schedules provided by [Nottingham City
Council](https://www.nottinghamcity.gov.uk/binreminders), serving the
city of Nottingham City, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nottingham_city_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: nottingham_city_gov_uk
      args:
        uprn: "100031540175"
```

## How to get the source argument

The UPRN code can be found in the network request when entering your
postcode and selecting your address on the [Nottingham City Council
Bin Reminders
page](https://www.nottinghamcity.gov.uk/binreminders). You should look
for a request ending in `/livebin/<some numbers>` the last segment is your UPRN
code.
