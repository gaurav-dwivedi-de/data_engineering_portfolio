# ============================================================
# Weather Intelligence Platform
# Dashboard Styles
# ============================================================


# ============================================================
# Global Page
# ============================================================

PAGE_STYLE = {
    "backgroundColor": "#06111f",
    "minHeight": "100vh",
    "width": "100%",
    "color": "#e8f1ff",
    "fontFamily": (
        "Inter, -apple-system, BlinkMacSystemFont, "
        "'Segoe UI', sans-serif"
    ),
    "overflowX": "hidden",
    "boxSizing": "border-box",
}


# ============================================================
# Main Content
#
# The dashboard now uses a top navigation bar rather than a
# sidebar. Bootstrap controls the responsive layout.
# ============================================================

MAIN_STYLE = {
    "width": "100%",
    "minWidth": "0",
    "minHeight": "100vh",
    "backgroundColor": "#06111f",
    "boxSizing": "border-box",
}


# ============================================================
# Dashboard Content
# ============================================================

CONTENT_STYLE = {
    "width": "100%",
    "maxWidth": "100%",
    "minWidth": "0",
    "padding": "28px",
    "backgroundColor": "#06111f",
    "minHeight": "100vh",
    "boxSizing": "border-box",
}


# ============================================================
# Header
# ============================================================

HEADER_STYLE = {
    "padding": "0 0 20px 0",
    "width": "100%",
    "maxWidth": "100%",
    "boxSizing": "border-box",
}


HEADER_TITLE_STYLE = {
    "fontSize": "26px",
    "fontWeight": "800",
    "color": "#ffffff",
    "margin": "0",
    "maxWidth": "100%",
    "lineHeight": "1.2",
}


HEADER_SUBTITLE_STYLE = {
    "fontSize": "13px",
    "color": "#8ea7c4",
    "marginTop": "5px",
    "maxWidth": "100%",
}


# ============================================================
# Top Navigation
# ============================================================

NAVBAR_STYLE = {
    "width": "100%",
    "backgroundColor": "#04101d",
    "borderBottom": "1px solid rgba(120, 180, 255, 0.12)",
    "padding": "12px 28px",
    "boxSizing": "border-box",
}


NAVBAR_INNER_STYLE = {
    "width": "100%",
    "maxWidth": "100%",
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "space-between",
    "gap": "20px",
    "boxSizing": "border-box",
}


BRAND_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "gap": "9px",
    "textDecoration": "none",
    "flexShrink": "0",
}


BRAND_TEXT_STYLE = {
    "lineHeight": "1.1",
}


BRAND_TITLE_STYLE = {
    "fontSize": "12px",
    "fontWeight": "700",
    "color": "#ffffff",
}


BRAND_ACCENT_STYLE = {
    "fontSize": "12px",
    "fontWeight": "700",
    "color": "#46c8ff",
}


BRAND_TAGLINE_STYLE = {
    "fontSize": "7px",
    "letterSpacing": "0.8px",
    "color": "#59728d",
    "marginTop": "4px",
}


