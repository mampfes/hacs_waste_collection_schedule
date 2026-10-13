# Legacy sources: classification

Working document. It sorts the 281 remaining legacy (`fetch()`) sources on `release/3.0.0` by
**what the migration to a `BaseSource` pipeline source actually takes**, so the
backlog can be worked in the order that pays most. The total comes from
`python tools/arch_coverage.py --debt`; the scan that produced this file is
heuristic (request counts, endpoints, shared hosts, size), so treat a class as a
starting hypothesis and confirm it by reading the module before you migrate.
See [`legacy_deprecation_plan.md`](legacy_deprecation_plan.md) for what happens
when the count reaches zero.

## Summary

| # | Class | Sources | What it means |
|---|---|---:|---|
| 1 | Special / not a provider | 4 | Not a provider. Decide per module whether it stays a utility or gets a pipeline form. |
| 2 | Retire (deprecated shim or broken stub) | 8 | Delete, or reduce to an alias, in the major release following the deprecation lifecycle in `versioning.md`. Migrating them is wasted work. |
| 3 | Login required (policy conflict) | 10 | `CLAUDE.md` forbids login-required endpoints. Decide: keep as is, move out of the default set, or remove. |
| 4 | Migrate onto an existing platform component | 2 left (of 9) | A reusable component already exists in `service/`. Mostly mechanical; verify with a cassette. |
| 5 | Shared backend, build one component for the cluster | 1 left (of 44) | Several legacy sources share one backend. Write the shared component once, then each source is a few lines. Highest leverage. |
| 6 | PDF schedule | 1 left (of 14) | The schedule is a PDF: use the PDF parsers and preprocessors from the guide. |
| 7 | Singleton, small (<150 lines, <=2 requests) | 25 left (of 58) | Standalone and simple: one or two requests, short module. Fast, independent migrations. |
| 8 | Singleton, medium | 112 | Standalone, moderate: needs a declared multi-step retriever (`Lookup`/`Chain`) or a custom `pick`. |
| 9 | Singleton, large (>=350 lines or >=5 requests) | 24 (+1 from class 4) | Standalone, large or many-step. Likely wants a new shared component or a split; do last. |
| | **Total** | **183** (281 before class 4; the clusters, thirteen PDF sources and thirty-five small singletons are migrated, see the notes in class 5, 6 and 7) | |

## 1. Special / not a provider

- `example`: template for new sources
- `multiple`: wrapper combining several sources
- `static`: user-configured static schedule (no provider)
- `ukbcd`: reads JSON produced by an external project

## 2. Retire (deprecated shim or broken stub)

- `awb_mainz_bingen_de`: delegates to kaw_mainz_bingen_de, marked deprecated
- `byron_nsw_gov_au`: runtime deprecation warning (recyclecoach covers it)
- `chiltern_gov_uk`: subclass of iapp_itouchvision_com, marked deprecated
- `east_ayrshire_gov_uk`: runtime deprecation warning (ReCollect covers it)
- `grenchen_ch`: delegated to localcities_ch and was marked deprecated; it is a small pipeline source of its own now, because a `@final` source cannot be subclassed
- `lrasha_de`: raises on init, points to app_abfallplus_de
- `wieliczka_kiedyodpady_pl`: TITLE "(Deprecated)", runtime warning
- `wuerzburg_de`: TITLE "(deprecated)", points to the ICS source

## 3. Login required (policy conflict)

- `aen_minasidor_se`: needs account credentials
- `berlin_recycling_de`: needs account credentials
- `citiesapps_com`: takes a calendar password (check: shared calendar secret or account?)
- `fylde_gov_uk`: needs account credentials
- `kiertokapula_fi`: needs account credentials
- `mustankorkea_fi`: token login to oma.mustankorkea.fi (user name and password), every data call needs the token; not a shared backend with `rosknroll_fi`
- `rosknroll_fi`: Acegi session login with bill number and password, all data calls under `/secure/`
- `prodnik_si`: needs account credentials
- `recyclesmart_com`: needs account credentials
- `waste_havant_gov_uk`: needs account credentials

