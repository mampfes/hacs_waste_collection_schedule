import voluptuous as vol
from homeassistant.helpers import selector

from .const import CONF_COUNTRY, CONF_SOURCE_NAME

# schema for initial config flow, entered by "Add Integration"
COUNTRY_LIST = [
    "generic",
    # Begin of country section
    "au",
    "at",
    "be",
    "ca",
    "dk",
    "fr",
    "de",
    "hu",
    "lt",
    "lu",
    "nl",
    "nz",
    "no",
    "pl",
    "si",
    "se",
    "ch",
    "uk",
    "us",
    # End of country section
]


DATA_SCHEMA_COUNTRY_LIST = vol.Schema(
    {
        vol.Required(CONF_COUNTRY): selector.SelectSelector(
            selector.SelectSelectorConfig(
                options=COUNTRY_LIST,
                mode=selector.SelectSelectorMode.DROPDOWN,
                translation_key="country",
            )
        ),
    }
)

# Begin of source_list section
SOURCE_LIST_au = [
    "armadale_wa_gov_au",
    "act_gov_au",
    "banyule_vic_gov_au",
    "belmont_wa_gov_au",
    "brisbane_qld_gov_au",
    "campbelltown_nsw_gov_au",
    "cardinia_vic_gov_au",
    "canadabay_nsw_gov_au",
    "kingston_vic_gov_au",
    "onkaparingacity_com",
    "cumberland_nsw_gov_au",
    "goldcoast_qld_gov_au",
    "hume_vic_gov_au",
    "innerwest_nsw_gov_au",
    "ipswich_qld_gov_au",
    "kuringgai_nsw_gov_au",
    "lakemac_nsw_gov_au",
    "logan_qld_gov_au",
    "mrsc_vic_gov_au",
    "maribyrnong_vic_gov_au",
    "maroondah_vic_gov_au",
    "melton_vic_gov_au",
    "nillumbik_vic_gov_au",
    "nawma_sa_gov_au",
    "portenf_sa_gov_au",
    "recyclesmart_com",
    "stonnington_vic_gov_au",
    "thehills_nsw_gov_au",
    "unley_sa_gov_au",
    "whittlesea_vic_gov_au",
    "wollongongwaste_com_au",
    "wyndham_vic_gov_au",
]

SOURCE_LIST_at = [
    "citiesapps_com",
    "bmv_at",
    "baden_umweltverbaende_at",
    "scheibbs_umweltverbaende_at",
    "infeo_at",
    "korneuburg_stadtservice_at",
    "data_umweltprofis_at",
    "wsz_moosburg_at",
]

SOURCE_LIST_be = [
    "hygea_be",
    "recycleapp_be",
]

SOURCE_LIST_ca = [
    "calgary_ca",
    "toronto_ca",
]

SOURCE_LIST_dk = [
    "renosyd_dk",
]

SOURCE_LIST_fr = [
    "mamirolle_info",
]

SOURCE_LIST_de = [
    "stuttgart_de",
    "abfall_io",
    "offenbach_de",
    "wuerzburg_de",
    "abfallnavi_de",
    "abfalltermine_forchheim_de",
    "abfallwirtschaft_germersheim_de",
    "aw_harburg_de",
    "alw_wf_de",
    "awn_de",
    "nuernberger_land_de",
    "abfallwirtschaft_pforzheim_de",
    "awr_de",
    "abfallwirtschaft_fuerth_eu",
    "schweinfurt_de",
    "awsh_de",
    "zva_wmk_de",
    "abfall_zollernalbkreis_de",
    "awb_emsland_de",
    "awb_es_de",
    "abki_de",
    "meinawb_de",
    "awb_mainz_bingen_de",
    "abfall_lippe_de",
    "ahe_de",
    "art_trier_de",
    "asr_chemnitz_de",
    "abfallwirtschaft_vechta_de",
    "awb_bad_kreuznach_de",
    "awbkoeln_de",
    "awb_oldenburg_de",
    "awido_de",
    "awigo_de",
    "berlin_recycling_de",
    "bsr_de",
    "bielefeld_de",
    "buergerportal_de",
    "c_trace_de",
    "chiemgau_recycling_lk_rosenheim",
    "karlsruhe_de",
    "cmcitymedia_de",
    "dillingen_saar_de",
    "ead_darmstadt_de",
    "egn_abfallkalender_de",
    "hausmuell_info",
    "heilbronn_de",
    "jumomind_de",
    "kaev_niederlausitz",
    "ks_boerde_de",
    "kwb_goslar_de",
    "kwu_de",
    "erlangen_hoechstadt_de",
    "landkreis_kusel_de",
    "geoport_nwm_de",
    "rv_de",
    "landkreis_rhoen_grabfeld",
    "lrasha_de",
    "landkreis_wittmund_de",
    "mags_de",
    "muellabfuhr_de",
    "muellmax_de",
    "abfall_neunkirchen_siegerland_de",
    "potsdam_de",
    "regioentsorgung_de",
    "rh_entsorgung_de",
    "sector27_de",
    "stadtreinigung_dresden_de",
    "stadtreinigung_hamburg",
    "stadtreinigung_leipzig_de",
    "stadtservice_bruehl_de",
    "staedteservice_de",
    "sbazv_de",
    "wermelskirchen_de",
    "was_wolfsburg_de",
    "zakb_de",
    "aha_region_de",
    "zva_sek_de",
]

