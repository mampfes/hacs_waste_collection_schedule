# Komunala Kranj

Support for schedules provided by [Komunala Kranj](https://www.komunala-kranj.si/).

Source for Komunala Kranj.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: komunala_kranj_si
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
    - name: komunala_kranj_si
      args:
        address: "Koro\u0161ka cesta 1, Kranj, 4000 Kranj"
```

## How to get the source arguments

Enter the address exactly as the Komunala Kranj address search shows it, e.g. 'Koroška cesta 1, Kranj, 4000 Kranj'. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
