# Pointe-Claire (QC)

Waste collection schedules for the [City of Pointe-Claire](https://www.pointe-claire.ca), Québec, Canada.

Dates come from the iCal feed published by the city through its [Espace citoyen](https://espace.pointe-claire.ca) portal. <!-- codespell:ignore espace -->

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pointe_claire_qc_ca
      args:
        sector: SECTOR
```

### Configuration Variables

**SECTOR**
*(string) (required)*

Your collection sector — either `A` or `B`.

#### How do I find my sector?

Enter your address in the city's [address search tool](https://www.pointe-claire.ca/en/community-life/citizen-services/search-by-address). It shows your collection sector.

- **Sector A:** the entire area west of Saint-Jean Boulevard, and the entire area south of Highway 20.
- **Sector B:** north of Highway 20, east of Saint-Jean Boulevard and south of Hymus Boulevard.

The city's printable PDF calendars for each sector are on the [Collection Calendar and Sorting Guide](https://www.pointe-claire.ca/en/household-collections-and-residual-materials/collections/collection-calendar-and-sorting-guide) page.

## Collection Types

| Type | City feed title |
|------|-----------------|
| Household Waste | Déchets domestiques |
| Organic Waste | Matières organiques |
| Recyclables | Recyclage |
| Bulky Items | Encombrants |
| Leaf Collection | Feuilles |
| Christmas Tree Collection | Arbre de Noël |

Mattress and box-spring collections and Saturday ecocentre days appear on the city's PDF calendars but are not included in the city's iCal feed, so this source does not report them.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pointe_claire_qc_ca
      calendar_title: Pointe-Claire Waste Collection
      args:
        sector: A
```
