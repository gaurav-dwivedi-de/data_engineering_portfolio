# ============================================================
# Weather Intelligence Platform
# Dashboard Styles
# ============================================================


PAGE_STYLE = {
    "backgroundColor": "#06111f",
    "minHeight": "100vh",
    "color": "#e8f1ff",
    "fontFamily": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
}


SIDEBAR_STYLE = {
    "width": "240px",
    "minHeight": "100vh",
    "position": "fixed",
    "left": "0",
    "top": "0",
    "bottom": "0",
    "backgroundColor": "#04101d",
    "borderRight": "1px solid rgba(120, 180, 255, 0.12)",
    "padding": "24px 16px",
    "zIndex": "1000",
}


MAIN_STYLE = {
    "marginLeft": "240px",
    "minHeight": "100vh",
    "backgroundColor": "#06111f",
}


CONTENT_STYLE = {
    "padding": "28px",
    "backgroundColor": "#06111f",
    "minHeight": "100vh",
}


HEADER_STYLE = {
    "padding": "0 0 20px 0",
}


HEADER_TITLE_STYLE = {
    "fontSize": "26px",
    "fontWeight": "800",
    "color": "#ffffff",
    "margin": "0",
}


HEADER_SUBTITLE_STYLE = {
    "fontSize": "13px",
    "color": "#8ea7c4",
    "marginTop": "5px",
}


NAV_SECTION_STYLE = {
    "fontSize": "9px",
    "fontWeight": "700",
    "letterSpacing": "1px",
    "color": "#59728d",
    "marginTop": "18px",
    "marginBottom": "8px",
    "paddingLeft": "8px",
}


NAV_ITEM_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "12px",
    "padding": "11px 14px",
    "marginBottom": "6px",
    "borderRadius": "10px",
    "color": "#a9c0dc",
    "textDecoration": "none",
    "fontSize": "14px",
}


ACTIVE_NAV_STYLE = {
    **NAV_ITEM_STYLE,
    "background": (
        "linear-gradient("
        "90deg, "
        "rgba(35, 117, 235, 0.35), "
        "rgba(35, 117, 235, 0.12)"
        ")"
    ),
    "color": "#ffffff",
}


CARD_STYLE = {
    "backgroundColor": "#0b1b2d",
    "border": "1px solid rgba(120, 180, 255, 0.14)",
    "borderRadius": "16px",
    "boxShadow": "0 10px 30px rgba(0,0,0,0.20)",
}


KPI_CARD_STYLE = {
    **CARD_STYLE,
    "minHeight": "145px",
    "padding": "20px",
}


MODEL_CARD_STYLE = {
    **CARD_STYLE,
    "minHeight": "105px",
    "padding": "18px",
}


KPI_ROW_STYLE = {
    "display": "flex",
    "gap": "14px",
    "width": "100%",
}


KPI_COLUMN_STYLE = {
    "flex": "1",
    "minWidth": "0",
}


MODEL_ROW_STYLE = {
    "display": "flex",
    "gap": "14px",
    "width": "100%",
}


MODEL_COLUMN_STYLE = {
    "flex": "1",
    "minWidth": "0",
}


SECTION_STYLE = {
    "marginTop": "22px",
}


SECTION_TITLE_STYLE = {
    "fontSize": "20px",
    "fontWeight": "700",
    "color": "#f3f7ff",
    "marginBottom": "4px",
}


SECTION_SUBTITLE_STYLE = {
    "fontSize": "13px",
    "color": "#8ea7c4",
    "marginBottom": "18px",
}


HERO_STYLE = {
    **CARD_STYLE,
    "padding": "34px",
    "minHeight": "250px",
    "background": (
        "radial-gradient("
        "circle at 85% 20%, "
        "rgba(91,112,255,0.40), "
        "transparent 30%), "
        "radial-gradient("
        "circle at 60% 90%, "
        "rgba(0,191,255,0.22), "
        "transparent 35%), "
        "linear-gradient("
        "135deg, "
        "#0b2340 0%, "
        "#102b50 45%, "
        "#171d46 100%)"
    ),
    "overflow": "hidden",
}


