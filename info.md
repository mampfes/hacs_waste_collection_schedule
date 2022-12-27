<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Waste Collection Schedule
![hacs_badge](https://img.shields.io/badge/HACS-Default-orange)
![hacs installs](https://img.shields.io/endpoint.svg?url=https%3A%2F%2Flauwbier.nl%2Fhacs%2Fwaste_collection_schedule)
![Community Discussion](https://img.shields.io/badge/Home%20Assistant%20Community-Discussion-orange)

**A custom component for Home Assistant that retrieves waste collection schedules from a wide range of service providers.**

<img src="/images/wcs_animated.gif" alt="Waste Collection Schedule animation" title="Waste Collection Schedule" align="right" height="200" />
Waste collection schedules from service provider web sites are updated daily, derived from local ICS/iCal files, or generated from user-specified dates or regularly repeating date patterns. The Home Assistant built-in Calendar is automatically populated with schedules, and there is a high degree of flexibility in how information can be format and displayed in entity cards or pop-ups. The framework can easily be extended to support additional waste collection service providers, or other services which provide schedules.


## Supported Service Providers

| Country | Service Providers |
|--|--|
| Generic | ICS / iCal files |
| Static | User-defined dates or repeating date patterns |
| Australia | Banyule City Council, Belmont City Council, Brisbane City Council, Campbelltown City Council, City of Canada Bay Council, Inner West Council (NSW), Ku-ring-gai Council, Macedon Ranges Shire Council (Melbourne), Maroondah City Council, Melton City Council (Melbourne), Nillumbik Shire Council, North Adelaide Waste Management Authority (South Australia), RecycleSmart, Stonnington City Council (Melbourne), The Hills Council (Sydney), Wyndham City Council (Melbourne) |
| Austria | BMV, Data.Umweltprois, Korneuburg Stadtservice, WSZ-Moosburg |
| Belgium | Hyhea, Recycle! / RecycleApp |
| Canada | City of Toronto |
| Germany | Abfall.IO / AbfallPlus, AbfallNavi (RegioIT.de), Abfallkalender Würzburg, Abfalltermine Forchheim, Abfallwirtschaft Bremen, Abfallwirtschaft Landkreis Harburg, Abfallwirtschaft Landkreis Wolfenbüttel, Abfallwirtschaft Neckar-Odenwald-Kreis, Abfallwirtschaft Rendsburg, Abfallwirtschaft Stuttgart, Abfallwirtschaft Südholstein, Abfallwirtschaft Zollernalbkreis, Alb-Donau-Kreis, ART Trier, AWB Bad Kreuznach, AWB Esslingen, AWB Landkreis Ausburg, AWB Limburg-Weilburg, AWB Oldenburg, AWBKoeln, AWIDO-online, Berlin-Recycling, Bogenschuetz-Entsorgung, Biedenkopf MZF, BSR.de / Berliner Stadtreinigungsbetriebe, C-Trace, Cochem-Zell, EGN-Abfallkalender, Erlangen-Höchstadt, Jumomind, KAEV Niederlausitz, KWB-Goslar, KWU-Entsorgung, Landkreis-Wittmund, Landkreis Rhön Grabfeld, Landkreis Schwäbisch Hall, Muellmax, MyMuell App, Neunkirchen Siegerland, RegioEntsorgung, Rhein-Hunsrück Entsorgung (RHE), Sector27, Stadtreinigung Dresden, Stadtreinigung.Hamburg, Stadtreinigung-Leipzig, Stadt-Willich, StadtService Brühl, Städteservice Raunheim Rüsselsheim, Südbrandenburgischer Abfallzweckverband, Umweltbetrieb Stadt Bielefeld, WAS Wolfsburg, Wermeldkirchen, Zweckverband Abfallwirtschaft Werra-Meißner-Kreis |
| Lituania | Kauno švara |
| Netherlands | HVCGroep, Ximmio |
| New Zealand | Auckland, Christchurch, Gore, Invercargill & Shouthand, Horowhenua District, Wapia District, Wellington |
| Norway | Min Renovasjon, Oslo Kommune |
| Poland | Warsaw, Multiple Communities (Echoharmonogram) |
| Sweden | Lerum, Ronneby Miljöteknik, SSAM, Srvatervinning, Sysav, Vasyd |
| Switzerland | A-region, Lindau |
| USA | PGT.ST, Republic Services, Seattle Public Utilities |
| UK | Bracknell Forest Council, Bradford Metropolitan District Council, Braintree District Council, Cambridge City Council, Canterbury City Council, Cheshire East Council, Chesterfield Borough Council, Colchester Borough Council, Cornwall Council, Derby City Council, Eastbourne Borough Council, Elmbridge Borough Council, Guildford Borough Council, Harborough District Council, Huntingdonshire District Council, The Royal Borough of Kingston, Lewes District Council, London Borough of Lewisham, Manchester City Council, Newcastle City Council, North Somerset Council, Nottingham City Council, Peterborough City Council, Richmondshire District Council, Rushmoor Borough Council, Sheffield City Council, South Cambridgeshire District Council, South Norfolk and Broadland Council, Stevenage Borough Council, Tewkesbury Borough Council, City of York Council, Walsall Council, West Berkshire Council, Wiltshire Council |

For full details on supported service providers, and more project details, visit us on [GitHub](https://github.com/mampfes/hacs_waste_collection_schedule)
