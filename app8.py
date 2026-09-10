import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO
import os

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="Inventory Analytics Dashboard",
    page_icon="📦",
    layout="wide"
)

# =====================================================
# CONFIG
# =====================================================

LATEST_FILE = "latest_inventory.xlsx"

USERS = {
    "admin": {
        "password": "admin123",
        "role": "admin"
    },
    "spadmin": {
        "password": "spadmin123",
        "role": "spadmin"
    }
}

# =====================================================
# SESSION STATE
# =====================================================

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if "username" not in st.session_state:
    st.session_state.username = ""

if "role" not in st.session_state:
    st.session_state.role = ""

# =====================================================
# LOGIN PAGE
# =====================================================


def login_page():

    left_col, right_col = st.columns([3, 1])

    # Left Side Image
    with left_col:

        st.image(
            "login_image.jpg",
            use_container_width=True
        )

    # Right Side Login Form
    with right_col:

        st.title("📦 MMS")
        st.caption("Material Management System")

        st.divider()

        username = st.text_input(
            "Username"
        )

        password = st.text_input(
            "Password",
            type="password"
        )

        if st.button(
            "Login",
            use_container_width=True
        ):

            if (
                username in USERS
                and USERS[username]["password"] == password
            ):

                st.session_state.logged_in = True
                st.session_state.username = username
                st.session_state.role = USERS[username]["role"]

                st.rerun()

            else:

                st.error(
                    "Invalid Username or Password"
                )


# =====================================================
# AUTH CHECK
# =====================================================

if not st.session_state.logged_in:
    login_page()
    st.stop()

# =====================================================
# HEADER
# =====================================================

header_left, header_right = st.columns([8, 2])

with header_left:
    st.title("📦 Material Management System")
    st.caption("Weekly Inventory Monitoring & Analysis")


# =====================================================
# FILE UPLOAD
# =====================================================

if st.session_state.role == "spadmin":

    uploaded_file = st.file_uploader(
        "Upload Weekly Inventory File",
        type=["xlsx"]
    )

    if uploaded_file is not None:

        with open(LATEST_FILE, "wb") as f:
            f.write(uploaded_file.getbuffer())

        st.success(
            "Inventory file uploaded successfully."
        )

else:

    st.info(
        "Upload permission available only for SP Admin."
    )

# =====================================================
# CHECK FILE
# =====================================================

if not os.path.exists(LATEST_FILE):

    st.warning(
        "No inventory file uploaded yet."
    )
    st.stop()

# =====================================================
# LOAD DATA
# =====================================================


@st.cache_data
def load_data():

    df = pd.read_excel(LATEST_FILE)

    df.columns = df.columns.str.strip()

    if "Column1" in df.columns:
        df.rename(
            columns={"Column1": "Aging"},
            inplace=True
        )

    if "Column2" in df.columns:
        df.rename(
            columns={"Column2": "Status"},
            inplace=True
        )

    filter_cols = [
        "Region",
        "Sloc Des",
        "SUB",
        "Aging",
        "Status",
        "AssetID",
        "Serial No",
        "Mat Des"
    ]

    for col in filter_cols:

        if col in df.columns:

            df[col] = (
                df[col]
                .fillna("")
                .astype(str)
                .str.strip()
            )

    return df


df = load_data()

# =====================================================
# FILTERS
# =====================================================

# =====================================================
# SIDEBAR
# =====================================================

# =====================================================
# SIDEBAR USER PANEL
# =====================================================

st.sidebar.markdown(
    f"**👤 Logged as: {st.session_state.username}**"
)

if st.sidebar.button(
    "🚪 Logout",
    use_container_width=True
):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.role = ""
    st.rerun()

st.sidebar.divider()

st.sidebar.header("Filters")


regions = sorted(
    [x for x in df["Region"].unique() if x]
)

selected_regions = st.sidebar.multiselect(
    "Region",
    regions,
    default=regions
)

region_df = df[
    df["Region"].isin(selected_regions)
]

slocs = sorted(
    [x for x in region_df["Sloc Des"].unique() if x]
)

selected_slocs = st.sidebar.multiselect(
    "Location (SLOC)",
    slocs,
    default=slocs
)

sloc_df = region_df[
    region_df["Sloc Des"].isin(selected_slocs)
]

categories = sorted(
    [x for x in sloc_df["SUB"].unique() if x]
)

selected_categories = st.sidebar.multiselect(
    "Asset Category",
    categories,
    default=categories
)

category_df = sloc_df[
    sloc_df["SUB"].isin(selected_categories)
]

aging_values = sorted(
    [x for x in category_df["Aging"].unique() if x]
)

selected_aging = st.sidebar.multiselect(
    "Aging",
    aging_values,
    default=aging_values
)

filtered_df = category_df[
    category_df["Aging"].isin(selected_aging)
]

