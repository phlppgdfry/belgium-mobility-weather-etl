with ranked as (
  select *, row_number() over (partition by station_id order by snapshot_at desc) as row_num
  from {{ ref('stg_station_status') }}
)
select * exclude (row_num)
from ranked
where row_num = 1
