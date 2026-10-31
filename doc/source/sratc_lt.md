# Šiaulių regiono atliekų tvarkymo centras (Šiauliai city)

Support for schedules provided by [Šiaulių regiono atliekų tvarkymo centras (Šiauliai city)](https://www.sratc.lt).

Source for the Šiauliai city waste collection schedule of individual households (ŠRATC, Lithuania)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sratc_lt
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sratc_lt
      args:
        street: "Plateli\u0173 g."
```

## How to get the source arguments

Enter your street as printed in the yearly schedule for individual households ("Visų rūšių atliekų surinkimas") on https://www.sratc.lt/grafikai-siauliu-miestas/, e.g. "Platelių g.". Where a street is split by house numbers, use the full entry, e.g. "Bielskio g. (nuo 44 iki 88 ir nuo 59 iki 101)"; an ambiguous street lists the possible entries. Apartment blocks (daugiabučiai) are not supported.
