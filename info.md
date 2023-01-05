<img src="https://raw.githubusercontent.com/mampfes/hacs_waste_collection_schedule/master/images/icon.png?raw=true" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Waste Collection Schedule

![hacs_badge](https://img.shields.io/badge/HACS-Default-orange) ![hacs installs](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fwaste_collection_schedule) [![Community Discussion](https://img.shields.io/badge/Home%20Assistant%20Community-Discussion-orange)](https://community.home-assistant.io/t/waste-collection-schedule-framework/186492)

**A custom component for Home Assistant that retrieves waste collection schedules from a wide range of service providers.**

<img src="https://raw.githubusercontent.com/mampfes/hacs_waste_collection_schedule/master/images/wcs_animated.gif" alt="Waste Collection Schedule animation" title="Waste Collection Schedule" align="right" height="200" />

Waste collection schedules from service provider web sites are updated daily, derived from local ICS/iCal files, or generated from user-specified dates or regularly repeating date patterns. The Home Assistant built-in Calendar is automatically populated with schedules, and there is a high degree of flexibility in how information can be format and displayed in entity cards or pop-ups. The framework can easily be extended to support additional waste collection service providers, or other services which provide schedules.

## Supported Service Providers

| Country | Service Providers |
|--|--|
| Generic | ICS / iCal files |
| Static | User-defined dates or repeating date patterns |<!--Begin of country section-->
| Australia | Banyule City Council, Belmont City Council, Brisbane City Council, Campbelltown City Council, City of Canada Bay Council, Gold Coast City Council, Inner West Council (NSW), Ipswich City Council, Ku-ring-gai Council, Macedon Ranges Shire Council, Maroondah City Council, Melton City Council, Nillumbik Shire Council, North Adelaide Waste Management Authority, RecycleSmart, Stonnington City Council, The Hills Shire Council, Sydney, Wyndham City Council, Melbourne |
| Austria | Burgenländischer Müllverband, infeo, Stadtservice Korneuburg, Umweltprofis, WSZ Moosburg |
| Belgium | Hygea, Recycle! |
| Canada | City of Toronto |
| Germany | Abfall Stuttgart, Abfall.IO / AbfallPlus, Abfallkalender Würzburg, AbfallNavi (RegioIT.de), Abfalltermine Forchheim, Abfallwirtschaft Alb-Donau-Kreis, Abfallwirtschaft Landkreis Harburg, Abfallwirtschaft Landkreis Wolfenbüttel, Abfallwirtschaft Neckar-Odenwald-Kreis, Abfallwirtschaft Nürnberger Land, Abfallwirtschaft Rendsburg, Abfallwirtschaft Südholstein, Abfallwirtschaft Werra-Meißner-Kreis, Abfallwirtschaft Zollernalbkreis, Abfallwirtschaftsbetrieb Esslingen, Abfallwirtschaftsbetrieb Landkreis Ahrweiler, ART Trier, AWB Bad Kreuznach, AWB Köln, AWB Landkreis Augsburg, AWB Oldenburg, AWIDO Online, Berlin Recycling, Berliner Stadtreinigungsbetriebe, Bielefeld, Bogenschütz Entsorgung, Bremener Stadreinigung, Bürgerportal, C-Trace, Dillingen Saar, EGN Abfallkalender, Jumomind, KAEV Niederlausitz, Kreiswirtschaftsbetriebe Goslar, KV Cochem-Zell, KWU Entsorgung Landkreis Oder-Spree, Landkreis Erlangen-Höchstadt, Landkreis Nordwestmecklenburg, Landkreis Rhön Grabfeld, Landkreis Schwäbisch Hall, Landkreis Wittmund, MZV Bidenkopf, Müllmax, Neunkirchen Siegerland, RegioEntsorgung Städteregion Aachen, Rhein-Hunsrück Entsorgung (RHE), Sector 27 - Datteln, Marl, Oer-Erkenschwick, Stadt Willich, Stadtreinigung Dresden, Stadtreinigung Hamburg, Stadtreinigung Leipzig, StadtService Brühl, Städteservice Raunheim Rüsselsheim, Südbrandenburgischer Abfallzweckverband, Wermelskirchen, Wolfsburger Abfallwirtschaft und Straßenreinigung, WZV Kreis Segeberg |
| Lithuania | Kauno švara |
| Netherlands | ACV Group, Alpen an den Rijn, Area Afval, Avalex, Avri, Bar Afvalbeheer, Circulus, Cyclus NV, Dar, Den Haag, GAD, Gemeente Almere, Gemeente Berkelland, Gemeente Cranendonck, Gemeente Hellendoorn, Gemeente Lingewaard, Gemeente Meppel, Gemeente Middelburg + Vlissingen, Gemeente Peel en Maas, Gemeente Schouwen-Duiveland, Gemeente Sudwest-Fryslan, Gemeente Venray, Gemeente Voorschoten, Gemeente Wallre, Gemeente Westland, HVC Groep, Meerlanden, Mijn Blink, PreZero, Purmerend, RAD BV, Reinigingsbedrijf Midden Nederland, Reinis, Spaarne Landen, Stadswerk 072, Twente Milieu, Waardlanden, Ximmio, ZRD |
| New Zealand | Auckland Council, Christchurch City Council, Gore, Invercargill & Southland, Horowhenua District Council, Waipa District Council, Wellington City Council |
| Norway | Min Renovasjon, Oslo Kommune |
| Poland | Ecoharmonogram, Warsaw |
| Sweden | Lerum Vatten och Avlopp, Ronneby Miljöteknik, SRV Återvinning, SSAM, Sysav Sophämntning, VA Syd Sophämntning |
| Switzerland | A-Region, Andwil, Appenzell, Berg, Bühler, Eggersriet, Gais, Gaiserwald, Goldach, Grub, Heiden, Herisau, Horn, Hundwil, Häggenschwil, Lindau, Lutzenberg, Muolen, Mörschwil, Rehetobel, Rorschach, Rorschacherberg, Schwellbrunn, Schönengrund, Speicher, Stein, Steinach, Teufen, Thal, Trogen, Tübach, Untereggen, Urnäsch, Wald, Waldkirch, Waldstatt, Wittenbach, Wolfhalden |
| United Kingdom | Ashfield District Council, Bracknell Forest Council, Bradford Metropolitan District Council, Braintree District Council, Breckland Council, Cambridge City Council, Canterbury City Council, Cheshire East Council, Chesterfield Borough Council, City of York Council, Colchester Borough Council, Cornwall Council, Derby City Council, Eastbourne Borough Council, Elmbridge Borough Council, Environment First, FCC Environment, Guildford Borough Council, Harborough District Council, Horsham District Council, Huntingdonshire District Council, Lewes District Council, London Borough of Lewisham, Manchester City Council, Middlesbrough Council, Newcastle City Council, North Somerset Council, Nottingham City Council, Peterborough City Council, Richmondshire District Council, Rushmoor Borough Council, Salford City Council, Sheffield City Council, South Cambridgeshire District Council, South Hams District Council, South Norfolk and Broadland Council, Stevenage Borough Council, Tewkesbury Borough Council, The Royal Borough of Kingston Council, Walsall Council, West Berkshire Council, West Devon Borough Council, Wiltshire Council |
| United States of America | City of Pittsburgh, Republic Services, Seattle Public Utilities |
<!--End of country section-->

For full details on supported service providers, and more project details, visit us on [GitHub](https://github.com/mampfes/hacs_waste_collection_schedule).
