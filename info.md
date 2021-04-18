# Waste Collection Schedule

Waste Collection Schedule provides schedules from waste collection service providers to Home Assistant. Additionally, it supports schedules from generic ICS files which can be stored locally or fetched from a web site. There is a high flexibility in providing the information to be displayed.

## Examples

Per default (without further configuration), the time to the next collection will be shown in an [entity card](https://www.home-assistant.io/lovelace/entity/):

![Default Lovelace Card](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/default-entity.png)

You can also setup dedicated entities per waste type and show the schedule in various formats:

![Days to next collections](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/days-to-next-collections.png)
![Date of next collections](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/date-of-next-collections.png)
![Date and days to next collections](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/next-collections-date-and-days.png)

The information in the more-info popup can be displayed in different formats:

1. List of upcoming collections:

   ![More info: upcoming](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/more-info-upcoming.png)

2. List of waste types and collection date:

   ![Moe info: waste types](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/more-info-appointment-types.png)

[Button Card](https://github.com/custom-cards/button-card) can be used to create individual Lovelace cards:

![Button Card](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/button-cards.png)

## Documentation

- [Full Documentation](https://github.com/mampfes/hacs_waste_collection_schedule)

## Supported Service Providers

Currently the following service providers are supported:

### Australia

- [Brisbane City Council](./doc/source/brisbane_qld_gov_au.md)
- [The Hills Council, Sidney](./doc/source/thehills_nsw_gov_au.md)

### Germany

- [Abfall.IO / AbfallPlus.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_io.md)
- [Abfall_Kreis_Tuebingen.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_kreis_tuebingen_de.md)
- [AbfallNavi.de (RegioIT.de)](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfallnavi_de.md)
- [Abfallwirtschaft Stuttgart](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stuttgart_de.md)
- [AWBKoeln.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/awbkoeln_de.md)
- [BSR.de / Berliner Stadtreinigungsbetriebe](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/bsr_de.md)
- [Generic ICS / iCal File](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/ics.md)
- [Jumomind.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/jumomind_de.md)
- [Muellmax.de](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/muellmax_de.md)
- [Stadtreinigung.Hamburg](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/stadtreinigung_hamburg.md)
- [Abfallwirtschaft Zollernalbkreis](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/abfall_zollernalbkreis_de.md)
- [MyMuell App](./doc/source/jumomind_de.md)

### United States of America

- [PGH.ST](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/pgh_st.md)
- [Seattle Public Utilities](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/seattle_gov.md)
