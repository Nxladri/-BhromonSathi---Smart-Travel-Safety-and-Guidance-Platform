-- What is the average rainfall per zone, across all years?
SELECT LocationName, ROUND(AVG(Rainfall),2) AverageRainfallPerZone
FROM sundarban_weather_history1 swh
GROUP BY LocationName
-- What is the highest single-day rainfall recorded, and in which zone/date did it happen?
SELECT TOP 1 swh.Rainfall HighestRainfall, swh.LocationName, swh.Date 
FROM sundarban_weather_history1 swh
ORDER BY swh.Rainfall DESC

-- What is the average rainfall per month (all zones combined), to see the overall monsoon pattern?
SELECT DATENAME(MONTH, swh.Date) Months,
ROUND(AVG(swh.Rainfall),2) AverageRainfall
FROM sundarban_weather_history1 swh
GROUP BY DATENAME(MONTH, swh.Date)
