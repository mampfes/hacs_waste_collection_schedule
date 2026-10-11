# Municipium

Support for schedules provided by [Municipium](https://www.municipiumapp.it).

Source for the Municipium app (Maggioli S.p.A.), used by many Italian municipalities to publish their door-to-door waste collection calendar.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: municipium_it
      args:
        municipality: MUNICIPALITY
        area: AREA
```

### Configuration Variables

**municipality**  
*(string) (required)*

**area**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: municipium_it
      args:
        municipality: Serrastretta
        area: Zona 2
```

## How to get the source arguments

Enter the name of your municipality (comune) as it appears in the Municipium app. If the municipality has more than one collection zone (area), the error message will list the available zone names; pass the one that matches your address as 'area'. A partial name (e.g. 'Zona 2') is enough, or you can pass the numeric calendar id.
