# Vatten och Miljöresurs

Support for schedules provided by [Vatten och Miljöresurs](https://www.vattenmiljoresurs.se).

Source for Vatten och Miljöresurs waste collection in Jämtland, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vattenmiljoresurs_se
      args:
        municipality: MUNICIPALITY
        street_address: STREET_ADDRESS
```

### Configuration Variables

**municipality**  
*(string) (required)*

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vattenmiljoresurs_se
      args:
        municipality: bracke
        street_address: Hantverksgatan 25
```

## How to get the source arguments

Find your address on the provider website for your municipality and enter it exactly as shown (street name and number).
