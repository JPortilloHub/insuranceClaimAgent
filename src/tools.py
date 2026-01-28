"""
Insurance Claim Agent Tools
Contains all the tools the agent can use for processing claims.
"""

import pandas as pd
import re
import json
from datetime import datetime
from typing import Optional
from pathlib import Path

# Load client database
CLIENTS_PATH = Path(__file__).parent.parent / "docs" / "Clients.csv"

# Policy coverage definitions based on the Insurance Policy PDF
POLICY_COVERAGE = {
    "Simple": {
        "tier_name": "Simple (Basic Liability & Catastrophe)",
        "bodily_injury_liability": "$25k per person / $50k per accident",
        "property_damage_liability": "$25,000",
        "collision_coverage": "Not Included",
        "comprehensive": "Fire & Theft Only",
        "comprehensive_deductible": "$1,500",
        "uninsured_motorist": "$25k / $50k",
        "medical_payments": "$1,000",
        "roadside_assistance": "Pay-per-use",
        "rental_car_reimbursement": "Not Included",
        "new_car_replacement": "Not Included",
        "personal_effects": "Not Included",
        "glass_coverage": "Not covered unless caused by named peril",
        "restrictions": [
            "Only designated drivers listed on policy are covered (No Permissive Use)",
            "Glass damage not covered unless caused by named peril"
        ],
        "covered_perils": ["Fire", "Lightning", "Theft", "Attempted Theft"],
        "excluded_perils": ["Hail", "Flood", "Falling Objects", "Collision", "Vandalism"]
    },
    "Advanced": {
        "tier_name": "Advanced (Standard Comprehensive)",
        "bodily_injury_liability": "$100k per person / $300k per accident",
        "property_damage_liability": "$100,000",
        "collision_coverage": "Included ($1,000 deductible)",
        "collision_deductible": "$1,000",
        "comprehensive": "Full (Fire, Theft, Vandalism, Weather)",
        "comprehensive_deductible": "$500",
        "uninsured_motorist": "$100k / $300k",
        "medical_payments": "$5,000",
        "roadside_assistance": "Included (15-mile tow limit)",
        "rental_car_reimbursement": "$30/day (Max 30 days)",
        "new_car_replacement": "Not Included",
        "personal_effects": "Up to $200",
        "windshield_repair": "Chip repairs free, full replacement $100 deductible",
        "covered_perils": ["Fire", "Lightning", "Theft", "Attempted Theft", "Flood", "Hail", "Animal Strikes", "Vandalism"],
        "excluded_perils": ["Standard wear and tear"]
    },
    "Premium": {
        "tier_name": "Premium (All-Inclusive Elite)",
        "bodily_injury_liability": "$500k per person / $1M per accident",
        "property_damage_liability": "$250,000",
        "collision_coverage": "Included ($250 deductible)",
        "collision_deductible": "$250",
        "comprehensive": "Full + Zero Deductible Glass",
        "comprehensive_deductible": "$250",
        "uninsured_motorist": "$500k / $1M",
        "medical_payments": "$25,000",
        "roadside_assistance": "Included (100-mile tow limit + Trip Interruption)",
        "rental_car_reimbursement": "$75/day (Max 45 days) or Valet Service",
        "new_car_replacement": "Included (First 3 Years)",
        "personal_effects": "Up to $1,500",
        "glass_coverage": "$0 deductible on windshield replacement",
        "gap_insurance": "Included",
        "oem_parts_guarantee": "Always OEM parts, never aftermarket",
        "pet_injury_coverage": "Up to $1,000",
        "worldwide_coverage": "Up to 30 days in foreign countries",
        "valet_service": "Included",
        "diminished_value_protection": "Included",
        "concierge_claims": "24/7 Dedicated Concierge Claims Line",
        "covered_perils": ["All Perils"],
        "excluded_perils": ["Standard wear and tear"]
    }
}

