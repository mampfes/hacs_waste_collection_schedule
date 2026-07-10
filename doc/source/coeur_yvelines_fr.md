# Coeur d'Yvelines

Support for schedules provided by [Communauté de Communes Cœur d'Yvelines](https://www.coeur-yvelines.fr/environnement/calendriers-de-collecte-des-dechets/), serving french communes :

- Auteuil-le-Roi
- Autouillet
- Bazoches-sur-Guyonne
- Behoust
- Beynes
- Boissy-sans-Avoir
- Flexanville
- Galluis
- Gambais
- Garancières
- Goupillières
- Grosrouvre
- Jouars-Pontchartrain
- La Queue-lez-Yvelines
- Le Tremblay-sur-Mauldre
- Les Mesnuls
- Marcq
- Mareil-le-Guyon
- Méré
- Millemont
- Montfort-l'Amaury
- Neauphle-le-Château
- Neauphle-le-Vieux
- Saint-Germain-de-la-Grange
- Saint-Rémy-l'Honoré
- Saulx-Marchais
- Thiverval-Grignon
- Thoiry
- Vicq
- Villiers-le-Mahieu
- Villiers-Saint-Frédéric

Collection days on the source website are described as a weekday plus, in
some cases, a validity period or a short list of one-off dates (mostly for
bulky waste collections). A few communes describe an appointment-based
bulky-waste service instead of a fixed schedule; in that case no
"Encombrants" events are produced for that commune.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: coeur_yvelines_fr
      args:
        commune: <commune from the list>
```

### Configuration Variables

**commune**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: coeur_yvelines_fr
      args:
        commune: Jouars-Pontchartrain
```

## How to get the source argument

Use the commune list above or visit [https://www.coeur-yvelines.fr/environnement/calendriers-de-collecte-des-dechets/](https://www.coeur-yvelines.fr/environnement/calendriers-de-collecte-des-dechets/) and select your commune from the drop-down list.
