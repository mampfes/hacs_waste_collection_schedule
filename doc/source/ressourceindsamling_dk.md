# RessourceIndsamling.dk

Support for schedules provided by [RessourceIndsamling](https://www.ressourceindsamling.dk/selvbetjening/ballerup-kommune-selvbetjening/), serving the municipality of Ballerup, Denmark.

Even though RessourceIndsamling handles multiple municipalities, only Ballerup is supported in this integration.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ressourceindsamling_dk
      args:
        streetName: street name
        number: house number
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
        streetName: Kløvertoften
        number: 61
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://www.ressourceindsamling.dk/selvbetjening/ballerup-kommune-selvbetjening/).
