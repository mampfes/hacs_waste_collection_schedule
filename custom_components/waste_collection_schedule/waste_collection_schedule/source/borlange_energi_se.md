# Borlänge Energi

Waste collection schedule for Borlänge, Sweden

## Configuration

To use this integration, you need to provide your waste collection pickup address.

```yaml
waste_collection_schedule:
  sources:
    - name: borlange_energi_se
      args:
        pickup_address: PICKUP_ADDRESS
```

### Configuration Variables

**pickup_address**  
*(String) (required)*

### How to find your `pickup_address`

1. Visit the Borlänge Energi waste collection website:
   https://www.borlange-energi.se/avfall-och-atervinning/sophamtning

2. Enter your address in the address search field.

3. Use the address exactly as shown on the website, including correct spelling
   and house number (e.g. `Mats Knuts Väg 100`).

### Example YAML Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: borlange_energi_se
      args:
        pickup_address: "Mats Knuts Väg 100"
```
