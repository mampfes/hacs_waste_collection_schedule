# Town of Huntington, NY

Support for schedules provided by [Town of Huntington, NY](https://huntingtonny.gov/trash-recycling).

Source for Town of Huntington, NY refuse, recycling and yard waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: huntington_ny_us
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: huntington_ny_us
      args:
        address: 242 E Main St, Huntington, NY
```

## How to get the source arguments

Enter your full street address including town and state (e.g. '242 E Main St, Huntington, NY'). Only the weekdays are published, so holiday shifts and the yard waste season are not reflected.