# General exclusions for all tiers
GENERAL_EXCLUSIONS = [
    "Ridesharing (Uber, Lyft, delivery services) - unless specific endorsement purchased",
    "Intentional Acts - damage caused on purpose by the insured",
    "Racing - any loss while vehicle used on track or competitive event",
    "Wear and Tear - mechanical breakdown, rust, tire wear, electrical failure not caused by accident"
]


def lookup_client_by_policy(policy_number: str) -> dict:
    """
    Look up a client in the database by their policy number.

    Args:
        policy_number: The policy number to search for

    Returns:
        Dictionary with client information or error message
    """
    try:
        df = pd.read_csv(CLIENTS_PATH)

        # Clean up the policy number input
        policy_number = policy_number.strip().upper()

        # Search for the policy
        client = df[df['Policy Number'].str.upper().str.strip() == policy_number]

        if len(client) == 0:
            return {
                "found": False,
                "error": f"No client found with policy number: {policy_number}",
                "suggestion": "Please verify the policy number format (e.g., POL-12345678-A)"
            }

        client_data = client.iloc[0].to_dict()
        return {
            "found": True,
            "client_id": int(client_data['Id']),
            "name": f"{client_data['Name']} {client_data['Surname']}",
            "address": client_data['Address'],
            "country": client_data['Country'],
            "tier": client_data['Tier'],
            "policy_number": client_data['Policy Number']
        }
    except Exception as e:
        return {
            "found": False,
            "error": f"Database error: {str(e)}"
        }


def lookup_client_by_name(name: str) -> dict:
    """
    Look up a client in the database by their name.

    Args:
        name: The client's name (first, last, or full name)

    Returns:
        Dictionary with client information or list of matches
    """
    try:
        df = pd.read_csv(CLIENTS_PATH)
        name_lower = name.strip().lower()

        # Search in both Name and Surname columns
        matches = df[
            df['Name'].str.lower().str.contains(name_lower, na=False) |
            df['Surname'].str.lower().str.contains(name_lower, na=False)
        ]

        if len(matches) == 0:
            return {
                "found": False,
                "error": f"No client found with name matching: {name}"
            }

        if len(matches) == 1:
            client_data = matches.iloc[0].to_dict()
            return {
                "found": True,
                "client_id": int(client_data['Id']),
                "name": f"{client_data['Name']} {client_data['Surname']}",
                "address": client_data['Address'],
                "country": client_data['Country'],
                "tier": client_data['Tier'],
                "policy_number": client_data['Policy Number']
            }

        # Multiple matches
        clients = []
        for _, row in matches.iterrows():
            clients.append({
                "name": f"{row['Name']} {row['Surname']}",
                "policy_number": row['Policy Number'],
                "tier": row['Tier']
            })

        return {
            "found": True,
            "multiple_matches": True,
            "count": len(clients),
            "clients": clients,
            "message": "Multiple clients found. Please specify the policy number."
        }
    except Exception as e:
        return {
            "found": False,
            "error": f"Database error: {str(e)}"
        }


def get_coverage_details(tier: str) -> dict:
    """
    Get detailed coverage information for a specific tier.

    Args:
        tier: The policy tier (Simple, Advanced, or Premium)

    Returns:
        Dictionary with coverage details
    """
    tier = tier.strip().capitalize()

    if tier not in POLICY_COVERAGE:
        return {
            "error": f"Unknown tier: {tier}. Valid tiers are: Simple, Advanced, Premium"
        }

    coverage = POLICY_COVERAGE[tier].copy()
    coverage["general_exclusions"] = GENERAL_EXCLUSIONS
    return coverage


