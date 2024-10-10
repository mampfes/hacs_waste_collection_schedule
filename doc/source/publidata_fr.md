#publidata_fr.md
# Publidata — provider for waste management schedules

Support for schedules provided by [Publidata](https://www.publidata.io/fr/).

They operate the schedules of at least the following communities:

- GPSEO
- Orléans Métropole
- Tours métropole

A specific source is provided for GPSEO, Orléans Métropole and Tours Métropole. But you have the possibility to
use this generic implementation, the only additional information you need is your community’s "instance id".

Example about how to get it (for GPSEO, adapt with your community’s dedicated widget page):

- go to https://infos-dechets.gpseo.fr/
- provide a random address
- open your browser’s network inspector
- refresh the page
- filter the queries for "api.publidata"
- the first call should be something like https://api.publidata.io/v2/search?types[]=Platform::Services::AdministrativeProcedure&size=1000&instances[]=1294

In that case your instance ID is 1294.

If collection data is available for the address provided, it will return waste collection dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dechets_gpseo_fr
      args:
        address: "ADDRESS"
        insee_code: "INSEE_CODE"
        instance_id: 1294
```

### Configuration Variables

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: dechets_gpseo_fr
      args:
        address: 11 rue Jean Moulin
        insee_code: "78362"
        instance_id: 1294
```

## How to find the insee code of your town

You should find it very easily on google.

## How to ensure your address is valid

Go on [GPSEO’s website](https://dechets.gpseo.fr/) and check how the autocomplete formats your address.
