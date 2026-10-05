# Tonnenticker Pro

Support for schedules provided by [Tonnenticker Pro](https://www.regioit.de).

Source for Tonnenticker Pro (RegioIT) waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tonnenticker_pro_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tonnenticker_pro_de
      args:
        city: Steinhagen
        street: "Waldbadstra\xDFe (Bahnhofstr. bis Rote Erde)"
```

## How to get the source arguments

Select your municipality, then use the street name shown in the Tonnenticker Pro app or on the provider's website.
