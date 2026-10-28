# Standalone fallback. During integration, prefer Person 2's canonical compatibility module.
RBC_COMPATIBILITY = {
    "O-": ["O-"], "O+": ["O-", "O+"],
    "A-": ["O-", "A-"], "A+": ["O-", "O+", "A-", "A+"],
    "B-": ["O-", "B-"], "B+": ["O-", "O+", "B-", "B+"],
    "AB-": ["O-", "A-", "B-", "AB-"],
    "AB+": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
}
# Recipient group -> compatible donor groups for RBC/whole blood.
PLASMA_COMPATIBILITY = {
    "O-": ["O-", "O+", "A-", "A+", "B-", "B+", "AB-", "AB+"],
    "O+": ["O+", "A+", "B+", "AB+"],
    "A-": ["A-", "A+", "AB-", "AB+"],
    "A+": ["A+", "AB+"],
    "B-": ["B-", "B+", "AB-", "AB+"],
    "B+": ["B+", "AB+"],
    "AB-": ["AB-", "AB+"],
    "AB+": ["AB+"],
}
def compatible_groups(recipient_group: str, component_type: str) -> list[str]:
    if component_type == "PLASMA":
        return PLASMA_COMPATIBILITY[recipient_group]
    return RBC_COMPATIBILITY[recipient_group]
