# Kópavogsbær

Support for schedules provided by [Kópavogsbær](https://www.kopavogur.is).

Source for Kópavogur, Iceland (Kubbur collection calendar)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kopavogur_is
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kopavogur_is
      args:
        district: "Vesturb\xE6r - Sm\xE1rahverfi"
```

## How to get the source arguments

Enter the collection district (zone) as shown in the legend of the calendar: Vesturbær - Smárahverfi, Austurbær sunnan Álfhólsvegar, Austurbær norðan Álfhólsvegar or Lindir, Salir, Kórar, Hvörf og Þing. A partial, case-insensitive match is accepted.
