import streamlit as st
import pandas as pd

# Load the dataset
@st.cache_data
def load_data():
    return pd.read_excel("data.xlsx")  # Ensure 'data.xlsx' is in the same folder

df = load_data()

# Extract case-sensitive ID variations
id_variations = {}
for id in df["ID"].astype(str):
    lower_id = id.lower()
    if lower_id in id_variations:
        id_variations[lower_id].add(id)
    else:
        id_variations[lower_id] = {id}

# Identify IDs that are **specifically lowercase** in the database
lowercase_specific_ids = {id for id in df["ID"].astype(str) if id.islower()}

# Keep only IDs that have uppercase versions but **no lowercase versions**
filtered_case_correction_map = {
    key: next(iter(value)) for key, value in id_variations.items()
    if key not in lowercase_specific_ids and len(value) == 1  # Auto-correct only when there's one correct version
}

# Title of the app
st.title("🚀 Troubleshooting Guide")

# Allow users to enter multiple IDs separately (30 smaller boxes in correct tab order)
st.subheader("Enter up to 30 IDs:")
id_inputs = []
invalid_ids = set()
corrected_ids = {}

# Store each ID's corrected version to ensure all corrections apply correctly
updated_inputs = {}

# Create **5 rows** of 6 columns for proper tabbing behavior
for row in range(5):  # 5 rows
    cols = st.columns(6)  # 6 columns per row
    for col in range(6):  # Iterate within each row
        index = row * 6 + col  # Calculate correct tab order
        id_input = cols[col].text_input(f"ID {index+1}", "").strip()

        # Auto-correct ID capitalization **only if it's not a lowercase-specific ID**
        if id_input.lower() in filtered_case_correction_map:
            corrected_id = filtered_case_correction_map[id_input.lower()]
            updated_inputs[id_input] = corrected_id  # Store corrected value
            id_inputs.append(corrected_id)  # Store the corrected version
            corrected_ids[id_input] = corrected_id  # Store correction info
        else:
            id_inputs.append(id_input)  # Store as is

# Remove empty entries & keep only valid inputs
ids_to_search = [id for id in id_inputs if id]

if ids_to_search:
    # Separate found & not found IDs (CASE SENSITIVE!)
    found_ids = df["ID"].tolist()  # Keep exact casing
    missing_ids = [id for id in ids_to_search if id not in found_ids]
    valid_ids = [id for id in ids_to_search if id in found_ids]

    # Store invalid IDs to keep red highlight
    invalid_ids.update(missing_ids)

    # Capture case-sensitive variations & show in brackets
    matched_ids = []
    for id in valid_ids:
        lower_id = id.lower()
        if lower_id in id_variations and id not in id_variations[lower_id]:
            matched_case = next(iter(id_variations[lower_id]))  # Get one case variation
            matched_ids.append(f"{id} ({matched_case})")  # Show both formats
        else:
            matched_ids.append(id)

    # Highlight IDs not found in database
    if missing_ids:
        st.warning(f"⚠️ The following IDs were **not found in the database**: {', '.join(missing_ids)}")

    # Show corrected IDs message
    if corrected_ids:
        correction_list = [f"{old} → {new}" for old, new in corrected_ids.items()]
        st.success(f"✅ Auto-corrected IDs: {', '.join(correction_list)}")

    # Warning for case-sensitive duplicates
    case_sensitive_found = [id for id in valid_ids if id.lower() in id_variations and len(id_variations[id.lower()]) > 1]
    if case_sensitive_found:
        duplicate_warnings = [f"{id} (Matches: {', '.join(id_variations[id.lower()])})" for id in case_sensitive_found]
        st.warning(f"⚠️ Case-Sensitive IDs detected: {', '.join(duplicate_warnings)}")

    if valid_ids:
        # Filter the dataframe for matching valid IDs
        filtered_df = df[df["ID"].isin(valid_ids)].reset_index(drop=True)

        st.subheader("🔍 Search Results")
        st.dataframe(filtered_df.style.set_properties(**{
            'text-align': 'left',
            'white-space': 'normal'
        }), height=400, width=1400)  # Shorter height & Wider width

        # Extract only "Suspect 1" to "Suspect 7-10" columns for frequency count
        suspect_columns = ["Suspect 1", "Suspect 2", "Suspect 3", "Suspect 4", "Suspect 5", "Suspect 6", "Suspect 7-10"]
        suspect_data = filtered_df[suspect_columns].values.flatten()  # Flatten the suspect columns

        # Remove NaN values
        suspects = [s for s in suspect_data if pd.notna(s)]

        # Count occurrences of each suspect
        suspect_count = pd.Series(suspects).value_counts()

        st.subheader("📊 Suspect Frequency Count")

        # **Dynamically adjust height based on row count**
        suspect_table_height = min(50 + (len(suspect_count) * 35), 400)  # Auto adjust, max 400px
        st.dataframe(suspect_count.to_frame("Count"), height=suspect_table_height)

    else:
        st.warning("⚠️ No valid ID(s) found in the database. Please check your input.")

# Apply CSS to **permanently** highlight invalid ID fields in red
if invalid_ids:
    css_style = "".join([
        f"input[value='{id}'] {{ border: 2px solid red !important; background-color: #ffcccc !important; }}\n"
        for id in invalid_ids
    ])
    st.markdown(f"<style>{css_style}</style>", unsafe_allow_html=True)

# Footer
st.markdown("Developed with ❤️ using Streamlit")
