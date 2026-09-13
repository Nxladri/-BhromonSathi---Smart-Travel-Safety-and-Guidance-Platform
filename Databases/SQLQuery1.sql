-- Simulates: user selects "Dobanki" as their destination
-- Returns: all General precautions + anything specific to Dobanki

SELECT PrecautionID, ScopeType, Phase, Category, Description
FROM Safety_Precautions
WHERE ScopeType = 'General' 
   OR LocationName = 'Dobanki'
ORDER BY 
    CASE Phase 
        WHEN 'BeforeTrip' THEN 1 
        WHEN 'DuringTrip' THEN 2 
        WHEN 'Emergency' THEN 3 
    END,
    ScopeType DESC;  -- shows zone-specific precautions before general ones within each phase