## 4. Migrate onto an existing platform component

Worked through on `release/3.0.0`. Done (7), with what the "existing platform" turned out to be:

- `braintree_gov_uk`: `JaduXfp.XfpFormRetriever`, matching the property by `address=`.
- `norwich_gov_uk`: `WhitespaceWRP` (street as an extra form field).
- `jointwastesolutions_org`: `WhitespaceWRP`; `WhitespaceRetriever(base_url=...)` now also takes a callable of the source params, for the per-borough hosts, plus `REGIONS`.
- `goap_poznan_pl`: not the `CTrace` ICS component. Only the cookieless session handshake is shared with it, so this is a declared `Request` with a `Lookup(allow_redirects=False)` and `HtmlGroupedDates`.
- `movar_no`: same fraction/calendar shape as MinRenovasjon but another host, token and camelCase keys; `MinRenovasjonParser` now reads either casing, the requests are a declared `FanOutRetriever`.
- `evv_voelklingen_de`: same vendor as `Buergerportal`, but a different parameter model (district only, container filter), so a declared `YearlyRetriever` cascade rather than the shared retriever.
- `sumavfall_no`: the `Tommekalender` parser does not fit this markup; `HtmlLabelledDates` does. Combined rounds are now split into canonical types.

Not done:

- `lerum_se`: fits `EdpFutureWeb` (written and discarded), but `vatjanst.lerum.se` answers this environment with `403 Access denied`, so it can be neither verified nor recorded. Retry from an allowed network.
- `south_norfolk_and_broadland_gov_uk`: reclassify as class 9. Three retrieval paths (cookie payload, postcode lookup, and a SOAP calendar chosen by a link on the summary page) need a component of their own; `WebAspxCollections` only covers the SOAP leg.

## 5. Shared backend: one component per cluster

