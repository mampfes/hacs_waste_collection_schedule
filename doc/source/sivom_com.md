# SIVOM de la Vallée de l'Yerres et des Sénarts

Support for schedules provided by [SIVOM de la Vallée de l'Yerres et des Sénarts](https://www.sivom.com).

Source for waste collection schedules from the SIVOM de la Vallée de l'Yerres et des Sénarts (sivom.com).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sivom_com
      args:
        commune: COMMUNE
        street: STREET
```

### Configuration Variables

**commune**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sivom_com
      args:
        commune: VILLECRESNES
        street: "ACACIAS All\xE9e des"
```

## How to get the source arguments

Go to https://www.sivom.com/mesjoursdecollectes/?v=YOUR_COMMUNE to find your commune name and street name.
