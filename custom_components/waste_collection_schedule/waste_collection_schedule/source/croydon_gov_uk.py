import json
import re
from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import postcode, street_address
from waste_collection_schedule.transformers import HtmlTransformer

API_URLS = {
    "BASE": "https://service.croydon.gov.uk",
    "CSRF": "/wasteservices/w/webpage/bin-day-enter-address",
    "SEARCH": "/wasteservices/w/webpage/bin-day-enter-address?webpage_subpage_id=PAG0000898EECEC1&webpage_token=faab02e1f62a58f7bad4c2ae5b8622e19846b97dde2a76f546c4bb1230cee044&widget_action=fragment_action",
    "SCHEDULE": "/wasteservices/w/webpage/bin-day-enter-address?webpage_subpage_id=PAG0000898EECEC1&webpage_token=faab02e1f62a58f7bad4c2ae5b8622e19846b97dde2a76f546c4bb1230cee044",
}

HEADER_COMPONENTS = {
    "BASE": {
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Host": "service.croydon.gov.uk",
        "Origin": API_URLS["BASE"],
        "sec-ch-ua": '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-User": "?1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    },
    "GET": {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Sec-Fetch-Mode": "none",
    },
    "POST": {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Sec-Fetch-Mode": "same-origin",
        "X-Requested-With": "XMLHttpRequest",
    },
}

SESSION_STORAGE = {
    "destination_stack": [
        "w/webpage/bin-day-enter-address",
        "w/webpage/your-bin-collection-details?context_record_id=86086077&webpage_token=5c047b2c10b4aad66bef2054aac6bea52ad7a5e185ffdf7090b01f8ddc96728f",
        "w/webpage/bin-day-enter-address",
        "w/webpage/your-bin-collection-details?context_record_id=86085229&webpage_token=cf1b8fd6213f4823277d98c1dd8a992e6ebef1fabc7d892714e5d9dade448c37",
        "w/webpage/bin-day-enter-address",
        "w/webpage/your-bin-collection-details?context_record_id=86084221&webpage_token=7f52fb51019bf0e6bfe9647b1b31000124bd92a9d95781f1557f58b3ed40da52",
        "w/webpage/bin-day-enter-address",
        "w/webpage/your-bin-collection-details?context_record_id=86083209&webpage_token=de50c265da927336f526d9d9a44947595c3aa38965aa8c495ac2fb73d272ece8",
        "w/webpage/bin-day-enter-address",
    ],
    "last_context_record_id": "86086077",
}
_GET_HEADERS = {**HEADER_COMPONENTS["BASE"], **HEADER_COMPONENTS["GET"]}
_POST_HEADERS = {**HEADER_COMPONENTS["BASE"], **HEADER_COMPONENTS["POST"]}


def _csrf(response, **_):
    script = BeautifulSoup(response.text, "html.parser").select_one(
        "div.app-body script[type='text/javascript']"
    )
    match = re.search(
        r"""var CSRF = ('|\")(.*?)('|\");""",
        script.get_text() if script is not None else "",
    )
    if match is None:
        raise ValueError("CSRF token not found")
    return match.group(2)


def _input(soup, name, *, last=False):
    inputs = soup.select(f'input[name="{name}"]')
    if not inputs:
        raise ValueError(f"Form field {name!r} not found")
    value = inputs[-1 if last else 0].get("value")
    if not isinstance(value, str):
        raise ValueError(f"Form field {name!r} has no value")
    return value


def _form_state(response, csrf, **_):
    page = response.json()["data"]
    soup = BeautifulSoup(page, "html.parser")
    return {
        "key": re.findall(r'data-unique_key="(C_[a-f0-9]+)"', page)[-1],
        "submitted_widget_group_id": _input(
            soup, "submitted_widget_group_id", last=True
        ),
        "submission_token": _input(soup, "submission_token"),
        "submitted_page_id": _input(soup, "submitted_page_id"),
    }


def _search_data(csrf, form_state, postcode, **_):
    return {
        "code_action": "search",
        "code_params": '{"search_item":"' + str(postcode).upper() + '","is_ss":true}',
        "fragment_action": "handle_event",
        "fragment_id": "PCF0020408EECEC1",
        "fragment_collection_class": "formtable",
        "fragment_collection_editable_values": '{"PCF0021449EECEC1":"1"}',
        "_session_storage": json.dumps(
            {
                "/wasteservices/w/webpage/bin-day-enter-address": {},
                "_global": SESSION_STORAGE,
            }
        ),
        "action_cell_id": "PCL0005629EECEC1",
        "action_page_id": "PAG0000898EECEC1",
        "form_check_ajax": csrf,
    }


def _address_id(response, csrf, form_state, houseID, **_):
    address_id = "0"
    for address in response.json()["response"]["items"]:
        if str(houseID) in str(address["address_single_line"]):
            address_id = str(address["id"])
    return address_id


def _select_data(csrf, form_state, address_id, **_):
    key = form_state["key"]
    return {
        "form_check": csrf,
        "submitted_page_id": form_state["submitted_page_id"],
        "submitted_widget_group_id": form_state["submitted_widget_group_id"],
        "submitted_widget_group_type": "modify",
        "submission_token": form_state["submission_token"],
        f"payload[PAG0000898EECEC1][PWG0002644EECEC1][PCL0005629EECEC1][formtable][{key}][PCF0020408EECEC1]": address_id,
        f"payload[PAG0000898EECEC1][PWG0002644EECEC1][PCL0005629EECEC1][formtable][{key}][PCF0021449EECEC1]": "1",
        f"payload[PAG0000898EECEC1][PWG0002644EECEC1][PCL0005629EECEC1][formtable][{key}][PCF0020072EECEC1]": "Next",
        "submit_fragment_id": "PCF0020072EECEC1",
        "_session_storage": json.dumps({"_global": SESSION_STORAGE}),
        "_update_page_content_request": 1,
        "form_check_ajax": csrf,
    }


def _calendar_data(csrf, *keys, **_):
    return {
        "_dummy": 1,
        "_session_storage": json.dumps({"_global": SESSION_STORAGE}),
        "_update_page_content_request": 1,
        "form_check_ajax": csrf,
    }


def _text(element: Tag, selector: str) -> str:
    found = element.select_one(selector)
    if found is None:
        raise ValueError(f"Collection field {selector!r} not found")
    return found.get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "Croydon Council"
    DESCRIPTION = "Source for croydon.gov.uk services for Croydon Council, UK."
    URL = "https://croydon.gov.uk"
    COUNTRY = "uk"
    TEST_CASES: ClassVar[dict] = {
        "Test_001": {"postcode": "CR0 6LN", "houseID": "64 Coniston Road"},
        "Test_002": {"postcode": "SE25 5BU", "houseID": "23B Howard Road"},
        "Test_003": {"postcode": "CR0 6EG", "houseID": "48 Exeter Road"},
        "Test_004": {"postcode": "CR5 2BG", "houseID": "18 South Drive"},
    }
    PARAMS = (postcode(), street_address("houseID"))
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "Enter your postcode and address as shown at https://service.croydon.gov.uk/wasteservices/w/webpage/bin-day-enter-address. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.Request(
        lambda csrf, form_state, address_id, redirect_url, **_: redirect_url,
        method="POST",
        headers=_POST_HEADERS,
        data=_calendar_data,
        before=(
            retrievers.Lookup(
                API_URLS["BASE"] + API_URLS["CSRF"], headers=_GET_HEADERS, pick=_csrf
            ),
            retrievers.Lookup(
                API_URLS["BASE"] + API_URLS["CSRF"],
                method="POST",
                headers=_POST_HEADERS,
                data=lambda csrf, **_: {
                    "_dummy": "1",
                    "_session_storage": '{"_global":{}}',
                    "_update_page_content_request": "1",
                    "form_check_ajax": csrf,
                },
                pick=_form_state,
            ),
            retrievers.Lookup(
                API_URLS["BASE"] + API_URLS["SEARCH"],
                method="POST",
                headers=_POST_HEADERS,
                data=_search_data,
                pick=_address_id,
            ),
            retrievers.Lookup(
                API_URLS["BASE"] + API_URLS["SCHEDULE"],
                method="POST",
                headers=_POST_HEADERS,
                data=_select_data,
                pick=lambda response, *keys, **_: (
                    API_URLS["BASE"] + response.json()["redirect_url"]
                ),
            ),
        ),
    )
    parse = parsers.HtmlParser("div.listing_template_record", from_json_key="data")
    transform = HtmlTransformer(
        date_getter=lambda element: _text(element, "span.value-as-text"),
        type_getter=lambda element: _text(
            element, "div.fragment_presenter_template_show"
        ),
        parse_date=date_parsers.for_format("%A %d %B %Y"),
        type_value_map={
            "Food waste": wt.FOOD_WASTE,
            "General rubbish": wt.GENERAL_WASTE,
            "Paper and card recycling": wt.PAPER,
            "Glass, plastics, cans and cartons recycling": wt.RECYCLABLES,
        },
    )
