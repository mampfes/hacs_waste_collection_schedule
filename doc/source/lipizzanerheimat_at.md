# Lipizzanerheimat APP

Support for schedules provided by the [Lipizzanerheimat APP](https://www.lipizzanerheimat.at/news/lag-news-detail?tx_news_pi1%5Baction%5D=detail&tx_news_pi1%5Bcontroller%5D=News&tx_news_pi1%5Bnews%5D=521&cHash=b979d9afeb84d16185624b20289747c8).

## Supported cities

<!--Begin of service section-->

| Town                        | Website                                                                |
| --------------------------- | ---------------------------------------------------------------------- |
| Bärnbach                    | [baernbach.gv.at](https://baernbach.gv.at/)                            |
| Edelschrott                 | [edelschrott.gv.at](https://www.edelschrott.gv.at/)                    |
| Geistthal-Södingberg        | [geistthal-soedingberg.at](https://geistthal-soedingberg.at/)          |
| Hirschegg-Pack              | [hirschegg-pack.gv.at](https://www.hirschegg-pack.gv.at/)              |
| Kainach                     | [kainach.at](https://www.kainach.at/)                                  |
| Köflach                     | [koeflach.at](https://www.koeflach.at/)                                |
| Krottendorf-Gaisfeld        | [krottendorf-gaisfeld.gv.at](https://www.krottendorf-gaisfeld.gv.at)   |
| Ligist                      | [ligist.gv.at](https://www.ligist.gv.at/)                              |
| Maria Lankowitz             | [maria-lankowitz.at](https://www.maria-lankowitz.at/)                  |
| Mooskirchen                 | [mooskirchen.at](https://www.mooskirchen.at/)                          |
| Rosental a.d Kainach        | [rosental-kainach.at](https://www.rosental-kainach.at/)                |
| Sankt Martin am Wöllmißberg | [st-martin-woellmissberg.gv.at](https://st-martin-woellmissberg.gv.at) |
| Söding-Sankt Johann         | [soeding-st-johann.gv.at](https://www.soeding-st-johann.gv.at/)        |
| Stallhofen                  | [stallhofen.gv.at](https://www.stallhofen.gv.at/)                      |
| Voitsberg                   | [voitsberg.gv.at](https://voitsberg.gv.at/)                            |

<!--End of service section-->

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lipizzanerheimat_at
      args:
        street: POST_CODE
        town: HOUSE_NAME
        map_name: HOUSE_NUMBER
        garbage_calendar_id: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### How to get configuration variables

Open the Lipizzanerheimat app, login or use guest mode, select your town, go to the garbage calendar view and select the street you want to get the garbage collection dates for. You can either provide the calendar name in the lower center, the street name and town as written in the dropdown or provide the garbage_calendar_id directly.

### Configuration Variables

**street**
_(string) (optional)_

This is required if you want to use address lookup. In this case "town" is also required. The street must be equal to the one in the app's dropdown menu.

**town**
_(string) (optional)_

This is required if you want to use address lookup. In this case "street" is also required.

**map_name**
_(string) (optional)_

This is required if you want to use the "map name" that you find in the lower center area. It might look like this: "8570 Voitsberg 2/3/5/32"

**garbage_calendar_id**
_(string) (optional)_

This is the only required field if you want to get your data by the garbage_calendar_id that you found programmatically.

## Example using map_name

```yaml
waste_collection_schedule:
  sources:
    - name: lipizzanerheimat_at
      args:
        map_name: '8570 Voitsberg 2/3/5/32'
```

## Example using Address lookup

```yaml
waste_collection_schedule:
  sources:
    - name: lipizzanerheimat_at
      args:
        street: Voitsberg
        town: Mühlgasse
```
