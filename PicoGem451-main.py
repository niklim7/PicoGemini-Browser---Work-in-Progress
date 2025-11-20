# PicoGem 451 - A Gemini Browser for Raspberry Pi Pico W
# Hardware: Pico W / Pico 2 W, Maker Pi Pico Mini, Waveshare 3.7" E-Paper
# Author: [Your Name/Handle]
# Date: October 2025

import time
# Ensure the driver file on Pico is named 'Pico_ePaper_3_7.py'
# and contains the class 'EPD' that inherits framebuf.FrameBuffer
import Pico_ePaper_3_7 as epd
import framebuf
import network
import machine
import socket
import ssl
import ure as re

# --- Hardware Configuration ---
# Buttons connected to GPIOs via Maker Pi Pico Mini headers
UP_PIN = 0
DOWN_PIN = 1
LEFT_PIN = 4  # Back
RIGHT_PIN = 5 # Select/Forward

# --- Wi-Fi Credentials ---
# TODO: Move to external config file in future
WIFI_SSID = "Your SSID" 
WIFI_PASSWORD = "Your wifi password"

# --- Gemini Protocol Settings ---
GEMINI_PORT = 1965
current_url = f"gemini://geminiprotocol.net/"
history = [] # Stores previous URLs for 'Back' functionality

# --- Display Configuration ---
# Physical: 280x480 (Portrait). Logical: 480x280 (Landscape)
LANDSCAPE_WIDTH = 480
LANDSCAPE_HEIGHT = 280
FONT_WIDTH = 8  # Standard MicroPython font
FONT_HEIGHT = 8
LINE_SPACING = 2
STATUS_BAR_HEIGHT = FONT_HEIGHT + LINE_SPACING
CONTENT_START_Y = STATUS_BAR_HEIGHT
# Calculate lines per screen based on font size
MAX_LINES_ON_SCREEN = (LANDSCAPE_HEIGHT - CONTENT_START_Y) // (FONT_HEIGHT + LINE_SPACING)
MAX_CHARS_PER_LINE = LANDSCAPE_WIDTH // FONT_WIDTH

# --- Runtime State ---
parsed_content = []      # Stores the parsed lines of the current page
current_selection = 0    # Index of the currently selected line
top_item_index = 0       # Index of the first line displayed at the top

# ==========================================
# Hardware Initialization
# ==========================================

print("Initializing display object (Landscape)...")
# SPI Pins for Maker Pi Pico Mini + Waveshare 3.7" E-Paper
spi = machine.SPI(1, sck=machine.Pin(10), mosi=machine.Pin(11))
cs_pin = machine.Pin(9, machine.Pin.OUT)
dc_pin = machine.Pin(8, machine.Pin.OUT)
rst_pin = machine.Pin(12, machine.Pin.OUT)
busy_pin = machine.Pin(13, machine.Pin.IN)

# Initialize display driver with landscape orientation
display = epd.EPD(spi, cs_pin, dc_pin, rst_pin, busy_pin, landscape=True)
print(f"Display object created. Width={display.width}, Height={display.height}")

# The display object itself acts as the framebuffer
fb = display 
print(f"Using display object as framebuffer.")

