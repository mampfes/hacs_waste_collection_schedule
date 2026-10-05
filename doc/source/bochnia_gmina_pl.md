# Gmina Bochnia

Support for schedules provided by [Gmina Bochnia](https://bochnia-gmina.pl).

Source for Gmina Bochnia waste collection schedule (Poland)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bochnia_gmina_pl
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
    - name: bochnia_gmina_pl
      args:
        town: "Baczk\xF3w"
```

## How to get the source arguments

Enter the name of the town in Gmina Bochnia (e.g. Baczków, Damienice, Proszówki, Łapczyca, etc.).
