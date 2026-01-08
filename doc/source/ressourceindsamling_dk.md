# Vestforbrændning

Support for schedules provided by [RessourceIndsamling](https://www.ressourceindsamling.dk/selvbetjening/ballerup-kommune-selvbetjening/), serving the municipality of Ballerup, Denmark.

Even though RessourceIndsamling handles multiple municipality, only Ballerup is support in this integration.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ressourceindsamling_dk
      args:
        streetName: street name
        number: house number
        zipCode: zip code
```

### Configuration Variables

**streetName**  
*(string) (required)*

**number**  
*(string) (required)*

**zipCode**  
*(string) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ressourceindsamling_dk
      args:
        streetName: Kløvertoften
        number: 61
        zipCode: 2740
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://selvbetjening.vestfor.dk/Adresse/Toemmekalender).
