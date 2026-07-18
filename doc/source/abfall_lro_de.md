# Landkreis Rostock

Support for schedules provided by [Landkreis Rostock](https://www.abfall-lro.de/).

Source for Landkreis Rostock.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_lro_de
      args:
        municipality: MUNICIPALITY
        street: STREET
        black_rhythm: BLACK_RHYTHM
        green_rhythm: GREEN_RHYTHM
        black_seasonal: BLACK_SEASONAL
        green_seasonal: GREEN_SEASONAL
```

### Configuration Variables

**municipality**  
*(string) (required)*

**street**  
*(string) (optional)*

**black_rhythm**  
*(string) (optional)*

**green_rhythm**  
*(string) (optional)*

**black_seasonal**  
*(string) (optional)*

**green_seasonal**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_lro_de
      args:
        municipality: "Alt K\xE4twin"
        black_rhythm: 2w
        green_rhythm: 4w
```

## How to get the source arguments

Provide the municipality name as shown at https://www.abfall-lro.de/de/abfuhrtermine/ (including any sub region in brackets). Use 'Güstrow' with a street for Güstrow city streets. black_rhythm/green_rhythm are '2w', '4w' or blank, as shown for your municipality on that page; tick black_seasonal / green_seasonal if that bin is only collected seasonally.
