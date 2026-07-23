# Předměřice nad Labem

Support for waste collection schedules provided by [Předměřice nad Labem](https://www.predmericenl.cz/odpady), Czech Republic.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: predmerice_nad_labem_cz
```

### Configuration Variables

None. The schedule is village-wide, so this source takes no arguments.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: predmerice_nad_labem_cz
```

## Bin types returned

| Provider description       | Returned type              | Icon                     |
|----------------------------|----------------------------|--------------------------|
| Směsný komunální odpad     | Směsný komunální odpad     | `Icons.GENERAL_WASTE`    |
| Plasty                     | Plasty                     | `Icons.PLASTIC_PACKAGING`|
| Papír a lepenky            | Papír a lepenky            | `Icons.PAPER`            |
