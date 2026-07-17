# Falu Energi & Vatten (FEV)

Support for the waste collection schedule provided by [Falu Energi & Vatten](https://fev.se/) for addresses in Falun municipality, Sweden. Data is fetched from the address search widget on the "Sophämtning" (waste collection) page.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fev_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(String) (required)* — Street address including house number, exactly as it appears on fev.se, e.g. `Rådmansvägen 3`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fev_se
      args:
        address: Rådmansvägen 3
```

## How to get the source arguments

Go to [fev.se/atervinning/sophamtning.html](https://fev.se/atervinning/sophamtning.html), search for your address and copy the street name and house number exactly as shown in the results, e.g. `Rådmansvägen 3`.

## Notes

The website only publishes the next two occurrences ("next pickup" and "the one after") per container/waste type. This source measures the interval between those two dates and extrapolates further future collections at that same interval. Collection times may shift around holidays or route changes; such shifts are not reflected by this extrapolation until the website itself is updated.
