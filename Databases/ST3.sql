--What is the average rainfall and average wind speed, per zone, per month?

SELECT swh.LocationName ZoneName, DATENAME(MONTH, swh.Date) Months, 
ROUND(AVG(swh.Rainfall),2) AverageRainfall, ROUND(AVG(swh.WindSpeed),2) AverageWindSpeed 
FROM sundarban_weather_history1 swh
GROUP BY swh.LocationName, DATENAME(MONTH, swh.Date);

--Which zone-month combinations have the highest average rainfall?
SELECT TOP 1 swh.LocationName ZoneName, DATENAME(MONTH, swh.Date) Months, 
	ROUND(AVG(swh.Rainfall),2) AverageRainfall
	FROM sundarban_weather_history1 swh
	GROUP BY swh.LocationName, DATENAME(MONTH, swh.Date)
	ORDER BY ROUND(AVG(swh.Rainfall),2) DESC



--How many years of data contributed to each zone-month average?
SELECT LocationName, DATENAME(MONTH, Date) AS Months, 
       COUNT(DISTINCT YEAR(Date)) AS YearsOfData
FROM sundarban_weather_history1
GROUP BY LocationName, DATENAME(MONTH, Date);

-- For a given zone and month, what single query returns rainfall, wind, and a CASE-based risk label (Low/Moderate/High)?
-- Step 1: see the actual spread of monthly rainfall averages across ALL zone-months
WITH ZoneMonthAvg AS (
    SELECT LocationName, DATENAME(MONTH, Date) AS Months,
           AVG(Rainfall) AS AvgRainfall
    FROM sundarban_weather_history1
    GROUP BY LocationName, DATENAME(MONTH, Date)
)
SELECT 
    PERCENTILE_CONT(0.33) WITHIN GROUP (ORDER BY AvgRainfall) OVER() AS P33,
    PERCENTILE_CONT(0.66) WITHIN GROUP (ORDER BY AvgRainfall) OVER() AS P66
FROM ZoneMonthAvg;

-- Same for WindSpeed

WITH ZoneMonthAvg AS (
    SELECT LocationName, DATENAME(MONTH, Date) AS Months,
           AVG(WindSpeed) AS AvgWindSpeed
    FROM sundarban_weather_history1
    GROUP BY LocationName, DATENAME(MONTH, Date)
)
SELECT 
    PERCENTILE_CONT(0.33) WITHIN GROUP (ORDER BY AvgWindSpeed) OVER() AS P33,
    PERCENTILE_CONT(0.66) WITHIN GROUP (ORDER BY AvgWindSpeed) OVER() AS P66
FROM ZoneMonthAvg;



-- Creating the table risk thershold with the help of the computed p33 and p66 value for rainfall and windspeed
CREATE TABLE RiskThresholds (
    HazardType VARCHAR(30),
    P33 DECIMAL(6,2),
    P66 DECIMAL(6,2),
    LastCalculated DATE
);

INSERT INTO RiskThresholds (HazardType, P33, P66, LastCalculated)
VALUES 
    ('Rainfall', 1.64, 7.90, GETDATE()),
    ('WindSpeed', 12.91, 18.56, GETDATE());


-- Step 2: use those data-derived thresholds in the CASE statement
DECLARE @Zone VARCHAR(50) = 'Jharkhali'
DECLARE @Month VARCHAR(50) = 'October'

SELECT 
    w.LocationName,
    ROUND(AVG(w.Rainfall), 2) AS AvgRainfall,
    ROUND(AVG(w.WindSpeed), 2) AS AvgWindSpeed,
    CASE 
        WHEN AVG(w.Rainfall) < rt_rain.P33 THEN 'Low'
        WHEN AVG(w.Rainfall) < rt_rain.P66 THEN 'Moderate'
        ELSE 'High'
    END AS RainfallRisk,
    CASE 
        WHEN AVG(w.WindSpeed) < rt_wind.P33 THEN 'Low'
        WHEN AVG(w.WindSpeed) < rt_wind.P66 THEN 'Moderate'
        ELSE 'High'
    END AS WindRisk
FROM sundarban_weather_history1 w
CROSS JOIN (SELECT P33, P66 FROM RiskThresholds WHERE HazardType = 'Rainfall') rt_rain
CROSS JOIN (SELECT P33, P66 FROM RiskThresholds WHERE HazardType = 'WindSpeed') rt_wind
WHERE w.LocationName = @Zone AND DATENAME(MONTH, w.Date) = @Month
GROUP BY w.LocationName, rt_rain.P33, rt_rain.P66, rt_wind.P33, rt_wind.P66;






