import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="JMIS Data Cleaner", layout="wide")
st.title("🧹 JMIS Training Data Cleaner")

# Dropdown valid options
valid_genders = ["Male", "Female", "Intersex"]
valid_ta_modes = ["In person", "Virtual", "Mixed"]
valid_segments = ["Micro", "SME"]
valid_ta_types = ["Post-lending", "Pre-lending", "Non-lending", "Mentorship", "Voucher scheme"]
valid_yes_no = ["Yes", "No"]
valid_sectors = ["Agriculture", "Artists/artisans", "Manufacturing", "Trading & Retail", "Other"]
valid_counties = [
    "Baringo", "Bomet", "Bungoma", "Busia", "Elgeyo-Marakwet", "Embu", "Garissa", "Homa Bay", "Isiolo",
    "Kajiado", "Kakamega", "Kericho", "Kiambu", "Kilifi", "Kirinyaga", "Kisii", "Kisumu", "Kitui",
    "Kwale", "Laikipia", "Lamu", "Machakos", "Makueni", "Mandera", "Marsabit", "Meru", "Migori",
    "Mombasa", "Murang'a", "Nairobi", "Nakuru", "Nandi", "Narok", "Nyamira", "Nyandarua", "Nyeri",
    "Samburu", "Siaya", "Taita-Taveta", "Tana River", "Tharaka-Nithi", "Trans Nzoia", "Turkana",
    "Uasin Gishu", "Vihiga", "Wajir", "West Pokot"
]

sample_record_map = {
    "purchase record": "Purchase record",
    "record of sales": "Record of sales",
    "delivery records": "Delivery records",
    "record of expenses": "Record of expenses",
    "receipts": "Receipts",
    "other": "Other"
}

def normalize_sample_records(val):
    if pd.isna(val):
        return ""
    tokens = [x.strip().lower() for x in str(val).split(",")]
    matched = [sample_record_map[tok] for tok in tokens if tok in sample_record_map]
    return ", ".join(matched)

def normalize_list(val, allowed_values):
    if pd.isna(val):
        return ""
    return ", ".join([x.strip().title() for x in str(val).split(",") if x.strip().title() in allowed_values])

uploaded_file = st.file_uploader("Upload Raw Training Data File (Excel)", type=["xlsx", "xls", "csv"])

