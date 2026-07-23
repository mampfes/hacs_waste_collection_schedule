# Wokingham Borough Council

Support for schedules provided by [Wokingham Borough Council](https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day), serving Wokingham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wokingham_gov_uk
      args:
        postcode: POSTCODE
        property: UPRN
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

- Supply both the `postcode` and `address` args. The script tries to match your address within the results returned from the website and assumes the first match is your property.
- Supply both the `postcode` and `property` args. The `property` arg is the UPRN (Unique Property Reference Number) for your address within the given postcode. See below for how to find your UPRN.

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
        property: "10032935729"
```

## How to find your UPRN

When viewing your collection schedule on the [Wokingham](https://www.wokingham.gov.uk/rubbish-and-recycling/waste-collection/find-your-bin-collection-day) web site, inspect the page source and search for your address. You should see something like this:

`<option value="10032935729">32, SAMBORNE DRIVE, WOKINGHAM</option>`

The number in the `value` attribute is your UPRN and should be used as the `property` arg.

Alternatively, you can run the [wokingham_uk](/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/wokingham_uk.py) wizard script. For a given postcode, it will list addresses and associated UPRN values. For example:

```bash
Enter your postcode: RG40 1GE
10032935700 = 2  Samborne Drive  Wokingham
10032935702 = 4  Samborne Drive  Wokingham
10032935704 = 6  Samborne Drive  Wokingham
...
10032935729 = 32  Samborne Drive  Wokingham
10032935731 = 34  Samborne Drive  Wokingham
```
