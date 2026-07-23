# Älvsbyns Energi

Waste collection schedule for Älvsbyns Energi, Sweden.

## Configuration

Enter the street address and house number used for waste collection.

```yaml
waste_collection_schedule:
  sources:
    - name: alvsbyns_energi_se
      args:
        address: STREET_ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*

The street address and house number, for example `Storgatan 24`.

### How to find your address

1. Visit https://www.alvsbynsenergi.se/.
2. Find **Kolla din sophämtning**.
3. Enter your street and house number.
4. Use the address shown by the website's address search.

### Example YAML Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: alvsbyns_energi_se
      args:
        address: "Storgatan 24"
```