def analyze_coverage_applicability(tier: str, claim_type: str, claim_details: str) -> dict:
    """
    Analyze whether a claim is covered under the policy and to what extent.

    Args:
        tier: The policy tier
        claim_type: Type of claim (collision, theft, fire, vandalism, etc.)
        claim_details: Description of the incident

    Returns:
        Dictionary with coverage analysis
    """
    tier = tier.strip().capitalize()
    claim_type_lower = claim_type.lower().strip()

    if tier not in POLICY_COVERAGE:
        return {"error": f"Unknown tier: {tier}"}

    coverage = POLICY_COVERAGE[tier]
    result = {
        "tier": tier,
        "claim_type": claim_type,
        "analysis": [],
        "covered": False,
        "deductible": None,
        "coverage_limit": None,
        "warnings": [],
        "next_steps": []
    }

    # Check general exclusions first
    details_lower = claim_details.lower()
    if any(keyword in details_lower for keyword in ['uber', 'lyft', 'doordash', 'delivery']):
        result["warnings"].append("ALERT: Ridesharing/delivery use detected. This may void coverage unless specific endorsement was purchased.")

    if any(keyword in details_lower for keyword in ['racing', 'track', 'competition']):
        result["covered"] = False
        result["analysis"].append("EXCLUDED: Racing or competitive events are not covered under any tier.")
        return result

    if any(keyword in details_lower for keyword in ['intentional', 'on purpose', 'deliberately']):
        result["covered"] = False
        result["analysis"].append("EXCLUDED: Intentional acts are not covered under any tier.")
        return result

    # Analyze by claim type
    if claim_type_lower in ['collision', 'crash', 'accident', 'hit']:
        if tier == "Simple":
            result["covered"] = False
            result["analysis"].append("Collision coverage is NOT included in the Simple tier.")
            result["analysis"].append("The policyholder is responsible for all vehicle damage from collisions.")
            result["warnings"].append("Consider upgrading to Advanced tier for collision coverage.")
        else:
            result["covered"] = True
            result["deductible"] = coverage.get("collision_deductible")
            result["analysis"].append(f"Collision coverage is included with {result['deductible']} deductible.")
            if tier == "Premium":
                result["analysis"].append("Diminished Value protection is included.")
                result["analysis"].append("OEM parts will be used for all repairs.")

    elif claim_type_lower in ['theft', 'stolen', 'break-in']:
        result["covered"] = True
        result["deductible"] = coverage.get("comprehensive_deductible")
        result["analysis"].append(f"Theft is covered under comprehensive coverage.")
        result["analysis"].append(f"Deductible: {result['deductible']}")
        if tier == "Simple":
            result["analysis"].append("Note: Simple tier covers theft as a named peril.")

    elif claim_type_lower in ['fire', 'burn', 'arson']:
        result["covered"] = True
        result["deductible"] = coverage.get("comprehensive_deductible")
        result["analysis"].append("Fire damage is covered under all tiers.")
        result["analysis"].append(f"Deductible: {result['deductible']}")

    elif claim_type_lower in ['vandalism', 'keyed', 'graffiti']:
        if tier == "Simple":
            result["covered"] = False
            result["analysis"].append("Vandalism is NOT covered under the Simple tier.")
            result["analysis"].append("Simple tier only covers: Fire, Lightning, Theft, Attempted Theft.")
        else:
            result["covered"] = True
            result["deductible"] = coverage.get("comprehensive_deductible")
            result["analysis"].append(f"Vandalism is covered with {result['deductible']} deductible.")

    elif claim_type_lower in ['hail', 'flood', 'weather', 'storm']:
        if tier == "Simple":
            result["covered"] = False
            result["analysis"].append("Weather damage (hail, flood) is NOT covered under the Simple tier.")
        else:
            result["covered"] = True
            result["deductible"] = coverage.get("comprehensive_deductible")
            result["analysis"].append(f"Weather damage is covered with {result['deductible']} deductible.")

    elif claim_type_lower in ['glass', 'windshield', 'window']:
        if tier == "Simple":
            result["covered"] = False
            result["analysis"].append("Glass damage is NOT covered unless caused by a named peril (fire, theft).")
        elif tier == "Advanced":
            result["covered"] = True
            result["analysis"].append("Chip repairs are FREE. Full replacement has $100 deductible.")
            result["deductible"] = "$100 for full replacement, $0 for chip repair"
        else:  # Premium
            result["covered"] = True
            result["deductible"] = "$0"
            result["analysis"].append("Full glass coverage with $0 deductible.")

    elif claim_type_lower in ['bodily injury', 'injury', 'medical']:
        result["covered"] = True
        result["coverage_limit"] = coverage.get("bodily_injury_liability")
        result["analysis"].append(f"Bodily injury liability coverage: {result['coverage_limit']}")
        result["analysis"].append(f"Medical payments coverage: {coverage.get('medical_payments')}")

    elif claim_type_lower in ['property damage', 'property']:
        result["covered"] = True
        result["coverage_limit"] = coverage.get("property_damage_liability")
        result["analysis"].append(f"Property damage liability coverage: {result['coverage_limit']}")

    elif claim_type_lower in ['uninsured', 'hit and run']:
        result["covered"] = True
        result["coverage_limit"] = coverage.get("uninsured_motorist")
        result["analysis"].append(f"Uninsured motorist coverage: {result['coverage_limit']}")

    elif claim_type_lower in ['animal', 'deer', 'wildlife']:
        if tier == "Simple":
            result["covered"] = False
            result["analysis"].append("Animal strikes are NOT covered under the Simple tier.")
        else:
            result["covered"] = True
            result["deductible"] = coverage.get("comprehensive_deductible")
            result["analysis"].append(f"Animal strikes are covered with {result['deductible']} deductible.")

    else:
        result["analysis"].append(f"Claim type '{claim_type}' needs manual review.")
        result["warnings"].append("Unable to automatically determine coverage. Please consult policy details.")

    # Add tier-specific benefits
    if result["covered"]:
        if tier == "Premium":
            result["next_steps"].append("Contact 24/7 Concierge Claims Line for priority service.")
            if 'total' in details_lower or 'totaled' in details_lower:
                result["analysis"].append("Gap Insurance is included if vehicle is totaled.")
                result["analysis"].append("New Car Replacement available if within first 3 years.")
        elif tier == "Advanced":
            result["next_steps"].append("File claim via App or Web Portal.")
            result["next_steps"].append("Digital inspection available for faster processing.")
        else:
            result["next_steps"].append("File claim via App or Web Portal.")

    # Add rental car info if applicable
    if result["covered"] and claim_type_lower in ['collision', 'crash', 'theft', 'stolen']:
        rental = coverage.get("rental_car_reimbursement", "Not Included")
        if rental != "Not Included":
            result["analysis"].append(f"Rental car reimbursement: {rental}")

    return result


