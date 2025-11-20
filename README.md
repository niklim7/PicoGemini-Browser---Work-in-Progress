# PicoGemini Browser - Work in Progress

## Project Goal

PicoGemini Browser is a custom-built, low-power, minimalist hardware browser designed specifically for navigating the text-focused Gemini protocol. The aim is to create a dedicated, distraction-free device for exploring Geminispace, emphasizing simplicity, readability, and energy efficiency, inspired by retro computing principles but using modern microcontroller technology.

## Device Overview

### 1. Physical Design & Ergonomics

The device is a custom-designed, multi-material desktop "hub" with a distinct, ergonomic, and non-symmetrical form. It's not a simple box; it's a "split-level" or "multi-planar" chassis.

Form: The chassis is slanted, starting taller at the back (80mm) and angling down towards the user.

  Ergonomic Zones: This slant is split into two distinct, top-facing levels:

  A high-angle "display zone" at the back, holding the e-paper screen for easy, at-a-glance viewing.

  A low-angle "interaction zone" at the front, housing the keypad in a more comfortable position for the hand.

   Side Panels: The Wenge wood side panels are a key design feature, acting as an architectural frame. They run the full depth of the device, following the main slant and extending slightly over the lower keypad level to act as a protective "brow" or "guard."

### 2. Materials & Construction

The design's "premium hi-fi" aesthetic comes from its specific and carefully chosen combination of wood, metal, and leather.

Chassis & Body: The internal structure is a robust plywood sub-frame. This frame is then wrapped in a Dark Petrol Faux Leather, giving the main body a cool-toned, tactile, and sophisticated finish. This leather covers the front, back, and bottom panels.

Side Panels (Wood): The 8mm-thick side panels are made from Wenge, a very dark, dense, and minimalist exotic wood. This was chosen specifically over warmer woods (like Rosewood) or lighter woods (like Bamboo) to create a stark, modern, and high-contrast neutral frame. The Wenge will be finished with Danish Oil to protect it and bring out its deep, almost-black color.

Top Plates (Metal): The two top-facing levels (for the screen and keypad) are made from 1.5mm Brushed Aluminum. This specific thickness was chosen after analysis showed that a thicker 3mm plate would cause a critical functional failure ("keycap bind"). The 1.5mm plate is the industry standard that allows the keycaps to travel freely. The aluminum plates are fastened with visible, countersunk black Philips screws, contributing to the "engineered" aesthetic.

### 3. Unique Input Method (Switches & Keycaps)

The tactile interface is not an off-the-shelf keypad; it's a custom-built mechanical keypad designed for a specific acoustic and tactile feel.

Switches: The device uses Gazzew Boba U4 (62g) switches. These are a high-end, "silent tactile" switch, chosen specifically to avoid the loud "click" of typical mechanical keyboards. Their goal is to provide a very satisfying, deep "thocky" sound that is quiet enough for any environment. The 62g weight was selected for a responsive, snappy feel suitable for quick navigation taps.

Keycaps: The keycaps are TMT Taho "Ube" in a Cherry profile. The "Ube" (purple) color was deliberately selected to create a rich, analogous color harmony against the cool-toned dark petrol (blue-green) leather and the dark Wenge wood.

Layout: The keys are arranged in the standard inverted-T arrow key configuration. This was a key ergonomic decision. While a single horizontal row was considered (for cleaner aesthetics), the inverted-T was chosen because it allows for intuitive, "no-look" operation, which was a core functional goal.

Some initial design ideas:

![Image](https://github.com/user-attachments/assets/c901a455-1bbd-4b68-8f79-c48a73389f5c)
![Image](https://github.com/user-attachments/assets/07d909cd-4029-4fb6-a02b-c683f778c750)
![Image](https://github.com/user-attachments/assets/67fceb47-a0fd-409f-9b68-6cbd85d38a9f)
![Image](https://github.com/user-attachments/assets/bda028fd-cd28-4b0a-b7bd-22dde72a2127)

## Technical Stack

### Hardware:

Raspberry Pi Pico W (RP2040/RP2350 microcontroller with Wi-Fi)

Cytron Maker Pi Pico Mini (Baseboard with battery management, GPIO breakouts, buzzer)

Waveshare 3.7" E-Paper Display (480x280, monochrome, partial refresh capable)

4-Switch Digital Joystick/Keypad (Connected via GPIO)

18650 Li-ion Battery (or other LiPo)

Hardware Power Switch

### Software:

MicroPython firmware for Raspberry Pi Pico W

Custom MicroPython application code using built-in modules (network, socket, ssl, framebuf, machine, ure, time)

Waveshare E-Paper Driver (adapted for MicroPython)

Current Status (As of October 28, 2025)

## Core Functionality:

Successfully connects to Wi-Fi networks.

Fetches content from Gemini servers over TLS (Port 1965).

Parses basic text/gemini format (headings, links, lists, quotes, preformatted text).

Displays formatted content on the e-ink screen in landscape mode (480x280).

Handles basic line wrapping (attempting word breaks).

Basic navigation implemented:

Cursor selection moves line-by-line using UP/DOWN buttons.

Handles basic scrolling when the cursor reaches screen edges.

Link following (Select/Forward button) works for Gemini URLs.

Back navigation using history works.

Handles memory errors gracefully for pages too large to load.

Basic button input reading and debouncing.

## Known Issues / Immediate Next Steps:

Screen refresh uses slow full refresh (~3 sec) for all updates, including cursor movement. Implementing partial refresh is the top priority.

Scrolling currently moves one line/item at a time; needs optimization (link jumping, page turns).

## Planned Features / Roadmap

### UI/UX:

Implement Fast Partial Refresh for cursor movement and status updates.

Implement Link-Jumping / Page-Scrolling navigation logic via short UP/DOWN presses.

Implement Status Bar (Wi-Fi, Battery %, Sleep indicator).

Add On-Screen Keyboard for input.

Integrate Custom Fonts (writer.py library) for improved readability.

Audible feedback (beeps) on button presses.

### Functionality:

Wi-Fi Management: Scan, select, save/load credentials via on-screen keyboard (Long Press UP).

Search Function: Navigate to search engine, use on-screen keyboard (Long Press DOWN).

Bookmarks: Save current URL (Long Press RIGHT), Load/navigate bookmarks menu (Long Press LEFT).

Sleep/Wake: Light sleep on inactivity (wake on any button), Deep sleep sequence (via Long Press or combination), save/restore state on wake from deep sleep.

Improved handling of different Gemini status codes (redirects, input prompts).

Handle non-Gemini URLs more gracefully.

Display startup/shutdown logos and tunes.

## Future / Stretch Goals:

True streaming reader for arbitrarily large documents.

Support for displaying inline images (with inversion fix).

Gemini client certificate ("Identity") support.

