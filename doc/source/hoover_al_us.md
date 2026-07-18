# Hoover, AL

Support for schedules provided by [Hoover, AL](https://hooveralabama.gov).

Source for Hoover, AL garbage collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hoover_al_us
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
    - name: hoover_al_us
      args:
        address: 2255 Tyler Rd, Hoover, AL
```

## How to get the source arguments

Enter your street address within Hoover, AL (e.g. '2255 Tyler Rd, Hoover, AL').
