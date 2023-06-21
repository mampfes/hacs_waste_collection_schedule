import voluptuous as vol
from homeassistant.helpers import selector

# schema for initial config flow, entered by "Add Integration"
COUNTRY_LIST = [
    "generic",
    # Begin of country section
    "au",
    "at",
    "be",
    "ca",
    "de",
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

CONF_COUNTRY = "country"
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
    "source_au_banyule_vic_gov_au",
    "source_au_belmont_wa_gov_au",
    "source_au_brisbane_qld_gov_au",
    "source_au_campbelltown_nsw_gov_au",
    "source_au_cardinia_vic_gov_au",
    "source_au_canadabay_nsw_gov_au",
    "source_au_onkaparingacity_com",
    "source_au_goldcoast_qld_gov_au",
    "source_au_hume_vic_gov_au",
    "source_au_innerwest_nsw_gov_au",
    "source_au_ipswich_qld_gov_au",
    "source_au_kuringgai_nsw_gov_au",
    "source_au_lakemac_nsw_gov_au",
    "source_au_mrsc_vic_gov_au",
    "source_au_maribyrnong_vic_gov_au",
    "source_au_maroondah_vic_gov_au",
    "source_au_melton_vic_gov_au",
    "source_au_nillumbik_vic_gov_au",
    "source_au_nawma_sa_gov_au",
    "source_au_recyclesmart_com",
    "source_au_stonnington_vic_gov_au",
    "source_au_thehills_nsw_gov_au",
    "source_au_unley_sa_gov_au",
    "source_au_whittlesea_vic_gov_au",
    "source_au_wollongongwaste_com_au",
    "source_au_wyndham_vic_gov_au",
]

SOURCE_LIST_at = [
    "source_at_citiesapps_com",
    "source_at_bmv_at",
    "source_at_infeo_at",
    "source_at_korneuburg_stadtservice_at",
    "source_at_data_umweltprofis_at",
    "source_at_wsz_moosburg_at",
]

SOURCE_LIST_be = [
    "source_be_hygea_be",
    "source_be_recycleapp_be",
]

SOURCE_LIST_ca = [
    "source_ca_toronto_ca",
]

SOURCE_LIST_de = [
    "source_de_stuttgart_de",
    "source_de_abfall_io",
    "source_de_offenbach_de",
    "source_de_wuerzburg_de",
    "source_de_abfallnavi_de",
    "source_de_abfalltermine_forchheim_de",
    "source_de_abfallwirtschaft_germersheim_de",
    "source_de_aw_harburg_de",
    "source_de_alw_wf_de",
    "source_de_awn_de",
    "source_de_nuernberger_land_de",
    "source_de_abfallwirtschaft_pforzheim_de",
    "source_de_awr_de",
    "source_de_abfallwirtschaft_fuerth_eu",
    "source_de_schweinfurt_de",
    "source_de_awsh_de",
    "source_de_zva_wmk_de",
    "source_de_abfall_zollernalbkreis_de",
    "source_de_awb_es_de",
    "source_de_abki_de",
    "source_de_meinawb_de",
    "source_de_awb_mainz_bingen_de",
    "source_de_art_trier_de",
    "source_de_asr_chemnitz_de",
    "source_de_abfallwirtschaft_vechta_de",
    "source_de_awb_bad_kreuznach_de",
    "source_de_awbkoeln_de",
    "source_de_awb_oldenburg_de",
    "source_de_awido_de",
    "source_de_berlin_recycling_de",
    "source_de_bsr_de",
    "source_de_bielefeld_de",
    "source_de_buergerportal_de",
    "source_de_c_trace_de",
    "source_de_cmcitymedia_de",
    "source_de_dillingen_saar_de",
    "source_de_ead_darmstadt_de",
    "source_de_egn_abfallkalender_de",
    "source_de_hausmuell_info",
    "source_de_heilbronn_de",
    "source_de_jumomind_de",
    "source_de_kaev_niederlausitz",
    "source_de_ks_boerde_de",
    "source_de_kwb_goslar_de",
    "source_de_kwu_de",
    "source_de_erlangen_hoechstadt_de",
    "source_de_geoport_nwm_de",
    "source_de_landkreis_rhoen_grabfeld",
    "source_de_lrasha_de",
    "source_de_landkreis_wittmund_de",
    "source_de_muellabfuhr_de",
    "source_de_muellmax_de",
    "source_de_abfall_neunkirchen_siegerland_de",
    "source_de_regioentsorgung_de",
    "source_de_rh_entsorgung_de",
    "source_de_sector27_de",
    "source_de_stadt_willich_de",
    "source_de_stadtreinigung_dresden_de",
    "source_de_stadtreinigung_hamburg",
    "source_de_stadtreinigung_leipzig_de",
    "source_de_stadtservice_bruehl_de",
    "source_de_staedteservice_de",
    "source_de_sbazv_de",
    "source_de_wermelskirchen_de",
    "source_de_was_wolfsburg_de",
    "source_de_zaw_online_de",
    "source_de_zakb_de",
    "source_de_aha_region_de",
    "source_de_zva_sek_de",
]

