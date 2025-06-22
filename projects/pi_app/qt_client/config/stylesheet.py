# config/stylesheet.py
# This file contains the QSS (Qt Style Sheet) for the application.

STYLESHEET = """
/* General Window Styling */
QMainWindow {
    background-color: #f0f2f5; /* Light grey background */
}

/* Main content frames for left and right panels */
QFrame#main_frame {
    background-color: #ffffff;
    border-radius: 8px;
}

/* General Label Styling */
QLabel {
    color: #333333; /* Dark grey text */
    font-family: Arial, sans-serif;
}

/* Specific Label Styling */
QLabel#title_label {
    font-size: 24px;
    font-weight: bold;
    color: #1c1e21;
}

QLabel#header_label {
    font-size: 11px;
    font-weight: bold;
    color: #606770;
}

QLabel#product_name_label {
    font-size: 16px;
    font-weight: bold;
}

QLabel#product_subtitle_label {
    font-size: 12px;
    color: #606770;
}

QLabel#total_cost_label {
    font-size: 18px;
    font-weight: bold;
}

/* Button Styling */
QPushButton {
    border-radius: 6px;
    font-size: 14px;
    font-weight: bold;
    padding: 10px 16px;
    border: 1px solid transparent;
}

QPushButton:hover {
    opacity: 0.9;
}

/* Primary "Checkout" Button */
QPushButton#checkout_button {
    background-color: #4c5fd7; /* Purple */
    color: white;
}

QPushButton#checkout_button:hover {
    background-color: #4051b8;
}

/* Secondary "Apply" Button */
QPushButton#apply_button {
    background-color: #e74c3c; /* Reddish-pink */
    color: white;
}

QPushButton#apply_button:hover {
    background-color: #c0392b;
}

/* Link-style Buttons */
QPushButton#link_button {
    background-color: transparent;
    border: none;
    color: #4c5fd7; /* Purple to match theme */
    font-size: 13px;
    text-align: left;
    padding: 0;
}

QPushButton#link_button:hover {
    text-decoration: underline;
}

/* Quantity Adjuster Buttons */
QPushButton#quantity_button {
    font-size: 18px;
    font-weight: bold;
    background-color: #e4e6eb;
    color: #1c1e21;
    min-width: 30px;
    max-width: 30px;
    padding: 5px;
}

QPushButton#quantity_button:hover {
    background-color: #d8dbe0;
}


/* Line Edit for Promo Code */
QLineEdit {
    border: 1px solid #ccd0d5;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    background-color: #f5f7f9;
}

QLineEdit:focus {
    border-color: #4c5fd7; /* Highlight with theme color on focus */
}

/* Dropdown for Shipping */
QComboBox {
    border: 1px solid #ccd0d5;
    border-radius: 6px;
    padding: 10px;
    font-size: 14px;
    background-color: #f5f7f9;
}

QComboBox::drop-down {
    border: none;
}

QComboBox::down-arrow {
    image: url(down_arrow.png); /* A proper implementation would use a real icon */
    width: 14px;
    height: 14px;
    padding-right: 15px;
}

/* Separator Line */
QFrame[objectName="separator"] {
    max-height: 1px;
    background-color: #e0e0e0;
}

/* TextEdit for Serial Output */
QTextEdit#serial_output_area {
    border: 1px solid #ccd0d5;
    border-radius: 6px;
    padding: 5px;
}
"""
