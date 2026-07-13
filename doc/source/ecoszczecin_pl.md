# EcoSzczecin

Support for waste collection schedules in Szczecin, Poland, provided by [ecoszczecin.pl](https://ecoszczecin.pl).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ecoszczecin_pl
      args:
        street: "TCZEWSKA"
        house_number: "7A"
```

### Configuration Variables

**street**
*(String) (required)* Street name in Szczecin, as shown on ecoszczecin.pl. Not case-sensitive.

**house_number**
*(String) (required)* House number for the given street, as shown on ecoszczecin.pl.

## How to get the source arguments

1. Open <https://ecoszczecin.pl/harmonogramy/> in your browser.
2. Step through the address selection UI — choose your street, then your house number.
3. Copy the `street` and `house_number` values exactly as displayed in the dropdown lists.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ecoszczecin_pl
      args:
        street: "Aleja Piastów"
        house_number: "1"
```
