# SUIBR

SUIBR (Stanser Umweltdienste Interkommunale Betriebsgemeinschaft) is the waste management service for the canton of Nidwalden, Switzerland. It serves 11 municipalities with waste collection schedules available through the kvvnw.sammelkalender.ch platform.

## Supported Municipalities

All 11 municipalities in the canton of Nidwalden:

- Beckenried
- Buochs
- Dallenwil
- Emmetten
- Ennetbürgen
- Ennetmoos
- Hergiswil
- Oberdorf
- Stans
- Stansstad
- Wolfenschiessen

## Configuration

| Parameter | Required | Description |
|-----------|----------|-------------|
| `municipality` | Yes | Name of the municipality (one of the 11 listed above) |
| `street` | No | Street name for more precise scheduling |
| `hnr` | No | House number |

## API

The source uses the kvvnw.sammelkalender.ch API:
- Municipality list: `https://www.kvvnw.sammelkalender.ch/kunden_WANN_auswahl_form.php?optGem=GEM`
- Street list: `https://www.kvvnw.sammelkalender.ch/kunden_WANN_auswahl_form.php?optGem=<id>&Jahr=`
- Collection data: `https://www.kvvnw.sammelkalender.ch/kunden_sammlung_ausw_cont.php`

## Waste Types

Common waste types returned by this source:
- `Kehricht` - General waste
- `Grüngut` - Organic waste
- `Karton` - Cardboard
- `Papier` - Paper
- `Alteisen/Metall` - Metal
- `Christbaum` - Christmas trees

## Links

- [SUIBR Website](https://www.suibr.ch)
- [Sammelkalender (Collection Calendar)](https://www.suibr.ch/online-services/sammelkalender/)