def extract_entities(text: str) -> dict:
    """
    Extract key entities from claim text (policy numbers, dates, amounts, etc.)

    Args:
        text: The text to extract entities from

    Returns:
        Dictionary with extracted entities
    """
    entities = {
        "policy_numbers": [],
        "dates": [],
        "amounts": [],
        "names": [],
        "locations": [],
        "vehicle_info": [],
        "phone_numbers": [],
        "emails": []
    }

    # Policy number patterns (e.g., POL-12345678-A, HME-12345678-X)
    policy_pattern = r'[A-Z]{2,3}-\d{8}-[A-Z]'
    entities["policy_numbers"] = re.findall(policy_pattern, text.upper())

    # Date patterns (various formats)
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY or M/D/YY
        r'\d{1,2}-\d{1,2}-\d{2,4}',  # MM-DD-YYYY
        r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{4}',  # Month DD, YYYY
        r'\d{4}-\d{2}-\d{2}'  # YYYY-MM-DD
    ]
    for pattern in date_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        entities["dates"].extend(matches)

    # Dollar amounts
    amount_pattern = r'\$[\d,]+(?:\.\d{2})?'
    entities["amounts"] = re.findall(amount_pattern, text)

    # Also look for amounts without $ sign followed by keywords
    numeric_amounts = re.findall(r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:dollars?|USD)', text, re.IGNORECASE)
    entities["amounts"].extend([f"${amt}" for amt in numeric_amounts])

    # Phone numbers
    phone_pattern = r'(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
    entities["phone_numbers"] = re.findall(phone_pattern, text)

    # Email addresses
    email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
    entities["emails"] = re.findall(email_pattern, text)

    # Vehicle info (basic patterns for make/model/year)
    year_pattern = r'(19|20)\d{2}\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)?'
    vehicle_matches = re.findall(year_pattern, text)
    if vehicle_matches:
        entities["vehicle_info"] = [text[text.find(m):text.find(m)+30].split(',')[0].strip()
                                    for m in [str(y) for y in vehicle_matches]]

    # Remove duplicates
    for key in entities:
        entities[key] = list(set(entities[key]))

    return entities