SOURCE_LIST_hu = [
    "fkf_bp_hu",
    "fkf_bo_hu",
]

SOURCE_LIST_lt = [
    "grafikai_svara_lt",
]

SOURCE_LIST_lu = [
    "esch_lu",
]

SOURCE_LIST_nl = [
    "circulus_nl",
    "ximmio_nl",
]

SOURCE_LIST_nz = [
    "aucklandcouncil_govt_nz",
    "ccc_govt_nz",
    "dunedin_govt_nz",
    "wastenet_org_nz",
    "hcc_govt_nz",
    "horowhenua_govt_nz",
    "waipa_nz",
    "wellington_govt_nz",
]

SOURCE_LIST_no = [
    "iris_salten_no",
    "minrenovasjon_no",
    "movar_no",
    "oslokommune_no",
    "remidt_no",
    "sandnes_no",
    "stavanger_no",
]

SOURCE_LIST_pl = [
    "ecoharmonogram_pl",
    "sepan_remondis_pl",
    "warszawa19115_pl",
    "ekosystem_wroc_pl",
]

SOURCE_LIST_si = [
    "mojiodpadki_si",
]

SOURCE_LIST_se = [
    "affarsverken_se",
    "juneavfall_se",
    "lsr_nu",
    "lerum_se",
    "tekniskaverken_se",
    "gotland_se",
    "miljoteknik_se",
    "samiljo_se",
    "srvatervinning_se",
    "ssam_se",
    "sysav_se",
    "uppsalavatten_se",
    "vasyd_se",
]

SOURCE_LIST_ch = [
    "a_region_ch",
    "grosswangen_ch",
    "lindau_ch",
    "muenchenstein_ch",
    "real_luzern_ch",
]

SOURCE_LIST_uk = [
    "aberdeenshire_gov_uk",
    "allerdale_gov_uk",
    "ambervalley_gov_uk",
    "ashfield_gov_uk",
    "ashford_gov_uk",
    "aylesburyvaledc_gov_uk",
    "basildon_gov_uk",
    "basingstoke_gov_uk",
    "bathnes_gov_uk",
    "bedford_gov_uk",
    "binzone_uk",
    "blackburn_gov_uk",
    "west_norfolk_gov_uk",
    "bracknell_forest_gov_uk",
    "bradford_gov_uk",
    "braintree_gov_uk",
    "breckland_gov_uk",
    "bristol_gov_uk",
    "south_norfolk_and_broadland_gov_uk",
    "broxtowe_gov_uk",
    "chiltern_gov_uk",
    "burnley_gov_uk",
    "cambridge_gov_uk",
    "canterbury_gov_uk",
    "cardiff_gov_uk",
    "centralbedfordshire_gov_uk",
    "cherwell_gov_uk",
    "cheshire_east_gov_uk",
    "cheshire_west_and_chester_gov_uk",
    "chesterfield_gov_uk",
    "chichester_gov_uk",
    "doncaster_gov_uk",
    "lincoln_gov_uk",
    "york_gov_uk",
    "colchester_gov_uk",
    "cornwall_gov_uk",
    "crawley_gov_uk",
    "croydon_gov_uk",
    "derby_gov_uk",
    "dudley_gov_uk",
    "durham_gov_uk",
    "eastcambs_gov_uk",
    "eastherts_gov_uk",
    "east_northamptonshire_gov_uk",
    "east_renfrewshire_gov_uk",
    "eastriding_gov_uk",
    "elmbridge_gov_uk",
    "environmentfirst_co_uk",
    "exeter_gov_uk",
    "fareham_gov_uk",
    "fccenvironment_co_uk",
    "fenland_gov_uk",
    "fife_gov_uk",
    "gateshead_gov_uk",
    "glasgow_gov_uk",
    "guildford_gov_uk",
    "gwynedd_gov_uk",
    "harlow_gov_uk",
    "herefordshire_gov_uk",
    "highland_gov_uk",
    "horsham_gov_uk",
    "huntingdonshire_gov_uk",
    "iweb_itouchvision_com",
    "jointwastesolutions_org",
    "kirklees_gov_uk",
    "biffaleicester_co_uk",
    "lisburn_castlereagh_gov_uk",
    "liverpool_gov_uk",
    "bexley_gov_uk",
    "bromley_gov_uk",
    "camden_gov_uk",
    "lewisham_gov_uk",
    "merton_gov_uk",
    "maidstone_gov_uk",
    "maldon_gov_uk",
    "manchester_uk",
    "mansfield_gov_uk",
    "midsussex_gov_uk",
    "middlesbrough_gov_uk",
    "milton_keynes_gov_uk",
    "newcastle_gov_uk",
    "newcastle_staffs_gov_uk",
    "newport_gov_uk",
    "northherts_gov_uk",
    "north_kesteven_org_uk",
    "northlincs_gov_uk",
    "nsomerset_gov_uk",
    "northyorks_hambleton_gov_uk",
    "nottingham_city_gov_uk",
    "oxford_gov_uk",
    "peterborough_gov_uk",
    "portsmouth_gov_uk",
    "reading_gov_uk",
    "redbridge_gov_uk",
    "reigatebanstead_gov_uk",
    "rctcbc_gov_uk",
    "richmondshire_gov_uk",
    "rotherham_gov_uk",
    "runnymede_gov_uk",
    "rushcliffe_gov_uk",
    "rushmoor_gov_uk",
    "salford_gov_uk",
    "sheffield_gov_uk",
    "scambs_gov_uk",
    "southderbyshire_gov_uk",
    "southglos_gov_uk",
    "sholland_gov_uk",
    "southtyneside_gov_uk",
    "southampton_gov_uk",
    "stevenage_gov_uk",
    "stockport_gov_uk",
    "stockton_gov_uk",
    "stoke_gov_uk",
    "stratford_gov_uk",
    "swindon_gov_uk",
    "tameside_gov_uk",
    "telford_gov_uk",
    "tewkesbury_gov_uk",
    "kingston_gov_uk",
    "tmbc_gov_uk",
    "uttlesford_gov_uk",
    "walsall_gov_uk",
    "warrington_gov_uk",
    "waverley_gov_uk",
    "wealden_gov_uk",
    "welhat_gov_uk",
    "westberks_gov_uk",
    "west_dunbartonshire_gov_uk",
    "wigan_gov_uk",
    "wiltshire_gov_uk",
    "rbwm_gov_uk",
    "wirral_gov_uk",
    "wokingham_gov_uk",
    "wyreforestdc_gov_uk",
]

