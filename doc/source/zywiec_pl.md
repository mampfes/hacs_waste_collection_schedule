# Miasto Żywiec

Support for schedules provided by [Miasto Żywiec](https://zywiec.pl/harmonogram-wywozu-smieci).

Source for Miasto Żywiec waste collection schedule (Poland)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zywiec_pl
      args:
        region: REGION
```

### Configuration Variables

**region**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zywiec_pl
      args:
        region: Rejon V
```

## How to get the source arguments

Select your collection region (rejon). The schedule PDF linked on https://zywiec.pl/harmonogram-wywozu-smieci lists the streets of each region next to its dates. Streets marked with * changed region in the current schedule, so check your region whenever a new half-year schedule is published.