def assess_risk(claim_details: dict) -> dict:
    """
    Assess the risk level of a claim based on provided details.

    Args:
        claim_details: Dictionary containing claim information

    Returns:
        Dictionary with risk assessment
    """
    risk_score = 0
    risk_factors = []
    recommendations = []

    # Extract relevant fields with defaults
    estimated_amount = claim_details.get("estimated_amount", 0)
    claim_type = claim_details.get("claim_type", "").lower()
    injuries = claim_details.get("injuries_reported", False)
    police_report = claim_details.get("police_report", False)
    witnesses = claim_details.get("witnesses", False)
    photos = claim_details.get("photos_provided", False)
    description = claim_details.get("description", "").lower()
    days_since_incident = claim_details.get("days_since_incident", 0)

    # Amount-based risk
    if isinstance(estimated_amount, str):
        estimated_amount = float(estimated_amount.replace('$', '').replace(',', ''))

    if estimated_amount > 50000:
        risk_score += 30
        risk_factors.append("High-value claim (>$50,000)")
        recommendations.append("Requires senior adjuster review")
    elif estimated_amount > 20000:
        risk_score += 20
        risk_factors.append("Significant claim amount ($20,000-$50,000)")
    elif estimated_amount > 10000:
        risk_score += 10
        risk_factors.append("Moderate claim amount ($10,000-$20,000)")

    # Injury-related risk
    if injuries:
        risk_score += 25
        risk_factors.append("Injuries reported")
        recommendations.append("Coordinate with medical review team")
        recommendations.append("Request medical documentation")

    # Documentation status
    if not police_report and claim_type in ['theft', 'vandalism', 'collision', 'hit and run']:
        risk_score += 15
        risk_factors.append("No police report filed")
        recommendations.append("Request police report number")

    if not photos:
        risk_score += 10
        risk_factors.append("No photos provided")
        recommendations.append("Request photos of damage")

    if not witnesses and claim_type in ['collision', 'hit and run']:
        risk_score += 5
        risk_factors.append("No witnesses identified")
        recommendations.append("Request witness contact information if available")

    # Timing concerns
    if days_since_incident > 30:
        risk_score += 20
        risk_factors.append("Claim filed more than 30 days after incident")
        recommendations.append("Investigate reason for delayed reporting")
    elif days_since_incident > 7:
        risk_score += 10
        risk_factors.append("Claim filed more than 7 days after incident")

    # Suspicious patterns in description
    suspicious_keywords = ['total loss', 'totaled', 'stolen', 'break-in', 'hit and run', 'unwitnessed']
    for keyword in suspicious_keywords:
        if keyword in description:
            risk_score += 5

    # Determine risk level
    if risk_score >= 50:
        risk_level = "HIGH"
        recommendations.insert(0, "Flag for Special Investigation Unit (SIU) review")
    elif risk_score >= 30:
        risk_level = "MEDIUM"
        recommendations.insert(0, "Standard investigation with additional documentation")
    else:
        risk_level = "LOW"
        recommendations.insert(0, "Standard processing pathway")

    return {
        "risk_level": risk_level,
        "risk_score": risk_score,
        "risk_factors": risk_factors,
        "recommendations": recommendations,
        "requires_siu": risk_score >= 50
    }


