# Publidata — provider for waste management schedules

Support for schedules provided by [Publidata Canada] (https://www.publidata.ca).

They operate the schedules of at least the following communities:

  - Calixa-Lavallée
  - Contrecoeur
  - Saint-Amable
  - Sainte-Julie
  - Varennes
  - Verchères


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: publidata_ca
      args:
        address: "1580 Chem. du Fer-à-Cheval, Sainte-Julie, QC J3E 0A2"

```

### Configuration Variables

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: publidata_ca
      args:
        address: "1580 Chem. du Fer-à-Cheval, Sainte-Julie, QC J3E 0A2"
```


## How to ensure your address is valid

Go on the [MRC's website](https://margueritedyouville.ca/environnement/matieres-residuelles/tri-facile-pour-une-saine-gestion-de-vos-matieres-residuelles) and check how the autocomplete formats your address.
