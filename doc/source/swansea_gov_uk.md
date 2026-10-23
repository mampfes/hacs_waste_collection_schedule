# Swansea Council

Support for schedules provided by [Swansea Council](https://swansea.gov.uk/), UK.

If collection data is available for the address provided, it will return pink week and green week collection dates.


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: swansea_gov_uk
      args:
        post_code: POST_CODE
        street_name: STREET_NAME
        uprn: UPRN
```

### Configuration Variables

**post_code**

_(string) (required)_

Full postcode of the property

**street_name**

_(string) (optional)_

Any part of the address (e.g. the street name or house number and street). Used to pick an address when the postcode covers more than one street. If omitted (and no `uprn` is given), the first address in the postcode is used.

**uprn**

_(string) (optional)_

Unique Property Reference Number of the property. Takes priority over `street_name`.

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: swansea_gov_uk
      args:
        post_code: "SA2 0RA"
        street_name: "Cwmdonkin Drive"
```

```yaml
waste_collection_schedule:
    sources:
    - name: swansea_gov_uk
      args:
        post_code: "SA2 0RA"
        uprn: "100100351698"
```

## How to verify that your address works

Visit [swansea.gov.uk/recyclingsearch](https://www.swansea.gov.uk/recyclingsearch), enter your postcode, click "Find address" and select your address.

## How to find your UPRN

An easy way to find your UPRN is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
