# Gmina Radłów

Support for schedules provided by [Gmina Radłów](https://www.gminaradlow.pl).

Source for Gmina Radłów (Małopolska) waste collection schedule

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_radlow_pl
      args:
        town: TOWN
```

### Configuration Variables

**town**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_radlow_pl
      args:
        town: "Rad\u0142\xF3w"
```

## How to get the source arguments

Select your village in Gmina Radłów.
