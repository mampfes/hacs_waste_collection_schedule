# Uddevalla Energi

Support for waste collection schedules provided by
[Uddevalla Energi](https://www.uddevallaenergi.se/privat/sophamtning.html),
serving Uddevalla municipality, Sweden.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: uddevallaenergi_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*

The property address, including the town, exactly as shown by the address
search on the Uddevalla Energi website.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: uddevallaenergi_se
      args:
        address: Fjällvägen 11, Ljungskile
```

## How to get the source argument

Visit the
[Uddevalla Energi waste collection page](https://www.uddevallaenergi.se/privat/sophamtning.html#Hamtningsdagar),
search for your property, and copy the complete suggested address, including
the town.