HERO_TITLE_STYLE = {
    "fontSize": "42px",
    "fontWeight": "800",
    "lineHeight": "1.1",
    "color": "#ffffff",
}


HERO_ACCENT_STYLE = {
    "color": "#46c8ff",
}


HERO_TEXT_STYLE = {
    "fontSize": "17px",
    "color": "#dceaff",
    "marginTop": "8px",
}


HERO_SMALL_TEXT_STYLE = {
    "fontSize": "12px",
    "color": "#8ea7c4",
    "marginTop": "6px",
}


BADGE_STYLE = {
    "display": "inline-block",
    "padding": "7px 12px",
    "marginRight": "8px",
    "marginTop": "16px",
    "borderRadius": "20px",
    "backgroundColor": "rgba(61,174,255,0.12)",
    "border": "1px solid rgba(61,174,255,0.25)",
    "color": "#9bdcff",
    "fontSize": "12px",
}


ICON_BOX_STYLE = {
    "width": "38px",
    "height": "38px",
    "borderRadius": "10px",
    "backgroundColor": "rgba(70,200,255,0.08)",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "center",
    "flexShrink": "0",
}


KPI_LABEL_STYLE = {
    "fontSize": "12px",
    "fontWeight": "600",
    "color": "#8ea7c4",
}


KPI_VALUE_STYLE = {
    "fontSize": "30px",
    "fontWeight": "700",
    "color": "#ffffff",
    "marginTop": "3px",
}


KPI_DESCRIPTION_STYLE = {
    "fontSize": "11px",
    "color": "#617892",
}


MODEL_LABEL_STYLE = {
    "fontSize": "10px",
    "fontWeight": "700",
    "color": "#8ea7c4",
    "letterSpacing": "0.4px",
}


MODEL_VALUE_STYLE = {
    "fontSize": "22px",
    "fontWeight": "750",
    "color": "#ffffff",
    "marginTop": "8px",
}


MODEL_NAME_STYLE = {
    "fontSize": "10px",
    "color": "#617892",
    "marginTop": "10px",
}


LABEL_STYLE = {
    "fontSize": "11px",
    "fontWeight": "600",
    "color": "#8ea7c4",
    "display": "block",
    "marginBottom": "6px",
}


DROPDOWN_STYLE = {
    "backgroundColor": "#0a1929",
    "color": "#ffffff",
    "border": "1px solid rgba(120, 180, 255, 0.20)",
    "borderRadius": "8px",
}


DATE_STYLE = {
    "backgroundColor": "#0a1929",
    "color": "#ffffff",
    "border": "1px solid rgba(120, 180, 255, 0.20)",
    "borderRadius": "8px",
}


TABLE_STYLE = {
    "overflowX": "auto",
    "backgroundColor": "#0b1b2d",
}


TABLE_CELL_STYLE = {
    "backgroundColor": "#0b1b2d",
    "color": "#e8f1ff",
    "border": "1px solid rgba(120,180,255,0.10)",
    "fontSize": "11px",
    "padding": "8px",
}


TABLE_HEADER_STYLE = {
    "backgroundColor": "#10263d",
    "color": "#dceaff",
    "fontWeight": "700",
    "border": "1px solid rgba(120,180,255,0.12)",
    "fontSize": "11px",
}


GRAPH_STYLE = {
    "backgroundColor": "#0b1b2d",
    "borderRadius": "16px",
    "padding": "4px",
    "marginBottom": "14px",
}


FOOTER_STYLE = {
    "padding": "25px 0 5px",
    "color": "#617892",
    "fontSize": "12px",
}


SIDEBAR_FOOTER_STYLE = {
    "position": "absolute",
    "bottom": "24px",
    "left": "16px",
    "right": "16px",
    "padding": "12px",
    "borderTop": "1px solid rgba(120,180,255,0.10)",
}


# ============================================================
# Dropdown + Date Picker CSS
# Dash 4.4.1
# ============================================================