if uploaded_file:
    try:
        raw_df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith(".csv") else pd.read_excel(uploaded_file)
        st.subheader("Preview of Uploaded Raw Data")
        st.dataframe(raw_df.head(10))

        rename_map = {
            "First Name": "First Name",
            "Last Name": "Last Name",
            "WHAT IS YOUR NATIONAL ID?": "Unique JGP ID (National ID)*",
            "Business Phone Number": "Business phone number",
            "Gender": "Gender of owner* (Male/Female/Intersex)",
            "WHAT IS THE MAIN INDUSTRY SECTOR IN WHICH YOU OPERATE IN?": "Industry sector(Agriculture, Artists/artisans, Manufacturing, Trading & Retail, Other)",
            "Age": "Age of owner (full years)*",
            "TYPE OF TA ACCESSED": "Type of TA*",
            "Timestamp": "Training date(yyyy-MM-dd)*",
            "WHAT WAS YOUR ESTIMATED MONTHLY REVENUE (KES) IN A PARTICULARLY GOOD MONTH": "Monthly revenues in best month (KES)",
            "WHAT WAS YOUR ESTIMATED MONTHLY REVENUE (KES) IN A PARTICULARLY BAD MONTH?": "Monthly revenues in worst month (KES)"
        }

        df = raw_df.rename(columns=rename_map)

        df["Participant Name*"] = (
            df["First Name"].fillna("").astype(str).str.title() + " " +
            df["Last Name"].fillna("").astype(str).str.title()
        ).str.replace(r"\s+", " ", regex=True).str.strip()

        df["Business phone number"] = df["Business phone number"].astype(str).str.replace("[^0-9]", "", regex=True)
        df["Business phone number"] = df["Business phone number"].apply(lambda x: "254" + x[-9:] if len(x) >= 9 else x)

        df["Training date(yyyy-MM-dd)*"] = df["Training date(yyyy-MM-dd)*"].apply(lambda val: pd.to_datetime(val, errors='coerce').strftime("%Y-%m-%d") if not pd.isna(val) else "")
        df["Gender of owner* (Male/Female/Intersex)"] = df["Gender of owner* (Male/Female/Intersex)"].str.strip().str.title()
        df["Industry sector(Agriculture, Artists/artisans, Manufacturing, Trading & Retail, Other)"] = df["Industry sector(Agriculture, Artists/artisans, Manufacturing, Trading & Retail, Other)"].str.strip().str.title()
        df["Type of TA*"] = df["Type of TA*"].str.strip().str.title()

        if "Business Location (County)*" not in df.columns:
            county_input = st.text_input("📍 'Business Location (County)*' column missing. Enter county name to apply to all:")
            df["Business Location (County)*"] = county_input.strip().title()
        else:
            df["Business Location (County)*"] = df["Business Location (County)*"].str.strip().str.title()

        df["Training Partner*"] = "KNCCI"
        df["Business segment*(Micro/SME)"] = "Micro"
        df["TA delivery mode*(In person/Virtual/Mixed)"] = "In person"
        df["Passport"] = ""
        df["Business Registration Number"] = ""
        df["Total number of regular employees including owner*"] = df.get("WHAT IS THE NUMBER OF YOUR REGULAR EMPLOYEES INCLUDING BUSINESS OWNER?", "")
        df["Regular, of which are youth (18-35)*"] = df.get("OF THESE, HOW MANY ARE YOUTH? (18 -35 YEARS OLD)", "")
        df["Total number of casual employees excluding owner*"] = df.get("WHAT IS THE NUMBER OF CASUAL EMPLOYEES", "")
        df["Casual, of which are youth (18-35)*"] = df.get("OF THESE, HOW MANY ARE YOUTH? (18 -35 YEARS OLD)", "")
        df["Sample records kept*(Purchase record/Record of sales/Delivery records/Record of expenses/Receipts/Other)"] = df.get(
            "DO YOU KEEP ANY OF THE FOLLOWING RECORDS IN YOUR BUSINESS OPERATIONS? [ PLEASE SELECT ALL THAT APPLY]", ""
        ).apply(normalize_sample_records)
        df["TA needs*(Financial Literacy/Record Keeping/Digitization/Market Access/Other)"] = df.get(
            "WHAT ARE THE MOST PRESSING TECHNICAL ASSISTANCE NEEDS TO IMPROVE YOUR BUSINESS OPERATIONS? [PLEASE SELECT UP TO TWO]", ""
        ).apply(lambda x: normalize_list(x, ["Financial Literacy", "Record Keeping", "Digitization", "Market Access", "Other"]))
        df["Other TA Needs"] = ""
        df["Person with Disability*(Yes/No)"] = df.get("DO YOU IDENTIFY AS A PERSON WITH A DISABILITY? (THIS QUESTION IS OPTIONAL AND YOUR RESPONSE WILL NOT AFFECT YOUR ELIGIBILITY FOR THE PROGRAM.)", "").str.strip().str.title()
        df["Refugee status*(Yes/No)"] = "No"
        df["Is applicant eligible?(Yes/No)"] = "Yes"
        df["Recommended for finance (Yes/No)"] = ""
        df["Pipeline Decision Date (yyyy-MM-dd)"] = ""
        df["FI business is referred to*"] = "KNCCI"

        final_columns = [
            "Participant Name*", "Unique JGP ID (National ID)*", "Training Partner*", "Business phone number",
            "Gender of owner* (Male/Female/Intersex)", "Age of owner (full years)*", "Passport",
            "Business Location (County)*", "Industry sector(Agriculture, Artists/artisans, Manufacturing, Trading & Retail, Other)",
            "Business segment*(Micro/SME)", "TA delivery mode*(In person/Virtual/Mixed)", "Business Registration Number",
            "Monthly revenues in best month (KES)", "Monthly revenues in worst month (KES)",
            "Total number of regular employees including owner*", "Regular, of which are youth (18-35)*",
            "Total number of casual employees excluding owner*", "Casual, of which are youth (18-35)*",
            "Sample records kept*(Purchase record/Record of sales/Delivery records/Record of expenses/Receipts/Other)",
            "TA needs*(Financial Literacy/Record Keeping/Digitization/Market Access/Other)", "Other TA Needs", "Type of TA*",
            "Person with Disability*(Yes/No)", "Refugee status*(Yes/No)", "Is applicant eligible?(Yes/No)",
            "Recommended for finance (Yes/No)", "Pipeline Decision Date (yyyy-MM-dd)", "FI business is referred to*",
            "Training date(yyyy-MM-dd)*"
        ]

        for col in final_columns:
            if col not in df.columns:
                df[col] = ""

        cleaned_df = df[final_columns]

        st.subheader("Cleaned & Formatted Data for JMIS Upload")
        st.dataframe(cleaned_df.head(10))

        st.download_button(
            label="⬇️ Download JMIS Ready Excel",
            data=cleaned_df.to_excel(index=False, engine='openpyxl'),
            file_name="JMIS_CLEANED_UPLOAD.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"❌ Error processing file: {e}")
else:
    st.info("Please upload a raw training data file to begin.")
