# Gmina Nawojowa

Support for schedules provided by [Gmina Nawojowa](https://nawojowa.pl).

Source for Gmina Nawojowa waste collection schedule (Poland)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nawojowa_pl
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nawojowa_pl
      args:
        area: Nawojowa I
```

## How to get the source arguments

Select your village. Nawojowa is split into Nawojowa I and Nawojowa II by street; see the street lists in the schedule PDF linked on https://nawojowa.pl.
