# Update these IDs to control access
# Use SRNs or PESU email IDs (case-insensitive)
SUPERADMIN_IDS = {
    "PES1UG25CS527",
}

# Map class_id -> set of CR SRNs/emails
# class_id format: Sem<Semester>-<Section>
# Example: "Sem2-A"
CR_IDS_BY_CLASS = {
    # "Sem2-A": {"SRN123", "cr@pesu.pes.edu"},
    "Sem2-SectionC9": {"PES1UG25CS527"},
    
}