Done: **umweltverbaende.at (AT)**: `umweltverbaende_at` (15 districts as `REGIONS`) and `baden_umweltverbaende_at` on `service/Umweltverbaende.py`, which probes a district's site and reads the old HTML pages, direct ICS links or the WordPress admin-ajax form. `scheibbs_umweltverbaende_at` stays legacy: its district now publishes PDF files only, and the legacy source returns nothing for all its test cases; it is a candidate for removal at the next major release. All four `baden_umweltverbaende_at` test cases returned nothing with the legacy code (the `?kat=32` pages are gone), so they are replaced. **Recycle Coach (US/CA/AU)**, `recyclecoach_com` (`service/RecycleCoach.py`; holiday notices are dropped, events become "Other" with their title as the description) and `ccc_tas_gov_au` (own WordPress API, migrated declaratively; it was never a Recycle Coach source). **Publidata (FR/CA)**, `publidata_fr` and `publidata_ca` (`service/Publidata.py`: geocoder plus search retriever and an `opening_hours` schedule expander). **localcities.ch (CH)**, `localcities_ch`, `buchegg_so_ch` and `grenchen_ch` (`service/Localcities.py`; `buchegg_so_ch` also reads the municipality's i-web page). **Košice (SK)**, `kositeast_sk` and `kositwest_sk` (`service/KositCalendar.py`, colour-rectangle PDF year planners; `kositwest_sk` no longer imports another source). **kiedyodpady.pl (PL)**, `kiedyodpady_pl` (`service/Kiedyodpady.py`; further municipalities are one-line regions). **Italian municipal apps**: `comune_digital_it` (GoodBarber) and `municipium_it` (Maggioli) share no protocol, so these were two independent migrations without a component. **Opendatasoft (FR)**: `rueil_malmaison_fr`, `data_angers_fr`, `data_nantesmetropole_fr` and `opendata_bordeauxmetropole_fr` only share the data host, so four independent migrations; Rueil and Bordeaux let the API do the zone match with `intersects(geo_shape, geom'POINT(...)')`, the BAN geocoder is a declared `Lookup`. **Finnish portals** turned out to need account credentials (see class 3). **Sammelkalender (CH)**, both (`sammelkalender_ch`, `suibr_ch`; `service/Sammelkalender.py`: municipality, street or collection area, year calendar). `suibr_ch` was a copy of `sammelkalender_ch` with a fixed host and now shares the component. Two `sammelkalender_ch` test cases that failed with the legacy code (a `None.lower()` on a street without a name, a street list that had changed) are replaced by valid ones; an unknown street is reported with suggestions instead of a `ValueError`. **Jolioo app (AT)**, both (`gaenserndorf_city_at`, `lipizzanerheimat_at`; `service/Jolioo.py`: the signed call as a `Request` and the calendar parser; `lipizzanerheimat_at` now lists its 15 communities as `REGIONS`). **MOHU Budapest (HU)**, both (`mohu_bp_hu`, `fkf_bo_hu`; `service/OctoberCms.py`: the handler post as a `Request`). `fkf_bo_hu` was broken: its `www.` URL redirects and the redirected POST came back as a page, not JSON; it posts to the bare host now. **Infovision (DK)**, both (`kolding_dk`, `kalundborg_dk`; `service/Infovision.py`: the public container call and the parser; each municipality cleans its container wording and maps it). The legacy test ids returned nothing, so the test cases are other address ids of the same ranges. **ISL Fusion (NI)**, both (`fermanaghomagh_gov_uk`, `lisburn_castlereagh_gov_uk`; `service/IslFusion.py`: address search, property by house number, calendar, parser). Lisburn's difflib guess at the street part is replaced by the same "address starts with the house number" rule as Fermanagh's. **OnCreate (UK)**, both (`cheltenham_gov_uk`, `doncaster_gov_uk`). The host name was the only thing they shared: Cheltenham is a CSRF form post, Doncaster a postcode search with a fresh form per search and a collection page whose events sit in a `data-params` attribute (so `AttributeJsonParser` gained `from_json_key`), and the already-migrated `sevenoaks_gov_uk` is a third variant. No shared component came out of it, each is declared with `Lookup` / `Request`. **Salesforce Aura community (UK)**, all three (`cotswold_gov_uk`, `forest_of_dean_gov_uk`, `westoxon_gov_uk`; `service/AuraWasteEnquiry.py` holds the Aura flow and the table parser, each council is a host, a `vClientCode` and a bin-name map; the legacy `verify=False` is gone, curl_cffi verifies these hosts). **Verint empro forms (UK)**, all three (`bolton_gov_uk`, `fife_gov_uk`, `manchester_uk`; `service/VerintCloud.py` holds the token handshake and the steps, each council keeps its calls and the reading of the answer; Bolton's test address and Fife's label list changed with the platform). **Jadu apiserver (UK)**, all six. It was two backends under one CMS name: the `/apiserver/ajaxlibrary` JSON-RPC endpoint (`breckland_gov_uk`, `sholland_gov_uk`, `southtyneside_gov_uk`, `westberks_gov_uk`; shared envelope in `service/JaduApiserver.py`, each council's methods stay in its source) and the GOSS `formsservice` multi-page forms (`boston_gov_uk`, `st_helens_gov_uk`; `service/GossForm.py`). The legacy St Helens flow was already broken: the form's nonce now lives in the page's own `action`, not in a hidden input, and its old test addresses return no data.

| Cluster | Legacy sources | Evidence |
|---|---|---|

## 6. PDF schedule

Done (13 of 14): `brimbank_vic_gov_au` (link by text on the bins page, `PdfWordLayoutParser`; fixes a legacy bug that dropped the 29th to 31st in the first week row), `easthants_gov_uk` (coloured date cells via `PdfLayoutParser`; the council map host has no working certificate and is used over plain HTTP, UPRN test case included), `feuerthalen_ch` (`PdfLinkRetriever` + `PdfWordLayoutParser`), `hornsby_nsw_gov_au` (on the OpenCities pipeline; its PDF fallbacks were dead code and are dropped), `kvatg_ch` (`service/KvaThurgau.py`, 66 communities as `REGIONS`, the zone is now the event location), `metropole_rennes_fr` (Heyzine flip-book resolved to its PDF), `sictomvds_com` (leaflet PDF via the map's JS, `RecurrenceExpander` with week parity), `smolo_cz` (`service/SmoloSchedule.py`; the PDF link is found by file-name pattern only, the legacy also matched the link text), `rybnik_pl` (three PDF layouts: per-district text blocks and the city-wide multifamily ruled table, `service/PdfRuledTable.py` + `service/RybnikSchedule.py`; rybnik.eu serves a JS bot-challenge page to scripted clients after a handful of requests, so cassettes must be recorded from an unblocked IP), `cc-montesquieu_fr` (HTML weekday table plus a yearly PDF poster read by `service/PdfPlaceColumns.py`; the legacy source read one poster, not per-commune PDFs; 13 cassettes of about 1.5 MB each because the index page is recorded twice per case), `deponia_hu` and `siokom_hu` (one shared `service/HuWasteCalendar.py`), `sutherlandshire_nsw_gov_au` (misclassified as PDF: it queries a public ArcGIS layer for the collection weekday, zone and recycling frequency; migrated with `ArcGisFeatureRetriever` / `ArcGisFeatureParser` and `RecurrenceExpander`; the recycling and garden fortnight is anchored on a Monday taken from the council's published 2026/27 calendar, `_ZONE1_RECYCLING_WEEK`, exactly as in the legacy source).

Left as legacy on purpose (1): `orange_nsw_gov_au`. Its PDF is only a zone guide without dates; the legacy source computes fixed Wednesday rules (general waste weekly, recycling fortnightly, zone A from the first and zone B from the second Wednesday of the year), which contradicts the "no hard-coded schedules" rule and cannot be verified. Candidate for removal at the next major release.

- `orange_nsw_gov_au` (199L, 2 req)

## 7. Standalone, small

Done in the first block (7): `ittre_be`, `mijnafvalwijzer_nl`, `sidec_lu`, `egn_abfallkalender_de`, `schweinfurt_de`, `tonnenleerung_de`, `mestorudna_cz` (new shared pieces: `service/SidecLu.py`, `parsers.HtmlMonthColumns`, `preprocessors.NestedDateGroups`, `CsvParser(columns=...)`, `KeyedDateListsParser(from_element=...)`).

Done in the second block (10): `sivom_rivedroite_fr`, `warszawa19115_pl`, `ekosystem_wroc_pl`, `renodjurs_dk`, `varmdo_se` (rebuilt on `EdpFutureWeb`, the old page was gone), `poznan_pl`, `nvaa_se`, `ressourceindsamling_dk` (fixes a DST-window 400), `pireva_se`, `lumire_se` (new shared pieces: `parsers.HtmlColumnDates`, `date_parsers.named_month` / `iso_week` / `first_of` / `in_timezone`, additive options on `HtmlMonthColumns` (`month_attr`) and `HtmlMonthHeadedRows` (`all_tables`, `day_pattern`, `current_year`)).

Done in the third block (10, UK councils): `oldham_gov_uk`, `bromsgrove_gov_uk`, `solihull_gov_uk`, `eaststaffsbc_gov_uk`, `cornwall_gov_uk`, `walsall_gov_uk`, `glasgow_gov_uk`, `torbay_council_gov_uk`, `folkestone_hythe_gov_uk`, `canterbury_gov_uk` (new shared pieces: `service/AspNetPostbackPager.py`, additive options `ArgumentGuard(matches=)` and `FirmstepAddressFormRetriever(value_prefix=, address_lookup_url=None)`).

Done in the fourth block (8 of 10, UK councils): `ardsandnorthdown_gov_uk`, `pembrokeshire_gov_uk`, `charnwood_gov_uk`, `knowsley_gov_uk` (class 8), `fenland_gov_uk`, `dorset_gov_uk`, `cardiff_gov_uk` (the council moved to a new endpoint with an anti-forgery token), `e_lindsey_gov_uk` (class 8; new shared pieces: `service/MendixBinForm.py`, `date_parsers.relative_words` / `without_ordinals`, `FanOutRetriever(include_prepared=)`, regex form names in `GossFormRetriever`, `WebAspxCollections` accepts the JSON reply and `Gls`).

Found broken upstream, not migrated (3): `hygea_be` (the JSON calendar is gone after a site relaunch and the server sends an incomplete certificate chain), `grosswangen_ch` (the page no longer carries dates, only a yearly PDF and prose rules since the collection changed hands), `araccolta_it` (serves a maintenance page for every URL; the legacy source also has a bug: its waste-type generator is exhausted after the first weekday of a card). They stay legacy until a decision (fix, rewrite or remove). The second block found three more providers gone: `odenserenovation_dk` (API removed, 404), `ecoapp_ecoservice_lt` (API host no longer resolves) and `tkeliai_lt` (the calendar feature was removed from the site). Also not migrated: `dover_gov_uk` (host `collections.dover.gov.uk` no longer resolves) and `wolverhampton_gov_uk` (the page no longer carries any bin content); `blackpool_gov_uk` and `swansea_gov_uk` were unreachable from the UK exit (TLS closed / no response) and are deferred. `merton_gov_uk` (the old portal returns 404) and `newcastle_gov_uk` (the lookup was retired) are dead; both councils are already covered by shared ICS entries ("London Borough of Merton (New)", and ReCollect area `NewcastleUponTyneUK` in `recollect.yaml`), so they are removal candidates for the next major release. `hastings_gov_uk` is deferred: its server omits the intermediate certificate (the pipeline verifies TLS strictly; the legacy source disables verification), a decision on shipping the intermediate certificate is open. `vestfor_dk` is deferred: its self-service host is unreachable from the German exit and needs a Danish IP.

- **html** (7): `apps_ci_minneapolis_mn_us`, `araccolta_it`, `dover_gov_uk`, `geelongaustralia_com_au`, `mundaring_wa_gov_au`, `swansea_gov_uk`, `wolverhampton_gov_uk`
- **json** (10): `armadale_wa_gov_au`, `blackpool_gov_uk`, `hygea_be`, `odenserenovation_dk`, `palmcoast_fl_gov`, `panda_ie`, `poriruacity_govt_nz`, `tkeliai_lt`, `vestfor_dk`, `wastenet_org_nz`
- **?** (2): `victoriapark_wa_gov_au`, `villagebonconseil_ca`
- **ics/json** (1): `ecoapp_ecoservice_lt`
- **ics/html** (2): `grosswangen_ch`, `merton_gov_uk`
- **ics** (2): `newcastle_gov_uk`, `strathfield_nsw_gov_au`

## 8. Standalone, medium

- **json** (36): `affarsverken_se`, `afvalstoffendienst_nl`, `aksd_hu`, `amsa_it`, `apricaspa_it`, `awb_ammerland_de`, `bristol_gov_uk`, `burgerportaal_nl`, `casey_vic_gov_au`, `ccc_govt_nz`, `cem_ambiente_it`, `chesterfield_gov_uk`, `cockburn_wa_gov_au`, `czystyregion_pl`, `data_grandlyon_com`, `enfield_gov_uk`, `fcc_group_eu`, `grafikai_svara_lt`, `hastings_gov_uk`, `heidelberg_de`, `joondalup_wa_gov_au`, `kaw_mainz_bingen_de`, `komunala_kranj_si`, `lacity_gov`, `nwrrr_com_au`, `omrin_nl`, `roslagsvatten_se`, `sictom_lons_le_saunier_fr`, `silea_it`, `sivom_com`, `sunshinecoast_qld_gov_au`, `thehills_nsw_gov_au`, `valorlux_lu`, `vattenmiljoresurs_se`, `waikato_district_council_govt_nz`, `ximmio_nl`
- **html** (30): `adur_worthing_gov_uk`, `antrimandnewtownabbey_gov_uk`, `aucklandcouncil_govt_nz`, `belfast_city_gov_uk`, `castlepoint_gov_uk`, `chichester_gov_uk`, `clissonsevremaine_fr`, `coeur_yvelines_fr`, `dardanup_wa_gov_au`, `east_renfrewshire_gov_uk`, `environmentfirst_co_uk`, `fairfieldcity_nsw_gov_au`, `gardenbags_co_nz`, `gmina_sroda_slaska_pl`, `ipswich_gov_uk`, `irado_nl`, `islington_gov_uk`, `midsussex_gov_uk`, `newforest_gov_uk`, `newham_gov_uk`, `northumberland_gov_uk`, `samiljo_se`, `stadtwerke_singen_de`, `stamford_ct_us`, `swale_gov_uk`, `teignbridge_gov_uk`, `terrestouloises_com`, `ville_quebec_qc_ca`, `warrnambool_vic_gov_au`, `wigan_gov_uk`
- **json/html** (17): `gateshead_gov_uk`, `gleneira_vic_gov_au`, `gmina_zgierz_pl`, `goldenplains_vic_gov_au`, `gosport_gov_uk`, `great_yarmouth_gov_uk`, `greyhound_ie`, `hastingsdc_govt_nz`, `iris_salten_no`, `lewisham_gov_uk`, `memotri_agglo_pau_fr`, `powys_gov_uk`, `rfd_no`, `royalgreenwich_gov_uk`, `south_ayrshire_gov_uk`, `stockton_gov_uk`, `vogeldisposal_com`
- **ics/json** (10): `airdrie_ca`, `api_golemio_cz`, `ekonovus_lt`, `greatershepparton_com_au`, `maitland_nsw_gov_au`, `npdc_govt_nz`, `potsdam_de`, `republicservices_com`, `sanantonio_gov`, `smiecioplan_pl`
- **?** (4): `eth_erd_hu`, `popuvky_cz`, `southampton_gov_uk`, `tsceskybrod_cz`
- **ics/json/html** (3): `barrie_ca`, `beg_logistics_de`, `rir_no`
- **json/xml** (2): `ciudad_de_la_costa_uy`, `grandbesancon_fr`
- **csv** (2): `data_montpellier3m_fr`, `scenicrim_qld_gov_au`
- **ics/html** (2): `portenf_sa_gov_au`, `preston_gov_uk`
- **ics/json/xml** (1): `amberg_de`
- **xml** (1): `laznebohdanec_cz`
- **ics/csv** (1): `luxembourg_lu`
- **ics** (1): `ritl_ca`

## 9. Standalone, large

- **json** (14): `ahk_heidekreis_de`, `avfallsapp_se`, `cbcity_nsw_gov_au`, `cistomesto_si`, `delight_system_com`, `geovest_it`, `hvcgroep_nl`, `irenambiente_it`, `montreal_ca`, `montri_fr`, `olo_sk`, `pendle_gov_uk`, `sudestavenir_fr`, `wm_com`
- **json/html** (3): `iapp_itouchvision_com`, `sesaeste_it`, `sunderland_gov_uk`
- **html** (2): `abfall_wiener_neustadt_at`, `mywastewatcher_de`
- **ics/json** (2): `awb_bad_kreuznach_de`, `awido_de`
- **ics/json/html** (2): `baltimore_county_md_us`, `croydon_gov_uk`
- **ics/html** (1): `kom_lub_com_pl`

## How to use this

1. Start with **class 2**: cheap removals shrink the count and the maintenance surface. Settle the policy questions in classes 1 and 3, which change the target but block nothing.
2. Work **class 4**, then **class 5** cluster by cluster: each cluster is one new component plus a few small migrations, verified by cassette replay.
3. **Class 7** is independent and parallelisable; **class 8** and **9** follow and are where a new shared component is most likely needed.

Update the counts when a class empties. Delete this file when the legacy count reaches zero.
