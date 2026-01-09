# Roslagsvatten Sweden

Support for upcoming pick-ups provided by [Roslagsvatten self-service portal](https://roslagsvatten.se/hamtningsschema).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: roslagsvatten_se
      args:
        street_address: "YOUR_STREET_ADDRESS" # Formatted as: Streetname number, City
        municipality: "YOUR_MUNICIPALITY" # One of: osteraker, vaxholm, ekero
```

### Configuration Variables

**street_address**  
*(string) (required)*

**municipality**  
*(string) (required)* one of 

## Example

An example configuration:

```yaml
waste_collection_schedule:
  sources:
    - name: roslagsvatten_se
      args:
        street_address: "Andromedavägen 1, Åkersberga" 
        municipality: "osteraker"
```

