select
  city,
  observed_at,
  temperature_c,
  precipitation_mm,
  is_rainy,
  estimated_mobility_demand
from {{ source('public', 'fact_mobility_weather') }}

