# Circular City

Support for schedules provided by [Circular City](https://circularcity.world).

Source for local authorities using the Circular City waste app.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: circularcity_world
      args:
        customer: CUSTOMER
        address: ADDRESS
```

### Configuration Variables

**customer**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: circularcity_world
      args:
        customer: lunel
        address: 50 Rue des Hauts de Boisseron 34160 Boisseron
```

## How to get the source arguments

Pick your authority's Circular City app as the customer and enter your address exactly as the app's address search suggests it, including postcode and town (e.g. '41 Place de la Mairie 34160 Saussines').
