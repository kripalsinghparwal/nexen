from datetime import datetime


def format_date(date_str):
    """
    Convert ISO date to DD-MM-YYYY format
    """
    if not date_str:
        return None

    try:
        return datetime.fromisoformat(date_str).strftime("%d-%m-%Y")
    except:
        return date_str


def prepare_ngo_dict(summary_data, detail_data):
    """
    Merge NGO summary API data + detail API data into final fixed dict
    """

    # Primary + Secondary sectors
    primary_sectors = []
    secondary_sectors = []

    for item in detail_data.get("workAreas", []):
        for p in item.get("primarySectors", []):
            if p.get("value"):
                primary_sectors.append(p["value"])

        for s in item.get("secondarySectors", []):
            if s.get("value"):
                secondary_sectors.append(s["value"])

    # Operational states & districts
    operational_states = []
    operational_districts = []

    for item in detail_data.get("workAreas", []):
        district = item.get("district", {})

        if district.get("districtName"):
            operational_districts.append(district["districtName"])

        state = district.get("state", {})
        if state.get("stateName"):
            operational_states.append(state["stateName"])

    # Office bearers
    office_bearers = []

    for member in detail_data.get("memberInfo", []):
        office_bearers.append({
            "name": member.get("name"),
            "designation": member.get("designation")
        })

    final_dict = {
        "ngo_name": summary_data.get("ngoName"),
        "registration_details": f"{summary_data.get('registrationNo')}\n"
                                f"{summary_data.get('districtName')} "
                                f"({summary_data.get('stateName')})",

        "main_address": (
            f"{summary_data.get('address', '').replace(chr(10), ' ')}, "
            f"{summary_data.get('subDstName')}, "
            f"{summary_data.get('districtName')} "
            f"({summary_data.get('stateName')}) - "
            f"{summary_data.get('pinCode')}"
        ),

        "detail_url": "https://ngodarpan.gov.in/#/search-ngo",

        "darpan_id": summary_data.get("darpanId"),

        "darpan_registration_date": format_date(
            summary_data.get("lastUpdateOn")
        ),

        "registered_with": detail_data.get("regAuthrty"),

        "type_of_npo": summary_data.get("ngoType"),

        "registration_no": summary_data.get("registrationNo"),

        "act_name": detail_data.get("actName"),

        "city_of_registration": detail_data.get("distrctName"),

        "state_of_registration": detail_data.get("stateName"),

        "date_of_registration": format_date(
            detail_data.get("registrationDate")
        ),

        "address": (
            f"{detail_data.get('address', '').replace(chr(10), ' ')}, "
            f"{detail_data.get('subDstName')}, "
            f"{detail_data.get('distrctName')} "
            f"({detail_data.get('stateName')}) - "
            f"{detail_data.get('pincode')}"
        ),

        "mobile": detail_data.get("mobile"),

        "email": detail_data.get("email"),

        "website": detail_data.get("ngoUrl") or "--",

        "primary_sectors": list(set(primary_sectors)),

        "secondary_sectors": list(set(secondary_sectors)),

        "operational_states": list(set(operational_states)),

        "operational_districts": list(set(operational_districts)),

        "office_bearers": office_bearers
    }

    return final_dict