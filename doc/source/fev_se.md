# Falu Energi & Vatten (FEV)

Support for schedules provided by [Falu Energi & Vatten (FEV)](https://fev.se).

Source for Falu Energi & Vatten waste collection schedule, Falun, Sweden.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fev_se
      args:
        address: "R\xE5dmansv\xE4gen 3"
```

## How to get the source arguments

Go to https://fev.se/atervinning/sophamtning.html, search for your address and copy the street name and house number exactly as shown in the results, e.g. `Rådmansvägen 3`. The website only publishes the next two collections per waste type, so the interval between them is used to project further collections; shifts around holidays appear only once the website itself shows them.
