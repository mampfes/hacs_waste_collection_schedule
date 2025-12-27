# Afvalstoffendienst.nl

Support for schedules provided by [Afvallstoffendienst.nl](https://www.afvalstoffendienst.nl/), serving 's Hertogenbosch, Heusden, Vught, Oisterwijk, Altena, Bernheze. Netherlands. The source now talks directly to the afvalstoffendienst API using postcode and house number (with optional addition); the `region` parameter is no longer used.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: afvalstoffendienst_nl
      args:
        postcode: POSTCODE
        house_number: "HOUSE NUMBER (huisnummer)"
        addition: "ADDITION (toevoeging/huisletter)"
```

### Configuration Variables

**postcode**
*(String) (required)*

**house_number**
*(String | Integer) (required)*

**addition**  
*(String) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: afvalstoffendienst_nl
      args:
        postcode: 5151MS
        house_number: "37"
```

```yaml
waste_collection_schedule:
    sources:
    - name: afvalstoffendienst_nl
      args:
        postcode: 5256EJ
        house_number: 44
        addition: "C"
```

## How to get the source argument

You can check weather your parameter return a valid result using the website <https://www.afvalstoffendienst.nl>
