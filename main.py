from operator import itemgetter
import asyncio
import aiohttp
from pprint import pprint

REQUEST_HEADERS = {
    "Host": "www.oreillyauto.com",
    # Make a POST request via the "Add by License Plate" menu and copy/paste the request headers here
    # NOTE: the website will not send a response unless you include a valid, recent "Cookie" header
}

result_count = 0


def main():
    # Example input
    results = asyncio.run(get_all_vehicles("AZ", "RI", 50, model="Camry"))
    results = sorted(results, key=lambda d: d["plate_number"])
    print("-" * 30)
    print("RESULTS:")
    pprint(results, sort_dicts=False)


async def get_all_vehicles(
    alphabetical_part: str,
    state: str,
    step: int,
    year: str = "",
    make: str = "",
    model: str = "",
):
    print("Searching for:")
    print("\tState:", state)
    print("\tYear:", year if year else "any")
    print("\tMake:", make if make else "any")
    print("\tModel:", model if model else "any")
    print(
        "If the script shows no progress, ensure that the REQUEST_HEADERS dict is up-to-date."
    )
    results = []
    async with aiohttp.ClientSession() as session:
        # NOTE: Larger "step" values may cause you to be rate-limited (the server will respond with "403 Forbidden")
        for numerical_section in range(0, 1000, step):
            results.append(
                await asyncio.gather(
                    *[
                        get_vehicle_data(
                            session,
                            f"{alphabetical_part}-{str(numerical_part).zfill(3)}",
                            state,
                            year=year,
                            make=make,
                            model=model,
                        )
                        for numerical_part in range(
                            numerical_section, numerical_section + step
                        )
                    ]
                )
            )
            print(
                f"Up to plate {alphabetical_part}-{numerical_section + step - 1}... ({result_count} matches found)"
            )
            await asyncio.sleep(5)
    results = [element for sublist in results for element in sublist]
    return filter(lambda e: e is not None, results)


async def get_vehicle_data(
    session: aiohttp.ClientSession,
    plate_number: str,
    state: str,
    year: str,
    make: str,
    model: str,
) -> dict[str, str] | None:
    url = f"https://www.oreillyauto.com/vehicle/plate/{plate_number}/{state}/false"
    async with session.get(url, headers=REQUEST_HEADERS) as response:
        if response.status != 200:
            print("ERROR: Response", response.status, "at plate", plate_number)
            return
        json_response = await response.json()

    plate_data = json_response["plates"]
    if not plate_data:
        return

    # Results other than the 0th index are vehicles that were registered to the plate in the past, it seems
    vehicle_data = plate_data[0]

    if year and year not in vehicle_data["year"]:
        return

    if make and make not in vehicle_data["make"]:
        return

    if model and model not in vehicle_data["model"]:
        return

    global result_count
    result_count += 1

    _year, _make, _model = itemgetter("year", "make", "model")(vehicle_data)
    return {
        "plate_number": plate_number,
        "year": _year,
        "make": _make,
        "model": _model,
    }


if __name__ == "__main__":
    main()
