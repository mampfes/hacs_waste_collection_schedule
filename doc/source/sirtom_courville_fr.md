# SIRTOM de Courville-sur-Eure

Support for schedules provided by [SIRTOM de Courville-sur-Eure](https://www.sirtom-courville.fr).

Source for the SIRTOM de Courville-sur-Eure (Eure-et-Loir), France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sirtom_courville_fr
      args:
        commune: COMMUNE
```

### Configuration Variables

**commune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sirtom_courville_fr
      args:
        commune: Fontaine-la-Guyon
```

## How to get the source arguments

Open https://www.sirtom-courville.fr/mes-dechets/jours-de-collecte/ and enter the name of your calendar as printed after 'Téléchargez le calendrier des collectes :', without the year, for example `Fontaine-la-Guyon`. Hamlets with their own calendar include it, for example `Digny – Les Hauts Cornets, La Gatine`.