def generate_investigation_checklist(claim_type: str, tier: str, claim_details: dict) -> dict:
    """
    Generate a customized investigation checklist based on claim details.

    Args:
        claim_type: Type of claim
        tier: Policy tier
        claim_details: Details about the claim

    Returns:
        Dictionary with investigation checklist
    """
    checklist = {
        "required_documents": [],
        "investigation_steps": [],
        "follow_up_questions": [],
        "timeline": {}
    }

    claim_type_lower = claim_type.lower()

    # Common required documents
    checklist["required_documents"] = [
        "Completed claim form",
        "Copy of driver's license",
        "Copy of vehicle registration",
        "Photos of damage (minimum 4 angles)"
    ]

    # Type-specific documents
    if claim_type_lower in ['collision', 'crash', 'accident']:
        checklist["required_documents"].extend([
            "Police report (if applicable)",
            "Other driver's insurance information",
            "Witness statements",
            "Repair estimate from approved shop"
        ])
        checklist["investigation_steps"] = [
            "Verify policy was active at time of incident",
            "Confirm driver was authorized under policy",
            "Review accident description for coverage determination",
            "Obtain repair estimates from network shop",
            "Verify no exclusions apply (racing, rideshare, etc.)"
        ]
        checklist["follow_up_questions"] = [
            "What was the exact date and time of the accident?",
            "What was the location (street address/intersection)?",
            "Who was driving the vehicle?",
            "Was anyone injured?",
            "Were there any witnesses?",
            "Was a police report filed? If so, what is the report number?",
            "Has the vehicle been moved from the accident scene?",
            "What is the extent of damage to your vehicle?",
            "Was the other driver at fault? Do you have their information?"
        ]

    elif claim_type_lower in ['theft', 'stolen']:
        checklist["required_documents"].extend([
            "Police report (REQUIRED)",
            "Proof of ownership",
            "List of personal items in vehicle (if applicable)",
            "Last known location documentation"
        ])
        checklist["investigation_steps"] = [
            "Verify police report filed",
            "Confirm all keys accounted for",
            "Review for any suspicious circumstances",
            "Check if vehicle had tracking device",
            "Verify no prior theft claims"
        ]
        checklist["follow_up_questions"] = [
            "When did you last see the vehicle?",
            "Where was the vehicle parked?",
            "Were all keys in your possession?",
            "Did the vehicle have an alarm or tracking system?",
            "Were there any signs of forced entry?",
            "What personal items were in the vehicle?"
        ]

    elif claim_type_lower in ['vandalism', 'keyed']:
        checklist["required_documents"].extend([
            "Police report (recommended)",
            "Photos showing extent of vandalism",
            "Witness statements if available"
        ])
        checklist["investigation_steps"] = [
            "Review photos for damage assessment",
            "Check for security camera footage",
            "Verify no disputes with neighbors/others",
            "Obtain repair estimate"
        ]
        checklist["follow_up_questions"] = [
            "When did you discover the vandalism?",
            "Where was the vehicle when vandalized?",
            "Are there security cameras in the area?",
            "Do you know of anyone who might have done this?",
            "Have you experienced vandalism before?"
        ]

    elif claim_type_lower in ['fire', 'burn']:
        checklist["required_documents"].extend([
            "Fire department report",
            "Police report",
            "Photos of fire damage"
        ])
        checklist["investigation_steps"] = [
            "Obtain fire marshal report if available",
            "Determine origin and cause of fire",
            "Verify no arson indicators",
            "Assess total loss vs. repairable"
        ]
        checklist["follow_up_questions"] = [
            "How did the fire start?",
            "Where was the vehicle when the fire occurred?",
            "Was the vehicle running or parked?",
            "When was the last maintenance performed?",
            "Was there anyone in or near the vehicle?"
        ]

    elif claim_type_lower in ['glass', 'windshield']:
        checklist["required_documents"] = [
            "Photos of glass damage",
            "Repair/replacement estimate"
        ]
        checklist["investigation_steps"] = [
            "Determine if damage is chip or full replacement",
            "Verify approved glass repair vendor",
            "Confirm coverage based on tier"
        ]
        checklist["follow_up_questions"] = [
            "How did the glass get damaged?",
            "Is this a chip or crack?",
            "What is the size of the damage?",
            "Is the damage in the driver's line of sight?"
        ]

    elif claim_type_lower in ['weather', 'hail', 'flood']:
        checklist["required_documents"].extend([
            "Weather report for date of incident",
            "Photos of weather-related damage"
        ])
        checklist["investigation_steps"] = [
            "Verify weather event occurred in area",
            "Assess extent of damage",
            "Determine repair vs. total loss"
        ]
        checklist["follow_up_questions"] = [
            "What date did the weather event occur?",
            "Where was the vehicle during the event?",
            "Was the vehicle in a covered or open area?",
            "What type of damage occurred (dents, flooding, etc.)?"
        ]

    else:
        checklist["follow_up_questions"] = [
            "What type of incident occurred?",
            "When did it happen?",
            "Where did it happen?",
            "What is the extent of the damage?",
            "Was anyone injured?"
        ]
        checklist["investigation_steps"] = [
            "Gather complete incident details",
            "Determine applicable coverage",
            "Request supporting documentation"
        ]

    # Tier-specific additions
    if tier.capitalize() == "Premium":
        checklist["investigation_steps"].insert(0, "Assign to Concierge Claims team")
        if claim_type_lower in ['collision', 'theft']:
            checklist["investigation_steps"].append("Coordinate Valet Service if requested")

    # Set timeline based on complexity
    injuries = claim_details.get("injuries_reported", False)
    if injuries:
        checklist["timeline"] = {
            "initial_contact": "Within 4 hours",
            "documentation_deadline": "5 business days",
            "investigation_complete": "15-30 business days",
            "resolution_target": "30-45 business days"
        }
    else:
        checklist["timeline"] = {
            "initial_contact": "Within 24 hours",
            "documentation_deadline": "7 business days",
            "investigation_complete": "7-14 business days",
            "resolution_target": "14-21 business days"
        }

    return checklist