SOURCE_LIST_us = [
    "okc_gov",
    "pgh_st",
    "recyclecoach_com",
    "republicservices_com",
    "seattle_gov",
]

# End of source_list section


DATA_SCHEMA_SOURCE_LIST = {
    # Begin of select_source section
    "au": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_au,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_au",
                )
            ),
        }
    ),
    "at": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_at,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_at",
                )
            ),
        }
    ),
    "be": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_be,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_be",
                )
            ),
        }
    ),
    "ca": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_ca,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_ca",
                )
            ),
        }
    ),
    "dk": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_dk,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_dk",
                )
            ),
        }
    ),
    "fr": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_fr,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_fr",
                )
            ),
        }
    ),
    "de": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_de,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_de",
                )
            ),
        }
    ),
    "hu": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_hu,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_hu",
                )
            ),
        }
    ),
    "lt": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_lt,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_lt",
                )
            ),
        }
    ),
    "lu": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_lu,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_lu",
                )
            ),
        }
    ),
    "nl": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_nl,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_nl",
                )
            ),
        }
    ),
    "nz": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_nz,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_nz",
                )
            ),
        }
    ),
    "no": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_no,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_no",
                )
            ),
        }
    ),
    "pl": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_pl,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_pl",
                )
            ),
        }
    ),
    "si": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_si,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_si",
                )
            ),
        }
    ),
    "se": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_se,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_se",
                )
            ),
        }
    ),
    "ch": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_ch,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_ch",
                )
            ),
        }
    ),
    "uk": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_uk,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_uk",
                )
            ),
        }
    ),
    "us": vol.Schema(
        {
            vol.Required(CONF_SOURCE_NAME): selector.SelectSelector(
                selector.SelectSelectorConfig(
                    options=SOURCE_LIST_us,
                    mode=selector.SelectSelectorMode.DROPDOWN,
                    translation_key="source_list_us",
                )
            ),
        }
    ),
    # End of select_source section
}


