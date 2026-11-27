# Kenya destinations and operator routes — data notes

This directory is intentionally separated into three kinds of information:

1. **Operator-published passenger routes** — routes shown on the named operator's website. These are not automatically parcel routes.
2. **Published courier outlets** — use the operator's live branch directory and reconfirm the outlet before dispatch.
3. **Historical coverage** — the Communications Authority's 2022 baseline survey. This is useful for planning a nationwide destination directory, but it is not proof that an outlet still operates.

## Safety and accuracy rules

- A Communications Authority licence listing is not proof of a particular route, branch, timetable, fare, or parcel service.
- Do not enable a passenger coach as a parcel carrier until the company confirms parcel/cargo acceptance and the specific route.
- Do not invent intermediate stops. An empty `stops` array means the source did not establish stops.
- Do not publish fares, schedules, capacity, or delivery estimates from this dataset.
- Treat historical stations as research leads. Verify with the operator before creating active dispatch points.
- Keep source URL, check date, and verification status with every imported operator/route.

## Data file

`data/kenya_transport_network.json` contains the source register, operator classifications, passenger routes found on operator websites, and historical courier station coverage. It is a research seed and is not yet connected to parcel booking or dispatch.

## Sources

- Communications Authority of Kenya, Postal and Courier Operators register (15 February 2026): https://ca.go.ke/sites/default/files/2026-03/POSTAL%20AND%20COURIER%20OPERATORS%20AS%20AT%2015TH%20FEB%202026.pdf
- Communications Authority, Baseline Survey for Postal and Courier Services in Kenya (2022): https://www.ca.go.ke/sites/default/files/2023-06/Baseline%20urvey%20for%20Postal%20and%20Courier%20Services%20in%20Kenya%20Report%202022.pdf
- Fargo Courier, branches: https://www.fargocourier.co.ke/our-branches/
- Tahmeed Coach: https://tahmeedcoach.co.ke/
- Modern Coast: https://moderncoast.co.ke/
- Mash Poa: https://www.mashpoabus.com/
