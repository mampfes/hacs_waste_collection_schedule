# Affärsverken

Support for schedules provided by [Affärsverken](https://www.affarsverken.se/).

Source for Affärsverken.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: affarsverken_se
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
    - name: affarsverken_se
      args:
        address: "Albatrossv\xE4gen 5, Ramdala"
```

## How to get the source arguments

Enter the address as the Affärsverken website writes it, street and number followed by the locality, e.g. `Albatrossvägen 5, Ramdala`.