NAV_LINKS_STYLE = {
    "display": "flex",
    "alignItems": "center",
    "justifyContent": "flex-end",
    "flexWrap": "wrap",
    "gap": "6px",
    "minWidth": "0",
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
    "display": "inline-flex",
    "alignItems": "center",
    "justifyContent": "center",
    "gap": "7px",
    "padding": "9px 12px",
    "borderRadius": "9px",
    "color": "#a9c0dc",
    "textDecoration": "none",
    "fontSize": "12px",
    "fontWeight": "600",
    "whiteSpace": "nowrap",
    "boxSizing": "border-box",
    "transition": "background-color 0.15s ease, color 0.15s ease",
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


# ============================================================
# General Cards
# ============================================================

CARD_STYLE = {
    "backgroundColor": "#0b1b2d",
    "border": "1px solid rgba(120, 180, 255, 0.14)",
    "borderRadius": "16px",
    "boxShadow": "0 10px 30px rgba(0,0,0,0.20)",
    "boxSizing": "border-box",
    "maxWidth": "100%",
    "width": "100%",
}


# ============================================================
# KPI Cards
# ============================================================

KPI_CARD_STYLE = {
    **CARD_STYLE,
    "minHeight": "145px",
    "padding": "20px",
}


# ============================================================
# Model Cards
# ============================================================

MODEL_CARD_STYLE = {
    **CARD_STYLE,
    "minHeight": "105px",
    "padding": "18px",
}


# ============================================================
# Legacy Row Styles
#
# Kept because layout.py imports them.
# Actual KPI/model rows now use dbc.Row.
# ============================================================

KPI_ROW_STYLE = {
    "width": "100%",
    "maxWidth": "100%",
}


KPI_COLUMN_STYLE = {
    "width": "100%",
    "minWidth": "0",
    "boxSizing": "border-box",
}


MODEL_ROW_STYLE = {
    "width": "100%",
    "maxWidth": "100%",
}


MODEL_COLUMN_STYLE = {
    "width": "100%",
    "minWidth": "0",
    "boxSizing": "border-box",
}


# ============================================================
# Sections
# ============================================================

SECTION_STYLE = {
    "marginTop": "22px",
    "width": "100%",
    "maxWidth": "100%",
    "minWidth": "0",
    "boxSizing": "border-box",
}


SECTION_TITLE_STYLE = {
    "fontSize": "20px",
    "fontWeight": "700",
    "color": "#f3f7ff",
    "marginBottom": "4px",
    "lineHeight": "1.2",
}


SECTION_SUBTITLE_STYLE = {
    "fontSize": "13px",
    "color": "#8ea7c4",
    "marginBottom": "18px",
    "lineHeight": "1.4",
}


# ============================================================
# Hero
# ============================================================

HERO_STYLE = {
    **CARD_STYLE,

    "padding": "34px",
    "minHeight": "250px",

    # Layer order:
    # 1. Dark blue gradient keeps the left side readable.
    # 2. Blue/purple gradients preserve the existing visual style.
    # 3. Mountain image becomes increasingly visible toward the right.
    "background": (
        "linear-gradient("
        "90deg, "
        "rgba(11,35,64,0.98) 0%, "
        "rgba(11,35,64,0.94) 28%, "
        "rgba(16,43,80,0.78) 52%, "
        "rgba(23,29,70,0.62) 100%"
        "), "

        "radial-gradient("
        "circle at 85% 20%, "
        "rgba(91,112,255,0.38), "
        "transparent 32%"
        "), "

        "radial-gradient("
        "circle at 60% 90%, "
        "rgba(0,191,255,0.18), "
        "transparent 38%"
        "), "

        "url('/assets/mountain-background.jpg') "
        "right center / cover no-repeat"
    ),

    "backgroundPosition": "center",
    "backgroundSize": "cover",

    "overflow": "hidden",
}



HERO_TITLE_STYLE = {
    "fontSize": "42px",
    "fontWeight": "800",
    "lineHeight": "1.1",
    "color": "#ffffff",
    "maxWidth": "100%",
    "wordBreak": "break-word",
}


HERO_ACCENT_STYLE = {
    "color": "#46c8ff",
}


HERO_TEXT_STYLE = {
    "fontSize": "17px",
    "color": "#dceaff",
    "marginTop": "8px",
    "maxWidth": "100%",
    "lineHeight": "1.4",
}


HERO_SMALL_TEXT_STYLE = {
    "fontSize": "12px",
    "color": "#8ea7c4",
    "marginTop": "6px",
    "maxWidth": "100%",
    "lineHeight": "1.4",
}


# ============================================================
# Hero Badges
# ============================================================

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
    "maxWidth": "100%",
    "boxSizing": "border-box",
}


# ============================================================
# Icons
# ============================================================

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


# ============================================================
# KPI Typography
# ============================================================

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
    "maxWidth": "100%",
    "overflowWrap": "break-word",
}


KPI_DESCRIPTION_STYLE = {
    "fontSize": "11px",
    "color": "#617892",
    "maxWidth": "100%",
}


# ============================================================
# Model Typography
# ============================================================

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
    "maxWidth": "100%",
    "overflowWrap": "break-word",
}