SOURCE_LIST_lt = [
    "source_lt_grafikai_svara_lt",
]

SOURCE_LIST_lu = [
    "source_lu_esch_lu",
]

SOURCE_LIST_nl = [
    "source_nl_circulus_nl",
    "source_nl_ximmio_nl",
]

SOURCE_LIST_nz = [
    "source_nz_aucklandcouncil_govt_nz",
    "source_nz_ccc_govt_nz",
    "source_nz_wastenet_org_nz",
    "source_nz_horowhenua_govt_nz",
    "source_nz_waipa_nz",
    "source_nz_wellington_govt_nz",
]

SOURCE_LIST_no = [
    "source_no_minrenovasjon_no",
    "source_no_movar_no",
    "source_no_oslokommune_no",
    "source_no_remidt_no",
    "source_no_stavanger_no",
]

SOURCE_LIST_pl = [
    "source_pl_ecoharmonogram_pl",
    "source_pl_sepan_remondis_pl",
    "source_pl_warszawa19115_pl",
    "source_pl_ekosystem_wroc_pl",
]

SOURCE_LIST_si = [
    "source_si_mojiodpadki_si",
]

SOURCE_LIST_se = [
    "source_se_affarsverken_se",
    "source_se_juneavfall_se",
    "source_se_lsr_nu",
    "source_se_lerum_se",
    "source_se_tekniskaverken_se",
    "source_se_gotland_se",
    "source_se_miljoteknik_se",
    "source_se_samiljo_se",
    "source_se_srvatervinning_se",
    "source_se_ssam_se",
    "source_se_sysav_se",
    "source_se_uppsalavatten_se",
    "source_se_vasyd_se",
]

SOURCE_LIST_ch = [
    "source_ch_a_region_ch",
    "source_ch_grosswangen_ch",
    "source_ch_lindau_ch",
    "source_ch_muenchenstein_ch",
]

