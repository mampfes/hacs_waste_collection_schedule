# Ronneby Miljöteknik Sophämtning

Support for schedules provided by [Ronneby Miljöteknik](http://www.fyrfackronneby.se/hamtningskalender/), serving the municipality of Ronneby, Sweden.

Note that they only provide their calendar service for customers with the "Fyrfack" bins which means this will only work for regular residential houses and not for apartment buildings, city services locations or similar.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: miljoteknik_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: miljoteknik_se
      args:
        street_address: Hjortsbergavägen 16, Johannishus
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](http://www.fyrfackronneby.se/hamtningskalender/).

## Types returned

The following waste types will be returned:

* "Mat, Brännbart, färgat glas, tidningar."

* "Plast, pappersförpackningar, ofärgat glas, metall."

