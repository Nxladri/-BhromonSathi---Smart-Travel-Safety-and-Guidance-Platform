CREATE TABLE EmergencyCenters (
    CenterID INT PRIMARY KEY,
    CenterName VARCHAR(100) NOT NULL,
    CenterType VARCHAR(30) NOT NULL,        -- 'Hospital', 'Police Station', 'Forest Office'
    NearestLocationName VARCHAR(50),
);

INSERT INTO EmergencyCenters (CenterID, CenterName, CenterType, NearestLocationName)
VALUES
(1, 'Gosaba Rural Hospital', 'Hospital', 'Gosaba'),
(2, 'Canning Sub-Divisional Hospital', 'Hospital', 'Canning'),
(3, 'Basanti Rural Hospital', 'Hospital', 'Basanti'),
(4, 'Sundarban Coastal Police Station', 'Police', ' Chhota Molla Khali'),
(5, 'Gosaba Police Station', 'Police', 'Gosaba'),
(6, 'Sundarban Tiger Reserve', 'Forest Office', 'Canning')

ALTER TABLE EmergencyCenters
DROP COLUMN CenterAddress 

SELECT * FROM EmergencyCenters