def get_missing_information(claim_data: dict) -> dict:
    """
    Identify missing information needed to process a claim.

    Args:
        claim_data: Dictionary with current claim information

    Returns:
        Dictionary with missing fields and questions to ask
    """
    required_fields = {
        "policy_number": "What is your policy number?",
        "incident_date": "When did the incident occur?",
        "incident_location": "Where did the incident occur?",
        "claim_type": "What type of incident was this (collision, theft, vandalism, etc.)?",
        "description": "Can you describe what happened?",
        "estimated_damage": "Do you have an estimate of the damage amount?",
        "injuries": "Were there any injuries?"
    }

    optional_fields = {
        "police_report": "Was a police report filed? If so, what is the report number?",
        "photos": "Do you have photos of the damage?",
        "witnesses": "Were there any witnesses?",
        "other_party_info": "If another party was involved, do you have their contact/insurance information?"
    }

    missing_required = []
    missing_optional = []
    questions_to_ask = []

    for field, question in required_fields.items():
        if field not in claim_data or not claim_data[field]:
            missing_required.append(field)
            questions_to_ask.append(question)

    for field, question in optional_fields.items():
        if field not in claim_data or not claim_data[field]:
            missing_optional.append(field)

    return {
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "questions_to_ask": questions_to_ask,
        "is_complete": len(missing_required) == 0,
        "completeness_percentage": round((1 - len(missing_required) / len(required_fields)) * 100)
    }