MODEL_NAME_STYLE = {
    "fontSize": "10px",
    "color": "#617892",
    "marginTop": "10px",
    "maxWidth": "100%",
    "overflowWrap": "break-word",
}


# ============================================================
# Form Labels
# ============================================================

LABEL_STYLE = {
    "fontSize": "11px",
    "fontWeight": "600",
    "color": "#8ea7c4",
    "display": "block",
    "marginBottom": "6px",
}


# ============================================================
# Dropdown
# ============================================================

DROPDOWN_STYLE = {
    "backgroundColor": "#0a1929",
    "color": "#ffffff",
    "border": "1px solid rgba(120, 180, 255, 0.20)",
    "borderRadius": "8px",
    "width": "100%",
    "maxWidth": "100%",
    "boxSizing": "border-box",
}


# ============================================================
# Date Picker
# ============================================================

DATE_STYLE = {
    "backgroundColor": "#0a1929",
    "color": "#ffffff",
    "border": "1px solid rgba(120, 180, 255, 0.20)",
    "borderRadius": "8px",
    "maxWidth": "100%",
    "boxSizing": "border-box",
}


# ============================================================
# Historical Table
# ============================================================

TABLE_STYLE = {
    "overflowX": "auto",
    "backgroundColor": "#0b1b2d",
    "maxWidth": "100%",
    "width": "100%",
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


# ============================================================
# Graphs
# ============================================================

GRAPH_STYLE = {
    "backgroundColor": "#0b1b2d",
    "borderRadius": "16px",
    "padding": "4px",
    "marginBottom": "14px",
    "maxWidth": "100%",
    "width": "100%",
    "boxSizing": "border-box",
}


# ============================================================
# Footer
# ============================================================

FOOTER_STYLE = {
    "padding": "25px 0 5px",
    "color": "#617892",
    "fontSize": "12px",
    "maxWidth": "100%",
    "lineHeight": "1.5",
}


# ============================================================
# Legacy Sidebar Footer Compatibility
#
# Kept so older imports do not fail. The new top-navigation
# layout does not use this style.
# ============================================================

SIDEBAR_FOOTER_STYLE = {
    "marginTop": "30px",
    "padding": "12px",
    "borderTop": "1px solid rgba(120,180,255,0.10)",
}


# ============================================================
# Dropdown + Date Picker + Component CSS
#
# Bootstrap handles the overall responsive page layout.
# This CSS is only for Dash-specific components and small
# responsive adjustments.
# ============================================================

DROPDOWN_CSS = """
<style>

/* ============================================================
   Global
   ============================================================ */

html,
body {
    width: 100%;
    max-width: 100%;
    margin: 0;
    padding: 0;
    overflow-x: hidden;
}

* {
    box-sizing: border-box;
}


/* ============================================================
   Dashboard structure
   ============================================================ */

.weather-dashboard-page {
    width: 100%;
    max-width: 100%;
    min-width: 0;
    margin: 0;
    padding: 0;
}


/* ============================================================
   Top navigation
   ============================================================ */

.weather-navbar {
    width: 100%;
    max-width: 100%;
}

.weather-navbar-inner {
    width: 100%;
    max-width: 100%;
}

.weather-nav-links {
    min-width: 0;
}


/* ============================================================
   General dropdown container
   ============================================================ */

.weather-dropdown {
    width: 100%;
    max-width: 100%;
}


/* ============================================================
   Dash 4.x City dropdown
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
   Dash dropdown wrapper
   ============================================================ */

.weather-dropdown .dash-dropdown-wrapper {
    background-color: #0a1929 !important;
    border: 1px solid rgba(120, 180, 255, 0.20) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    width: 100% !important;
    max-width: 100% !important;
}


/* ============================================================
   Dropdown button
   ============================================================ */

.weather-dropdown .dash-dropdown-wrapper > button,
.weather-dropdown .dash-dropdown-wrapper button {
    background-color: #0a1929 !important;
    color: #ffffff !important;
    border: none !important;
    box-shadow: none !important;
    max-width: 100% !important;
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
   Dropdown menu
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
    max-width: 100% !important;
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
   Bootstrap rows
   ============================================================ */

.row {
    max-width: 100%;
}


/* ============================================================
   Plotly responsiveness
   ============================================================ */

.js-plotly-plot,
.plot-container,
.plotly {
    max-width: 100% !important;
}


/* ============================================================
   Dash DataTable responsiveness
   ============================================================ */

.dash-table-container {
    width: 100%;
    max-width: 100%;
    overflow-x: auto !important;
}


/* ============================================================
   Labels
   ============================================================ */

label {
    color: #a9c0dc !important;
}


/* ============================================================
   Tablet
   768px - 991px
   ============================================================ */

@media (min-width: 768px) and (max-width: 991px) {

    #weather-dashboard-content {
        padding: 22px !important;
    }

    #weather-dashboard-hero {
        padding: 28px !important;
    }

    #weather-dashboard-hero h1 {
        font-size: 36px !important;
    }

    .weather-navbar {
        padding-left: 20px !important;
        padding-right: 20px !important;
    }

    .weather-navbar-inner {
        flex-wrap: wrap;
    }

    .weather-nav-links {
        justify-content: flex-start;
        width: 100%;
    }
}


/* ============================================================
   Mobile
   <= 767px
   ============================================================ */

@media (max-width: 767px) {

    #weather-dashboard-content {
        width: 100% !important;
        max-width: 100% !important;
        padding: 18px !important;
    }

    .weather-navbar {
        padding: 12px 18px !important;
    }

    .weather-navbar-inner {
        flex-direction: column;
        align-items: stretch !important;
        gap: 12px !important;
    }

    .weather-brand {
        width: 100%;
    }

    .weather-nav-links {
        width: 100%;
        justify-content: flex-start !important;
        gap: 6px !important;
    }

    .weather-nav-links a {
        flex: 1 1 auto;
        text-align: center;
        min-width: 0;
    }

    #weather-dashboard-hero {
        width: 100% !important;
        max-width: 100% !important;
        padding: 22px !important;
        min-height: auto !important;

        background-position: center right !important;
        background-size: cover !important;
    }

    #weather-dashboard-hero h1 {
        font-size: 30px !important;
        line-height: 1.15 !important;
        word-break: break-word;
    }

    #weather-dashboard-hero span {
        margin-right: 5px !important;
        margin-top: 8px !important;
        padding: 6px 9px !important;
        font-size: 10px !important;
    }

    #weather-dashboard-content .row {
        width: 100% !important;
        max-width: 100% !important;
    }

    #weather-dashboard-content .row > [class*="col-"] {
        min-width: 0;
        max-width: 100%;
    }

    #current-temperature,
    #predicted-temperature,
    #prediction-difference,
    #model-name,
    #model-trained-at {
        max-width: 100%;
        overflow-wrap: break-word;
        word-break: break-word;
    }

    .DatePickerSingleInput,
    .DateInput,
    .DateInput_input {
        width: 100% !important;
        max-width: 100% !important;
    }

    .dash-table-container {
        width: 100% !important;
        max-width: 100% !important;
        overflow-x: auto !important;
    }

    .js-plotly-plot {
        width: 100% !important;
        max-width: 100% !important;
    }

    #weather-dashboard-content footer {
        text-align: center;
        line-height: 1.5;
    }
}


/* ============================================================
   Small phones
   <= 480px
   ============================================================ */

@media (max-width: 480px) {

    #weather-dashboard-content {
        padding: 14px !important;
    }

    #weather-dashboard-hero {
        padding: 18px !important;
        border-radius: 14px !important;

        background-position: center right !important;
        background-size: cover !important;
    }

    #weather-dashboard-hero h1 {
        font-size: 26px !important;
    }

    .weather-nav-links {
        display: grid !important;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        width: 100%;
    }

    .weather-nav-links a {
        width: 100%;
    }

    .weather-dropdown {
        width: 100% !important;
    }

    #weather-dashboard-content .row {
        --bs-gutter-x: 0.75rem;
    }

    #weather-dashboard-content .row > [class*="col-"] {
        padding-left: 0.375rem;
        padding-right: 0.375rem;
    }
}

</style>
"""