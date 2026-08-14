select
  city,
  date(observed_at) as forecast_date,
  round(avg(estimated_mobility_demand)) as avg_demand_signal,
  round(sum(precipitation_mm), 1) as precipitation_mm,
  sum(case when is_rainy then 1 else 0 end) as rainy_hours
from {{ ref('stg_mobility_weather') }}
group by 1, 2