DATA_SCHEMA_SOURCE_CONFIG = {
    # Begin of source_config section
    "armadale_wa_gov_au": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "act_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Optional("split_suburb"): selector.TextSelector(),
        }
    ),
    "banyule_vic_gov_au": vol.Schema(
        {
            vol.Optional("street_address"): selector.TextSelector(),
            vol.Optional("geolocation_id"): selector.TextSelector(),
        }
    ),
    "belmont_wa_gov_au": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "brisbane_qld_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "campbelltown_nsw_gov_au": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "cardinia_vic_gov_au": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "canadabay_nsw_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "kingston_vic_gov_au": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "onkaparingacity_com": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "cumberland_nsw_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "goldcoast_qld_gov_au": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "hume_vic_gov_au": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
            vol.Optional("predict"): selector.TextSelector(),
        }
    ),
    "innerwest_nsw_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "ipswich_qld_gov_au": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("suburb"): selector.TextSelector(),
        }
    ),
    "kuringgai_nsw_gov_au": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "lakemac_nsw_gov_au": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "logan_qld_gov_au": vol.Schema(
        {
            vol.Required("property_location"): selector.TextSelector(),
        }
    ),
    "mrsc_vic_gov_au": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "maribyrnong_vic_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "maroondah_vic_gov_au": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "melton_vic_gov_au": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "nillumbik_vic_gov_au": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "nawma_sa_gov_au": vol.Schema(
        {
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("suburb"): selector.TextSelector(),
            vol.Optional("street_number"): selector.TextSelector(),
            vol.Optional("pid"): selector.TextSelector(),
        }
    ),
    "portenf_sa_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("unit_number"): selector.TextSelector(),
        }
    ),
    "recyclesmart_com": vol.Schema(
        {
            vol.Required("email"): selector.TextSelector(),
            vol.Required("password"): selector.TextSelector(),
        }
    ),
    "stonnington_vic_gov_au": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "thehills_nsw_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("houseNo"): selector.TextSelector(),
        }
    ),
    "unley_sa_gov_au": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "whittlesea_vic_gov_au": vol.Schema(
        {
            vol.Required("suburb"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "wollongongwaste_com_au": vol.Schema(
        {
            vol.Required("propertyID"): selector.TextSelector(),
        }
    ),
    "wyndham_vic_gov_au": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "citiesapps_com": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("calendar"): selector.TextSelector(),
        }
    ),
    "bmv_at": vol.Schema(
        {
            vol.Required("ort"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hausnummer"): selector.TextSelector(),
        }
    ),
    "baden_umweltverbaende_at": vol.Schema(
        {
            vol.Required("region"): selector.TextSelector(),
        }
    ),
    "scheibbs_umweltverbaende_at": vol.Schema(
        {
            vol.Required("region"): selector.TextSelector(),
        }
    ),
    "infeo_at": vol.Schema(
        {
            vol.Required("customer"): selector.TextSelector(),
            vol.Optional("zone"): selector.TextSelector(),
            vol.Optional("city"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
            vol.Optional("housenumber"): selector.TextSelector(),
        }
    ),
    "korneuburg_stadtservice_at": vol.Schema(
        {
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
            vol.Optional("teilgebiet"): selector.TextSelector(),
        }
    ),
    "data_umweltprofis_at": vol.Schema(
        {
            vol.Optional("url"): selector.TextSelector(),
            vol.Optional("xmlurl"): selector.TextSelector(),
        }
    ),
    "wsz_moosburg_at": vol.Schema(
        {
            vol.Required("args"): selector.TextSelector(),
        }
    ),
    "hygea_be": vol.Schema(
        {
            vol.Optional("streetIndex"): selector.TextSelector(),
            vol.Optional("cp"): selector.TextSelector(),
        }
    ),
    "recycleapp_be": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("add_events"): selector.TextSelector(),
        }
    ),
    "calgary_ca": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "toronto_ca": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "renosyd_dk": vol.Schema(
        {
            vol.Required("kommune"): selector.TextSelector(),
            vol.Required("husnummer"): selector.TextSelector(),
        }
    ),
    "mamirolle_info": vol.Schema(
        {
            vol.Required("args"): selector.TextSelector(),
            vol.Required("kwargs"): selector.TextSelector(),
        }
    ),
    "stuttgart_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("streetnr"): selector.TextSelector(),
        }
    ),
    "abfall_io": vol.Schema(
        {
            vol.Required("key"): selector.TextSelector(),
            vol.Required("f_id_kommune"): selector.TextSelector(),
            vol.Required("f_id_strasse"): selector.TextSelector(),
            vol.Optional("f_id_bezirk"): selector.TextSelector(),
            vol.Optional("f_id_strasse_hnr"): selector.TextSelector(),
            vol.Optional("f_abfallarten"): selector.TextSelector(),
        }
    ),
    "offenbach_de": vol.Schema(
        {
            vol.Required("f_id_location"): selector.TextSelector(),
        }
    ),
    "wuerzburg_de": vol.Schema(
        {
            vol.Optional("district"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
        }
    ),
    "abfallnavi_de": vol.Schema(
        {
            vol.Required("service"): selector.TextSelector(),
            vol.Required("ort"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Optional("hausnummer"): selector.TextSelector(),
        }
    ),
    "abfalltermine_forchheim_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("area"): selector.TextSelector(),
        }
    ),
    "abfallwirtschaft_germersheim_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
        }
    ),
    "aw_harburg_de": vol.Schema(
        {
            vol.Required("level_1"): selector.TextSelector(),
            vol.Required("level_2"): selector.TextSelector(),
            vol.Optional("level_3"): selector.TextSelector(),
        }
    ),
    "alw_wf_de": vol.Schema(
        {
            vol.Required("ort"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
        }
    ),
    "awn_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("address_suffix"): selector.TextSelector(),
        }
    ),
    "nuernberger_land_de": vol.Schema(
        {
            vol.Required("id"): selector.TextSelector(),
        }
    ),
    "abfallwirtschaft_pforzheim_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("address_suffix"): selector.TextSelector(),
        }
    ),
    "awr_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "abfallwirtschaft_fuerth_eu": vol.Schema(
        {
            vol.Required("id"): selector.TextSelector(),
        }
    ),
    "schweinfurt_de": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
            vol.Optional("showmobile"): selector.TextSelector(),
        }
    ),
    "awsh_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "zva_wmk_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "abfall_zollernalbkreis_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("types"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
        }
    ),
    "awb_emsland_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("address_suffix"): selector.TextSelector(),
        }
    ),
    "awb_es_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
        }
    ),
    "abki_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("number"): selector.TextSelector(),
        }
    ),
    "meinawb_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("address_suffix"): selector.TextSelector(),
        }
    ),
    "awb_mainz_bingen_de": vol.Schema(
        {
            vol.Required("bezirk"): selector.TextSelector(),
            vol.Required("ort"): selector.TextSelector(),
            vol.Optional("strasse"): selector.TextSelector(),
        }
    ),
    "abfall_lippe_de": vol.Schema(
        {
            vol.Required("gemeinde"): selector.TextSelector(),
            vol.Optional("bezirk"): selector.TextSelector(),
        }
    ),
    "ahe_de": vol.Schema(
        {
            vol.Required("plz"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hnr"): selector.TextSelector(),
        }
    ),
    "art_trier_de": vol.Schema(
        {
            vol.Required("district"): selector.TextSelector(),
            vol.Required("zip_code"): selector.TextSelector(),
        }
    ),
    "asr_chemnitz_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("object_number"): selector.TextSelector(),
        }
    ),
    "abfallwirtschaft_vechta_de": vol.Schema(
        {
            vol.Required("stadt"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
        }
    ),
    "awb_bad_kreuznach_de": vol.Schema(
        {
            vol.Required("ort"): selector.TextSelector(),
            vol.Optional("strasse"): selector.TextSelector(),
            vol.Optional("nummer"): selector.TextSelector(),
            vol.Optional("stadtteil"): selector.TextSelector(),
        }
    ),
    "awbkoeln_de": vol.Schema(
        {
            vol.Required("street_code"): selector.TextSelector(),
            vol.Required("building_number"): selector.TextSelector(),
        }
    ),
    "awb_oldenburg_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "awido_de": vol.Schema(
        {
            vol.Required("customer"): selector.TextSelector(),
            vol.Required("city"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
            vol.Optional("housenumber"): selector.TextSelector(),
        }
    ),
    "awigo_de": vol.Schema(
        {
            vol.Required("ort"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hnr"): selector.TextSelector(),
        }
    ),
    "berlin_recycling_de": vol.Schema(
        {
            vol.Required("username"): selector.TextSelector(),
            vol.Required("password"): selector.TextSelector(),
        }
    ),
    "bsr_de": vol.Schema(
        {
            vol.Required("abf_strasse"): selector.TextSelector(),
            vol.Required("abf_hausnr"): selector.TextSelector(),
        }
    ),
    "bielefeld_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("address_suffix"): selector.TextSelector(),
        }
    ),
    "buergerportal_de": vol.Schema(
        {
            vol.Required("operator"): selector.TextSelector(),
            vol.Required("district"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Optional("subdistrict"): selector.TextSelector(),
            vol.Optional("number"): selector.TextSelector(),
            vol.Optional("show_volume"): selector.TextSelector(),
        }
    ),
    "c_trace_de": vol.Schema(
        {
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hausnummer"): selector.TextSelector(),
            vol.Optional("gemeinde"): selector.TextSelector(),
            vol.Optional("ort"): selector.TextSelector(),
            vol.Optional("ortsteil"): selector.TextSelector(),
            vol.Optional("service"): selector.TextSelector(),
        }
    ),
    "chiemgau_recycling_lk_rosenheim": vol.Schema(
        {
            vol.Required("district"): selector.TextSelector(),
        }
    ),
    "karlsruhe_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("hnr"): selector.TextSelector(),
        }
    ),
    "cmcitymedia_de": vol.Schema(
        {
            vol.Required("hpid"): selector.TextSelector(),
            vol.Optional("realmid"): selector.TextSelector(),
            vol.Optional("district"): selector.TextSelector(),
        }
    ),
    "dillingen_saar_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "ead_darmstadt_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "egn_abfallkalender_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("district"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("housenumber"): selector.TextSelector(),
        }
    ),
    "hausmuell_info": vol.Schema(
        {
            vol.Required("subdomain"): selector.TextSelector(),
            vol.Optional("ort"): selector.TextSelector(),
            vol.Optional("ortsteil"): selector.TextSelector(),
            vol.Optional("strasse"): selector.TextSelector(),
            vol.Optional("hausnummer"): selector.TextSelector(),
        }
    ),
    "heilbronn_de": vol.Schema(
        {
            vol.Required("plz"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hausnr"): selector.TextSelector(),
        }
    ),
    "jumomind_de": vol.Schema(
        {
            vol.Required("service_id"): selector.TextSelector(),
            vol.Optional("city"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
            vol.Optional("city_id"): selector.TextSelector(),
            vol.Optional("area_id"): selector.TextSelector(),
            vol.Optional("house_number"): selector.TextSelector(),
        }
    ),
    "kaev_niederlausitz": vol.Schema(
        {
            vol.Required("abf_suche"): selector.TextSelector(),
        }
    ),
    "ks_boerde_de": vol.Schema(
        {
            vol.Required("village"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "kwb_goslar_de": vol.Schema(
        {
            vol.Required("pois"): selector.TextSelector(),
        }
    ),
    "kwu_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("number"): selector.TextSelector(),
        }
    ),
    "erlangen_hoechstadt_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "landkreis_kusel_de": vol.Schema(
        {
            vol.Required("ortsgemeinde"): selector.TextSelector(),
        }
    ),
    "geoport_nwm_de": vol.Schema(
        {
            vol.Required("district"): selector.TextSelector(),
        }
    ),
    "rv_de": vol.Schema(
        {
            vol.Required("ort"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hnr"): selector.TextSelector(),
            vol.Required("hnr_zusatz"): selector.TextSelector(),
        }
    ),
    "landkreis_rhoen_grabfeld": vol.Schema(
        {
            vol.Optional("city"): selector.TextSelector(),
            vol.Optional("district"): selector.TextSelector(),
        }
    ),
    "lrasha_de": vol.Schema(
        {
            vol.Required("location"): selector.TextSelector(),
        }
    ),
    "landkreis_wittmund_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
        }
    ),
    "mags_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("number"): selector.TextSelector(),
            vol.Optional("turnus"): selector.TextSelector(),
        }
    ),
    "muellabfuhr_de": vol.Schema(
        {
            vol.Required("client"): selector.TextSelector(),
            vol.Required("city"): selector.TextSelector(),
        }
    ),
    "muellmax_de": vol.Schema(
        {
            vol.Required("service"): selector.TextSelector(),
            vol.Optional("mm_frm_ort_sel"): selector.TextSelector(),
            vol.Optional("mm_frm_str_sel"): selector.TextSelector(),
            vol.Optional("mm_frm_hnr_sel"): selector.TextSelector(),
        }
    ),
    "abfall_neunkirchen_siegerland_de": vol.Schema(
        {
            vol.Required("strasse"): selector.TextSelector(),
        }
    ),
    "potsdam_de": vol.Schema(
        {
            vol.Required("ortsteil"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Optional("rest_rhythm"): selector.TextSelector(),
            vol.Optional("papier_rhythm"): selector.TextSelector(),
            vol.Optional("bio_rhythm"): selector.TextSelector(),
            vol.Optional("gelb_rhythm"): selector.TextSelector(),
        }
    ),
    "regioentsorgung_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "rh_entsorgung_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("address_suffix"): selector.TextSelector(),
        }
    ),
    "sector27_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "stadtreinigung_dresden_de": vol.Schema(
        {
            vol.Required("standort"): selector.TextSelector(),
        }
    ),
    "stadtreinigung_hamburg": vol.Schema(
        {
            vol.Required("hnId"): selector.TextSelector(),
            vol.Optional("asId"): selector.TextSelector(),
        }
    ),
    "stadtreinigung_leipzig_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "stadtservice_bruehl_de": vol.Schema(
        {
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hnr"): selector.TextSelector(),
        }
    ),
    "staedteservice_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "sbazv_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("district"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
        }
    ),
    "wermelskirchen_de": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "was_wolfsburg_de": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "zakb_de": vol.Schema(
        {
            vol.Required("ort"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hnr"): selector.TextSelector(),
            vol.Optional("hnr_zusatz"): selector.TextSelector(),
        }
    ),
    "aha_region_de": vol.Schema(
        {
            vol.Required("gemeinde"): selector.TextSelector(),
            vol.Required("strasse"): selector.TextSelector(),
            vol.Required("hnr"): selector.TextSelector(),
            vol.Optional("zusatz"): selector.TextSelector(),
        }
    ),
    "zva_sek_de": vol.Schema(
        {
            vol.Required("bezirk"): selector.TextSelector(),
            vol.Required("ortsteil"): selector.TextSelector(),
            vol.Optional("strasse"): selector.TextSelector(),
        }
    ),
    "fkf_bp_hu": vol.Schema(
        {
            vol.Required("district"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "fkf_bo_hu": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
        }
    ),
    "grafikai_svara_lt": vol.Schema(
        {
            vol.Required("region"): selector.TextSelector(),
            vol.Required("street"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Optional("district"): selector.TextSelector(),
            vol.Optional("waste_object_ids"): selector.TextSelector(),
        }
    ),
    "esch_lu": vol.Schema(
        {
            vol.Required("zone"): selector.TextSelector(),
        }
    ),
    "circulus_nl": vol.Schema(
        {
            vol.Required("postal_code"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "ximmio_nl": vol.Schema(
        {
            vol.Required("company"): selector.TextSelector(),
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "aucklandcouncil_govt_nz": vol.Schema(
        {
            vol.Required("area_number"): selector.TextSelector(),
        }
    ),
    "ccc_govt_nz": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "dunedin_govt_nz": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "wastenet_org_nz": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "hcc_govt_nz": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "horowhenua_govt_nz": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("town"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "waipa_nz": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "wellington_govt_nz": vol.Schema(
        {
            vol.Optional("streetId"): selector.TextSelector(),
            vol.Optional("streetName"): selector.TextSelector(),
        }
    ),
    "iris_salten_no": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
            vol.Required("kommune"): selector.TextSelector(),
        }
    ),
    "minrenovasjon_no": vol.Schema(
        {
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Required("street_code"): selector.TextSelector(),
            vol.Required("county_id"): selector.TextSelector(),
        }
    ),
    "movar_no": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "oslokommune_no": vol.Schema(
        {
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
            vol.Required("house_letter"): selector.TextSelector(),
            vol.Required("street_id"): selector.TextSelector(),
        }
    ),
    "remidt_no": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "sandnes_no": vol.Schema(
        {
            vol.Required("id"): selector.TextSelector(),
            vol.Required("municipality"): selector.TextSelector(),
            vol.Required("gnumber"): selector.TextSelector(),
            vol.Required("bnumber"): selector.TextSelector(),
            vol.Required("snumber"): selector.TextSelector(),
        }
    ),
    "stavanger_no": vol.Schema(
        {
            vol.Required("id"): selector.TextSelector(),
            vol.Required("municipality"): selector.TextSelector(),
            vol.Required("gnumber"): selector.TextSelector(),
            vol.Required("bnumber"): selector.TextSelector(),
            vol.Required("snumber"): selector.TextSelector(),
        }
    ),
    "ecoharmonogram_pl": vol.Schema(
        {
            vol.Required("town"): selector.TextSelector(),
            vol.Optional("district"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
            vol.Optional("house_number"): selector.TextSelector(),
            vol.Optional("additional_sides_matcher"): selector.TextSelector(),
            vol.Optional("community"): selector.TextSelector(),
        }
    ),
    "sepan_remondis_pl": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("street_number"): selector.TextSelector(),
        }
    ),
    "warszawa19115_pl": vol.Schema(
        {
            vol.Optional("street_address"): selector.TextSelector(),
            vol.Optional("geolocation_id"): selector.TextSelector(),
        }
    ),
    "ekosystem_wroc_pl": vol.Schema(
        {
            vol.Required("location_id"): selector.TextSelector(),
        }
    ),
    "mojiodpadki_si": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "affarsverken_se": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "juneavfall_se": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "lsr_nu": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "lerum_se": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "tekniskaverken_se": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("city"): selector.TextSelector(),
        }
    ),
    "gotland_se": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "miljoteknik_se": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "samiljo_se": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("city"): selector.TextSelector(),
        }
    ),
    "srvatervinning_se": vol.Schema(
        {
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "ssam_se": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "sysav_se": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "uppsalavatten_se": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("city"): selector.TextSelector(),
        }
    ),
    "vasyd_se": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "a_region_ch": vol.Schema(
        {
            vol.Required("municipality"): selector.TextSelector(),
            vol.Optional("district"): selector.TextSelector(),
        }
    ),
    "grosswangen_ch": vol.Schema({}),
    "lindau_ch": vol.Schema(
        {
            vol.Required("city"): selector.TextSelector(),
        }
    ),
    "muenchenstein_ch": vol.Schema(
        {
            vol.Required("waste_district"): selector.TextSelector(),
        }
    ),
    "real_luzern_ch": vol.Schema(
        {
            vol.Required("municipality_id"): selector.TextSelector(),
            vol.Optional("street_id"): selector.TextSelector(),
        }
    ),
    "aberdeenshire_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "allerdale_gov_uk": vol.Schema(
        {
            vol.Optional("address_name_number"): selector.TextSelector(),
            vol.Optional("address_postcode"): selector.TextSelector(),
        }
    ),
    "ambervalley_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "ashfield_gov_uk": vol.Schema(
        {
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("number"): selector.TextSelector(),
            vol.Optional("name"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "ashford_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "aylesburyvaledc_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "basildon_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "basingstoke_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "bathnes_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("housenameornumber"): selector.TextSelector(),
        }
    ),
    "bedford_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "binzone_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "blackburn_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "west_norfolk_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "bracknell_forest_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "bradford_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "braintree_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "breckland_gov_uk": vol.Schema(
        {
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("address"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "bristol_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "south_norfolk_and_broadland_gov_uk": vol.Schema(
        {
            vol.Optional("address_payload"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("address"): selector.TextSelector(),
        }
    ),
    "broxtowe_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "chiltern_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "burnley_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "cambridge_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("number"): selector.TextSelector(),
        }
    ),
    "canterbury_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("number"): selector.TextSelector(),
        }
    ),
    "cardiff_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "centralbedfordshire_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("house_name"): selector.TextSelector(),
        }
    ),
    "cherwell_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "cheshire_east_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("name_number"): selector.TextSelector(),
        }
    ),
    "cheshire_west_and_chester_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "chesterfield_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "chichester_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "doncaster_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "lincoln_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "york_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "colchester_gov_uk": vol.Schema(
        {
            vol.Required("llpgid"): selector.TextSelector(),
        }
    ),
    "cornwall_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("housenumberorname"): selector.TextSelector(),
        }
    ),
    "crawley_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Optional("usrn"): selector.TextSelector(),
        }
    ),
    "croydon_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("houseID"): selector.TextSelector(),
        }
    ),
    "derby_gov_uk": vol.Schema(
        {
            vol.Optional("premises_id"): selector.TextSelector(),
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("house_number"): selector.TextSelector(),
        }
    ),
    "dudley_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "durham_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "eastcambs_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "eastherts_gov_uk": vol.Schema(
        {
            vol.Optional("address_name_numer"): selector.TextSelector(),
            vol.Optional("address_name_number"): selector.TextSelector(),
            vol.Optional("address_street"): selector.TextSelector(),
            vol.Optional("street_town"): selector.TextSelector(),
            vol.Optional("address_postcode"): selector.TextSelector(),
        }
    ),
    "east_northamptonshire_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "east_renfrewshire_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "eastriding_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "elmbridge_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "environmentfirst_co_uk": vol.Schema(
        {
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("number"): selector.TextSelector(),
            vol.Optional("name"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "exeter_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "fareham_gov_uk": vol.Schema(
        {
            vol.Required("road_name"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "fccenvironment_co_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Optional("region"): selector.TextSelector(),
        }
    ),
    "fenland_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("house_number"): selector.TextSelector(),
        }
    ),
    "fife_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "gateshead_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "glasgow_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "guildford_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "gwynedd_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "harlow_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "herefordshire_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("number"): selector.TextSelector(),
        }
    ),
    "highland_gov_uk": vol.Schema(
        {
            vol.Required("record_id"): selector.TextSelector(),
        }
    ),
    "horsham_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "huntingdonshire_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "iweb_itouchvision_com": vol.Schema(
        {
            vol.Required("council"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "jointwastesolutions_org": vol.Schema(
        {
            vol.Required("house"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
            vol.Optional("borough"): selector.TextSelector(),
        }
    ),
    "kirklees_gov_uk": vol.Schema(
        {
            vol.Required("door_num"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "biffaleicester_co_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("number"): selector.TextSelector(),
        }
    ),
    "lisburn_castlereagh_gov_uk": vol.Schema(
        {
            vol.Optional("property_id"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("house_number"): selector.TextSelector(),
        }
    ),
    "liverpool_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("name_number"): selector.TextSelector(),
        }
    ),
    "bexley_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "bromley_gov_uk": vol.Schema(
        {
            vol.Required("property"): selector.TextSelector(),
        }
    ),
    "camden_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "lewisham_gov_uk": vol.Schema(
        {
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("number"): selector.TextSelector(),
            vol.Optional("name"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "merton_gov_uk": vol.Schema(
        {
            vol.Required("property"): selector.TextSelector(),
        }
    ),
    "maidstone_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "maldon_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "manchester_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "mansfield_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "midsussex_gov_uk": vol.Schema(
        {
            vol.Optional("house_name"): selector.TextSelector(),
            vol.Optional("house_number"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("address"): selector.TextSelector(),
        }
    ),
    "middlesbrough_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "milton_keynes_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "newcastle_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "newcastle_staffs_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "newport_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "northherts_gov_uk": vol.Schema(
        {
            vol.Optional("address_name_numer"): selector.TextSelector(),
            vol.Optional("address_street"): selector.TextSelector(),
            vol.Optional("street_town"): selector.TextSelector(),
            vol.Optional("address_postcode"): selector.TextSelector(),
        }
    ),
    "north_kesteven_org_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "northlincs_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "nsomerset_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "northyorks_hambleton_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "nottingham_city_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "oxford_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "peterborough_gov_uk": vol.Schema(
        {
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("number"): selector.TextSelector(),
            vol.Optional("name"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "portsmouth_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "reading_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("housenameornumber"): selector.TextSelector(),
        }
    ),
    "redbridge_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "reigatebanstead_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "rctcbc_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "richmondshire_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "rotherham_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "runnymede_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "rushcliffe_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "rushmoor_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "salford_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "sheffield_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "scambs_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("number"): selector.TextSelector(),
        }
    ),
    "southderbyshire_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "southglos_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "sholland_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "southtyneside_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "southampton_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "stevenage_gov_uk": vol.Schema(
        {
            vol.Required("road"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "stockport_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "stockton_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "stoke_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "stratford_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "swindon_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "tameside_gov_uk": vol.Schema(
        {
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "telford_gov_uk": vol.Schema(
        {
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("name_number"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "tewkesbury_gov_uk": vol.Schema(
        {
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "kingston_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "tmbc_gov_uk": vol.Schema(
        {
            vol.Required("post_code"): selector.TextSelector(),
            vol.Required("address"): selector.TextSelector(),
        }
    ),
    "uttlesford_gov_uk": vol.Schema(
        {
            vol.Optional("house"): selector.TextSelector(),
        }
    ),
    "walsall_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "warrington_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "waverley_gov_uk": vol.Schema(
        {
            vol.Optional("address_name_numer"): selector.TextSelector(),
            vol.Optional("address_street"): selector.TextSelector(),
            vol.Optional("street_town"): selector.TextSelector(),
            vol.Optional("address_postcode"): selector.TextSelector(),
        }
    ),
    "wealden_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "welhat_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
            vol.Required("postcode"): selector.TextSelector(),
        }
    ),
    "westberks_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("housenumberorname"): selector.TextSelector(),
        }
    ),
    "west_dunbartonshire_gov_uk": vol.Schema(
        {
            vol.Optional("house_number"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("street"): selector.TextSelector(),
            vol.Optional("town"): selector.TextSelector(),
        }
    ),
    "wigan_gov_uk": vol.Schema(
        {
            vol.Required("postcode"): selector.TextSelector(),
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "wiltshire_gov_uk": vol.Schema(
        {
            vol.Optional("uprn"): selector.TextSelector(),
            vol.Optional("postcode"): selector.TextSelector(),
        }
    ),
    "rbwm_gov_uk": vol.Schema(
        {
            vol.Required("uprn"): selector.TextSelector(),
        }
    ),
    "wirral_gov_uk": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("suburb"): selector.TextSelector(),
        }
    ),
    "wokingham_gov_uk": vol.Schema(
        {
            vol.Optional("postcode"): selector.TextSelector(),
            vol.Optional("property"): selector.TextSelector(),
            vol.Optional("address"): selector.TextSelector(),
        }
    ),
    "wyreforestdc_gov_uk": vol.Schema(
        {
            vol.Optional("post_code"): selector.TextSelector(),
            vol.Optional("number"): selector.TextSelector(),
            vol.Optional("name"): selector.TextSelector(),
            vol.Optional("uprn"): selector.TextSelector(),
        }
    ),
    "okc_gov": vol.Schema(
        {
            vol.Required("objectID"): selector.TextSelector(),
        }
    ),
    "pgh_st": vol.Schema(
        {
            vol.Required("house_number"): selector.TextSelector(),
            vol.Required("street_name"): selector.TextSelector(),
            vol.Required("zipcode"): selector.TextSelector(),
        }
    ),
    "recyclecoach_com": vol.Schema(
        {
            vol.Required("street"): selector.TextSelector(),
            vol.Required("city"): selector.TextSelector(),
            vol.Required("state"): selector.TextSelector(),
            vol.Optional("project_id"): selector.TextSelector(),
            vol.Optional("district_id"): selector.TextSelector(),
            vol.Optional("zone_id"): selector.TextSelector(),
        }
    ),
    "republicservices_com": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
        }
    ),
    "seattle_gov": vol.Schema(
        {
            vol.Required("street_address"): selector.TextSelector(),
            vol.Optional("prem_code"): selector.TextSelector(),
        }
    ),
    # End of source_config section
}
