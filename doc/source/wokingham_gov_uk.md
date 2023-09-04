# Wokingham Borough Council

Support for schedules provided by [Wokingham Borough Council](https://www.wokingham.gov.uk/rubbish-and-recycling/find-your-bin-collection-day"), serving Wokingham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wokingham_gov_uk
      args:
        postcode: POSTCODE
        property: PROPERTY_REFERENCE_NUMBER
        address: ADDRESS
```

### Configuration Variables
**postcode**  
*(string) (required)*

**property**  
*(string) (optional)*

**address**  
*(string) (optional)*

There are two config options:
 - Supply both the `postcode` and `address` args. The script tries to match you address within the results returned from the website and assume the first match it makes is your property.
 - Supply both the  `postcode` and `property` args. The `property` arg uniquely identified your property within the given postcode. See below for how to identify your property id.


## Example using `address` arg

```yaml
waste_collection_schedule:
    sources:
    - name: wokingham_gov_uk
      args:
        postcode: "RG40 2LW"
        address: "16 Davy Close"
```
## Example using `property` arg

```yaml
waste_collection_schedule:
    sources:
    - name: wokingham_gov_uk
      args:
        postcode: "RG40 1GE"
        property: "56199"
```

## How to find your Property Reference Number
When viewing your collection schedule on the [Wokingham](https://www.wokingham.gov.uk/rubbish-and-recycling/find-your-bin-collection-day") web site. Inspect the page source and search for your address. You should seem something like this:

`<option value="17033" selected="selected">16, DAVY CLOSE, WOKINGHAM</option>`

The number in the _value_ attribute should be used as the `property` arg.

Alternatively, you can run the [wokingham_uk](/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/wokingham_uk.py) wizard script. For a given postcode, it will list addresses and associated Property Reference Number. For example:

```bash
Enter your postcode: RG40 1GE
56164 = 2 Samborne Drive Wokingham
56165 = 4 Samborne Drive Wokingham
56166 = 6 Samborne Drive Wokingham
...
56174 = 22 Samborne Drive Wokingham
56175 = 24 Samborne Drive Wokingham
56176 = 26 Samborne Drive Wokingham
```
