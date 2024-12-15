import pandas as pd
import streamlit as st
import os
from glob import glob

# Function to process assignments
def process_assignments(data, locations, max_members_per_location):
    group1 = data[(data['시간'] == '1군') & (data['비고'] != '후보')].sort_values(by='전투력', ascending=False).reset_index(drop=True)
    group2 = data[(data['시간'] == '2군') & (data['비고'] != '후보')].sort_values(by='전투력', ascending=False).reset_index(drop=True)

    waiting_list_group1 = data[(data['시간'] == '1군') & (data['비고'] == '후보')][['닉네임', '전투력']].values.tolist()
    waiting_list_group2 = data[(data['시간'] == '2군') & (data['비고'] == '후보')][['닉네임', '전투력']].values.tolist()

    assignments_group1 = {location: [] for location in locations}
    combat_power_sums_group1 = {location: 0 for location in locations}

    assignments_group2 = {location: [] for location in locations}
    combat_power_sums_group2 = {location: 0 for location in locations}

    def assign_member_to_location(member, group_assignments, group_sums):
        available_locations = [loc for loc in locations if len(group_assignments[loc]) < max_members_per_location]

        if available_locations:
            min_location = min(available_locations, key=lambda loc: group_sums[loc])
            group_assignments[min_location].append((member['닉네임'], member['전투력']))
            group_sums[min_location] += member['전투력']
        else:
            return False
        return True

    for _, member in group1.iterrows():
        if not assign_member_to_location(member, assignments_group1, combat_power_sums_group1):
            waiting_list_group1.append((member['닉네임'], member['전투력']))

    for _, member in group2.iterrows():
        if not assign_member_to_location(member, assignments_group2, combat_power_sums_group2):
            waiting_list_group2.append((member['닉네임'], member['전투력']))

    return assignments_group1, waiting_list_group1, assignments_group2, waiting_list_group2

# Function to save Excel file
def save_excel(data, file_name):
    output_path = f"saved_files/{file_name}"
    os.makedirs("saved_files", exist_ok=True)
    data.to_excel(output_path, index=False)
    return output_path

# Streamlit App
def main():
    st.title("Group Assignment Tool")

    if 'current_data' not in st.session_state or st.session_state.get("reset_state", False):
        st.session_state['current_data'] = []
        st.session_state['reset_state'] = False

    if 'files' not in st.session_state:
        st.session_state['files'] = []

    # Default locations
    default_locations = ['무기시험장(적군쪽)', '환승역', '무기시험장(아군쪽)', 
                         '무기정비소1', '무기정비소2', '무기정비소3', '무기정비소4', '증기보일러',
                         '노란색방향','보라색방향', '파란색방향']
    location_priority = st.multiselect("인원 할당 지역 선택(무공/협곡):", default_locations, default_locations)

    # Parameter for maximum members per location
    max_members_per_location = st.number_input("각 지역별 최대 인원:", min_value=1, max_value=20, value=3, step=1)

    # Select mode: Add members or upload CSV
    mode = st.radio("Select Input Mode:", ["Add Members", "Upload CSV"])

    data = None

    show_combat_power = st.checkbox("할당 후 전투력 같이 표기")

    if mode == "Add Members":
        # Add individual member inputs
        st.header("Add Members")
        with st.form("member_form"):
            name = st.text_input("Name (닉네임):")
            power = st.number_input("Combat Power (전투력):", min_value=0, step=1)
            group = st.selectbox("Group (1군/2군):", ["1군", "2군"])
            remark = st.text_input("Remark (비고):", value="")
            submitted = st.form_submit_button("Add Member")

            if submitted:
                st.session_state['current_data'].append({
                    '닉네임': name,
                    '전투력': power,
                    '시간': group,
                    '비고': remark
                })
                st.success(f"Added member: {name}")

        # Show current data
        st.header("Current Members")
        if st.session_state['current_data']:
            current_df = pd.DataFrame(st.session_state['current_data'])
            st.write(current_df)

            # Save to Excel
            file_name = st.text_input("Enter file name to save (e.g., members.xlsx):")
            if st.button("Save to Excel"):
                if file_name:
                    save_path = save_excel(current_df, file_name)
                    st.session_state['files'].append(file_name)
                    st.success(f"File saved as '{save_path}'")
                else:
                    st.warning("Please enter a valid file name.")

            data = current_df

    elif mode == "Upload CSV":
        # Upload file for additional processing
        st.header("Upload an Excel File")
        saved_files = glob("saved_files/*.xlsx")
        selected_file = st.selectbox("Select a saved file to load:", saved_files)

        if st.button("Load Selected File") and selected_file:
            data = pd.read_excel(selected_file)
            st.success(f"Loaded file: {selected_file}")
            st.write(data)

        # Option to upload a local file to saved_files
        st.header("Upload Local File to Saved Files")
        local_file = st.file_uploader("Choose a local Excel file to upload:", type=["xlsx"])
        if local_file is not None:
            with open(f"saved_files/{local_file.name}", "wb") as f:
                f.write(local_file.getbuffer())
            st.success(f"File '{local_file.name}' has been uploaded to 'saved_files'.")

    # Process assignments if data is available
    if data is not None:
        st.markdown("---")

        # Process assignments
        assignments_group1, waiting_list_group1, assignments_group2, waiting_list_group2 = process_assignments(data, location_priority, max_members_per_location)

        # Display results
        st.header("1군 Assignments")
        for location in location_priority:
            st.subheader(location)
            if show_combat_power:
                members = [f"{member[0]} (전투력: {member[1]})" for member in assignments_group1[location]]
            else:
                members = [member[0] for member in assignments_group1[location]]
            st.write(", ".join(members) if members else "No members assigned.")

        st.markdown("---"*10)
        st.subheader("1군 Waiting List")
        if show_combat_power:
            st.write(", ".join([f"{member[0]} (전투력: {member[1]})" for member in waiting_list_group1]))
        else:
            st.write(", ".join([member[0] for member in waiting_list_group1]))

        st.markdown("---"*10)

        st.header("2군 Assignments")
        for location in location_priority:
            st.subheader(location)
            if show_combat_power:
                members = [f"{member[0]} (전투력: {member[1]})" for member in assignments_group2[location]]
            else:
                members = [member[0] for member in assignments_group2[location]]
            st.write(", ".join(members) if members else "No members assigned.")

        st.subheader("2군 Waiting List")
        if show_combat_power:
            st.write(", ".join([f"{member[0]} (전투력: {member[1]})" for member in waiting_list_group2]))
        else:
            st.write(", ".join([member[0] for member in waiting_list_group2]))

if __name__ == "__main__":
    main()
