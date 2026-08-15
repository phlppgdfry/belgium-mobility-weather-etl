select
  status.station_id,
  station.station_name,
  station.city,
  status.snapshot_at,
  status.available_bikes,
  status.available_ebikes,
  status.available_docks,
  status.occupancy_pct,
  status.availability_state
from {{ source('public', 'fact_station_status') }} as status
inner join {{ source('public', 'dim_bike_station') }} as station using (station_id)
