-- 1. No of total rows in the weather record table - 36530
SELECT * FROM sundarban_weather_history1;\


--2. How many rows exist per zone (LocationName)?
SELECT swh.LocationName, COUNT(*) AS RowCounts
FROM sundarban_weather_history1 swh
GROUP BY swh.LocationName

--3. What's the earliest and latest date in the table, per zone?
SELECT swh.LocationName,
MIN(Date) EarliestDate,
MAX(Date) LatestDate
FROM  sundarban_weather_history1 swh
GROUP BY swh.LocationName

--4. Are there any duplicate rows for the same zone and date?
SELECT COUNT(*) UniqueRows
FROM  sundarban_weather_history1 swh
GROUP BY LocationName, Date
HAVING COUNT(*) > 1

--5. Are there any NULL values in Rainfall, WindSpeed, TempMax, or TempMin?
SELECT Rainfall, WindSpeed, TempMax, TempMin 
FROM sundarban_weather_history1
WHERE Rainfall IS NULL OR WindSpeed IS NULL OR TempMax IS NULL OR TempMin IS NULL




