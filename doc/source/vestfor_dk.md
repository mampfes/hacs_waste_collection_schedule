# Vestforbrændning

Support for schedules provided by [Vestforbrændning](https://selvbetjening.vestfor.dk/), serving the municipality of Albertslund, Ballerup, Furesø, Ishøj, and Vallensbæks, Denmark.

Note: From 2026 onwards, Ballerup will no longer use Vestforbrænding. Please take a look at the source: ressourceindsamling_dk.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vestfor_dk
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
    - name: vestfor_dk
      args:
        streetName: Kløvertoften
        number: 61
        zipCode: 2740
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://selvbetjening.vestfor.dk/Adresse/Toemmekalender).
