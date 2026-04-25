# Changelog

All notable changes to this project will be documented in this file.

Releases are listed in reverse chronological order.

## [2.21.0] - 2026-04-26

### New Services

- added `abfall_io_graphql` for the abfall.io v3 GraphQL API (thanks @miggi92) (#3788)
- added `AchieveForms` service helper (7 UK council sources refactored to use it)
- added `WhitespaceWRP` service helper (3 UK council sources refactored to use it)
- added `FirmstepSelfService` service helper (2 UK council sources refactored to use it)

### Added Sources

- added Saver, Roosendaal / Halderberge / Bergen op Zoom / Rucphen / Zundert / Steenbergen / Woensdrecht, NL (#6137)
- added ASM Pavia, IT (#6138)
- added Saalfelden am Steinernen Meer, AT (#6136)
- added Gemeinde Würenlos, CH (ICS) (#6140)
- added Wieliczka, PL (thanks @uberberben) (#6132)
- added Willoughby City Council, NSW, AU (thanks @happygray) (#6130)
- added Richmond upon Thames, UK (thanks @jimmym101) (#6128)
- added Spelthorne Borough Council, UK (#6125)
- added Community Waste Disposal (CWD), North Texas, US (thanks @ppritcha) (#4913)
- added Bundaberg Regional Council, QLD, AU (#6124)
- added Hinckley & Bosworth, UK (thanks @JackMottershaw) (#6115)
- added Brandenburg an der Havel (ICS), DE (thanks @dt215git) (#6109)
- added Tower Hamlets, UK (thanks @jimmym101) (#6107)
- added Havant Borough Council, UK (thanks @stegzilla) (#6092)
- added Golden Plains Shire Council, VIC, AU (thanks @smaurer3) (#6085)
- added City of Boroondara, VIC, AU (#6079)
- added East Staffs, UK (thanks @dt215git) (#6074)
- added Glenorchy City Council, TAS, AU to Recycle Coach (#6126)
- added Woerden / Oudewater to ximmio_nl (#6103)
- added Bischofshofen and Bruck an der Mur to CitiesApps (#6098)
- added Büren an der Aare, Liestal, and Therwil to localcities_ch
- added Vänersborg (token auth) to avfallsapp_se (thanks @zer0coo) (#6070)

### Fixed Sources

- fixed potsdam_de: exception chain order, added type 7, JSON safety (thanks @johannesvedder) (#6134)
- updated Wermelskirchen to its new domain and ICS schedule (thanks @crosserSniper) (#6131)
- fixed exeter_gov_uk: handle dates without comma and `<img>` in `<h3>` (#6127)
- fixed sector27_de: use first word of street as search prefix (#6123)
- fixed innherredrenovasjon_no: use curl_cffi to bypass Cloudflare (#6122)
- fixed winterthur_ch: update street lookup to new API endpoint (#6121)
- fixed geelongaustralia_com_au: follow domain redirect for POST request (#6120)
- fixed avfallsapp_se: typo Vänerborg → Vänersborg, removed unsupported `sv` language (#6119)
- fixed iris_salten_no (thanks @p-t-e-r) (#6102)
- fixed arun_gov_uk: ICON_MAP order (thanks @whi-tw) (#6099)
- fixed tewkesbury_gov_uk: handle API response without status field (thanks @davewins) (#6094)
- fixed toogoodtowaste_co_nz: Cloudflare-aware session flow and explicit API error paths (#6075)
- fixed barrie_ca: form submit (thanks @mroote) (#6095)
- fixed Overath: migrated from c_trace_de to abfallnavi_de (bav) (#6086)
- fixed abfall_io: removed migrated test cases, improved 401 error message (#6084)
- fixed junker_app: removed Veritas Spa (no longer served) (#6082)
- fixed e_lindsey_gov_uk: updated for changed form API (#6081)
- fixed kiedysmieci_info: validate district/municipality via streets endpoint (#6066)
- removed Ortenaukreis from abfall_io listings (now use app_abfallplus_de) (#6139)

### Removed Sources

- removed Białogard from ecoharmonogram_pl (no longer uses the platform) (thanks @kfulko) (#6089)

### Documentation

- listed Upper Austria municipalities for gem2go (#6101)
- listed Vorarlberg municipalities for Umweltv (zerowaste.io) (#6100)
- added Grey Highlands ON and Spruce Grove AB to ReCollect (#6104)
- added Community Recycling (Lunenburg, NS) and Colchester, NS to ReCollect (#6097)
- added Vafab Miljö to provider list (thanks @progtologist) (#6093)
- documented all burgerportaal_nl supported operators (#6096)
- migrated docs/examples to non-deprecated `waste_collection_schedule.sensors` YAML structure (#6064)

### Improvements

- exposed ICS `LOCATION` and `DESCRIPTION` on `Collection` (thanks @sneumeister) (#5930)
- expanded French (`fr`) defaults in `DEFAULT_PARAM_TRANSLATIONS` for common params (thanks @costajohnt) (#6087)
- added Lillehammer test case to minrenovasjon_no (#6106)
- added Tarnowskie Góry test case to ecoharmonogram_pl (#6105)
- added "Aare" to codespell ignore list (#6080)

### Tooling

- auto-generate documentation via CI on merge instead of requiring contributors to run `update_docu_links.py` themselves (#5901)

## [2.20.0] - 2026-04-19

### Added Sources

- added Epping Forest District Council, Essex, UK (#6058)
- added Muswellbrook Shire Council, NSW, AU (#6056)
- added City of South Perth, WA, AU (thanks @dt215git) (#6043)
- added London Borough of Lambeth, UK (thanks @jimmym101) (#6054)
- added East Lindsey District Council, UK (#6049)
- added Tonnenticker Pro (RegioIT) for Kreis Warendorf / Kreis Gütersloh, DE (#6047)
- added MSVA.se, SE (thanks @Cheezi747) (#6044)
- added Mijnafvalzaken.nl, NL (thanks @kay1010100) (#6011)
- added Clarence Valley Council, NSW, AU (thanks @dt215git) (#6029)
- added London Borough of Southwark, UK (thanks @cunners) (#6027)
- added Gosport Borough Council, UK (#6028)
- added Stadtgemeinde Klosterneuburg, AT (#6025)
- added Ecolan Lanciano (ICS), IT (#6019)
- added City of Barrie, Ontario, CA (#6015)
- added Enfield Council, UK (thanks @armaneshaghi) (#6013)
- added Sunbury, OH, US (thanks @dt215git) (#6012)
- added Marktgemeinde Eggelsberg, AT (#5984)
- added London Borough of Barnet, UK (thanks @cunners) (#5981)
- added 123abfallkalender.de for Ebsdorfergrund, DE (thanks @Erik-Donath) (#6034)
- added LaSalle, ON to Recycle Coach (#6024)
- added Plainville, CT to Recycle Coach (#6023)
- added Kelowna, BC to Recycle Coach (#6022)
- added NET SpA Udine to Junker APP (#5987)
- added Rogue Disposal & Recycling, Medford OR to ReCollect (#6048)

### Fixed Sources

- fixed ccc_govt_nz: overrides and loop limit (thanks @camcamnz) (#6045)
- fixed ICS: handle truncated DTSTART/DTEND with missing time after 'T' (#6046)
- fixed Sammelkalender, CH: after website update (thanks @JonasArnold) (#5213)
- fixed avfallsor_no: updated to new collection JSON API (thanks @Wuerger) (#6037)
- fixed Ressourceindsamling.dk: wrong schedule date (thanks @mbendtsen) (#6038)
- fixed ZKE Saarbrücken, DE: type filtering broken by trailing whitespace (#6018)
- fixed Thanet District Council, UK: bypass Cloudflare (#6017)
- fixed irenambiente_it: fortnightly schedule not being applied (#6016)
- fixed RegioEntsorgung, DE: street matching for whitespace variants (thanks @taker218) (#6004)
- fixed hvcgroep, NL: house_letter matching, added Hoorn test case (#5998)
- fixed North Norfolk, UK: website journey flow change (#5996)
- fixed Northern Beaches, NSW, AU: fortnightly alternation using ISO week number (#5995)
- fixed Newham, UK: date parsing after website format change (#5988)
- fixed Hastings Borough Council, UK: updated API URL (thanks @Demarcation) (#6006)
- fixed Richmondshire, UK: updated source (thanks @wozza999) (#6003)
- fixed Teignbridge, UK: switched to curl_cffi to bypass TLS fingerprinting (thanks @davewins) (#6000)
- fixed Stirling, UK: added address geocoding support (#5982)

### Removed Sources

- removed Linköping - Tekniska Verken, SE: provider removed public access (#6057)

### Improvements

- fixed bare Exception raises to use SourceArgument* exceptions (#6042)
- removed duplicate collection dates for Wakefield, UK (thanks @aboillat) (#6009)
- fixed CRLF line endings in update_docu_links.py output on Windows (#6014)
- enforced LF line endings across all platforms via .gitattributes (#5983)
- improved issue templates, added auto-labelling workflow (#5991)

## [2.19.0] - 2026-04-13

### New Services

- added ArcGIS REST API service for spatial queries and geocoding (#5954)
- added IntraMaps service for Australian council spatial queries (#5936)
- added Pozi GIS service for GeoJSON zone lookups and WFS spatial queries (#5980)

### Added Sources

- added Ballina Shire Council, NSW, AU (thanks @thazza) (#5869)
- added Byron Shire Council, NSW, AU (thanks @thazza) (#5869)
- added Mole Valley District Council, UK (thanks @elyobelyob) (#5889)
- added Métropole de Lyon, FR (thanks @babatoko) (#5887)
- added Grand Besançon Métropole, FR (thanks @babatoko) (#5903)
- added NSR (Nordvästra Skånes Renhållnings AB), SE (thanks @dt215git) (#5910)
- added SUM Avfall (Sunnfjord og Ytre Sogn Miljøverk IKS), NO (thanks @Ziggiz) (#5907)
- added ZVO Ostholstein, DE (thanks @dt215git) (#5913)
- added SAB Magdeburg, DE (thanks @Habile2019) (#5915)
- added Lane Cove Council, NSW, AU (#5922)
- added City of Tea Tree Gully, SA, AU (#5923)
- added City of Melville, WA, AU (#5924)
- added City of Swan, WA, AU (#5925)
- added Rohrbach an der Lafnitz, AT (thanks @textbookcal) (#5927)
- added Fraser Coast Regional Council, QLD, AU (#5936)
- added City of Kwinana, WA, AU (#5938)
- added Brimbank City Council, VIC, AU (thanks @dt215git) (#5950)
- added Rybnik, PL (thanks @matfiz) (#5948)
- added Warrnambool City Council, VIC, AU (#5952)
- added City of Bayswater, WA, AU (#5953)
- added Town of Bassendean, WA, AU (#5954)
- added Northville Township, MI, US (#5955)
- added Hoover, AL, US (#5956)
- added Launceston City Council, TAS, AU (#5957)
- added Rochester, NY, US (#5959)
- added City of Newcastle, NSW, AU (#5975)
- added City of Vincent, WA, AU (#5980)

### Fixed Sources

- fixed Hounslow, UK: new website (thanks @kiranbhakre) (#5879)
- fixed Blaby, UK: Food waste icon casing (thanks @dt215git) (#5880)
- fixed publidata_fr: IndexError on empty geocoder results (#5896)
- fixed Northern Beaches, AU: A/B zone fortnightly alternation (#5897)
- fixed Banyule, VIC, AU: bypass Incapsula bot protection via curl_cffi (#5905)
- fixed irenambiente_it: holidays with no replacement date (#5911)
- fixed portenf_sa_gov_au: crash on single-month calendar (#5918)
- fixed cardinia_vic_gov_au: crash on empty geocoder results (#5919)
- fixed moorabool_vic_gov_au: API blocking, wrong test cases, missing icon (#5920)
- fixed ecoharmonogram_pl: crash on mixed street sides with no matchers (thanks @czeslavo) (#5934)
- fixed wyreforestdc_gov_uk: value on current collection day (thanks @MeltonCG) (#5947)
- fixed westsuffolk_gov_uk: 404 (#5942)
- fixed config flow: wrong docs for ICS sources (#5965)
- fixed Armadale, WA, AU: updated to new API (#5940)

### Expanded Existing Sources

- updated FES Frankfurt to new frankfurtplus.de URL and format (#5899)
- added generic localcities.ch source, deprecates grenchen_ch (#5902)
- updated telge_se: distinguish kärl 1/kärl 2 as separate waste types (thanks @krissen) (#5871)
- added Pointe-Claire, QC Sector A and B (thanks @jordanconway) (#5891)
- added SIVOM Rive Droite to publidata_fr (#5921)
- added Wangen bei Olten to localcities_ch (#5942)
- migrated Reinis from Ximmio to Opzet/hvcgroep_nl (#5941)
- updated hvcgroep_nl (thanks @kay1010100) (#5971)
- updated EGLZ URLs (#5966)
- updated Stirling Council, UK (#5976)
- added jumomind_de warning when street spans multiple collection zones (#5949)

### ICS Additions

- added Erkelenz waste collection calendar (#5967)
- added WBL Lünen (DE) and Georgina, ON (CA) (#5900)
- added City of Lowell, MA to ReCollect (#5904)
- added Medicine Hat, AB, CA (#5970)

### Refactored

- refactored Bayside and Waipa to use IntraMaps service (#5937, #5939)
- refactored Frankston and Bendigo to use Pozi service (#5980)

### Removed

- removed regioentsorgung_de: backend dead (#5945)
- removed Gütersloh (Stadt) gt2 from AbfallNavi: dead (#5895)

### Documentation

- fixed mitchellshire_vic_gov_au parameter name (#5873)
- removed outdated Known Issues section from README (#5898)

## [2.18.0] - 2026-04-08

### Added Sources

- added Grenchen (CH) via localcities.ch (#5868)
- added Teignbridge District Council, UK (thanks @mediastreet for API investigation) (#5865)
- added Greater Dandenong City Council, VIC, AU (#5864)
- added Telge Återvinning (telge.se), SE (#5866)
- added Medway Council, UK (thanks @TecharyJames) (#5829)
- added Manningham City Council, VIC, AU (thanks @paul256) (#5823)
- added Mitchell Shire Council, VIC, AU (#5828)

### Fixed Sources

- fixed Dudley Council, UK: rewrite for new Granicus/AchieveForms platform (thanks @ribz for finding the API) (#5859)
- fixed Victoria Park, WA, AU: rewrite for new FOGO calendar system (#5860)
- fixed West Berkshire Council, UK: date parsing bug when SubText non-empty (#5856)
- fixed Sutton Council, UK: switch to curl_cffi to bypass bot protection (#5855)
- fixed Newham, UK: disable SSL verification for broken certificate chain (#5854)
- fixed AppAbfallplusDe: fall back to "Alle Hausnummern" when house number not found (#5858)
- fixed Blackpool Council, UK: add Food Caddy support for new collection type (#5863)
- fixed Landkreis Rostock: add Güstrow street support (#5867)
- fixed calendar: compare dates instead of datetimes so today's all-day events are not dropped (#5853)

### Expanded Existing Sources

- added Orillia (ON) to Recycle Coach, replacing old orillia_ca source (#5857)
- added Faaborg (FFV) to Affaldonline (thanks @nicolaibvm) (#5862)
- added Buchegg (SO) waste paper (Altpapier) collection (#5830)

### Documentation

- fixed regex in Landkreis Amberg-Sulzbach ICS doc examples (#5861)

## [2.17.0] - 2026-04-07

### Added Sources

- added Chorley Council, UK (thanks @jordanbruce1991-afk for investigation) (#5846)
- added MZV Hegau, DE (#5847)
- added Lismore City Council, NSW, AU (thanks @thazza) (#5827)
- added Luxembourg / Mäin Offall (thanks @fuatakgun) (#5826)
- added Bolsover District Council, UK (#5818)

### Fixed Sources

- fixed Wirral Council, UK: rewrite for new website (thanks @SolutechUK for investigation) (#5843)
- fixed Müllmax: auto-detect and match house number selection (thanks @SheepHead1988 for repro details) (#5838)
- fixed AbfallNavi: use shared domain for services with dead per-service subdomains (#5841)
- fixed Blackpool Council, UK: crash on unrecognised job names (#5844)
- fixed publidata_fr: instance_id type handling in config flow (#5845)
- fixed Oxford City Council: broken by seasonal banner (thanks @rbrunt) (#5837)
- fixed Torridge: handle parenthetical annotations in date strings (#5816)
- fixed Blackpool: regex fails on 'Paper & Card' job names (#5817)
- fixed EVV Völklingen: duplicated paper collection dates (thanks @Synthenses) (#5831)

### New ICS Sources

- added ENNI Energie & Umwelt Niederrhein (Moers), DE (thanks @nszkl29 for finding ICS endpoint) (#5842)
- added Gossau ZH, CH (#5848)

### Expanded Existing Sources

- added Landkreis Oldenburg to Abfall.IO source (#5849)

### Other

- improved ICS source GUI defaults and howto text (#5819)

## [2.16.0] - 2026-04-06

### Added Sources

- added Entsorgungsverband Völklingen (EVV), Saarland, DE (thanks @Synthenses) (#5812)
- added SmiecioPlan.pl (Szczecin, Gdańsk, Gdynia, Sopot), PL (#5813)
- added North Yorkshire Council - Craven, UK (thanks @Jakmg) (#5810)
- added Basel-Stadt (data.bs.ch), CH (#5807)
- added Gemeinde24, AT (thanks @svenbla) (#5799)
- added Buchegg (Solothurn), CH (thanks @CRZTFR) (#5791)

### Fixed Sources

- fixed frwa_com_au: use regex for ajax_nonce after website redesign (#5800)
- fixed ximmio/mijnblink: use correct Service URL (#5795)
- fixed publidata_fr: add optional public_type parameter for housing type filtering (#5814)

### New ICS Sources

- added Vlotho, DE (#5811)
- added Eupen (Oberstadt, Unterstadt, Kettenis), BE (#5804)

### Expanded Existing Sources

- added Landkreis Lichtenfels to AWIDO source (#5801)
- added CA Saint Germain Boucles de Seine to Publidata source (#5809)
- added Wöllersdorf-Steinabrückl to CITIES App source (#5806)
- added BAT Tilburg, Groningen, and Utrecht to BurgerPortaal source (#5805)

## [2.15.0] - 2026-04-05

### Core Changes

- Fix reconfigure wiping existing sensor and customization options (#5772)
- Fix ICS recurrence exceptions showing "None" as waste type (#5783)

### Added Sources

- added Kolding Kommune, DK (thanks @kongsted) (#5763)
- added Canterbury-Bankstown Council, NSW, AU (thanks @mmarquar) (#4974)
- added Québec city, QC, CA (thanks @louim) (#4038)
- added Kungälvs kommun, SE (thanks @MattiasC) (#5291)
- added Roslagsvatten (Österåker, Vaxholm, Ekerö), SE (thanks @taxx) (#5323)
- added Lipizzanerheimat App (15 Styrian municipalities), AT (thanks @wehrmannit) (#3411)
- added Gössendorf, Styria, AT (thanks @DaHofa02) (#4707)
- added Värmdo kommun, SE (thanks @fatuuse) (#4369)

### Fixed Sources

- fixed Oklahoma City: major rewrite supporting official and unofficial APIs (thanks @totallydifferent) (#5507)
- fixed Fylde, UK: migrated to new authenticated waste portal (thanks @j-webb) (#5300)
- fixed publidata_fr: handle malformed multi-date opening_hours (thanks @icarius) (#5758)
- fixed ecoharmonogram_pl: add Rzeszów support, improve house number matching (thanks @wszybisty) (#5757)
- fixed Hornsby Shire Council, AU: parse dates from HTML, update PDF URL patterns (#5779)
- fixed South Staffordshire Council, UK: website redesign (#5773)

### New ICS Sources

- added Dětmarovice (part Glembovec), CZ (thanks @aleswita) (#5231)
- added Abfallwirtschaft Ortenaukreis, DE (#5786)
- added Publicus d.o.o. (Kamnik, Komenda, Pivka, Postojna), SI (#5789)
- added Sacramento County, CA to ReCollect (#5780)
- added Markham, ON; Muskoka District, ON; St Clair Township, ON; Castlegar, BC to ReCollect (#5788)
- added Durham Region, ON; City of Kingston, ON; City of Guelph, ON to ReCollect (#5790)

### Documentation

- fixed Valorlux docs: parameter is `commune`, not `city` (#5785)
- fixed Müllmax docs: clarify street name only, no house numbers (#5784)
- documented Hume City Council waste type name changes (#5781)
- updated AWP Pfaffenhofen URL (#5787)

## [2.14.0] - 2026-04-04

### Core Changes

- Add sensor discovery support and deprecate legacy sensor platform (#5746)
- Fix generated translation placeholder mismatches across locales (#5751)

### Added Sources

- added Northern Beaches Council, NSW, AU (thanks @CRZTFR) (#5708)
- added Kempsey Shire Council, NSW, AU (thanks @MtnDrew94) (#5622)
- added Western Bay of Plenty District Council, NZ (thanks @samwalshnz) (#5612)
- added OZO Ostrava, CZ (thanks @viki-vavrik) (#5220)
- added Obdach, Styria, AT (thanks @DaHofa02) (#4706)
- added Wolverhampton City Council, UK (thanks @ed-tt) (#3907)

### Fixed Sources

- fixed Wanneroo, WA, AU: updated URLs, session handling, and parsing for API changes (thanks @BrunoCQ) (#5611)
- fixed aw_harburg_de, DE: normalize "Gelber Sack" to "Gelbe Tonne" and harden district matching (thanks @strausmann) (#5569)
- fixed Arun District Council, UK: migrated to shared Cloud9 API service (thanks @whi-tw) (#5548)
- fixed Philadelphia, US: cancel secondary pickup in holiday week (thanks @mseltzer94) (#5511)
- fixed Blaby District Council, UK: updated to new endpoint, switched to curl_cffi (thanks @textbookcal) (#5424)
- fixed Ards and North Down, UK: switched to SVG fill color parsing (thanks @dansollok) (#4605)
- fixed Bisamberg calendar example in umweltverbaende_at docs (#5755)

### New ICS Sources

- added Gemeente Venray, NL
- added VUE Waltrop, DE
- added abfall_export.php (vCal) municipalities, DE
- added EAW Sangerhausen (Gemos), DE
- added gem2go (Abfallverband), AT
- added EAW Rheingau-Taunus-Kreis, DE
- added Ginsheim-Gustavsburg (gigu.de), DE
- added mopage.ch (Wiedlisbach), CH
- added Ranstadt (AMBnet), DE
- added Rivière-Beaudette, CA
- added City of Windsor, CA
- added Gemeente Borsele, NL
- added Neuenrade, DE
- added Stallhofen, AT
- added Stadtwerke Bergheim, DE
- added Abfall Lippe, DE
- added Knittel Entsorgung Nersingen, DE
- added Landkreis Holzminden (Abfall App), DE
- added Bruchsal (Schlaue Blaue Tonne), DE
- added Denver (ReCollect), US
- added Saint-Nicolas (Ville de Lévis), CA
- added EVA Abfallentsorgung (Hohenpeissenberg, Peissenberg), DE
- added Burnaby, BC, CA (RecycleCoach)

## [2.13.0] - 2026-04-03

## Core Changes

- **Replace cloudscraper with curl_cffi**: Switched anti-bot scraping library from cloudscraper to curl_cffi with Chrome impersonation across 10+ sources for improved reliability (#5720)
- Fixed AttributeError on startup when YAML_CONFIG is absent from hass.data (#5701)
- Fixed translation placeholder mismatch causing HA startup errors for Bridgend, Cumberland, and Dartford sources (#5700)
- Replaced PyMuPDF with pdfminer.six/pypdf for PDF extraction to fix aarch64 installation failures (#5710)

## Added Sources

- added City of Kalamunda, WA, AU (thanks @Brodiemm) (#5566)
- added Watford Borough Council, UK (thanks @Cironni) (#5629)
- added City of Moonee Valley, VIC, AU (thanks @mvandersteen) (#5285)
- added Midlothian Council, Scotland, UK (thanks @vivekxp) (#5640)
- added Memotri - Agglomeration Pau Bearn Pyrenees, FR (thanks @vchatela) (#5620)

## Fixed Sources

- fixed Muellmax, DE: restored two-step street search, fixed session handling and duplicate key issues (#5702)
- fixed Rushcliffe, UK: handle address list format change and POST_ARGS mutation (#5672, #5717)
- fixed Gateshead, UK: 403 error resolved by switching to curl_cffi (#5706)
- fixed South Kesteven, UK: updated to use current selfservice endpoint (thanks @CraigBell) (#5505)
- fixed Christchurch (ccc_govt_nz), NZ: stale API dates causing missing collections (#5645)
- fixed Grafikai Svara, LT: GUI config returning empty response (#5646)
- fixed AHK Heidekreis, DE: handle API field name changes robustly (#5692)
- fixed Tauranga, NZ: updated API URLs and improved form field discovery (thanks @samwalshnz) (#5610)
- fixed Melton, VIC, AU: refactored date parsing and validation (thanks @viperaus) (#5715)
- fixed Umweltverbände (Gänserndorf), AT: fix street filtering and centralize filter keys (thanks @zaubara) (#5689)
- fixed Lumire, SE: API fix (thanks @chex7) (#5332)

## Improved Sources

- improved AWIDO, DE: added location and time attributes for Schadstoffmobil events (#5685)
- improved EcoHarmonogram, PL: added configurable language parameter (#5649)
- improved Wealden, UK: added food waste collections (thanks @ryanbdclark) (#5688)
- improved mijnblink/HVCGroep, NL: moved to Ximmio service (thanks @xesxen) (#5707)

## New Contributors

Welcome to the following first-time contributors! :tada:

@Brodiemm, @chex7, @Cironni, @CraigBell, @mvandersteen, @ryanbdclark, @samwalshnz, @vchatela, @vivekxp, @viperaus, @xesxen, @zaubara




## [2.12.1] - 2026-04-01

## Fixed

- **Remove PyMuPDF from global manifest requirements** — PyMuPDF failed to install on aarch64 platforms, which caused the entire integration to fail to load even for users who don't use the Hornsby Shire source. It is now lazily imported only when needed. (#5686)
- **Horsham District Council, UK**: Updated parser for website changes and added support for new food waste bins (thanks @mystcb) (#5683)

## New Contributors

Welcome to the following first-time contributor! :tada:

@mystcb




## [2.12.0] - 2026-04-01

## Breaking Changes

- **alw_wf_de removed**: GUI configurations will be automatically migrated to `jumomind_de`. YAML configurations need to manually migrate to `jumomind_de` with `service_id: wol`, renaming `ort` → `city` and `strasse` → `street`.
- **afvalstoffendienst_nl**: The `region` argument has been removed. GUI configurations will be migrated automatically. YAML users should remove the `region` parameter.

## Core Changes

- Fix blocking call to `import_module` in event loop for Python 3.14 / HA 2026.x compatibility
- Pre-import platforms in parallel to avoid blocking I/O in the event loop
- Config flow now pre-loads `sources.json` and `source_metadata.json` at module level for improved performance
- Add description placeholders for hassfest compliance (thanks @bbr111)
- Add CADDY BIN to ICON_MAP (thanks @aaroncurrington)
- Config minor version bumped to 13

## Added Sources

- added AWB Ammerland, DE (thanks @sascha-hemi)
- added Abfallwirtschaft Wiener Neustadt, AT (thanks @mindestens)
- added Bad Aussee, AT (thanks @Grisly00)
- added Bayside Council, Victoria, AU (thanks @StephenGoodall)
- added Belfast City Council, UK (thanks @Leeoc)
- added Borlänge Energi, SE (thanks @bbr111)
- added City of San Antonio, TX, USA (thanks @joshrmcdaniel)
- added City of Subiaco, WA, AU (thanks @elSpike)
- added FRWA (Victor Harbor), AU (thanks @dt215git)
- added GYHG, HU (thanks @soosp)
- added Heinz Entsorgung, DE (thanks @tsgoff)
- added Lázně Bohdaneč, CZ (thanks @djz88)
- added Liverpool City Council, NSW, AU (thanks @qkevinto)
- added City of Łódź, PL (thanks @Krecikkko)
- added Mid Devon, UK (thanks @niallrobinson)
- added MidCoast Council, NSW, AU (thanks @sh00t2kill)
- added Monmouthshire, UK (thanks @Dukeicon)
- added Mornington Peninsula Shire Council, VIC, AU (thanks @tbham)
- added Murray (Shire of), WA, AU (thanks @mattaustin)
- added Mustankorkea, FI (thanks @vhtkrk)
- added Oak Bay, BC, CA (thanks @MartyTremblay)
- added PreZero Bad Oeynhausen, DE (thanks @deankannenberg)
- added RessourceIndsamling, DK (thanks @mbendtsen)
- added Rockingham, WA, AU (thanks @Haych)
- added Sandwell Metropolitan Borough Council, UK (thanks @MrLyallCSIT)
- added St Helens, UK (thanks @gary-dickenson)
- added Stadtreinigung Gießen, DE (thanks @stanislavhannes)
- added Wandsworth Council, UK (thanks @Dukeicon)
- added Woollahra, NSW, AU (thanks @sh00t2kill)
- added Gemeinde Kranenburg to AbfallNavi, DE (thanks @bbr111)
- added LK Ebersberg municipalities to AWIDO, DE (thanks @FaserF)
- added Lancaster (UK) food waste collection (thanks @WillFantom)
- added Southampton food waste, UK (thanks @Wardy930)
- added Huntingdon food service, UK (thanks @johnnieblows)
- added BSR Christmas trees waste category, DE (thanks @tr4nt0r)
- added Valcobreizh to Publidata, FR (thanks @vinzd)
- added West Lindsey orange food waste, UK (thanks @bencope)

## Fixed Sources

- fixed afvalstoffendienst_nl: now uses correct API (thanks @nnielzz)
- fixed AHA Region, DE: special collection date naming (thanks @CiptaK)
- fixed Bath & North East Somerset (BANES), UK: updated to new API (thanks @trvrnrth)
- fixed Bedford Borough Council (formerly Ashfield), UK (thanks @ConfusedTA, @aaroncurrington)
- fixed Bendigo, AU: updated for API changes (thanks @iSnackTwoPointOh)
- fixed Binzone, UK: 403 error (thanks @matejkramny)
- fixed Bolton, UK: switched to verintcloudservices.com API (thanks @chartionic)
- fixed Calgary, CA: datetime parsing (thanks @D-Jeffrey)
- fixed Chichester, UK (thanks @5ila5)
- fixed Coburg (CEB), DE: parse dates from new ICS calendar (thanks @bbr111)
- fixed Coventry, UK (thanks @tymscar, @JustinWingChungHui)
- fixed Croydon, UK (thanks @dt215git)
- fixed Cumberland, UK (thanks @dt215git)
- fixed Dacorum, UK (thanks @dt215git)
- fixed Gateshead, UK (thanks @06benste)
- fixed Gmina Zgierz, PL: updated API URL for 2026 (thanks @Krecikkko)
- fixed Greenwich, UK: holidays parsing (thanks @timocov)
- fixed Hornsby Shire, NSW, AU (thanks @jourdant)
- fixed Hume City Council, VIC, AU (thanks @seedzero)
- fixed Jumomind, DE: improved street matching and accept encoding (thanks @5ila5, @Borderlane-HA)
- fixed Maidstone, UK: holiday duplicates and inactive service filtering (thanks @ArronTay)
- fixed MAGS, DE: updated API URL (thanks @chris3600410)
- fixed Mid Sussex, UK (thanks @Gdkkauowj33)
- fixed MZV Rotenburg/Bebra, DE: route filtering and ICS parsing (thanks @bbr111)
- fixed Neath Port Talbot, UK: updated base URL (thanks @ashkjc)
- fixed Norwich City Council, UK: new data provider (thanks @carrgilson)
- fixed OLO, SK: 4-week cycle pattern calculation (thanks @vaind)
- fixed Oslo Kommune, NO: updated to new API endpoint (thanks @Olen)
- fixed Örebro, SE: updated address search URL (thanks @joshua2a)
- fixed Philadelphia, US: recycling and holiday logic (thanks @flyingsubs)
- fixed Publidata, FR: missing 'bio' waste type mapping (thanks @klsx0)
- fixed Redbridge, UK: new PDF format parser and empty collection handling (thanks @bbodien, @ryanwr)
- fixed Renfrewshire Council, UK (thanks @JamiePhonic)
- fixed Rochdale Council, UK (thanks @tmwrrn)
- fixed Rudna, CZ: new service provider (thanks @danoh)
- fixed Rushcliffe, UK: handle multiple collection dates per bin row (thanks @ribz)
- fixed Rushmoor Borough Council, UK: 403 error from blocked User-Agent (thanks @SavageCore, @markvp)
- fixed Ryde, NSW, AU: updated headers to bypass bot protection (thanks @andrewkriley)
- fixed Silea, IT: updated for new API (thanks @achelius, @mvimercati)
- fixed Staedteservice Raunheim Rüsselsheim, DE: API call method (thanks @cgomm, @bbr111)
- fixed Stockton Borough Council, UK (thanks @06benste)
- fixed Swale Council, UK: refactored source (thanks @dolce08)
- fixed TBV Velbert, DE: updated API URL (thanks @ndt)
- fixed Toronto, CA: robust CSV parsing and waste type filtering (thanks @bbr111)
- fixed Umweltverbaende, AT: new URLs for Hollabrunn and Zwettl (thanks @thargor)
- fixed WAS Wolfsburg, DE (thanks @kenodai)
- fixed Wroclaw (Ekosystem), PL: Python 3.14 compatibility (thanks @c-soft)
- fixed Wyre Forest, UK: date parsing (thanks @matty)
- fixed ZYS Harmonogram, PL: 2026 support (thanks @sematuszewski)
- fixed awb_es_de: SSL error, switched to cloudscraper (thanks @5ila5, @meilon)
- fixed Ekosystem Wroclaw calendar URL HTML-encoded ampersand (thanks @piogas)
- fixed Gotland, SE: only handle valid waste types (thanks @oskarannas)
- fixed Alchenstorf, CH (thanks @1337hium)
- fixed Blacktown, NSW, AU (thanks @dt215git)

## Improved Sources

- improved EcoHarmonogram, PL: added configurable language parameter
- improved AbfallnaviDe service: optimized requests handling and simplified data processing (thanks @bbr111)
- improved BANES, UK: refactored API calls, dropped legacy session, added request timeouts (thanks @trvrnrth)
- improved FormStateParser: handle omitted optional HTML end tags (thanks @taker218)
- improved Neunkirchen Siegerland, DE: error handling and address fetching (thanks @bbr111)
- improved Regioentsorgung, DE: address validation (thanks @taker218)
- improved Seon, CH: updated calendar URL (thanks @starwarsfan)
- improved MidCoast Council, AU: refactored source URLs and error handling (thanks @sh00t2kill, @AkimboDadz)
- improved config flow: pre-fill city param for Ebersberg municipalities (thanks @FaserF)

## Removed Sources

- removed alw_wf_de: migrated to `jumomind_de` (GUI configurations auto-migrate, thanks @5ila5)
- removed legacy lra_ebersberg_de duplicate entries (thanks @FaserF)

## Other

- README: Add HACS install button (thanks @reedy)
- Fixed ICS documentation typo for Google Calendar example (thanks @kiat-huang)
- Updated contributing documentation for source argument retrieval (thanks @theGoodPotato)
- Clarified YAML vs UI support in documentation (thanks @Leeoc)

## New Contributors

Welcome to the following first-time contributors! :tada:

@achelius, @ashkjc, @chartionic, @chris3600410, @djz88, @knumskull, @markusdlugi, @MartyTremblay, @matejkramny, @mattaustin, @matty, @mvimercati, @niallrobinson, @nnielzz, @Olen, @piogas, @reedy, @ryanwr, @sematuszewski, @stanislavhannes, @theGoodPotato, @tmwrrn, @tsgoff, @vhtkrk, and @Wardy930




## [2.11.0] - 2025-12-26

## Breaking Changes

- deleted source for Ku-Ring-Gai: GUI configuration should be migrated automatically while YAML configuration need to configure the impactapps_com_au source
- derby_gov_uk no longer support Post code + house number lookup you may need to reconfigure the source
- Peterborough, UK probably needs to be reconfigured
- Königstein, DE: You need to reconfigure to the AWIDO source
- cambridge_gov_uk and scambs_gov_uk are deprecated GUI configurations will automatically be migrated to the new greater_cambridge_waste_org source YAML configuration should migrate (the old sources still work for now)
- Lippe, Germany: removed, use `abfallnavi_de` instead. GUI configurations will be migrated into a broken `abfallnavi_de` configuration and need to reconfigure (3 dots next to source -> reconfigure) and add a street here. Yaml configurations need to manually migrate to abfallnavi_de.

## Added sources

- added ICS documentation for Chicago and Flagstaff, USA (thanks @cdiaz2799, @5ila5)
- added Fuquay Varina, NC, USA (thanks @RyanJamesCaldwell)
- added Canning, WA, AUS (thanks @dt215git)
- added Waltham Forest, UK (thanks @bwemao99)
- added Pireva, Sweden (thanks @alu-)
- added Gmina Zgierz (thanks @Krecikkko)
- added Monash, AU (thanks @spexiono)
- added AMSA, IT (Thanks @francinze)
- added Komunala Kranj, Slovenia (thanks @TKosir)
- added Wrexham County Borough Council, UK (thanks @harrymilnes)
- added ICS documentation for Speyer, Germany (thanks @DerDreschner)
- added Lille metropole to Publidata, France (thanks @orandin)
- added Neath Port Talbot, UK (thanks @AledWatkins)
- added ICS documentation for North Tyneside, UK
- added Venlo, NL to ximmio_nl (thanks @ruudvanstrijp)
- added Betzdorf, LU (thanks @defuuss)
- added London Borough of Havering, UK (thanks @SamirHafez)
- added Stadtwerke Rösrath, DE (thanks @bbr111)
- added Calderdale, UK (thanks @BenWolstencroft)
- added Scottish Borders Council, UK (thanks @gaza1994)
- adding Plymouth City Council, UK (thanks @duffyboyo)
- added Angus Council, UK (thanks @gaza1994)
- added Greater Cambridge Waste, UK (thanks @dt215git)
- added MRC de Roussillon (QC), CA (thanks @cszou)
- added ICS documentation for Longueuil (QC), CA (thanks @ggzica)
- added Lippe to abfallnavi_de (@5ila5)

## Fixed sources

- fixed fix_midandeastantrim_gov_uk (thanks @dansollok)
- fixed Hume City Council, AU (thanks @seedzero)
- fixed cardinia_vic_gov_au (thanks @zachdekoning)
- fixed bolton_gov_uk (thanks @XargsUK)
- fixed north_norfolk_gov_uk failing for some addresses (thanks @dt215git)
- fixed edlitz.at (thanks @DaHofa02)
- fixed Sholland, UK (thanks @dansollok, @5ila5)
- fixed hvcgroep_nl for ZRD (thanks @dansollok)
- fixed Wokingham failing in some cases (thanks @Rujith)
- fixed ZKE Saarbrücken, Germany (thanks @YanKon)
- fixed Southglos, UK may break on expired garden waste subscription (thanks @AlexCPU)
- fixed Auckland Council, NZ (thanks @notf0und)
- fixed eko_tom_pl (thanks @kielich89)
- fixed stockton, UK (thanks @deanlongstaff)
- fixed Mid Sussex District Council, UK (thanks @olliebennett)
- fixed Peterborough, UK by reverting the "fix" of the last release (@5ila5)
- fixed samiljo_se (thanks @dansollok)
- fixed Waipa District Council, NZ (thanks @dansollok)
- fixed Auckland, NZ (thanks @fpayapaya)
- fixed Wellington, NZ (thanks @jbergler)
- fixed Derby, UK (thanks @Azelphur)
- fixed sammelkalender, CH sometimes returning data for wrong region (thanks @JonasArnold)
- fixed Valorlux, LU (thanks @Valorlux)
- fixed Armagh City Banbridge & Craigavon, UK (thanks @bmines67)
- fixed Muenchenstein, CH (thanks @r3turnNull)
- fixed Sutton, UK (thanks @dansollok)
- fixed Arun, UK sometimes not showing rubbish collections (thanks @whi-tw)
- fixed Westoxon, UK (thanks @jamesweale)
- fixed Fareham, UK: Now uses new API with correct collection dates (thanks @sam-kayg)
- fixed Herefordshire, UK (thanks @greytuk)
- fixed Buergerportal, Germany not working for some regions (thanks @jlai79)
- fixed North Hertfordshire, UK (thanks @Zepheus)
- fixed East Renfrewshire, UK (thanks @ianders)
- fixed Fife Council (thanks @MaxJW)
- fixed iapp_itouchvision_com (thanks @gwjbarton)
- fixed Birmingham City, UK (thanks @jamesonuk)
- fixed Stirling, AU (thanks @markvp)
- fixed Helmstedt, Germany (thanks @shaguarger)
- fixed Peterborough, UK (thanks @skipishere)
- fixed gfa_lueneburg_de did not return dates for 2025 anymore (thanks @CommSter)
- fixed Abfall.IO (thanks @TheDuffman85)
- fixed publidata_ca (thanks @jensenc)
- fixed Royal Borough Of Greenwich, UK (thanks @timocov)
- fixed Hobart City, AU (thanks @hobartcity)
- fixed Königstein moved to awido (thanks @AlexJacu)
- fixed olo_sk (thanks @vaind)
- fixed Sholland, UK (thanks @Lewis1352)
- fixed Umweltverbaende, AT (thanks @mindestens)
- fixed Stirling, AU (thanks @T1MB0-ZG)
- fixed Coventry, UK (thanks @JustinWingChungHui)


## Removed sources

- removed Ku-Ring-Gai (thanks @dt215git): users will automatically be migrated to the impactapps_com_au source if it was configured in the GUI (Not YAML)


## Improved sources

- plano_gov: improved config flow default arguments (thanks @GingerSnap-xx)
- renoweb_dk improved error logs (thanks @runejuhl)
- update Bodenseekreis, Germany ICS documentation (thanks @snowstoked)
- Frankenberg, Germany: actually apply street filter (thanks @hnrmrl)
- minor update to merri_bek_vic_gov_au (thanks @flythecoop10)
- Werra-Meißner-Kreis, Germany add 2026 support (thanks @Demel75)
- improved Newark & Sherwood, UK now get more collection dates in advance (thanks @Hatton920)
- CitiesAppsV2 now supports better search (thanks @tst-Me)
- Rushcliffe, UK improve bin name + icon for glass (thanks @ribz)
- Logan City Council, AU move to new API endpoint (thanks @KuzonCode)




## [2.10.0] - 2025-08-30

# Breaking changes

- Landkreis Schwäbisch Hall: move to the app_abfallplus_de source as lrasha_de does not work anymore due to changes by the service provider
- BSR (Berliner Stadtreinigungsbetriebe): changed configuration variables. GUI configuration should be migrated automatically, but there is no guarantee, and it might need manual reconfiguration.
- removed iweb_itouchvision_com uses who configured the source through the GUI should be automatically migrated to iapp_itouchvision_com, but users using a YAML configuration need to modify the configuration.

## fixed sources

- fixed Herefordshire, UK (thanks @dt215git)
- fixed kingston, Australia (thanks @LF2b2w)
- fixed Fix: Tauranga, NZ (thanks @conork123)
- fixed Blacktown, AU (@5ila5)
- fixed 1coast, AU (thanks @dt215git)
- fixed Blaby, UK (thanks @dt215git)
- fixed Chesterfield, UK (thanks @dt215git)
- fixed Afvalstoffendienst, NL (thanks @dt215git)
- fixed Solihull0, UK garden waste handling (thanks @dt215git)
- fixed Wyre, UK (thanks @dt215git)
- fixed Wiltshire, UK (thanks @dt215git)
- fixed Swale, UK (thanks @dt215git)
- fixed Fix Broxbourne, UK (thanks @SimonLeigh)
- fixed Blacktown, AU (thanks @dt215git)
- fixed Cardinia, AU (thanks @zachdekoning)
- fixed Peterborough, UK (thanks @dt215git)
- fixed Wokingham, UK (thanks @dt215git)
- fixed Fix Publidata, FR not working is some cases (thanks @GilDev)
- fixed Ashford, UK (thanks @dt215git)
- fixed TBV Velbert, DE (thanks @pl4st3, @5ila5)
- fixed East Herts, UK (thanks @dt215git)
- fixed Royalgreenwich, UK (thanks @timocov)
- fixed Horsham, UK (thanks @dt215git)
- fixed BCP Council, UK (thanks @iMiMx)
- fixed Mijnafvalwijze, NL (thanks @jankees0212)
- fixed Fix North Hertfordshire, UK (thanks @Zepheus)
- fixed AWN, DE (thanks @scoop)
- fixed BSR (Berliner Stadtreinigungsbetriebe), DE (thanks @mpw96)
- fixed kingston_vic_gov_au (thanks @andykelk)
- fixed Armadale, AU (thanks @stevene1919)
- fixed Umweltverbaende, AT (thanks @xmirakulix)
- fixed renodjurs_dk failing in some cases (thanks @dansollok)
- fixed Rushmoor, UK (thanks @JamieBriers)
- fixed Recyclecoach (thanks @dansollok)
- fixed Darlington, UK (thanks @dansollok)
- fixed South Glos, UK (thanks @dt215git)
- fixed Unley SA, AU (thanks @dansollok)
- fixed iweb_itouchvision_com now migrated to iapp_itouchvision_com (thanks @dt215git)
- fixed Darebin VIC, AU (thanks @jdndm)
- fixed skaraborg_se (thanks @Tjindarr)
- fixed Lancaster, UK (thanks @WillFantom)
- fixed KAEV Niederlausitz, DE (thanks @aschobba)
- fixed Campbelltown, AU (thanks @dansollok)
- fixed Update cardinia_vic_gov_au for now (thanks @seedzero)

## added sources

- added Kiama Municipal Council, NSW, Australia (thanks @daffster)
- added Moorabool Shire Council, AU (@5ila5)
- added North East Lincolnshire Council, UK (@5ila5)
- added Clarence City Council, AU (thanks @Clarence City Council)
- added ICS docuemntaiton for Wiesbaden, Germany (thanks @tomraithel)
- added West Lancashire Council, UK (thanks @nathanmarlor)
- added Landkreis Helmstedt, DE (thanks @shaguarger)
- added Kalundborg, Denmark (thanks @dansollok)
- added Assen + RMN, NL (thanks @staticdev)
- added Plano (TX), USA (thanks @GingerSnap-xx)
- added opole app to ecoharmonogram source (thanks @bogdal)
- added City Of Glen Eira, AU (thanks @jdgordon)
- added Greyhound Recycling, Ireland (thanks @JosyBan)
- added Hyndburn Borough Council to iapp_itouchvision_com (thanks @dt215git)
- added Murrindindi, Australia to impactapps_com_au (thanks @dt215git)
- added Nårab, SE (thanks @victordiges)
- added documentation for unofficial ICS source Bettembourg, LU (thanks @knuewelek)
- added SIDEC, LU (thanks @koosoli)
- added Valorlux, LU (thanks @koosoli)




## [2.9.0] - 2025-07-05

## Breaking changes

- aylesburyvaledc_gov_uk moved to iapp_itouchvision YAML configuration need to change. Configuration through the GUI should be migrated automatically (but not tested very well)
- awm_muenchen_de my need to be reconfigured for some regions
- ecoharmonogram_pl now requires house_number and depending on the region other parameters too, So you might need to reconfigure ecoharmonogram_pl

## fixed sources

- fixed awigo_de not working sometimes (thanks @Malfed)
- fixed westsuffolk_gov_uk (thanks @dt215git)
- fixed Lumire, Sweden (thanks @alu-)
- moved aylesburyvaledc_gov_uk to iapp_itouchvision (thanks @dt215git)
- fixed Blackpool, UK not working for some areas (thanks @puralpha, @5ila5)
- fixed nvaa_se (thanks @alu-)
- fixed East Riding, UK not working for some regions (thanks @dt215git)
- fixed Knowsley, UK (thanks @dt215git)
- fixed Highpeak, UK (thanks @drsgoodall)
- fixed GFA Lueneburg, Germany (@5ila5)
- fixed awm_muenchen_de not working for some regions (thanks @nouser2013)
- fixed ecoharmonogram_pl showing wrong collection dates (@5ila5)
- fixed Wigan Council, UK (thanks @PropaneDragon)
- fixed East Herts, UK (thanks @dt215git)
- fixed Chesterfield, UK failing in some cases (thanks @dt215git)
- fixed IlRifiutologo, IT (thanks @matteolel)
- fixed hvcgroep_nl not working for Cyclus (thanks @millmakerjm)
- fixed Lichfield DC, UK (thanks @Troon)
- fixed royalgreenwich, UK (thanks @timocov)
- fixed Central Bedfordshire Council, UK (thanks @chrisf4lc0n)
- fixed Swindon, UK (thanks @joshwillcock)
- fixed rbwm_gov_uk (thanks @geozza123)
- fixed Hull CIty Council, UK (thanks @MattThePandah)
- fixed Rotherham, UK (thanks @dt215git)
- fixed Runnymede, UK (thanks @dt215git)
- fixed Oxford City Council, UK (thanks @dt215git)
- fixed armadale_wa_gov_au (thanks @stevene1919)
- fixed welhat_gov_uk (thanks @pmharris77)


## added sources

- added Nodra/Norrköping, Sweden (thanks @alu-)
- added Ljungby kommun, Sweden (thanks @alu-)
- added more regions to edpevent, Sweden (thanks @alu-)
- added Örebro to edbevent, Sweden (thanks @joshua2a)
- added source for Hudiksvall, Sweden (thanks @alu-)
- added City of Greater Bendigo VIC, Australia (thanks @iSnackTwoPointOh)
- added Sjöbo, Sweden (thanks @alu-)
- added Skaraborg, Sweden (thanks @alu-)
- added ABC Council Northern Ireland (@5ila5)
- adddd ICS source Allenbach, Germany (@5ila5)
- added City of Philadelphia, PA, USA (thanks @dt215git)
- added City of Gosnells, AUS (thanks @dt215git)
- added Shoalhaven City Council, AU (thanks @nicespoon)
- added City of Casey, AU (thanks @mrvelic)
- added Herrljunga/Vårgårda, Sweden to edpevent (thanks @radhus)
- add ICS documentation for Recology San Francisco (thanks @lxfschr)
- added ecoservice.lt in Lithuania (thanks @paulius2k)
- added Hartlepool, UK (thanks @dt215git)

## Improvements

- added house number options to data_angers_fr (thanks @EnzDev)




## [2.8.0] - 2025-05-11

## Breaking changes:

The Royal Borough of Kingston Council: Source removed you need to move to the ICS source as the old source did not work anymore

## Fixed Sources

- fixed torridge_gov_uk (thanks @tigattack)
- fixed umweltverbaende_at not working for some regions (thanks @AustrianBarrel, @5ila5)
- fixed oxford_gov_uk (thanks @cunners)
- fixed Montreal, Canada shows wrong collections days (thanks @mfortin)
- The Royal Borough of Kingston Council: moved to ICS source (thanks @elyobelyob)
- fixed fkf_bo_hu (@5ila5)
- fixed North Kesteven, UK (thanks @dt215git)
- fixed North Ayrshire, UK not working for some addresses (thanks @dt215git)
- fixed Frankston, VIC, AU (thanks @dt215git)
- fixed Oxford, UK (thanks @rbrunt)
- fixed: Bexley, UK (thanks @chris-read896)
- fixed Bracknell Forest not working when using house names (thanks @tombotch)
- fixed AHA Zweckverband Region Hannover (thanks @Zappdidappdi)
- fixed Merri-bek, AU (thanks @dt215git)
- fixed Swale Council when return non-calendar dates (thanks @rmdtech)
- fixed Armadale, AU (thanks @dt215git)
- fixed Norht Somester, UK to fail when next collection is not supplied (@5ila5)
- fixed poriruacity_govt_nz (thanks @Nduva-Hey, @dt215git)
- fixed Adur & Worthing, UK (thanks @dt215git)
- fixed East Renfrewshire (thanks @ianders)
- fixed ccc_govt_nz (thanks @jonocairns)
- fixed canterbury_gov_uk (thanks @arphillips06)

## Added Sources

- added Marks, Sweden (thanks @alu-)
- added Komorniki and Kostrzyn, Poland (thanks @sematuszewski)
- added Preston, UK (thanks @RickSeymour)
- added West Lindsey, UK (thanks @dt215git)
- added sunshinecoast, Australia (thanks @soulvice)
- added Blaby, UK (thanks @dt215git)
- added Motala, Sweden to avfallsapp_se (thanks @calleel)
- added Rural City of Wangaratta VIC Australia (thanks @bprc)
- added Erewash Borough Council, UK (thanks @dt215git)
- added San Diego, CA, USA (thanks @dt215git)
- added Umweltbetriebe USK Kleve, Germany (thanks @nl2rma)
- added Hastings DC, NZ (thanks @dt215git)
- added East Dunbartonshire, UK (thanks @dt215git)
- added Chatham-Kent, CA (thanks @schovanec)

## Improved sources

- citiesapps_com updated documentation to add more regions (thanks @FilipHoertner, @5ila5)
- oslokommune_no now supports filtering on pickup point ID (thanks @lersveen)
- Updated service for Impact Apps, AU (thanks @dt215git)
- Buckinghamshire, UK does not show different bin name on Bank Holiday (thanks @dt215git)
- royalgreenwich_gov_uk added support for bank holiday overrides (thanks @timocov)




## [2.7.0] - 2025-03-05

## Breaking changes:

- source `fkf_bp_hu` is now `mohu_bp_hu`: GUI configuration will be automatically migrated but YAML based configurations need to be changed

## General Improvements

- added French translation to the configuration GUI (thanks @mfortin)

## Added Sources

- added Kiedy śmieci, Poland (thanks @d4m)
- added Ökrab, Sweden (thanks @ZynThaX)
- added Add Norwich City Council, UK (thanks @nathforge)
- added Simbio, Slovenia (thanks @archon-dev)
- added Bolton Council, UK (thanks @XargsUK)
- added Angers Loire, France (thanks @Aguay-val)
- added Gleisdorf to citiesapps_com (thanks @lbloder)
- added ICS Stadt Delmenhorst, Germany (thanks @nsd0tklostermann)
- added RosknRoll, Finland (thanks @timbba80)
- added ICS source Stadt Enger, Germany (thanks @DarthMoe)
- added Panda Waste, Ireland (thanks @gcacace)
- added ICS source Kreis Kaiserslautern (thanks @n-vent)
- added ICS source Landkreis Nordhausen (thanks @kyndadumb)
- added Kraków, Poland (thanks @dawidborek)
- added PreZero Bielsko-Biała, Poland (thanks @bladowski)
- added gardenbags.co.nz source (thanks @notf0und)
- added tsceskybrod_cz (thanks @moneytoo)
- added Innherred Renovasjon, Norway (thanks @cunners)
- added Torridge District Council UK (thanks @tigattack)
- added Prodnik, Slovenia (thanks @Alex9premium)


## Improved Sources

- montreal_ca now supports different waste collection sectors
- Republic Services better bin names (thanks @evanhsu)
- update tbr_reutlingen_de ICS documentation (thanks @srempfer)
- Cheshire East, UK allow to disable ssl verification as it fails for some HA installs (thanks @greghesp)
- Poznan, Poland shows more collection dates (thanks @czyzniek)


## Fixed Sources

- fixed citiesapps_com moving to a new API (thanks @lbloder)
- fixed kingston.gov.uk date parsing (thanks @cmsj)
- fixed swale_gov_uk (thanks @dt215git)
- fixed awn_de (thanks @GyroGearl00se)
- fixed opendata_bordeauxmetropole_fr not working for all supported regions (thanks @Chuckame)
- fixed zva_wmk_de (thanks @Demel75)
- fixed AWB Bad Kreuznach not working for all locations (thanks @alex-voigt)
- fkf_bp_hu renamed to mohu_bp_hu + add option to disable SSL verification (thanks @greghesp)
- fixed coventry_gov_uk (thanks @cunners)
- fixed ecoharmonogram_pl, sides_matcher behavior (thanks @amozeo)
- fixed recyclecoach (thanks @Icexist)




## [2.6.0] - 2025-01-08

## General Fixes

- Fixed issue by removing dependency recurring_ical_events
- Removed ICS_v1, ICS sources will use the newer parser

## Breaking Changes

- Mijnafvalwijzer does not offer ICS files anymore if you use Mijnafvalwijzer with the ICS source, please move to the new dedicated source
- Now fixed configurations using umwelverbaende_at might need reconfiguring
- Heidelberg, Germany now requires the use of the new dedicated source as the ICS source stopped working.


## Added sources

- Added City of Hobart, Australia (@5ila5)
- Added ICS documentation for Abfallwirtschaft Rems-Murr (thanks @fabyte)
- Added Hausmannstaetten, Austria (thanks @riger23)
- Added city of Los Angeles, CA, USA (thanks @cdiaz2799)
- Added Saarbrücken, Germany (thanks @phauch)
- Added Boise, USA to the recollect ICS documentation (thanks @dt215git)
- Added Ppendata Bordeaux, France (thanks @AthAshino)
- Added Minneapolis, MN, USA (thanks @jimternet)
- Added Scenic Rim, QLD, Australia (thanks @dt215git)
- Added ICS documentation for Delmenhorst, Germany (thanks @jay-eff)
- Added North Norfolk, UK (thanks @dt215git)
- Added Taranto, Italy (@5ila5)
- Added LK Verden, Germany (@5ila5)
- Added Kristiansand, Norway (@5ila5)
- Added Royal Borough Of Greenwich, UK (thanks @timocov)
- Added Mijnafvalwijzer, Netherlands (thanks @gilaberticus)
- Added Knowsley Council, UK (@5ila5)
- Added Joondalup, Australia (thanks @dt215git)
- Added Coventry City Council, UK (thanks @dt215git)
- Added sims.pl / Blisco, Poland (@5ila5)
- Added Publidata.ca, Canada (thanks @MrNunu)
- Added Melton District, UK (thanks @dt215git)
- Added Thurrock, UK (@5ila5)
- added Add Rother District Council, UK (thanks @sarumait)
- Added Cumberland Council, UK (thanks @dt215git)
- Added Bridgend, Wales (thanks @dt215git)
- Added Dartford, UK (thanks @dt215git)
- Added South Staffordshire, UK (thanks @dt215git)
- Added dedicated source for Heidelberg, Germany (thanks @DerDreschner)
- Added ICS Documentation for Litovel, Czech Republic (thanks @honza-kasik)
- Added Bremerhaven, Germany (@5ila5)
- Added Gmina Środa Śląska, Poland (thanks @ksciana)
- Added OLO, Bratislava, Slovakia (thanks @mniejo)
- Added BEP-Environnement, Belgium (thanks @amof)

## Fixed Sources

- fixed: AWB Emsland only showed next year's collection if this and next year's collections were available  (thanks @niklasdoerfler)
- fixed republicservices not working if holiday response is None (thanks @Jinra)
- fixed zva_wmk_de fetching correct ULR for specific yeards (thanks @Demel75)
- fixed wakefield_gov_uk (@5ila5)
- fixed carmarthenshire_gov_wales (@5ila5)
- fixed Rushcliffe, UK (thanks @ribz)
- fixed lrasha_de (thanks @toXel)
- fixed poznan_pl (thanks @czyzniek)
- fixed salford_gov_uk (thanks @FilHarr)
- fixed awm_muenchen_de not fetching next year if available (thanks @mhelff)
- fixed egn_abfallkalender_de failing for some addresses (@5ila5)
- fixed Dundee City returning wrong dates (thanks @dt215git)
- fixed stirling_wa_gov_au (thanks @dt215git)
- fixed recycleapp_be failing for a limited amount of addresses (@5ila5)
- fixed darebin_vic_gov_au (thanks @dt215git)
- fixed lewisham_gov_uk (@5ila5)
- fixed umwelverbaende_at not working for a lot of addresses (@5ila5)
- fixed Conwy County, UK (thanks @tomusher)
- fixed cederbaum_de (thanks @pogross)
- fixed lichfielddc_gov_uk date parsing in December for January collections (thanks @Troon)
- fixed abfall_havelland_de (thanks @arnonuem)
- fixed walsall_gov_uk (thanks @dt215git)
- fixed ALW-WF returning duplicate entries (thanks @envy)
- fixed Wokingham Council wrong collection schedule around Christmas (thanks @dt215git)
- fixed Nottingham City returning garbage dates (thanks @TurnrDev)




## [2.5.0] - 2024-12-02

# Breaking Changes for

- islington_gov_uk now requires a postcode and must be reconfigured

# Deprecating

- wuerzburg_de please move to the ICS source. The wuerzburg_de still works for now but will not get fixed if it breaks

## General Fixes

- fixed `day_offset` not working with YAML configuration (thanks @ReneNulschDE)
- fixed Blocking call in config_flow (thanks @ReneNulschDE)

# Sources

## Breaking

- Replaced sbazv_de with an ICS source, as the original source stopped working (thanks @Maddimax)

## Added Sources

- added Thanet, UK (thanks @northerngeek)
- added Wakefield, UK (thanks @northerngeek)
- added ICS Documentation for Wetzlar, Germany (thanks @arbue)
- added ICS Documentation for Castrop-Rauxel (thanks @Blitzbat)
- added Shire of Serpentine Jarrahdale, Australia  (thanks @michaelroper)
- added dedicated source for Neu-Ulm, Germany (thanks @ReneNulschDE)
- added Swale Borough Council (thanks @jamesonuk)
- added Moyne Shire Council, Australia (thanks @sunburntandblonde)
- added ICS Documentation for Valleyfield, Canada (@5ila5)
- added Central Coast, Australia (@5ila5)
- added Silea, Italy (thanks @mvimercati)
- added Kumberg, Austria (@5ila5)
- added AWV Ostthüringen, Germany (@5ila5)
- added MZV Rotenburg Bebra, Germany (@5ila5)
- added ICS Documentation for Bottrop, Germany (@5ila5)
- added ICS Documentation for Würzburg, Germany (thanks @rikroe)

## Fixed Sources

- fixed warszawa19115_pl (thanks @tomek-sienicki)
- fixed Yarra Ranges Council (thanks @ReneNulschDE)
- fixed nottingham_city_gov_uk (thanks @TurnrDev)
- fixed static source GUI configuration parameter validation failing if using dictionary weekdays (thanks @zolakt)
- fixed Bracknell Forest general waste not showing up (thanks @BenRutlandWeb)
- fixed Junaavfall_se failing for some addresses (thanks @ReneNulschDE)
- fixed hasting_gov_uk (@5ila5)
- fixed islington_gov_uk (thanks @ReneNulschDE)
- fixed landkreis_rhoen_grabfeld (thanks @Finghin)
- fixed awg_de (thanks @ReneNulschDE)
- fixed abfallwirtschaft_pforzheim_de (thanks @Jushav)
- fixed Warwickdc_gov_uk (thanks @ReneNulschDE)
- fixed landkreis_kusel_de (thanks @ReneNulschDE)
- fixed kingston_gov_uk (thanks @ilbarone87)
- fixed crawley_gov_uk (@5ila5)
- fixed tekniskaverken_se (@5ila5)

## Improves Sources

- improved publidata_fr (thanks @vinzd)




## [2.4.0] - 2024-10-30

# General Fixes

- better define dependencies: fixes an issue where icalendar 6 was installed which caused sources, that require ICS parsing to stop working
- improved error message if source has an import error.

## Added Sources

- Added Gojer, Austria (@5ila5)
- Added ICS documentation for Rhein-Lahn Kreis (@5ila5)
- Added City of Schwabach, Germany (@5ila5)
- Added Eisenkappel-Vellach, Austria (@5ila5)
- Added Midandeastantrim, UK (thanks @AHARVEY99)
- Added West Lothian, UK (thanks @alitheg)
- Added ICS documentation for Seon, Switzerland (thanks @starwarsfan)
- Added Sefton Council, UK (thanks @northerngeek)


## Fixed Sources

- fixed hvcgroep_nl could not be configured through the GUI (@5ila5)
- fixed southtyneside_gov_uk (thanks @CartesianJohn)
- fixed Stirling, UK (thanks @nagug)
- fixed Fix: GFA Lüneburg, house number was not set correctly correctly (thanks @ReneNulschDE)




## [2.3.0] - 2024-10-18

## Breaking changes

- removed sicaapp_lu, that was added in the last release, as there is already a (now even updated) sica_lu source. GUI confiugraiont should be migrated automatically

## General Improvements

- added forgotten option `day_offset` to the GUI customize section.

## Added Sources

- added Dorset, UK (thanks @J-shw)
- added Carmarthenshire, wales (thanks @dt215git)
- added Dundee, UK (thanks @dt215git)
- added Wyre, UK (thanks @tschofield)
- added Blaenau Gwent, UK (thanks @dt215git)
- added Richmond Hill, Ca to recyclecoach (thanks @gregprosser)
- added LK Rostock, Germany (@5ila5)
- added Eko tom, Poland (thanks @szyszkowink)
- added LK Neumarkt, Germany (@5ila5)
- added Norfolk County to RecycleCoach  (thanks @dt215git)
- added Malta (@5ila5)
- added Folkestone & Hythe, UK (thanks @dt215git)
- added Iren Ambiente, Italy (@5ila5)
- added Lüneburg, Germany (@5ila5)
- added Chelmsford, UK (thanks @jonware)
- added Renhållningen Kristianstad, Sweden (thanks @hansbacklund42)
- added AWG Wuppertal (@5ila5)
- added Rochdale, UK (@5ila5)
- added multiple services to impactapps_com_au (thanks @dt215git)
- added North Lanarkshire, UK (thanks @dt215git)
- added Communauté de Communes de Montesquieu, France (thanks @melankh)
- added ICS Source Edam-Volendam, Netherlands (thanks @Roohn)
- added Hastings Borough Council, UK (thanks @dt215git)
- added FCC, Slovakia (@5ila5)
- added Cuxhaven to abfallnavi_de (@5ila5)
- added Sunderland City Council (thanks @dt215git)
- added Söderköping, Sweden (thanks @dala318)
- added Junker.app, Italy (@5ila5)
- added Publidata supporting multiple French areas (thanks @vinzd)
- added city of Bamberg, Germany (@5ila5)
- added Frankenthal, Germany (@5ila5)
- added Ittre, Belgium (@5ila5)
- added Cannock Chase, UK (thanks @marcjay)
- added Shire of Mundaring, Australia (thanks @dt215git)


## Fixed Sources 

- fixed Impactapps_com_au not working for Blue Mountains (@5ila5) 
- fixed zakb_de not working for some addresses (@5ila5)
- fixed victoriapark_wa_gov_au failing for some addresses (thanks @dt215git)
- fixed herefordshire_gov_uk (thanks @Jab2870)
- fixed elmbridge_gov_uk (@5ila5)
- fixed recyclecoach_com (@5ila5)
- fixed kuringgai_nsw_gov_au (thanks @dt215git)
- fix app_my_localca_services_au may fail for some addresses (@5ila5)

## Improved Sources

- ambervalley_gov_uk can now predict collections further in the future. (@5ila5)
- Dunedin_govt_nz now showns the new bin types, moved to the API used by the APP (@5ila5)
- sica_lu now uses the API of the new App (thanks @Foxi352)
- adur_worthing_gov_uk can be configured using a UPRN now (thanks @dt215git)




## [2.2.0] - 2024-09-10

## FIX

- Fixed ICS sources or source relying on ICS praising to fail as a faulty version of icalevents may be installed

## Config Flow Improvements (@5ila5)

- Sources may show instructions directly in the configuration GUI
- Sources may show alternative values if your arguments result in errors 
- Errors may show at the faulty argument instead of always on the top of the configuration window
- Source arguments may be better translated
- Source arguments may have a description below the input field

## General improvements

- Customize setting random_fetch_time_offset now uses DurationSelector instead of just Integer selector (@5ila5)

## Added Sources

- added Winterthur, Switzerland (@5ila5)
- added ZAW Donau-Wald, Germany (@5ila5)
- added iapp_itouchvision_com, UK (@5ila5, thanks @craigsblackie)
- added MPGK Katowice, Poland (@5ila5)
- added Bassens France (@5ila5)
- added Napier City, NZ (thanks @redjungle)
- added ICS documentation for Siegen, Germany (@5ila5)
- added ICS documentation for Flörsheim, Germany (@5ila5)
- added Backend of My Local Services App serving multiple municipalities, Australia (@5ila5)
- added SICA, Luxembourg (@5ila5)
- added Dover District Council, UK (@5ila5)
- added Köniz, Swizerland (thanks @Hiekkan)
- added City of Ryde, Australia (thanks @harrytheeskimo)
- added Alia Servizi Ambientali S.p.A., Italy (@5ila5)
- added Ronchi dei legionari, Italy (@5ila5)
- added City of Wanneroo, Australia (@5ila5)
- added Rapperswil Bern, Switzerland (@5ila5)
- added Oadby and Wigston Council, UK (@5ila5)
- added New York City, USA (Thanks @domdomegg)
- added Islington Council, UK (Thanks @domdomegg)

## Fixed sources

- fixed chiltern_gov_uk: please move to iapp_itouchvision_com (thanks @craigsblackie)
- fixed Oxford city, Failing for some addresses (thanks @tboby)
- fixed okc_gov by using an inoffical server by @sanctas
- fixed real_luzer_ch (@5ila5)
- fixed kirlees_gov_uk not working for some addresses (@5ila5)

## Modified Sources

- a_region_ch some backend changes, bin types might be renamed
- renfrewshire_gov_uk shows correct dates if multiple waste  types are collected at one day (thanks @JamiePhonic)
- umweltverbaende_at allows to define multiple calendars in GUI configuration (@5ila5)




## [2.1.0] - 2024-08-18

# General improvements

- config_flow now asks whether to show the quite complicated sensor & customize window (@5ila5)
- fixed a bug where config_flow sensor configuration would suggest invalid waste_types if they contain whitespace at the start or end of the string.
- (re) added the fetch_data service, not present for GUI configurations
- fixed a bug where GUI senosors would just ignore details_format and not show future collections after a HA restart

# Sources

## Added Sources

- added ICS documentation for Brent Council, UK (thanks @johnnieblows)
- added St. Albans, UK (@5ila5)
- added Apss by imactivate serving Leads/Rotherham/Luton/Fenland , UK (@5ila5)
- added Mölndal, Sweden (thanks @bratanon)
- added Borås, Sweden to edpevent (thanks @morotsgurka)
- added Fosen, Norway (@5ila5)
- added Rotorua lakes. NZ (thanks @PMKA)
- added Reno Djurs, Denmark (thanks @MTrab)
- added App Moje Odpady, Poland (@5ila5)
- added Stirling, Australia (@5ila5)
- added Västervik, Sweden (@5ila5)
- added Arun, UK (thanks @whi-tw)
- added Whitehorse, Australia (@5ila5)
- added Rd4, Netherlands (@5ila5)
- added Highpeak, UK (@5ila5)
- added Charnwood, UK (@5ila5)
- added Frankenberg, Germany (@5ila5)
- added Lobbe App, Germany (@5ila5)
- added Odense, Denmark (thanks @frederikrosenberg)
- added Gifhorn, Germany (@5ila5)
- added Antrim and Newtownabbey, UK (@5ila5)
- added Luleå, Sweden (@5ila5)
- added West Oxfordshire, UK (@5ila5)
- added CIDIU S.p.A., Italy (thanks @glaaze)
- added Il Rifiutologo, Italy (thanks @fabio-garavini)
- added ICS documentation for Jena, Germany (thanks @c-mellueh)
- added Malvern Hills + Worcester City, UK (@5ila5)
- added ICS documentation for Chemnitzer Land (@shering1988)
- added Orillia, Canada (@5ila5)
- added ICS documentation for GDA Amstetten, Austria (thanks @tsparber)
- added Roslagsvatten, Sweden to edpevent_se (@5ila5)
- added City of Coburg, Germany (@5ila5)

## Fixed Sources

- fixed whittlesea_vic_gov_au (thanks @EthanBezz)
- fixed aha_region_de (@5ila5)
- fixed vivab_se not working with addresses in Falkenberg (@5ila5)
- fixed a_region_ch failing for some regions (@5ila5)
- Workingham, Australia, moved to new collection schedule (thanks @badguy99)
- fixed republicservices_com (@5ila5)
- fixed wokingham_gov_uk failing if collection day is Today (thanks @badguy99)
- fixed bielefeld_de only getting collections from next season (@5ila5)
- fixed South Kesteven, UK hardcoded address_id (thanks @inconspicuous-name)
- fixed muellmax_de not working for some regions (@5ila5)


## Improved Sources

- c_trace_de support of abfall keyword to filter out specific waste types, not filterable by customize because they have the same name (thanks @funknerGER)




## [2.0.1] - 2024-07-18

This is a minor release which will replace the 2.0.0 release as this one specifies a minimum HA version

# Release notes of 2.0.0
# Big News

We now support GUI configuration, it could not be tested with every source, so please report any issues on GitHub

added by @dan-r,  @mampfes, @5ila5

## Breaking Changes

- Removed vejle_dk and favrskovforsyning_dk (introduced 1.49.0) in favor of affaldonline_dk
- highland_gov_uk parameter changed from recod_id to uprn (take a look into the new documentation)

## Added Sources

- added Frankston, Australia (thanks @b-goold)
- added affaldonline_dk, Denmakr (thanks @danielklejnstrup)
- added Southkesteven, UK (@5ila5)
- added monaloga.de, Germany (@5ila5)
- added Hull, UK (@5ila5)
- added Pronatura Bydgoszcz, Poland (thanks @jestempablo)
- added Wychavon, UK (@5ila5)
- added Ards and North Down Borough Council (@5ila5)
- added ICS documentation for AWG Bassum / LK Diepholz, Germany (thanks @engels0n)
- added ICS documentation for Steinburg, Germany (@5ila5)
- added ICS documentation for Noardeast-Fryslân & Dantumadiel, Netherlands (thanks @ HA community user: htahta)
- added Townsville, Australia (@5ila5)
- added Solihull, UK (@5ila5)
- added Darlington, UK (@5ila5)
- moved Poznań from sepan_remondis_pl to its own source (thanks @Tom61680, @5ila5)
- added City of Darebin, Australia (thanks @joshuapmorgan)
- added Vale Of Glamorgan Council, Wales, UK (@5ila5)
- added Impactapps, Australia (thanks @morganpollock)
- moved abfall_havelland_de from ICS to a dedicated source as ICS source did not work properly (@5ila5)
- added Cockburn, Australia (thanks @jbyway)
- added  NVAA, Sweden (thanks @williamhogman)
- added ICS documentation for Kredsløb, Denmark (@5ila5)
- added Vestforbrænding, Denmark (thanks @mbendtsen)
- added Added Newark & Sherwood, UK (thanks @calvind80)
- added ICS documentation for Landkreis Amberg-Sulzbach, Germany (@5ila5)

## Improved Sources

- denbigshire_gov_uk moved to new API (@5ila5)
- awido_de address search is now case-insensitive (@5ila5)
- ecoharmonogram_pl now supports more municipalities by supporting it's android app API (@5ila5)

## Fixed Sources

- fixed lewisham_gov_uk (@5ila5)
- fixed highland_gov_uk (@5ila5)
- fixed stevenage_gov_uk (thanks @adam-prickett)
- fixed portenf_sa_gov_au (@5ila5)
- fixed ashfield_gov_uk with a complete rewrite (@5ila5)
- fixed wyreforestdc_gov_uk (requires new configuration) (@5ila5)
- fixed Hawkesbury NSW, Australia (thanks @zzznz27)
- fixed broxbourne_gov_uk (thanks @SimonLeigh)
- fixed App_AbfallPlus_de (thanks @ReneNulschDE)

# New fixes after 2.0.0

## Breaking changes

- Removed Newport City, UK source, please move to iweb_itouchvision_com
- Removed Middlesbrough, UK, please move to recollect with ical source

## Deprecated

- SSAM and UPSALLA, Sweden should move to the new edpevent_se source but the old configs still work for now.

## Added sources

- added East Lothian, UK (@5ila5)
- added Stroud District Council, UK (@5ila5)
- added AHK Heidekreis (thanks @ReneNulschDE)
- added edpevent and merge SSAM and Uppsalavatten (thanks @morotsgurka)

## Fixed source

- fixed bug in broxtowe_gov_uk only affecting a few addresses (@5ila5)
- fixed circulus_nl (@5ila5)
- fixed app_abfall_plus failing if a street contains a tab (@5ila5)
- fixed api_golemio_cz could not be configured in GUI (@5ila5)
- fixed ICS GUI configuration would not work with params argument (@5ila5)
- added RESO GMBH, Germany (@5ila5)
- fixed kwu_de may match wrong address (@5ila5)
- fixed was_wolfsburg_de (@5ila5)
- fixed Newport by moving to iweb_itouchvision_com (thanks @ReneNulschDE)
- fixed Manchester_UK (thanks @ReneNulschDE)

## Improves sources

- alw_wf_de matches case-insensitive and `str.` as `straße` and the other way around (@5ila5)




## [2.0.0] - 2024-07-13

# Big News

We now support GUI configuration, it could not be tested with every source, so please report any issues on GitHub

added by @dan-r,  @mampfes, @5ila5

## Breaking Changes

- Removed vejle_dk and favrskovforsyning_dk (introduced 1.49.0) in favor of affaldonline_dk
- highland_gov_uk parameter changed from recod_id to uprn (take a look into the new documentation)

## Added Sources

- added Frankston, Australia (thanks @b-goold)
- added affaldonline_dk, Denmakr (thanks @danielklejnstrup)
- added Southkesteven, UK (@5ila5)
- added monaloga.de, Germany (@5ila5)
- added Hull, UK (@5ila5)
- added Pronatura Bydgoszcz, Poland (thanks @jestempablo)
- added Wychavon, UK (@5ila5)
- added Ards and North Down Borough Council (@5ila5)
- added ICS documentation for AWG Bassum / LK Diepholz, Germany (thanks @engels0n)
- added ICS documentation for Steinburg, Germany (@5ila5)
- added ICS documentation for Noardeast-Fryslân & Dantumadiel, Netherlands (thanks @ HA community user: htahta)
- added Townsville, Australia (@5ila5)
- added Solihull, UK (@5ila5)
- added Darlington, UK (@5ila5)
- moved Poznań from sepan_remondis_pl to its own source (thanks @Tom61680, @5ila5)
- added City of Darebin, Australia (thanks @joshuapmorgan)
- added Vale Of Glamorgan Council, Wales, UK (@5ila5)
- added Impactapps, Australia (thanks @morganpollock)
- moved abfall_havelland_de from ICS to a dedicated source as ICS source did not work properly (@5ila5)
- added Cockburn, Australia (thanks @jbyway)
- added  NVAA, Sweden (thanks @williamhogman)
- added ICS documentation for Kredsløb, Denmark (@5ila5)
- added Vestforbrænding, Denmark (thanks @mbendtsen)
- added Added Newark & Sherwood, UK (thanks @calvind80)
- added ICS documentation for Landkreis Amberg-Sulzbach, Germany (@5ila5)

## Improved Sources

- denbigshire_gov_uk moved to new API (@5ila5)
- awido_de address search is now case-insensitive (@5ila5)
- ecoharmonogram_pl now supports more municipalities by supporting it's android app API (@5ila5)

## Fixed Sources

- fixed lewisham_gov_uk (@5ila5)
- fixed highland_gov_uk (@5ila5)
- fixed stevenage_gov_uk (thanks @adam-prickett)
- fixed portenf_sa_gov_au (@5ila5)
- fixed ashfield_gov_uk with a complete rewrite (@5ila5)
- fixed wyreforestdc_gov_uk (requires new configuration) (@5ila5)
- fixed Hawkesbury NSW, Australia (thanks @zzznz27)
- fixed broxbourne_gov_uk (thanks @SimonLeigh)
- fixed App_AbfallPlus_de (thanks @ReneNulschDE)




## [1.49.0] - 2024-06-15

## General improvements

- removed deprecated HA function call (@5ila5)
- removed warning for blocking call by: Importing from thread instead event loop (thanks @larena1)
- fixed bug where `random_fetch_time_offset: 0` would not work (@5ila5)
- add day_offset parameter to source configuration (@5ila5)
- improve error message if source_index is out of range (@5ila5)

## Added sources

- added Birmingham City Council, UK (thanks @dannya)
- added ICS documentation for Herten, Germany (@5ila5)
- added Austin, US to recollect documentation (thanks @dhicock)
- added Renfrewshire council, UK (thanks @ScottMcGready)
- added East Ayrshire, UK (thanks @ScottMcGready)
- added North Ayrshire, UK (thanks @ScottMcGready)
- added Kiertokapula, FInland (thanks @developerfromjokela)
- added Borough of Broxbourne Council, UK (thanks @SimonLeigh)
- added city of Bromsgrove, UK (thanks @MrMaxP)
- added ICS documentation for Gedling Borough Council, UK (unofficial) (thanks @jamesmacwhite)
- added Victoria Park, Australia (thanks @jedimonkey)
- added Favrskovforsyning, Denmark (thanks @danielklejnstrup)
- add ICS documentation for awd_online_de (@5ila5)
- added Vejle, Denmark (thanks @danielklejnstrup)

## Fixed sources

- fixed glasgow_gov_uk (thanks @shinrath)
- fixed mansfield_vic_gov_au error for some addresses (thanks @tathamoddie)
- fixed bsr_de returns collection dates one day later (@5ila5)
- fixed maidstone_gov_uk (@5ial5)
- fixed app_abfallplus_de for apps that show a lot of collection types below a Sondermüll Headline
- fixed ecoharmonogram_pl not working correctly for all streets (thanks @pawelhulek)
- fixed awn_de may cause problems with ssl verification (thanks @scoop)

## Improved sources

- maldon_gov_uk should now include current day collections (@5ila5)
- ashford_gov_uk now shows collections that are due 'Today' (@5ila5)




## [1.48.0] - 2024-05-04

# General changes

- removed deprecated method call

# Breaking changes

- Zollernalbkreis moved service. The dedicated source is deleted. Please migrate to the [ICS version](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/ics/abfall_io_ics.md) Or the [APP backend](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/source/app_abfallplus_de.md)


# Improved Sources

- renoweb_dk now supports include_ordered_pickup_entries argument (thanks @syre)

# Fixed Sources

- fixed aucklandcouncil_govt_nz (thanks @nicwise)
- fixed recycleapp_be (@5ila5)
- fixed ecoharmonogram_pl selected wrong town if multiple towns matched search (@5ila5)
- fix harringey_gov_uk not working for addresses that list communal collections (@5ila5)
- **fixed AppAbfallPlusDE** (thanks @ReneNulschDE)
- fixed AWLNeuss_DE (thanks @ReneNulschDE)
- fixed gateshead_gov_uk (@5ila5)
- fixed sepan_remodis_pl returning wrong dates (@5ila5)
- fixed ashford_gov_uk (@5ila5)

# Added Sources

- added ICS documentation for ESG Soest, Germany (thanks @affeldt28)
- added ICS documentation for Stadt Mainhausen, Germany (thanks @bloodscript)
- added Flintshire, United Kingdom (@5ila5)
- added Landkreis Spree-Neiße, Germany (thanks @homeassist24)
- added Gmina Miekinia, Poland  (thanks @marczykm)
- added Hawkesbury NSW, Australia (thanks @zzznz27)
- added ICS documentation for AWP Pfaffenhofen an der Ilm, Germany (thanks @computeralex92)
- added North Yorkshire - Scarborough, UK (thanks @ReneNulschDE)
- added Eastleigh Borough, UK (@5ila5)
- adding ICS documentation for St. Pölten, Austria (thanks @AleXXw1)
- added Sutton Council, London, UK (@5ila5)
- added West Northamptonshire council, UK (@5ila5)




## [1.47.0] - 2024-04-07

# Fixed sources

- fixed stavanger_no (@5ila5)
- fixed Chichester District Council (thanks @pmuir)
- fixed barnsley_gov_uk failing if date is 'Today' (@5ila5)
- basingstoke_gov_uk now shows a warning instead of failing completely if one collection type does not show a valid date (@5ila5)
- app_abfallplus_de now shows all collection schedules if you can select multiple different rhythms in the app (@5ila5)
- fixed aha_region_de for some addresses (@5ila5)
- fixed braintree_gov_uk only worked once (thanks @amildenhall)
- fixed rctcbc_gov_uk showing a lot of wrong collection events (@5ila5)
- fixed braintree_gov_uk breaking for some addresses (thanks @S33G)
- fixed merri_bek_vic_gov_au (@5ila5, thanks @superdeadguy)
- fixed static weekdays not working correctly (@5ila5)

# Added sources

- added Falkenberg and Varberg, Sweden (thanks @pid00)
- added Mosman Council, Australia (thanks @cemilbrowne)
- added Hornsby Shire Council, UK (thanks @sh00t2kill)
- added Tkeliai, Lithuania (thanks @elijusgust)
- added Port Stephens Council, Australia (thanks @sh00t2kill)
- added Knox City Council, Australia (thanks @DavidSpackman)
- added BCP Council, UK (thanks @jeromehettich)
- Added hubert schmid gmbh, Germany (thanks @MichaelAlt)
- Added staffordbc, UK (thanks @bicciess)

# Improved sources

- bradford_gov_uk now supports integer UPRNs (@5ila5)
- westberks_gov_uk now supports food waste (thanks @Jonnobrow)
- jumind_de uses a "new" API for getting collection Dates, which fixed a bug where entries appeared multiple times for some addresses (@5ila5)




## [1.46.0] - 2024-03-04

# General improvements

- wrong source names now lead to only one instead of two errors in the logs (thanks @ReneNulschDE)
- added `multiple` wrapper source to include multiple sources as one calendar entity

# Beaking changes

- renosyd_dk uses new API and breaks existing configurations using renosyd_dk (thanks @carlreid)

# Deprecated Sources

- art_trier_de fixed issue for some regions, marked as deprecated.  Please move to the [ICS source](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/ics/art_trier_de.md) (@5ila5)

# Added Sources

- Insert-IT replaces Mannheim & Offenbach, Germany (thanks @derDeno)
- added Hounslow Council, UK (@5ila5, thanks @kiranbhakre)
- added ICS documentation for Bamberg, Germany (@5ila5)
- added North Northamptonshire, UK (@5ila5)
- added Barnsley Council, UK (@5ila5)
- added Shropshire Council, UK (@5ila5)
- added Bürgerportal AWL Neuss (thanks @kueps)
- added ICS documentation for canton of Zürich (@5ila5)
- added Denbighshire, UK (thanks @cimeson)
- added ICS documentation for LK Freising, Germany (thanks @rgaida)
- added Northyorks Selby, UK (@5ila5)
- added Tauranga City Council, NZ (thanks @Kronoc123)
- added Tunbridge Wells, UK (@5ila5)
- added AWM München, Germany (thanks @ReneNulschDE)
- added tonnenleerung_de, Germany (@5ila5)
- added ICS documentation for Unstrut-Hainich-Kreis, Germany (thanks @rine77)
- added Stirling, UK (thanks @nagug)
- added Nwleics, UK (thanks @heyiamluke)
- added ICS documentation for Emden, Germany (@5ila5)
- added ICS documentation for Erftstadt, Germany
- added Rudna u Prahy, Czechia (thanks @danoh)
- added RenoWeb, supporting multiple municipalities, Denmark (thanks @r-poulsen)
- added api.golemio.cz, Prague (thanks @sairon)
- added ICS documentation for AZV Hof (@5ila5)
- added ICS documentation for Vogtland (@5ila5)
- added East Devon District Council, UK (thanks @SimonRice)
- added Fylde Council, UK (thanks @j-webb)
- added London Borough of Newham (thanks @richkershaw)


# Fixed Sources

- fixed recycleapp_be (thanks @janholbrouck)
- fixed portenf_sa_gov_au (@5ila5)
- fixed mamirolle_info (thanks @AghilasMessara)
- fixed oxford_gov_uk (thanks @ReneNulschDE)
- fixed fix wastenet_org_nz (@5ila5)
- fixed awido_de which was broken for at least one region (@5ila5)
- fixed moray_gov_uk (thanks @dewet22)
- fixed heilbronn_de (@5ila5, thanks @hubelbubel)
- fixed miljoteknik_se (@5ila5)
- fixed ICS breaking on February 29th in a leap year (@5ila5)

# Improved Sources

- removed unnecessary web request from muellmax_de (@5ila5)
- fixed end of year/next year logic for uttlesford_gov_uk logic (thanks @dearlove)
- added city argument to srvatervinning_se (thanks @clind922)




## [1.45.1] - 2024-01-26

# Quick Fix

- remove dependency shaply (numpy) as it conflicted with some unofficial HA installations

# Others


## Fixed sources

- Fix buergerportal_de bedburg (thanks @shelker)
- Updated AWHas ICS Documentation (thanks @auenkind)
- Fixed lrasha_de (thanks @steffenrapp)
- fixed blacktown_nsw_au_gov (thanks @ReneNulschDE)
- fixed exeter_gov_uk (thanks @ReneNulschDE)

## Added sources

- added London Borough of Barking and Dagenham (thanks @MrGench)
- added ICS source Stadtwerke Hürth
- added Hutt City Council, NZ (thanks @meringu)

## Improved Sources

- Fix Cheshire East Garden Waste naming (thanks @greghesp)




## [1.45.0] - 2024-01-15

## Sensor Improvements

- details_format now supports value "hidden" (thanks @swoga)

## Added sources

- added source rambo_se (@5ila5)
- added proper ICS documentation for Muensingen, Bern, Switzerland (thanks @splattner)
- added ICS documentation for Vancouver, Canada
- added source Lunds renhållningsverk, Sweden (thanks @VermiumSifell)
- added source Blackpool Council, UK (thanks @incognitojam)
- added documentation for multiple regions supported by jumomind_de (@5ila5)
- added Yarra Ranges Victoria, Australia (thanks @bdog720)
- added Swansea Council, UK (thanks @pe5er)
- added ICS documentation for ekm mittelsachsen (thanks @ksandig)
- added ICS documentation for Contarina, Treviso, Italy (thanks @CremaLuca)
- added ICS documentation for Kreis Plön (thanks @benjaminangerer)
- added ICS documentation for Gipsprojekt/Heidelberg (@5ila5)
- added ICS documentation for multiple Austrian areas: muellapp.com (thanks @fprokop)
- added Kreis Unna to AbfallnaviDe (thanks @maxirnilian)
- added City of Ballarat, Australia (thanks @jamhos)
- added ICS documentation for worms_de (thanks @omphteliba)
- added source Hobsons Bay City Council in VIC, Australia (thanks @MrBretticus)
- added source Redland City Council Australia
- added Lichfield District, UK (thanks @Troon)
- added  Merri-bek City Council in VIC, Australia (thanks @actuallydamo)
- added London Borough of Harrow, UK (thanks @AitorDB)
- added Winnipeg MB, Canada (thanks @coreyjansen)
- added Moray Council, UK (thanks @dewet22)
- added Montreal, UK (thanks @julienboriasse)
- added Gästrikland, Sweden (thanks @emiltorp)
- added Bedburg, Germany to buergerportal_de (@5ila5)

## Fixed sources

- fixed mojiodpadki.si (thanks @akomelj)
- fixed hausmuell_info for Erfurt (@5ila5, thanks @panteLx and @SavageCore) 
- fix rushmoor_gov_uk (@5ila5, thanks @panteLx)
- fixed minrenovasjon_no (@5ila5)
- fixed offenbach_de (thanks @deese)
- fixed renosyd_dk (thanks @lexitus)
- fixed geelongaustralia_com (thanks @dtbell91)
- fixed zva_wmk_de (@5ila5, thanks @Demel75) 
- fixed wirral_gov_uk (thanks @mikestir)
- fixed sysav_se ( @5ila5)
- fixed abfallnavi_de did not work for some regions like Unna (@5ila5)
- fixed stavanger_no (@5ila5)
- fixed Tonbridge & Malling, UK not showing next year collections (@5ila5)
- fixed Westberks, not showing next year collections (@5ila5)
- fixed fix_was_wolfsburg_de (@5ila5)
- fixed abfallwirtschaft_pforzheim_de properly collect next years data (@5ila5)
- fixed ccc_govt_nz not respecting holiday overwrites (thanks @georgenell)
- fixed movar_no (thanks @seedzero)
- fixed awb_bad_kreuznach_de (@5ila5)
- fixed karlsruhe_de (thanks @alu-ka / @5ila5)  
- fix fccenvirounment_co_uk for harbourough region (@5ila5)

## Source improvements

- sbazv_de does not show every event twice now
- muellabfuhr_de now supports district and street parameter (thanks @MedicusOne)
- dudley_gov_uk now respects xmas holidays
- app_abfallplus_de added corner case fix (thanks @neffs)
- cornwall_gov_uk now supports garden waste collections
- abfall_zolleralbkreis_de now supports city/street NAMES, removed types argument (@5ila5)
- abfall_lippe_de now fetches next year in December (@5ila5)
- abfallwirtschaft_vechta_de now fetches next year in December (thanks @snow2k9) 
- bsr_de now fetches next year in November & December and Christmas tree collections (thanks @tr4nt0r)
- basildon_gov_uk, now uses new API, Allows to use UPRN (thanks @Eyeanman)
- updated nuernberger_land_de documentation for new address id format (thanks @flushbug)
- update tewkesbury_gov_uk to use the new API switching to UPRN instead of postcode is recommended (thanks @tribey2)
- geoport_nwm_de now returns all collections (@5ila5)




## [1.44.0] - 2023-12-02

# General Improvements

- Allow to use other fields than summary in ical source for event title

# Sources 

## Added sources

- added source Warwick District Council, UK (thanks @dt215git)
- added source Erd, Hungary (thanks @TMShader)
- added source TBV Velbert, DE (thanks @ndt)
- added source Adur & Worthing Councils (thanks @kdavis)
- added Recycle Coach documentation for Aurora, ON, Canada (thanks @EthanGe77)
- added source cederbaum_de, Braunschweig paper collection (thanks @pogross)
- added source Edlitz, Austria  (thanks @dt215git)
- added source Blacktown City Council, Australia (thanks @rayoz12)
- added ICS documentation for abikw_de (@5ila5)
- added ICS documentation for Anglesey, UK (@5ila5)
- added ICS documentation for Moreton Bay, Australia (@5ila5)
- added source BIR, Norway (thanks @odin-h)
- added source haringey_gov_uk (thanks @marcjay)
- added ICS documentation for Frechen, Germany (thanks @panteLx)
- added source to read in json files created by [UKBinCollectionData](https://github.com/robbrad/UKBinCollectionData) (thanks @dt215git)
- added source Lancaster City Council, UK (thanks @WillFantom)
- add source County Borough Council (thanks @tomusher)
- add source Alchenstorf, CH (thanks @1337hium)

## Fixed sources

- fixed northlincs_gov_uk (thanks @dt215git)
- fixed source pgh.st (thanks @gazpachoking)
- fixed bristol_gov_uk failing on some collections (thanks @johnbutton1200)
- fixed mamirolle info (thanks @AghilasMessara)
- fixed stockton_gov_uk for some addresses (thanks @deanlongstaff)
- fixed newcastle_staffs_gov_uk (thanks @dt215git)
- fixed redbridge_gov_uk (thanks @chrisns)
- fixed bristol_gov_uk (thanks @M21B8)
- fixed staedteservice_de (@5ila5)
- fixed zva_sek_de (thanks @HolliDolli)
- fixed wokingham_gov_uk (thanks @badguy99)
- fixed waverley_gov_uk and northherts_gov_uk not properly checking house number any more (@5ila5)
- fixed portsmouth_gov_uk (@5ila5)
- fixed cardinia_vic_gov_au (thanks @Zachoz)
- fixed citiesapps, now requires authentication (@5ila5) 
- fixed midsussex_gov_uk (@5ila5)
- fixed rh_entsorgugn_de (@5ila5)

## Improved sources

- updated dudley_gov_uk (thanks @dt215git)
- improved Republic Services (thanks @dt215git)
- ICS source fixed a issue with reoccuring and excluded events (@5ila5)
- abfallnavi_de fixed a bug where only events in the next calendar year where returned for some very limited addresses (@5ila5)
- karlsruhe_de now supports the ladeort argument (thanks @acn128)
- nsomester_gov_uk now shows the next two collections of each type (@5ila5)
- southampton_gov_uk removed duplicate entries (thanks @paulschmeida)
- app_abfallplus_de now supports the bezirk parameter (@5ila5)




## [1.43.0] - 2023-10-17

# added sources

- awigo_de Landkreis Osnabrück, Germany (@5ila5)
- Yorkshire Council - Hambleton, UK (@5ila5)
- Allerdale, UK (thanks @dt215git)
- FKF Budaörs, HU (thanks @TMShader)
- Wokingham, UK (thankgs @dt215git)
- West and Chester, UK (thanks @bbrks)
- GVA Baden, Austria (thanks @dt215git)
- Enzkreis, Germany ICS documentation (@5ila5)
- Tameside, UK (thanks @dt215git)
- FKF Budapest, HU (thanks @TMShader)
- Lincoln, UK (@5ila5)
- Mansfield, UK (thanks @dt215git)
- Mamirolle, France (thanks @AghilasMessara)
- AHE, Germany (@5ila5)
- ICS source abfall_app_net (@5ila5)
- add source umweltverbaende.at  serving multiple municipalities (thanks @dt215git)
- ICS source eva_abfallentsurgung_de (thanks @benidiet)
- ICS source ALBA Braunschweig (@5ila5)
- add source mansfield.vic.gov.au (thanks @tathamoddie)
- add source app_abfallplus_de which supports a lot of apps provided by abfallplus, Germany (@5ila5)
- add source for Hart District Council (thanks @iangregory)
- add source Shellharbour Waste, AU (thanks @daffster) 

# source fixes

- fixed cities_apps_com (@5ila5))
- fixed recyclecoach_com does not display canceled events anymore
- fixed minor bug in Croydon, UK (thanks @dt215git)
- fixed bielefeld_de (@5ila5)
- fixed SRV återvinning (thanks @FedericoKlappenbach)
- fix Inner West AU displaying wrong collection dates (@5ila5)
- fixed okc_gov requests being blocked (@5ila5)
- minor fix for whittlesea_vic_gov_au (thanks @mikz-t)

# sources flagged deprecated

- source `scheibbs_umweltverbaende_at` and `baden_umweltverbaende_at` are deprecated and may be removed in the future please migrate to the new `umweltverbaende_at` source


# minor source improvements/fixes 

- renosyd_dk now shows all collection (previously missing "240 L") (thanks @LasseLegarth)
- Maroondah VIC AU use new system (old configurations should still work) (thanks @DanAE111)
- add Morris, MB, Canada to recollect documentation (thanks @JamesGiesbrecht)
- fixed issue with c_trace_de, added `gemeinde` parameter (@5ila5) 
- fixed not listed collections for southglos_gov_uk (thanks @AlexCPU)




## [1.42.0] - 2023-08-30

# General improvements

Added `event_index` as sensor parameter (@5ila5)

# Sources:

## new sources

- add source Renosyd, Denmark (thanks @lexitus)
- add source Dunedin, Otago, NZ (thanks @dt215git)
- add source Windsor & Maidenhead, UK (@5ila5)
- add source KIng's Lynn & West Norfolk, UK (thanks @dt215git)
- add source Landkreis Kusel, Germany (@5ila5)
- add source Stratford DC, UK (thanks @12pt)
- add source Burnley, UK (thanks @dt215git)
- add _unofficial_ source Chiemgau Recycling (thanks @cebor)
- add ICS source documentation Kreisstadt Groß-Gerau (thanks @thebub)
- add source Hamilton City, NZ (thanks @danzel)
- add source iTouchVision (Somerset + Test Valley), UK (thanks @dt215git)
- add source Woking Borough Council / Joint Waste Solutions, UK (thanks @dt215git)
- add source Kreis Lippe, Germany (@5ila5)
- add source Kreis Emsland, Germany (@5ila5)
- add source Cardiff, UK (thanks @sgsabbage)
- add source Aylesbury Vale District Council, UK (thanks @dt215git)
- add source GVU Scheibbs, Austria (thanks @dt215git)
- add source Calgary, AB, Canada (thanks @adechant)
- add source Stoke, UK (thanks @bbr111)
- added support for 'subcouncils' of innerwest.nsw.gov.au 
- added source Crawley, UK (@5ila5)
- added source East Renfrewshire, UK (thanks @EuanFH)
- added source Rhondda Cynon Taf, UK (thanks @dt215git)
- add source London Borough of Camden (@5ila5)
- add source Dudley, UK (thanks @dt215git)
- add source Gwynedd Council, UK (@5ila5)
- add source Durham County Council, UK (thanks @dt215git)
- add source Sandnes, Norway (@5ila5)
- add source iris-salten, Norway serving multiple municipalities (@5ila5)

## Fixes:

- fixed ssl error of CmCityMedia (thanks @Newspicel)
- fixed bug with recyclecoach_com when using not all capitalized district_id (thanks @smffraser (fixed by @5ila5))
- fixed Norfolk and Broadland
- now verifying SSL for kwu_de 
- fixed source eastriding_gov_uk (thanks @dt215git)
- fixed source cherwell_gov_uk (thanks @dt215git)
- fixed source basingstoke_gov_uk (@5ila5)
- fixed source hausmuell_info, that did not work correctly for some `subdomain` with `ortsteil` containing special characters (@5ila5)
- fixed source samilio_se (@5ila5)
- fixed source nottingham_city_gov_uk (thanks @jwhitbread)
- fixed source exeter_gov_uk (thanks @dt215git)
- fixed source maroondah_vic_gov_au (thanks @lyonzy)
- fixed source lakemac_nsw_gov_au (thanks @lachlan-stevens)
- fixed source Exeter, UK (thanks @AtomBrake)
- fixed source midsussex_gov_uk (@5ila5)

## minor improvements:

- Update warszawa19115_pl to use new API (thanks @FliesWithWind)
- bristol_gov_uk now shows collections that are due "today" (@5ila5)




## [1.41.0] - 2023-07-14

BREAKING CHANGES
- removed stadt_willich_de (not working anymore) Please migrate to the abfallnavi source
- Norfolk and Broadland Does not work for this release if you use the `Norfolk and Broadland` source skip this update or install the master version

ADDED
- add source North Kesteven, UK (thanks @dt215git )
- add source East Riding, UK (thanks @dt215git) 
- add source Bath & North East Somerset, UK (thanks @trvrnrth)
- add source Maidstone, UK (thanks @CalamityJames)
- add source Wealden County Council, UK (thanks @ryanbdclark)
- add ICS source HWS Halle, Germany (thanks @pomeloy)
- add source Redbridge, UK (thanks @chrisns)
- add ICS source Reutlingen, Germany (thanks @QWellCOD)
- add ICS source Trondheim, Norway (@5ila5)
- add source my waste mobi, USA (thanks @expl0ratory)
- add source mags Mönchengladbach, Germany (thanks @fr34kyn01535)
- add source Ashford, UK (@5ila5)
- add source Australian Captial Territory, Australia (thanks @eddster2309)
- add source Logan City Council, Australia (thanks @sh-nguyen)
- add source Broxtowe County, UK (@5ila5)
- add source Armadale WA, Australia (@5ila5)
- add source South Holland District Council, UK (@5ila5)
- add source Warrington, UK (thanks @PJnes)
- add source Highland, Scotland, UK (@5ila5)
- add documentation for Kulmbach to awido_de (thanks @raphaelheinz)

Fixes/improvements:
- fix aberdeenshire_gov_uk (thanks @dt215git)
- improve thehills_nsw_gov_au argument searching (@5ila5)
- eastherts_gov_uk Fixing variable names and add support for garden waste (thanks @WhimsySpoon)
- south_norfolk_and_broadland_gov_uk.py add better configuration options (@5ila5)
- awb_bad_kreuznach add support for the new App (@5ila5)
- fixed northlincs_gov_uk (thanks @dt215git)
- fixed documentation for `use_dedicated_calendar` and `dedicated_calendar_title` (thanks @pomeloy)
- fixed Republic Services sometimes showing wrong pickup dates near holydays 
- fixed bielefeld_de after an URL change (thanks @janpfischer)
- add Mühldorf to awido_de source (@mampfes)




## [1.40.0] - 2023-05-21

- fix source grafikai_svara_lt (thanks @justasmalinauskas)
- add source fareham.gov.uk (thanks @Sam-Killgallon)
- add source reigate gov uk (thanks @JonReed)
- improved source infeo_at (thanks @dm82m)
- add source South Tyneside Council, UK (thanks @dt215git)
- add source Portsmouth, UK (thanks @sailseaplymouth)
- add source South Gloucestershire, UK (thanks @mitchelldyer)
- add source Lisburn and Castlereagh, UK (thanks @benlyall)
- add source Exeter, UK (thanks @dt215git)
- add source Wirral, UK (thanks @dt215git)
- fix ReCollect docu (thanks @kaechele)
- add source Kirklees council, UK (thanks @SplinterHead)
- add source Aberdeenshire, UK (thanks @dt215git)
- add source City of Kingston, VIC, Australia (thanks @dt215git)
- add source Potsdam, Germany (@5ila5)
- add source Croydon, UK (thanks @dt215git)
- better display previously supported services by source jumomind_de (@5ila5)
- add source Welwyn Hatfield Borough Council, UK (thanks @tevers200)
- add source Port Adelaide Enfield, South Australia (@5ila5)
- add source real_luzern_ch (thanks @StefanHuettenmoser)




## [1.39.0] - 2023-04-20

- add source Wrocław, Poland (thanks @jbortkiewicz)
- improve HVCgroep, NL source (thanks @se-bastiaan)
- add source Stockton-on-Tees Borough Council, UK (thanks @5ila5)
- fix Stevenage, UK (thanks @dt215git)
- add source hausmuell.info (thanks @5ila5)
- update campbelltown_nsw_gov_au (thanks @dstreefkerk)
- add Buckinghamshire Waste Collection (thanks @kanthamohan)
- add a lot of examples for ICS source
- add source AWB Main-Bingen (thanks @5ila5)
- improve source SSAM.se (thanks @stefan-jonasson)
- add source Cherwell District Council, UK (thanks @dt215git)
- add source Region Hannover, Germany (thanks @5ila5)
- improve source C-Trace.de (thanks @5ila5)
- added source Kiel, Germany (thanks @5ila5)
- adding source Bexley, UK (thanks @dt215git)
- add source basildon, UK (thanks @Eyeanman)
- add source CITIES, for a lot of Austrian cities (@5ila5)
- some more fixes and new sources. Thanks to all contributors. I will not list every change here anymore, because this causes too much effort.




## [1.38.0] - 2023-04-01

- fix awido_de to work correctly if no street specified (thanks @5ila5)
- add source Wigan Council, UK (thanks @dt215git)
- add source North Lincolnshire Council, UK (thanks @5il5a)
- add source Esch-sur-Alzette, Luxembourg (thanks @framesfree)
- add source Leicester City Council, UK (thanks @lwward)
- add VIVO Landkreis Miesbach to abfall.io wizard (thanks @macrojames)
- add support for weekdays to status source (thanks @5ila5)
- add week support to sysav_se (thanks @5ila5)
- add source Heilbronn, Germany (thanks @5ila5)
- fix missing dates in meinawb_de (thanks @Andre0512)
- add source Uppsala Vatten och Avfall AB, Sweden (thanks @Lance0095)
- add source London Borough of Merton (thanks @ryck)
- add source West Dunbartonshire Council, UK (thanks @AndrewBarber)
- add source Fenland District Council, UK (thanks @michaeljones32)
- add source City of Doncaster Council, UK (thanks @dt215git)
- add source East Northamptonshire and Wellingborough, UK (thanks @5ila5)
- add source Gateshead Council, UK (thanks @elibretto)
- add source Runnymede Borough Council, UK (thanks @sjpickup)
- add source Tonbridge and Malling Borough Council, UK (thanks @5ila5)
- add source Rotherham Metropolitan Borough Council, UK (thanks @5ila5)
- add source ASR Stadt Chemnitz, Germany (thanks @5ila5)
- add source Zweckverband Abfallwirtschaft Kreis Bergstraße, Germany (thanks @5ila5)
- add source Bristol City Council, UK (thanks @5ila5)
- add source AWB Abfallwirtschaft Vechta, Germany (thanks @5ila5)
- fix Campbelltown NSW, AU (thanks @dstreefkerk)
- add source Fife Council, UK (thanks @5ila5)
- add source Abfallwirtschaft Pforzheim, Germany (thanks @5ila5)
- add source KS Börde, Germany (thanks @MeisterBob)




## [1.37.0] - 2023-03-18

- add Landkreis Fulda to awido_de (thanks @stbkde)
- fix source Oldenburg (thanks @dt215git)
- add example for ICS source ZAH Hildesheim (thanks @King3R)
- add source Mid-Sussex District Council, UK (thanks @dt215git)
- add source Uttlesford District Council (thanks @dearlove)
- add source Poznań/Koziegłowy/Objezierze/Oborniki, Poland (thanks @piotrmilcarz)
- add Landkreis Aschaffenburg to awido_de (thanks @Rodelkoenig)
- add source North Herts Council, UK (thanks @gingemonster)
- add source Southoxon, UK (thanks @andrew-schofield)
- add source Liverpool City Council, UK (thanks @dearlove)
- add source Swindon Borough Council, UK (thanks @joshwillcock)
- add source Offenburg, Germany (thanks @deese)
- workaround for KWU Entsorgung Landkreis Oder-Spree (thanks @paschdan)
- add source London Borough of Bromley, UK (thanks @dt215git)
- add source Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis (thanks @5ila5)




## [1.36.0] - 2023-03-01

- add source Schweinfurt, Germany (thanks @bbr111)
- add source ZAW-online, Germany (thanks @5ila5)
- add source EAD Darmstadt, Germany (thanks @5ila5)
- add source EGST to abfall.io, Germany (thanks @5ila5)
- add source ReMidt, Norway (thanks @5ila5)
- add source Basingstoke and Deane Borough Council], UK (thanks @dt215git)
- add Landkreis Weißenburg-Gunzenhausen to abfall.io (thanks @ChLah)
- add source AWV Isar-Inn (thanks @m4c3)
- add source Blackburn with Darwen Borough Council, UK (thanks @5ila5)
- add source Abfallwirtschaft Germersheim, Germany (thanks @5ila5)
- add source Herefordshire City Council, UK (thanks @Jab2870)
- add source City of Onkaparinga Council, Australia (thanks @nathanhaigh)
- add source Whittlesea City Council, Australia (thanks @jezzaaa)
- fix fetch_data service call
- add source Hume City Council, Australia (thanks @seedzero)
- add support for cmcitymedia.de, Germany (thanks @Newspicel)
- fix TLS issue with fccenvironment.co.uk (thanks @cpressland)
- add source Cardinia Shire Council, Australia (thanks @seedzero)
- extend ctrace_de source (thanks @5ila5)
- add source Movar IKS, Norway (thanks @seedzero)




## [1.35.0] - 2023-02-07

- add source Chichester District Council, UK (thanks @mikenorgate)
- add Glasgow City Council, UK (thanks @gingemonster)
- ics source: handle files with UTF BOM correctly
- add source Linköping - Tekniska Verken, Sweden (thanks @juppe1969)
- add source Region Gotland, Sweden (thanks @oskarannas)
- add source Oxford City Council, UK (thanks@rbrunt)
- add source Jönköping - June Avfall & Miljö, Sweden (thanks @arvjos)
- add source Maldon District Council, UK (thanks @gingemonster)
- add source Amber Valley Borough Council, UK (thanks @dt215git)
- add source South Derbyshire District Council, UK (thanks @gingemonster)
- add source Moji odpadki, Ljubljana, Slovenia (thanks @akomelj)
- add source Lake Macquarie City Council, Australia (thanks @bbr111)
- add source Wollongong City Council, Australia (thanks @daffster)
- add source Stavanger, Norway (thanks @bbr111)




## [1.34.0] - 2023-01-19

- fix braintree_gov_uk (thanks @BenSuskins)
- add source Wyre Forest District Council, UK (thanks @ConfusedTA)
- add source Grosswangen, Switzerland (thanks @bbr111)
- add source Newcastle under lyme, UK (thanks @dt215git)
- fix stadtreinigung_leipzig_de
- add source Abfallwirtschaft Stadt Fürth, Germany (thanks @sir106)
- fix missing waste type for c_trace_de (WZV)
- add Regensburg to awido_de (thanks @Jaegerstefan)
- add source Central Bedfordshire Council, UK (thanks @gingemonster)
- add source Harlow Council, UK (thanks @ConfusedTA)
- add Abfallwirtschaftsbetrieb Ilm-Kreis to ICS docu (thanks @immenz)
- add source Waverley Borough Council, UK (thanks @gingemonster)
- add source Münchenstein, Switzerland (thanks @r3turnNull)
- add source East Herts Council, UK (thanks @gingemonster)
- add source East Cambs District Council, UK (thanks @ConfusedTA)
- add source Newport City Council, UK (thanks @ConfusedTA)
- add source Maribyrnong Council, Australia (thanks @dpeluso)
- add source Stockport Council, UK (thanks @MuddyRock)




## [1.33.0] - 2023-01-06

- add source Ashfield District Council, UK (thanks @ConfusedTA)
- add source City of Gold Coast Council, Australia (thanks @TheBlackMini)
- add source AWB Kreis Ahrweiler, Germany (thanks @Andre0512)
- improve buergerportal_de (thanks @mirkolenz)
- add service providers to c_trace_de docu (thanks @dabenzel)
- fix kwu_de (thanks @maverickme)
- add source Abfallwirtschaft Nürnberger Land, Germany (thanks @jodli)
- split waste types for stadtservice_bruehl_de
- add source Salford City Council, UK (thanks @FilHarr)
- add source SWD Dillingen Saar, Germany (thanks @rubenkr)
- add Circulus, Netherlands (thanks @erik-jan-p)
- fix awb_oldenburg_de (thanks @chbartsch)
- add source Horsham District Council, UK (thanks @mystcb)
- add source Landskrona - Svalövs Renhållning, Sweden (thanks @troed)
- add source Southampton City Council, UK (thanks @dt215git)
- add source Telford and Wrekin Council, UK (thanks @alistairclare)




## [1.32.0] - 2022-12-30

- add source ART Trier, Germany (thanks @mirkolenz)
- add source Stadtservice Brühl, Germany (thanks @bbr111)
- add source Bracknell Forest Council, UK (thanks @cpressland)
- add source Braintree District Council, UK (thanks @cpressland)
- add source Abfallwirtschaft Werra-Meißner-Kreis, Germany (thanks @Demel75)
- awb_es_de: fetch all available ICS files (thanks @meilon)
- enhance hvcgroup_nl to support further Dutch municipalities
- add avalex and westland to ximmio_nl source
- remove defect source muenchenstein_ch
- remove defect source avl_ludwigsburg_de
- fix year transition issue for erlangen_hoechstadt_de
- fix year transition issue for elmbridge_gov_uk
- add source Nillumbik VIC, Australia (thanks @DanAE111)
- add source for Bürgerportal, Germany (thanks @mirkolenz)
  **NOTE**: This replaces the existing source for Cochem-Zell because it will not work anymore in 2023. Please upgrade your configuration.
- add source SRV Atervinning, Sweden (thanks @bbr111)
- add support for South Hams and West Devon, UK via fccenvironment_co_uk (thanks @cpressland)
- add source Landkreis Nordwestmecklenburg, Germany (thanks @fwinn)
- **improve documentation** (thanks @dt215git)
- add source Breckland Council, UK (thanks @bbr111)




## [1.31.0] - 2022-12-18

- add community support for ecoharmonogram_pl (thanks @tiwek)
- add source Maroondah City Council, Australia (thanks @DanAE111)
- add source Kauno švara, Lithuania (thanks @justasmalinauskas)
- add source London Borough of Lewisham, UK (thanks @barcar)
- add source Erlangen-Höchstadt, Germany (thanks @fwinn)
- add source RecycleSmart, Australia (thanks @calvinbui)
- add source KWU Landkreis Oder-Spree, Germany (thanks @maverickme)
- add examples for Bogenschütz to infea_at (thanks @dm82m)
- fix canterbury_gov_uk (thanks @GigaByte4711)
- add source Tewkesbury Borough Council, UK (thanks @Rohaq)
- add source Horowhenua District, New Zealand (thanks @craSH)`
- add support for multiple links to aw_harburg_de
- remove logging output for abfall_io
- add support for XML to umweltprofis_at
- add source Städteservice Raunheim/Rüsselsheim, Germany (thanks @ubl8)
- support to link a sensor to multiple sources
- add source Wermelskirchen, Germany (thanks @lal12)
- expand result for wiltshire_gov_uk (thanks @mcbalston)
- retrieve data of 1 year for canadabay_nsw_gov_au (thanks @calvinbui)
- add source Middlesbrough Council, UK (thanks @ximon)
- add source Kingston Council, UK (thanks @ximon)
- add source Abfall Neunkirchen Siegerland, Germany (thanks @bbr111)
- add source Toronto, Canada (thanks @constvariable)
- add source Korneuburg, Austria (thanks @53RT)




## [1.30.0] - 2022-11-24

- add source Südbrandenburger Abfallzweckverband (SBAZV), Germany (thanks @tj551955)
- fix aucklandcouncil_govt_nz (thanks @dt215git)
- adds districts to ecoharmogram (thanks @pawelhulek)
- add support for Limburg-Weilburg, Germany again (thanks @greenishhhh)
- add source City of Canada Bay Council, Australia (thanks @calvinbui)
- add source infeo.at - bogenschuetz-entsorgung.de (thanks @dm82m)
- add source Walsall Council, UK (thanks @dt215git)
- add source Sheffield City Council, UK (thanks @NSF12345)
- add source Landkreis Forchheim, Germany (thanks @fwinn)




## [1.29.0] - 2022-11-06

- fix chesterfield_gov_uk (thanks @dt215git)
- add source Richmondshire, North Yorkshire, UK (thanks @theanorak-keith + @dt215git)
- fix Wiltshire, UK (thanks @rust84)
- add new cities to abfallnavi_de (thanks @Mammut-Felix)
- fix recycleapp_be (thanks @dt215git)
- fix ecoharmonogram_pl (thanks @pawelhulek)
- add source Elmbridge Borough Council, UK (thanks @dt215git)
- add Umweltbetrieb Stadt Bielefeld, Germany (thanks @MFlasskamp)
- (temporary) fix awb_es_de (thanks @meilon)




## [1.28.0] - 2022-10-20

- add source Muenchenstein, BL, Switzerland (thanks @r3turnNull)
- add source Wyndham City Council, Australia (thanks @mukundv)
- fix chesterfield_gov_uk (thanks @dt215git)
- fix Oslo, Norway (thanks @dagingaa)
- fix Wuerzburg, Germany (thanks @tschlueter)
- fix Wiltshire, UK (thanks @eli-randi)
- add "Ostallgäu" to abfall_io wizard (thanks @ShadNex)
- add source Waipa District, New Zealand (thanks @DevilasNZ)
- add source Newcastle-Upon-Tyne, UK (thanks @SplinterHead)
- fix warszawa19115_pl (thanks @FliesWithWind)
- add Landkreis Bayreuth, Germany to abfall_io wizard (thanks @sti0)
- add source Abfallwirtschaft Neckar-Odenwald-Kreis, Germany (thanks @sti0)
- add source Landkreis Rhön Grabfeld, Germany (thanks @Random-Cow)




## [1.27.0] - 2022-10-02

- add source Oslo Kommune, Norway (thanks @ccsalvesen)
- add source KAEV Niederlausitz (thanks @aschobba)
- add example for Märkisch-Oderland to ics.md (thanks @Rocka84)
- add LK Traunstein to abfall.io wizard (thanks @abbe79)
- add London Borough of Bromley to ics (thanks @geozza123)
- add source ECO Harmonogram, Poland (thanks @pawelhulek)
- fix ccc_govt_nz (thanks @codyc1515)
- add Lübeck Entsorgungsbetriebe to ics (thanks @LennardPlay)
- add source Stevenage Borough Council, UK (thanks @mehstg)
- add source Stadt Willich, Germany (thanks @p-rintz)




## [1.26.0] - 2022-08-27

- add source Ronneby Miljöteknik, Sweden (thanks @crazzy)
- add support for ASO OHZ to Abfall.IO (thanks @misery)
- fix waste types for SSAM.se (thanks @vasaru)
- fix recycleapp.be (thanks @algra4)
- add source Rushmoor Borough Council, UK (thanks @SavageCore)
- add source Manchester City Council, UK (thanks @thinkl33t)
- remove python 3.10 type hints (to re-enable python 3.9 support)




## [1.25.0] - 2022-08-12

- add source South Norfolk and Broadland Council, UK (thanks @issy)
- update RepublicServices.com with yard waste marker (thanks @johnsonnc)
- add source Landkreis Schwäbisch Hall, Germany (thanks @steffenrapp)
- add source Min Renovasjon, Norway (thanks @ccsalvesen)
- add source Inner West Council, Australia (thanks @aaronpowell)




## [1.24.0] - 2022-07-31

- add source Guildford Borough Council, UK (thanks @brewston)
- add support for dedicated calendars per waste type (thanks @ejjoman)
- add source Melton City Council, Melbourne (thanks @ankycooper)
- add source for Republic Services, USA (thanks @DeadEnded)
- add source Wiltshire Council, UK (thanks @rust84)
- add source for static schedules (thanks @ejjoman)
- fix upcoming events in calendar (thanks @ejjoman)
- fix blocking call in source warszawa19115_pl (thanks @bertmelis)
- add source Canterbury City Council, UK (thanks @sultanhq)
- add source SSAM.se (thanks @vasaru)
- add source West Berkshire Council, UK (thanks @hdurdle)




## [1.23.0] - 2022-07-12

- fix TLS issue for bradford_gov_uk (thanks @medains)
- add source for Huntingdonshire District Council, UK (thanks @johnnieblows)
- update api endpoint for recycleapp_be (thanks @PieterVerledens)
- add source for Derby City Council, UK (thanks @Azelphur)
- add source for Nottingham City Council, UK (thanks @AaronJackson)
- add source for Chesterfield, UK (thanks @dt215git)
- fix wuerzburg_de (thanks @rikroe)
- add source for Cochem-Zell, Germany (thanks @mirkolenz)
- refactor ICS parser (thanks @mirkolenz)
- add support for regex for ICS source




## [1.22.0] - 2022-06-26

- new source North Somerset Council, UK (thanks @andrewbeaton)
- add support for devcontainer (thanks @ejjoman)
- new source Cornwall Council, UK (thanks @jaffakke)
- new source ALW Wolfenbüttel, Germany (thanks @envy)
- now source Harborough District Council, UK (thanks @dt215git)




## [1.21.0] - 2022-06-04

- fix source nawma_sa_gov_au
- add source scambs_gov_uk (thanks @dt215git)
- add source peterborough_gov_uk (thanks @skipishere)
- add source kuringgai_nsw_gov_au (thanks @dt215git)
- add source environmentfirst_co_uk (thanks @dt215git)
- add source belmont_wa_gov_au (thanks @robbo600)
- return date instead of datetime for banyule_vic_gov_au (thanks @ravngr)
- test_sources.py: test if source returns invalid date format
- add source cheshire_east_gov_uk (thanks @greghesp)




## [1.20.0] - 2022-05-12

- add source campbelltown_nsw_gov_au (thanks @jameshirka)
- use new HA calendar data model
- add source c_trace_de, used by Bremer Stadtreinigung
- add source warszawa19115, Poland (thanks @FliesWithWind)
- fix source york_gov_uk (thanks @marcoaddario)
- fix source bmv_at
- fix source rh_entsorgung_de




## [1.19.1] - 2022-04-24

- fix missing data for source a_region_ch




## [1.19.0] - 2022-04-23

- add source for AWB Oldenburg, Germany (thanks @chbartsch)
- add source for AWB Esslingen, Germany
- ignore special events for brisbane.gld.gov.au (thanks @trstns)
- add unique_id to calendar
- add source for AWB Limburg-Weilburg, Germany (thanks @AtryFox)
- add source for VA Syd, Sweden (thanks @stefanodesjo)
- fix source Christchurch City Council, New Zealand (thanks @codyc1515)
- add source for WSZ Moosburg (thanks @dweinber)
- add source for Ipswich City Council, Australia (thanks @tonymyatt)
- add source for A-Region, Switzerland




## [1.18.0] - 2022-04-02

- disable ssl check for berlin_recycling_de
- add source bmv.at
- add Ortenaukreis to abfall_io wizard (thanks @danuvius92)
- add support to disable ssl certificate check for ICS source
- add source for Harburg, Germany (thanks @percidae)
- add source for Ludwigsburg, Germany (thanks @percidae)




## [1.17.0] - 2022-03-22

- add source for AWB Bad Kreuznach, Germany
- add source for Wellington City Council, New Zealand (thanks @catatonicChimp)
- support events for recycleapp_be
- improve documentation (thanks @kellyatkinson, @snowstoked)
- add source for umweltprofis.at (thanks @andyboeh)
- add source for Stadtreinigung Dresden, Germany (thanks @tschnilo)




## [1.16.0] - 2022-03-06

- add Ostalbkreis to abfall_io wizard (thanks @ranseyer)
- add limburg.net to ics source docu (thanks @d3claes)
- add source for KWB Goslar.de (thanks @haitec)
- add source for banyule.vic.gov.au (thanks @ravngr)
- add source for mrsc.vic.gov.au (thanks @tathamoddie)
- add source for cambridge_gov_uk (thanks @ciscoski)
- use icalevents instead of recurring_ical_events for ICS handling

NOTE: This releases substitutes the underlying ICS parser. Previously, `recurring_ical_events` was used. Due to some issues, this release switches the default to `icalevents`. If this change causes problems, add the following variable to your configuration:
```yaml
version: 1
```




## [1.16.0-pre2] - 2022-02-12

Prerelease to test icalevents.




## [1.15.0] - 2022-01-16

- add Heilbronn to abfall.io wizard (thanks @dergeberl)
- add source for NAWMA (thanks @TheNoctambulist)
- add source egn_abfallkalender_de (thanks @audacity363)
- remove source abfall_kreis_tuebingen_de (they switched to awido_de)
- improve city-only support for awido_de (no need to specify street for city-only sources)
- add eBe Essen to abfall_io wizard (thanks @Z0mbiel0ne)
- minor bugfixes (thanks @rikroe)
- add Ludwigshafen am Rhein to abfall_io wizard (thanks @FHeilmann)
- add source for Christchurch City Council, NZ (thanks @codyc1515)
- add source for York, UK (thanks @spamoom)
- add source for Würzburg, Germany (thanks @rikroe)




## [1.14.0] - 2021-12-26

- remove source oberhausen.de (thanks @buffcode)
- fix stadtreinigung.hamburg
- add source for lindau_ch (thanks @atrox06)
- add source for awr_de (thanks @abroooo)




## [1.13.1] - 2021-12-12

fix datetime conversion in recycleapp.be




## [1.13.0] - 2021-12-12

- add source for sysav.se (thanks @MHultman)
- add source for recycleapp.be
- fix issue in next year handling for ics




## [1.12.1] - 2021-12-04

- fix problem in ics source (thanks @jberrenberg)




## [1.12.0] - 2021-12-03

- add source for stonnington.vic.gov.au (thanks @tathamoddie)
- add support for prem_code to seattle.gov (thanks @buckbanzai)
- improve ics docu (thanks @ThomDietrich)
- fix next-year handling in ICS scraper




## [1.11.0] - 2021-11-05

- add source for hygea.be (thanks @xorob0)
- fix for source seattle_gov (thanks @atkulp)
- temporary fix for aucklandcouncil_govt_nz: disable cert check
- add support for Rhein-Neckar-Kreis to abfall_io wizard (thanks @martin3000)
- improve docu (thanks @martin3000, @matt8707)




## [1.10.0] - 2021-10-28

- add support for Alba Berlin in abfall_io wizard (thanks to @Jakob-Gliwa)
- add source awsh_de (thanks to @issue)
- add source oberhausen_de (thanks to @buffcode)
- add source landkreis_wittmund_de (thanks to @buffcode)




## [1.9.1] - 2021-09-20

bugfix release:
Fixes error introduced with split_at support for ICS data: If a waste type consists of more than 1 word, all words except the first have been changed to lower caps.




## [1.9.0] - 2021-09-19

- add source berlin-recycling.de
- allow local file path for pictures
- change shebang in wizards to respect venvs (thanks to @danielrheinbay)
- use regex for split_at in ics --> enables recollect.net (thanks to @cpw)




## [1.8.0] - 2021-09-12

add source for WAS Wolfsburg, Germany




## [1.7.0] - 2021-09-09

- add source for Rhein-Hunsrück Entsorgung (thanks to FelixGail)
- add source for Sector27.de (thanks to lubeda)
- add option to split waste collection types in ICS files




## [1.6.0] - 2021-07-20

- add source for Auckland Council, New Zealand
- add source for AWIDO, Germany




## [1.5.0] - 2021-07-04

- add source for hvcgroep, Netherlands
- add source for Lerum, Sweden
- improve error logging for ICS




## [1.4.1] - 2021-04-29

fix seattle_gov source - thanks to #gabosom

!!!Note!!!:  This is a breaking change because the source now returns the original waste type names.




## [1.4.0] - 2021-04-18

- add source for the hills council, Sydney, Australia
- add source for WasteNet, New Zealand
- add option to use post instead of get for ICS
  (thanks to coccyx00)




## [1.3.0] - 2021-04-03

- add support for MyMuell (provided by jumomind_de / Junker Digital)
- fix documentation




## [1.2.0] - 2021-04-01

- add calender
- add option `daysTo` which can be used to sort entities by days to next collection




## [1.1.0] - 2021-03-18

- fix abfall_io
- add source for brisbane, australia (thanks to trstns)
- confirm ICS for Abfallwirtschaft Kreis Böblingen
  (thanks to ChristophCaina)




## [1.0.2] - 2021-02-28

fix images in hacs docu




## [1.0.1] - 2021-02-28

- improve documentation (thanks to GLehnhoff)
- confirm Awista Starnberg ICS (thanks to Paddy0174)




## [1.0.0] - 2021-02-27

initial release