# Tool definitions for the Anthropic API
TOOL_DEFINITIONS = [
    {
        "name": "lookup_client_by_policy",
        "description": "Look up a client in the database using their policy number. Returns client information including name, tier, address, and country.",
        "input_schema": {
            "type": "object",
            "properties": {
                "policy_number": {
                    "type": "string",
                    "description": "The policy number to search for (e.g., POL-12345678-A)"
                }
            },
            "required": ["policy_number"]
        }
    },
    {
        "name": "lookup_client_by_name",
        "description": "Look up a client in the database using their name. Can search by first name, last name, or full name.",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "The client's name to search for"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "get_coverage_details",
        "description": "Get detailed coverage information for a specific policy tier (Simple, Advanced, or Premium). Returns all coverage limits, deductibles, and included benefits.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {
                    "type": "string",
                    "description": "The policy tier (Simple, Advanced, or Premium)"
                }
            },
            "required": ["tier"]
        }
    },
    {
        "name": "analyze_coverage_applicability",
        "description": "Analyze whether a specific claim is covered under the policy based on the tier and claim type. Returns coverage determination, applicable deductibles, and next steps.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tier": {
                    "type": "string",
                    "description": "The policy tier (Simple, Advanced, or Premium)"
                },
                "claim_type": {
                    "type": "string",
                    "description": "Type of claim (e.g., collision, theft, vandalism, fire, glass, weather, bodily injury)"
                },
                "claim_details": {
                    "type": "string",
                    "description": "Description of the incident and claim"
                }
            },
            "required": ["tier", "claim_type", "claim_details"]
        }
    },
    {
        "name": "extract_entities",
        "description": "Extract key entities from text including policy numbers, dates, dollar amounts, phone numbers, and email addresses.",
        "input_schema": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to extract entities from"
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "assess_risk",
        "description": "Assess the risk level of a claim based on various factors. Returns risk score, risk factors, and recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_details": {
                    "type": "object",
                    "description": "Dictionary containing claim details including: estimated_amount, claim_type, injuries_reported, police_report, witnesses, photos_provided, description, days_since_incident"
                }
            },
            "required": ["claim_details"]
        }
    },
    {
        "name": "generate_investigation_checklist",
        "description": "Generate a customized investigation checklist based on the claim type and tier. Includes required documents, investigation steps, follow-up questions, and timeline.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_type": {
                    "type": "string",
                    "description": "Type of claim (e.g., collision, theft, vandalism)"
                },
                "tier": {
                    "type": "string",
                    "description": "The policy tier (Simple, Advanced, or Premium)"
                },
                "claim_details": {
                    "type": "object",
                    "description": "Dictionary with claim details including injuries_reported"
                }
            },
            "required": ["claim_type", "tier", "claim_details"]
        }
    },
    {
        "name": "get_missing_information",
        "description": "Identify what information is still needed to process a claim. Returns list of missing required and optional fields with questions to ask.",
        "input_schema": {
            "type": "object",
            "properties": {
                "claim_data": {
                    "type": "object",
                    "description": "Dictionary with current claim information"
                }
            },
            "required": ["claim_data"]
        }
    }
]


def execute_tool(tool_name: str, tool_input: dict) -> str:
    """
    Execute a tool by name with the given input.

    Args:
        tool_name: Name of the tool to execute
        tool_input: Input parameters for the tool

    Returns:
        JSON string with tool result
    """
    tool_functions = {
        "lookup_client_by_policy": lookup_client_by_policy,
        "lookup_client_by_name": lookup_client_by_name,
        "get_coverage_details": get_coverage_details,
        "analyze_coverage_applicability": analyze_coverage_applicability,
        "extract_entities": extract_entities,
        "assess_risk": assess_risk,
        "generate_investigation_checklist": generate_investigation_checklist,
        "get_missing_information": get_missing_information
    }

    if tool_name not in tool_functions:
        return json.dumps({"error": f"Unknown tool: {tool_name}"})

    try:
        result = tool_functions[tool_name](**tool_input)
        return json.dumps(result, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Tool execution error: {str(e)}"})
