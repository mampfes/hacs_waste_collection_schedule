# Angers Loire Métropole (ALM)

Support for schedules provided by [Open Data Angers)](https://data.angers.fr/pages/home/).

Datas are also used in Tri+ application from Angers Loire Métropole[link](https://www.angersloiremetropole.fr/mon-quotidien/gestion-des-dechets/la-collecte-des-dechets/index.html#c24663).

List of cities:
  - LES PONTS DE CE
  - SAINT BARTHELEMY D ANJOU
  - SAINT CLEMENT DE LA PLACE
  - SAINTE GEMMES SUR LOIRE
  - SAINT LAMBERT LA POTHERIE
  - SAINT LEGER DE LINIERES
  - SAINT-LEGER-DES-BOIS
  - SAINT MARTIN DU FOUILLOUX
  - LOIRE AUTHION
  - VERRIERES EN ANJOU
  - SARRIGNE
  - SAVENNIERES
  - SOULAINES SUR AUBANCE
  - SOULAIRE ET BOURG
  - TRELAZE
  - RIVES DU LOIR EN ANJOU
  - ANGERS
  - AVRILLE
  - BEAUCOUZE
  - BEHUARD
  - BOUCHEMAINE
  - BRIOLLAY
  - CANTENAY EPINARD
  - ECOUFLANT
  - ECUILLE
  - FENEU
  - LONGUENEE EN ANJOU
  - MONTREUIL JUIGNE
  - MURS ERIGNE
  - PELLOUAILLES LES VIGNES
  - LE PLESSIS GRAMMOIRE

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_angers_fr
      args:
        city: CITY
        typevoie: TYPE_VOIE
        address: ADDRESS
        num_voie: int
```

### Configuration Variables

**city**  
*(string) (required)*

**typevoie**  
*(string) (required)*

**address**  
*(string) (required)*

**num_voie**
*(int) (optional)*

### Example

```yaml
waste_collection_schedule:
  sources:
    - name: data_angers_fr
      args:
        city: ANGERS
        typevoie: RUE
        address: Jean Jaures
        num_voie: 7
```
