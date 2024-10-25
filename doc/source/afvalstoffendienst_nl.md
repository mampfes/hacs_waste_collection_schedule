# Afvalstoffendienst.nl

Support for schedules provided by [Afvallstoffendienst.nl](https://www.afvalstoffendienst.nl/), serving 's Hertogenbosch, Heusden, Vught, Oisterwijk, Altena, Bernheze. Netherlands.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: afvalstoffendienst_nl
      args:
        region: REGION
        postcode: POSTCODE
        house_number: "HOUSSE NUMBER (huisnummer)"
        addition: ADDITION (toevoeging)
```

### Configuration Variables

**region**
*(String) (required)* should be one of `heusden`, `vught`, `oisterwijk`, `altena`, `bernheze`, `s-hertogenbosch`

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
        region: s-hertogenbosch
        postcode: 5151MS
        house_number: "37"
```

```yaml
waste_collection_schedule:
    sources:
    - name: afvalstoffendienst_nl
      args:
        region: heusden
        postcode: 5256EJ
        house_number: 44 
        addition: "C"
```

## How to get the source argument

You can check weather your parameter return a valid result using the website <https://www.afvalstoffendienst.nl>