# =====================================================
# KPI
# =====================================================

total_assets = len(filtered_df)

# Pending Updates = inventory records where Status is blank
pending_updates = filtered_df["Status"].fillna(
    "").astype(str).str.strip().eq("").sum()

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Total Assets",
    total_assets
)

k2.metric(
    "Regions",
    filtered_df["Region"].nunique()
)

k3.metric(
    "Categories",
    filtered_df["SUB"].nunique()
)

k4.metric(
    "Pending Updates",
    pending_updates
)

st.divider()

# =====================================================
# CHARTS
# =====================================================

c1, c2 = st.columns(2)

with c1:

    region_chart = (
        filtered_df.groupby("Region")
        .size()
        .reset_index(name="Assets")
    )

    fig_region = px.bar(
        region_chart,
        x="Region",
        y="Assets",
        color="Assets",
        title="Assets by Region"
    )

    st.plotly_chart(
        fig_region,
        use_container_width=True
    )

with c2:

    cat_chart = (
        filtered_df.groupby("SUB")
        .size()
        .reset_index(name="Assets")
    )

    fig_cat = px.pie(
        cat_chart,
        names="SUB",
        values="Assets",
        title="Assets by Category"
    )

    st.plotly_chart(
        fig_cat,
        use_container_width=True
    )

# =====================================================
# TOP 20 LOCATIONS
# =====================================================

st.subheader("Top 20 Locations")

location_summary = (
    filtered_df.groupby("Sloc Des")
    .size()
    .reset_index(name="Assets")
    .sort_values(
        by="Assets",
        ascending=False
    )
    .head(20)
)

chart_data = location_summary.sort_values(
    by="Assets",
    ascending=True
)

fig_location = px.bar(
    chart_data,
    x="Assets",
    y="Sloc Des",
    orientation="h",
    text="Assets",
    title="Top 20 Locations by Asset Count"
)

fig_location.update_traces(
    textposition="outside"
)

fig_location.update_layout(
    height=700,
    showlegend=False,
    xaxis_title="Asset Count",
    yaxis_title="Location"
)

st.plotly_chart(
    fig_location,
    use_container_width=True
)

# =====================================================
# SEARCH
# =====================================================

st.subheader("🔍 Asset Search")

search_text = st.text_input(
    "Search Asset ID / Serial Number / Description"
)

display_df = filtered_df.copy()


# =====================================================
# HIDE COLUMNS FROM INVENTORY RECORDS DISPLAY
# =====================================================

hidden_columns = [
    "AssetID",
    "Team Type",
    "Day of Change on Date",
    "Day of GRN on Date",
    "Plant"

]

display_df = display_df.drop(
    columns=[
        col for col in hidden_columns
        if col in display_df.columns
    ],
    errors="ignore"
)

# ==============================================

if search_text:

    display_df = filtered_df[
        filtered_df["AssetID"].str.contains(
            search_text,
            case=False,
            na=False
        )
        |
        filtered_df["Serial No"].str.contains(
            search_text,
            case=False,
            na=False
        )
        |
        filtered_df["Mat Des"].str.contains(
            search_text,
            case=False,
            na=False
        )
    ]

# =====================================================
# DATA TABLE
# =====================================================

# =====================================================
# INVENTORY RECORDS
# =====================================================

st.subheader("Inventory Records")

# Predefined Status List
status_options = [
    "",
    "Installed",
    "Ready to return",
    "Return issue",
    "Maintenance"
]

# Ensure Status column exists
if "Status" not in display_df.columns:
    display_df["Status"] = "Pending Update"

# Editable Grid
edited_df = st.data_editor(
    display_df,
    use_container_width=True,
    height=600,
    column_config={
        "Status": st.column_config.SelectboxColumn(
            "Status",
            help="Select asset status",
            options=status_options,
            required=True,
        )
    },
    disabled=[
        col for col in display_df.columns
        if col != "Status"
    ],
    key="inventory_editor"
)

# Save Button
if st.button(
    "💾 Save ",
    use_container_width=True
):
    try:
        edited_df.to_excel(
            LATEST_FILE,
            index=False
        )
        st.success(
            "Status changes saved successfully."
        )
        st.cache_data.clear()
        st.rerun()

    except Exception as e:
        st.error(
            f"Error saving changes: {e}"
        )

# =====================================================
# DOWNLOAD CSV
# =====================================================

csv = display_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    "⬇ Download CSV",
    csv,
    "inventory_filtered.csv",
    "text/csv"
)

# =====================================================
# DOWNLOAD EXCEL
# =====================================================


def create_excel(data):

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        data.to_excel(
            writer,
            sheet_name="Inventory",
            index=False
        )

    output.seek(0)

    return output


st.download_button(
    "⬇ Download Excel",
    create_excel(display_df),
    "inventory_filtered.xlsx",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