SOURCE_LIST_uk = [
    "source_uk_ambervalley_gov_uk",
    "source_uk_ashfield_gov_uk",
    "source_uk_basildon_gov_uk",
    "source_uk_basingstoke_gov_uk",
    "source_uk_bedford_gov_uk",
    "source_uk_binzone_uk",
    "source_uk_blackburn_gov_uk",
    "source_uk_bracknell_forest_gov_uk",
    "source_uk_bradford_gov_uk",
    "source_uk_braintree_gov_uk",
    "source_uk_breckland_gov_uk",
    "source_uk_bristol_gov_uk",
    "source_uk_chiltern_gov_uk",
    "source_uk_cambridge_gov_uk",
    "source_uk_canterbury_gov_uk",
    "source_uk_centralbedfordshire_gov_uk",
    "source_uk_cherwell_gov_uk",
    "source_uk_cheshire_east_gov_uk",
    "source_uk_chesterfield_gov_uk",
    "source_uk_chichester_gov_uk",
    "source_uk_doncaster_gov_uk",
    "source_uk_york_gov_uk",
    "source_uk_colchester_gov_uk",
    "source_uk_cornwall_gov_uk",
    "source_uk_derby_gov_uk",
    "source_uk_eastcambs_gov_uk",
    "source_uk_eastherts_gov_uk",
    "source_uk_east_northamptonshire_gov_uk",
    "source_uk_elmbridge_gov_uk",
    "source_uk_environmentfirst_co_uk",
    "source_uk_fareham_gov_uk",
    "source_uk_fccenvironment_co_uk",
    "source_uk_fenland_gov_uk",
    "source_uk_fife_gov_uk",
    "source_uk_gateshead_gov_uk",
    "source_uk_glasgow_gov_uk",
    "source_uk_guildford_gov_uk",
    "source_uk_harlow_gov_uk",
    "source_uk_herefordshire_gov_uk",
    "source_uk_horsham_gov_uk",
    "source_uk_huntingdonshire_gov_uk",
    "source_uk_biffaleicester_co_uk",
    "source_uk_lisburn_castlereagh_gov_uk",
    "source_uk_liverpool_gov_uk",
    "source_uk_bexley_gov_uk",
    "source_uk_bromley_gov_uk",
    "source_uk_lewisham_gov_uk",
    "source_uk_merton_gov_uk",
    "source_uk_maldon_gov_uk",
    "source_uk_manchester_uk",
    "source_uk_midsussex_gov_uk",
    "source_uk_middlesbrough_gov_uk",
    "source_uk_newcastle_gov_uk",
    "source_uk_newcastle_staffs_gov_uk",
    "source_uk_newport_gov_uk",
    "source_uk_northherts_gov_uk",
    "source_uk_northlincs_gov_uk",
    "source_uk_nsomerset_gov_uk",
    "source_uk_nottingham_city_gov_uk",
    "source_uk_oxford_gov_uk",
    "source_uk_peterborough_gov_uk",
    "source_uk_portsmouth_gov_uk",
    "source_uk_reading_gov_uk",
    "source_uk_reigatebanstead_gov_uk",
    "source_uk_richmondshire_gov_uk",
    "source_uk_rotherham_gov_uk",
    "source_uk_runnymede_gov_uk",
    "source_uk_rushmoor_gov_uk",
    "source_uk_salford_gov_uk",
    "source_uk_sheffield_gov_uk",
    "source_uk_scambs_gov_uk",
    "source_uk_southderbyshire_gov_uk",
    "source_uk_southglos_gov_uk",
    "source_uk_south_norfolk_and_broadland_gov_uk",
    "source_uk_southtyneside_gov_uk",
    "source_uk_southampton_gov_uk",
    "source_uk_stevenage_gov_uk",
    "source_uk_stockport_gov_uk",
    "source_uk_stockton_gov_uk",
    "source_uk_swindon_gov_uk",
    "source_uk_telford_gov_uk",
    "source_uk_tewkesbury_gov_uk",
    "source_uk_kingston_gov_uk",
    "source_uk_tmbc_gov_uk",
    "source_uk_uttlesford_gov_uk",
    "source_uk_walsall_gov_uk",
    "source_uk_waverley_gov_uk",
    "source_uk_westberks_gov_uk",
    "source_uk_west_dunbartonshire_gov_uk",
    "source_uk_wigan_gov_uk",
    "source_uk_wiltshire_gov_uk",
    "source_uk_wyreforestdc_gov_uk",
]

SOURCE_LIST_us = [
    "source_us_okc_gov",
    "source_us_pgh_st",
    "source_us_republicservices_com",
    "source_us_seattle_gov",
]

# End of source_list section


CONF_SOURCE_NAME = "source_name"
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