DROPDOWN_CSS = """
<style>

/* ============================================================
   General dropdown container
   ============================================================ */

.weather-dropdown {
    width: 100%;
}


/* ============================================================
   Dash 4.4.1 - exact City dropdown buttons
   ============================================================ */

#city-dropdown,
#history-city-dropdown {
    background-color: #0a1929 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: none !important;
    appearance: none !important;
}


/* ============================================================
   Dash 4.4.1 dropdown wrapper
   ============================================================ */

.weather-dropdown .dash-dropdown-wrapper {
    background-color: #0a1929 !important;
    border: 1px solid rgba(120, 180, 255, 0.20) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}


/* ============================================================
   Actual dropdown button
   ============================================================ */

.weather-dropdown .dash-dropdown-wrapper > button,
.weather-dropdown .dash-dropdown-wrapper button {
    background-color: #0a1929 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: none !important;
}


/* ============================================================
   Dropdown text
   ============================================================ */

.weather-dropdown .dash-dropdown-wrapper button span {
    color: #ffffff !important;
}


/* ============================================================
   Dropdown arrow
   ============================================================ */

.weather-dropdown .dash-dropdown-wrapper button svg {
    color: #8ea7c4 !important;
    fill: #8ea7c4 !important;
}


/* ============================================================
   Legacy Dash dropdown selectors
   Kept for compatibility.
   ============================================================ */

.weather-dropdown .Select-control {
    background-color: #0a1929 !important;
    border: 1px solid rgba(120, 180, 255, 0.20) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
}


.weather-dropdown .Select-multi-value-wrapper {
    background-color: #0a1929 !important;
}


.weather-dropdown .Select-value {
    background-color: transparent !important;
}


.weather-dropdown .Select-placeholder {
    color: #8ea7c4 !important;
}


.weather-dropdown .Select-value-label {
    color: #ffffff !important;
}


.weather-dropdown .Select-input {
    background-color: transparent !important;
}


.weather-dropdown .Select-input input {
    color: #ffffff !important;
    background-color: transparent !important;
}


.weather-dropdown .Select-arrow {
    border-top-color: #8ea7c4 !important;
}


/* ============================================================
   Legacy dropdown menu
   ============================================================ */

.weather-dropdown .Select-menu-outer {
    background-color: #0b1b2d !important;
    border: 1px solid rgba(120, 180, 255, 0.20) !important;
}


.weather-dropdown .Select-menu {
    background-color: #0b1b2d !important;
}


.weather-dropdown .Select-option {
    background-color: #0b1b2d !important;
    color: #e8f1ff !important;
}


.weather-dropdown .Select-option.is-focused {
    background-color: #153451 !important;
    color: #ffffff !important;
}


.weather-dropdown .Select-option.is-selected {
    background-color: #2375eb !important;
    color: #ffffff !important;
}


/* ============================================================
   Date Picker
   ============================================================ */

.DateInput,
.DateInput_input {
    background-color: #0a1929 !important;
    color: #ffffff !important;
}


.DateInput_input {
    border: 1px solid rgba(120, 180, 255, 0.20) !important;
    border-radius: 8px !important;
}


.DateInput_input::placeholder {
    color: #8ea7c4 !important;
}


.DatePickerSingleInput {
    background-color: #0a1929 !important;
    border: 1px solid rgba(120, 180, 255, 0.20) !important;
    border-radius: 8px !important;
}


.DayPicker,
.CalendarMonth,
.CalendarMonth_table {
    background-color: #0b1b2d !important;
}


.CalendarMonth_caption {
    color: #ffffff !important;
}


.CalendarDay {
    background-color: #0b1b2d !important;
    color: #e8f1ff !important;
    border-color: rgba(120, 180, 255, 0.10) !important;
}


.CalendarDay:hover {
    background-color: #153451 !important;
    color: #ffffff !important;
}


.CalendarDay__selected,
.CalendarDay__selected:hover {
    background-color: #2375eb !important;
    color: #ffffff !important;
}


.DayPicker_weekHeader,
.DayPicker_weekHeader small {
    color: #8ea7c4 !important;
}


.DayPickerNavigation_button {
    background-color: #0b1b2d !important;
    border-color: rgba(120, 180, 255, 0.20) !important;
    color: #ffffff !important;
}


/* ============================================================
   General labels
   ============================================================ */

label {
    color: #a9c0dc !important;
}

</style>
"""