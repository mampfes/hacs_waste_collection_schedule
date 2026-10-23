# Gmina Zgierz

Support for schedules provided by [Gmina Zgierz](https://gminazgierz.pl).

Source for Gmina Zgierz garbage collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_zgierz_pl
      args:
        location_name: LOCATION_NAME
```

### Configuration Variables

**location_name**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gmina_zgierz_pl
      args:
        location_name: Grotniki
```

## How to get the source arguments

Enter the name of your village (location_name) as listed in the yearly schedule on https://bip.gminazgierz.pl, for example `Grotniki`. The schedule groups the villages into the regions Rejon I to IV.
