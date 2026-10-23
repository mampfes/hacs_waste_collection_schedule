# Aprica S.p.A.

Support for schedules provided by [Aprica S.p.A.](https://www.apricaspa.it).

Source for Aprica S.p.A. (Gruppo A2A) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: apricaspa_it
      args:
        address: ADDRESS
        house_number: HOUSE_NUMBER
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**house_number**  
*(string) (required)*

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: apricaspa_it
      args:
        address: Via Giovanni Pascoli
        house_number: '18'
        city: Borgo San Giacomo
```

## How to get the source arguments

You need to provide the street name, house number, and city of your address. Aprica serves cities like Brescia, Bergamo, Como, Cremona, Crema, Lodi and their provinces.
