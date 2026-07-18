# AWISTA Kommunal GmbH (Düsseldorf)

Support for schedules provided by [AWISTA Kommunal GmbH (Düsseldorf)](https://www.awista-kommunal.de/abfallkalender).

Source for AWISTA Kommunal GmbH, Düsseldorf, Germany.

## Configuration via configuration.yaml

### Using uuid

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        uuid: UUID
```

### Using street and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**uuid**  
*(string) (alternative)*

**street**  
*(string) (alternative)*

**house_number**  
*(string) (alternative)*

Provide one of: `uuid` or `street` + `house_number`.

## Example

### Using uuid

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        uuid: 5d1c4832-fd49-4fa7-a4e3-60dbe116cbc0
```

### Using street and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: awista_kommunal_de
      args:
        street: "Merkurstra\xDFe"
        house_number: '45'
```

## How to get the source arguments

Provide 'street' and 'house_number' as you would type them into the address search at https://www.awista-kommunal.de/abfallkalender. Alternatively, search for your address on that page and copy the UUID from the browser URL bar (e.g. https://www.awista-kommunal.de/abfallkalender/<uuid>) into 'uuid'; if 'uuid' is given, the address arguments are ignored.
