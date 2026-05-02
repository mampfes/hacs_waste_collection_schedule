# Komunala Kranj

Support for schedules provided by [Komunala Kranj](https://www.komunala-kranj.si/).

## Configuration via `configuration.yaml`

```yaml
waste_collection_schedule:
    sources:
    - name: komunala_kranj_si
      args:
        address: "Rakovica 31, Rakovica"
```

### Configuration Variables

**address**
*(string) (required)*

Full address as accepted by the Komunala Kranj search (street name and house number). If the address lookup returns multiple
matches, refine the value until a single match is returned.