# Initialize Navigation Buttons with internal pull-ups
up_button = machine.Pin(UP_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
down_button = machine.Pin(DOWN_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
left_button = machine.Pin(LEFT_PIN, machine.Pin.IN, machine.Pin.PULL_UP)
right_button = machine.Pin(RIGHT_PIN, machine.Pin.IN, machine.Pin.PULL_UP)

# ==========================================
# Network Functions
# ==========================================

def connect_wifi(ssid, password):
    """Connects to Wi-Fi and returns IP address or None."""
    print(f"Connecting to Wi-Fi network: {ssid}...")
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(ssid, password)
    max_wait = 15
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        time.sleep(1)
    if wlan.status() != 3:
        print("Wi-Fi connection failed!")
        return None
    else:
        status = wlan.ifconfig()
        ip_address = status[0]
        print(f"Connected! IP Address: {ip_address}")
        return ip_address

def fetch_gemini(url):
    """
    Fetches content from a Gemini URL.
    Returns: (header, body_text) on success, or (header, None) on error.
    Handles TLS connection and basic error checking.
    """
    header = None
    response = None
    try:
        # Basic URL parsing
        proto, _, host, path = url.split("/", 3)
        port = GEMINI_PORT
    except ValueError:
        print(f"Cannot parse URL: {url}")
        return None, None
    
    if not proto.startswith("gemini"):
        print("Not a Gemini URL")
        return None, None
        
    if path == host:
        path = ""
    path = "/" + path

    print(f"Fetching Gemini: {url}")
    s = None
    ssl_sock = None
    try:
        # DNS Lookup
        addr_info = socket.getaddrinfo(host, port)
        addr = addr_info[0][-1]
        
        # Socket Connection
        s = socket.socket()
        s.settimeout(20)
        s.connect(addr)
        
        # TLS Handshake (No cert verification for simplicity/memory)
        ssl_sock = ssl.wrap_socket(s)
        
        # Send Request
        request = url + "\r\n"
        ssl_sock.write(bytes(request, 'utf-8'))

        # Read Response
        response_bytes = b""
        header_bytes = ssl_sock.readline()
        header = header_bytes.decode('utf-8', 'ignore').strip()
        print(f"Received Header: {header}")

        # Check for success status (2x)
        if not header.startswith('2'):
             print(f"Non-success status: {header}")
             return header, None 

        # Read Body (with memory safety)
        while True:
            try:
                chunk = ssl_sock.read(512)
                if not chunk:
                    break
                response_bytes += chunk
            except MemoryError:
                 print("Memory Error: Page too large to load!")
                 return header, "[Page too large to load]"

        # Decode Body
        try:
            response = response_bytes.decode('utf-8')
        except UnicodeDecodeError:
            response = response_bytes.decode('latin-1') # Fallback
        
        return header, response

    except MemoryError:
        print("Memory Error: Page likely too large!")
        return header, "[Page too large to load]"
    except OSError as e:
        print(f"Gemini fetch error: {e}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None
    finally:
        if ssl_sock:
            ssl_sock.close()
        elif s:
            s.close()

def resolve_url(base_url, link_url):
    """Resolves relative links against the current base URL."""
    print(f"Resolving: base='{base_url}', link='{link_url}'")
    if "://" in link_url:
        print(f"Result (absolute): '{link_url}'")
        return link_url
    else:
        base_match = re.match(r"([a-z]+://[^/]+)(/.*)?", base_url)
        if not base_match:
            print("Error: Could not parse base URL")
            return None
        base_host_part = base_match.group(1)
        base_path_part = base_match.group(2) if base_match.group(2) else "/"
        
        if link_url.startswith("/"):
            resolved = base_host_part + link_url
            print(f"Result (root relative): '{resolved}'")
            return resolved
        else:
            last_slash = base_path_part.rfind('/')
            if last_slash <= 0:
                resolved = base_host_part + "/" + link_url
            else:
                resolved = base_host_part + base_path_part[:last_slash+1] + link_url
            print(f"Result (directory relative): '{resolved}'")
            return resolved

# ==========================================
# Parsing & Display Functions
# ==========================================

def parse_gemini_content(content):
    """Parses raw Gemini text into a list of typed lines."""
    parsed_lines = []
    lines = content.splitlines()
    link_counter = 1
    in_preformatted = False
    
    for line in lines:
        # Skip blank lines unless in preformatted block
        if not line.strip() and not in_preformatted:
            continue

        line_type = 'text'
        display_text = line
        url = None
        link_num = None

        if line.startswith("```"):
            in_preformatted = not in_preformatted
            line_type = 'preformat_toggle'
            display_text = line 
        elif in_preformatted:
            line_type = 'preformatted'
            display_text = line
        elif line.startswith("=>"):
            parts = line.split(None, 2)
            if len(parts) >= 2:
                line_type = 'link'
                url = parts[1]
                # Format link with number: [1] Link Title
                display_text = f"[{link_counter}] " + (parts[2] if len(parts) > 2 else url)
                link_num = link_counter
                link_counter += 1
            else: 
                display_text = line
        elif line.startswith("###"):
            line_type = 'h3'; display_text = line[3:].strip()
        elif line.startswith("##"):
            line_type = 'h2'; display_text = line[2:].strip()
        elif line.startswith("#"):
            line_type = 'h1'; display_text = line[1:].strip()
        elif line.startswith("*"):
            line_type = 'list'; display_text = "  " + line[1:].strip()
        elif line.startswith(">"):
            line_type = 'quote'; display_text = "> " + line[1:].strip()

        parsed_lines.append({
            'type': line_type, 
            'text': display_text, 
            'url': url, 
            'link_num': link_num
        })
    return parsed_lines

def draw_screen_line(fb, y, text_part, is_selected):
    """Draws a single line of text with optional inverted colors for selection."""
    x = 0
    # Colors: Black=0x00, White=0xFF
    # Invert colors if line is selected
    bg_color = 0x00 if is_selected else 0xFF 
    fg_color = 0xFF if is_selected else 0x00 
    
    # Clear background rect for this line
    fb.fill_rect(x, y, LANDSCAPE_WIDTH, FONT_HEIGHT + LINE_SPACING, bg_color)
    # Draw text
    fb.text(text_part, x, y, fg_color)

def display_content(fb, content, selection_idx, top_idx):
    """
    Draws the visible portion of content to the framebuffer.
    Handles line wrapping and scrolling.
    """
    # Clear content area to white
    fb.fill_rect(0, CONTENT_START_Y, LANDSCAPE_WIDTH, LANDSCAPE_HEIGHT - CONTENT_START_Y, 0xFF)
    
    y_pos = CONTENT_START_Y
    screen_lines_drawn = 0
    
    for i in range(top_idx, len(content)):
        if screen_lines_drawn >= MAX_LINES_ON_SCREEN:
            break # Stop if screen is full

        item = content[i]
        is_selected = (i == selection_idx)

        prefix = ""
        # Add visual prefixes for headings
        if item['type'] == 'h1': prefix = "# "
        elif item['type'] == 'h2': prefix = "## "
        elif item['type'] == 'h3': prefix = "### "

        full_line_text = prefix + item['text']
        remaining_text = full_line_text
        
        # Line Wrapping Logic
        first_part_of_item = True
        indent = ""
        
        while len(remaining_text) > 0 and screen_lines_drawn < MAX_LINES_ON_SCREEN:
            line_part = ""
            if len(remaining_text) <= MAX_CHARS_PER_LINE:
                line_part = remaining_text
                remaining_text = ""
            else:
                # Wrap at last space
                break_point = remaining_text.rfind(' ', 0, MAX_CHARS_PER_LINE)
                if break_point == -1:
                    line_part = remaining_text[:MAX_CHARS_PER_LINE]
                    remaining_text = remaining_text[MAX_CHARS_PER_LINE:]
                else:
                    line_part = remaining_text[:break_point]
                    remaining_text = remaining_text[break_point:].lstrip()

            # Draw the wrapped line part
            draw_screen_line(fb, y_pos, indent + line_part, is_selected)

            y_pos += FONT_HEIGHT + LINE_SPACING
            screen_lines_drawn += 1
            
            if not first_part_of_item:
                indent = "  " # Indent continuation lines
            first_part_of_item = False

def refresh_display(update_mode=0):
    """Triggers the hardware display update."""
    print("Calling FULL display function (display.show())...")
    display.show() # Driver handles partial/full refresh logic internally
    
    if hasattr(display, 'wait_until_ready'):
        display.wait_until_ready()
    else:
        print("Waiting for busy pin (manual)...")
        while hasattr(display, '_busy') and display._busy() == 1:
            time.sleep(0.1)
        print("Busy pin released.")

def show_message(message):
    """Displays a fullscreen message (loading, error)."""
    fb.fill(0xFF) # White background
    fb.text(message[:MAX_CHARS_PER_LINE], 0, CONTENT_START_Y, 0x00) # Black text
    refresh_display(0)

# ==========================================
# Main Execution Loop
# ==========================================

# 1. Initial Setup
needs_full_redraw = True
ip = connect_wifi(WIFI_SSID, WIFI_PASSWORD)

if not ip:
    show_message("WiFi Failed!")
    while True: time.sleep(1) # Halt if no Wi-Fi

# 2. Main Loop
debounce_delay = 0.2

while True:
    # --- Page Fetching Logic ---
    if needs_full_redraw:
        show_message("Fetching...")
        gemini_header, gemini_body = fetch_gemini(current_url)
        
        if gemini_body == "[Page too large to load]":
             show_message("Page too large!")
             time.sleep(1)
             if history:
                 current_url = history.pop() # Auto-go back
                 needs_full_redraw = True
                 print("Attempting to go back due to memory error...")
                 continue # Restart loop to fetch previous page
             else:
                 parsed_content = [] # Clear if no history
                 
        elif gemini_body:
            # Parse and Prepare Display
            parsed_content = parse_gemini_content(gemini_body)
            current_selection = 0
            top_item_index = 0
            display_content(fb, parsed_content, current_selection, top_item_index)
            refresh_display(0)
            
        else: # Fetch failed
            error_msg = f"Failed: {current_url[:MAX_CHARS_PER_LINE-10]}"
            if gemini_header: 
                error_msg = f"Error {gemini_header[:30]}"
            show_message(error_msg)
            time.sleep(1)
            if history:
                 current_url = history.pop()
                 needs_full_redraw = True
                 print("Attempting to go back due to fetch error...")
                 continue
            else:
                 parsed_content = []
        
        needs_full_redraw = False

    # --- Input Handling ---
    old_selection = current_selection
    old_top_index = top_item_index
    needs_refresh = False

    if up_button.value() == 0:
        if current_selection > 0:
            current_selection -= 1
            print(f"Selection: {current_selection}")
            # Basic scrolling
            if current_selection < top_item_index:
                top_item_index = current_selection
            needs_refresh = True
        time.sleep(debounce_delay)
        
    elif down_button.value() == 0:
        if current_selection < len(parsed_content) - 1:
            current_selection += 1
            print(f"Selection: {current_selection}")
            # Basic scrolling (approximate page check)
            if current_selection >= top_item_index + MAX_LINES_ON_SCREEN:
                top_item_index += 1
            needs_refresh = True
        time.sleep(debounce_delay)
        
    elif left_button.value() == 0: # Back
        print("Back button pressed")
        if history:
            previous_url = history.pop()
            print(f"Going back to: {previous_url}")
            current_url = previous_url
            needs_full_redraw = True
        else:
            print("No history.")
        time.sleep(debounce_delay)
        
    elif right_button.value() == 0: # Select/Forward
        print(f"Select button pressed on item {current_selection}")
        if parsed_content and current_selection < len(parsed_content):
            selected_item = parsed_content[current_selection]
            if selected_item.get('url'):
                target_url = selected_item['url']
                resolved_target_url = resolve_url(current_url, target_url)
                
                if resolved_target_url and resolved_target_url.startswith("gemini://"):
                    history.append(current_url) # Save current to history
                    current_url = resolved_target_url
                    needs_full_redraw = True
                elif resolved_target_url:
                    # Show msg for non-Gemini links
                    show_message(f"Non-Gemini:{resolved_target_url[:MAX_CHARS_PER_LINE-15]}")
                    time.sleep(2)
                    needs_refresh = True # Restore screen
                else:
                    show_message("Invalid URL?")
            else:
                print("Selected item is not a link.")
        time.sleep(debounce_delay)

    # --- Screen Update ---
    if needs_refresh and parsed_content:
        print(f"Redrawing visible lines: new={current_selection}, top={top_item_index}")
        display_content(fb, parsed_content, current_selection, top_item_index)
        refresh_display(0) # Full refresh
        needs_refresh = False

    time.sleep(0.05)
