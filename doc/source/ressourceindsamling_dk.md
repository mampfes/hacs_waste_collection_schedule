# RessourceIndsamling.dk

Support for schedules provided by [RessourceIndsamling.dk](https://www.ressourceindsamling.dk/).

Source for RessourceIndsamling.dk collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ressourceindsamling_dk
      args:
        streetName: STREETNAME
        number: NUMBER
```

### Configuration Variables

**streetName**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ressourceindsamling_dk
      args:
        streetName: "Kl\xF8vertoften"
        number: '61'
```

## How to get the source arguments

Enter the street name and house number as they appear on https://www.ressourceindsamling.dk/ (for example Kløvertoften and 61).
