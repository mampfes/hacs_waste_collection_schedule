# Belmont City Council

Support for schedules provided by [Belmont City Council Waste and Recycling](https://www.belmont.wa.gov.au/live/at-your-place/bins,-waste-and-recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: belmont_wa_gov_au
      args:
        post_code: POST_CODE
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**post_code**<br>
*(string) (required)*

**suburb**<br>
*(string) (required)*

**street_name**<br>
*(string) (required)*

**street_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: belmont_wa_gov_au
      args:
        post_code: 6104
        suburb: Belmont
        street_name: Abernethy Rd
        street_number: 196
```

## How to get the source arguments

Visit the [Belmont City Council Waste and Recycling](https://www.belmont.wa.gov.au/live/at-your-place/bins,-waste-and-recycling) page and search for your address. The arguments should exactly match the results shown for Post Code, Suburb, Street and number portion of the Property.
