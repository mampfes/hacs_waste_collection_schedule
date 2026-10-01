# Hedemora Energi

Support for schedules provided by [Hedemora Energi](https://www.hedemoraenergi.se/).

Source for Hedemora Energi waste collection schedules, Sweden.

## Configuration via configuration.yaml

### Using pickup_id

```yaml
waste_collection_schedule:
  sources:
    - name: hedemora_energi_se
      args:
        pickup_id: PICKUP_ID
```

### Using address

```yaml
waste_collection_schedule:
  sources:
    - name: hedemora_energi_se
      args:
        address: ADDRESS
```

### Configuration Variables

**pickup_id**  
*(string) (alternative)*

**address**  
*(string) (alternative)*

Provide one of: `pickup_id` or `address`.

## Example

### Using pickup_id

```yaml
waste_collection_schedule:
  sources:
    - name: hedemora_energi_se
      args:
        pickup_id: '1392000'
```

### Using address

```yaml
waste_collection_schedule:
  sources:
    - name: hedemora_energi_se
      args:
        address: "\xC5sgatan 28"
```

## How to get the source arguments

Use `pickup_id` if known. Otherwise enter the exact address as shown in Hedemora Energi's fetch planner search.
