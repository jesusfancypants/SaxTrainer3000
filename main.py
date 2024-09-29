import tkinter as tk
import random
import json
import pygame
import os
from tkinter import ttk
from PIL import Image, ImageTk

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
last_note = None # Keep track of the last displayed note
main_colour = "#323232"
debug_terminal = None
last_timer_mode = 'bpm'

def init_jsons() -> list:
    # Construct full paths to the JSON files
    notes_path = os.path.join(BASE_DIR, 'notes.json')
    resources_path = os.path.join(BASE_DIR, 'resources.json')
    # Load the JSON files
    with open(notes_path, 'r') as file:
        notes = json.load(file)
    with open(resources_path, 'r') as file:
        resources = json.load(file)
    return [notes, resources]

def get_selected_octaves() -> list:
    octaves = []
    if octave_3.get():
        octaves.append(3)
    if octave_4.get():
        octaves.append(4)
    if octave_5.get():
        octaves.append(5)
    if octave_6.get():
        octaves.append(6)
    return octaves

def prepare_notes(notes: dict, type: str, octaves: list, include_natural: bool, include_sharp: bool, include_enharmonic: bool) -> list:
    picked_notes = []
    for octave in octaves:
        for note in notes[type]["Octave"]:
            if note["name"] == octave:
                if include_natural:
                    picked_notes.extend([n for n in note["natural"]])
                if include_sharp:
                    picked_notes.extend([n for n in note["sharp"]])
                if include_enharmonic:
                    picked_notes.extend([n for n in note["enharmonic"]])
    return picked_notes

def get_resources(resources: dict, picked_notes: list, type: str) -> list:
    available_notes = []
    for picked_note in picked_notes:
        try:
            fcharts = ''
            fchart_path = ''
            fcharts = resources[type][picked_note]["finger_chart"].split(';')
            if alternate_fcharts.get():
                fchart_path = random.choice(fcharts)
            else:
                fchart_path = fcharts[0]
            note_data = {"note": picked_note, "finger_chart": fchart_path, "audio": resources[type][picked_note]["audio"]}
            available_notes.append(note_data)
        except KeyError:
            available_notes.append({"note": picked_note})
            log_debug_message(f'Warning: Not found resources for {picked_note}. Skipping.')
    return available_notes


def update_notes(notes_data, resources_data, octaves, include_natural, include_sharp, include_enharmonic):
    # Prepare and update the notes based on the current flag states
    selected_octaves = get_selected_octaves()
    picked_notes = prepare_notes(notes_data, "Alto", selected_octaves, include_natural.get(), include_sharp.get(), include_enharmonic.get())
    available_notes = get_resources(resources_data, picked_notes, "Alto")
    return available_notes

# Function to log debug messages
def log_debug_message(message):
    if debug_terminal is not None and debug_mode.get():
        debug_terminal.config(state='normal')
        debug_terminal.insert(tk.END, message + '\n')
        debug_terminal.config(state='disabled')
        debug_terminal.see(tk.END)

def start_gui(notes_data, resources_data):
    global click_enabled, note_sound, debug_terminal, debug_mode, \
           timer_running, timer_speed, timer_button, window, \
           octave_3, octave_4, octave_5, octave_6, fchart_enabled, \
           alternate_fcharts, show_note_label, dim_note_label, \
           backtrack_enabled
    
    # Tkinter setup
    window = tk.Tk()
    window.title("Saxophonator 3000")
    window.iconbitmap('icon.ico')
    window.config(bg=main_colour)
    # icon = tk.PhotoImage(file='icon.png')
    # window.iconphoto(True, icon)
    style = ttk.Style()
    style.configure("TButton", background=main_colour, foreground="black", font=("Helvetica", 14))

    # Set the window size to 300x400
    window.geometry("250x200")

    # Variables for menu options
    debug_mode = tk.BooleanVar(value=False)
    click_enabled = tk.BooleanVar(value=False)
    fchart_enabled = tk.BooleanVar(value=True)
    show_note_label = tk.BooleanVar(value=True)
    dim_note_label = tk.BooleanVar(value=False)
    alternate_fcharts = tk.BooleanVar(value=False)
    backtrack_enabled = tk.BooleanVar(value=False)
    # note choices
    include_natural = tk.BooleanVar(value=True)
    include_sharp = tk.BooleanVar(value=False)
    include_enharmonic = tk.BooleanVar(value=False)

    # octave choices
    octave_3 = tk.BooleanVar(value=False)
    octave_4 = tk.BooleanVar(value=True)
    octave_5 = tk.BooleanVar(value=False)
    octave_6 = tk.BooleanVar(value=False)

    # Mode variables
    timer_running = False
    timer_speed_bpm = tk.IntVar(value=12)
    timer_speed_seconds = tk.DoubleVar(value=5)
    note_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, 'sounds', 'click_01.wav'))

    def toggle_timer():
        global timer_running
        if timer_running:
            timer_running = False
            timer_button.config(text="Start timer")
            window.after_cancel(timer_id)  # Stop the timer
        else:
            timer_running = True
            timer_button.config(text="Stop")
            run_timer()

    def run_timer():
        global timer_running, timer_id, last_timer_mode
        if timer_running:
            # Adjust interval based on last updated mode
            if last_timer_mode == 'bpm':
                interval = int(60000 / timer_speed_bpm.get())  # BPM to milliseconds
            else:  # 'seconds' mode
                interval = int(timer_speed_seconds.get() * 1000)  # Seconds to milliseconds

            display_note(available_notes)
            timer_id = window.after(interval, run_timer)  # Recursive call to keep the timer running

    # Function to open a new window for setting the timer speed (in bpm)
    def open_bpm_timer_settings():
        global last_timer_mode
        settings_window = tk.Toplevel(window)  # Create a new window
        settings_window.title("Set timer speed (BPM)")
        settings_window.geometry("300x100")

        # Convert seconds to BPM if the last mode was 'seconds'
        if last_timer_mode == 'seconds':
            bpm_value = int(60 / timer_speed_seconds.get())
            timer_speed_bpm.set(bpm_value)

        # Timer speed slider inside the new window
        timer_speed_slider = tk.Scale(settings_window, from_=6, to=220,
                                    orient=tk.HORIZONTAL, variable=timer_speed_bpm,
                                    resolution=1, length=200)
        timer_speed_slider.pack(pady=20)

        # Update the last timer mode to BPM when this window is used
        last_timer_mode = 'bpm'
        # print(f"timer_speed bpm: {timer_speed_bpm.get()}")

    # Function to open a new window for setting the timer speed (in seconds)
    def open_s_timer_settings():
        global last_timer_mode
        settings_window = tk.Toplevel(window)  # Create a new window
        settings_window.title("Set timer speed (seconds)")
        settings_window.geometry("300x100")

        # Convert BPM to seconds if the last mode was 'bpm'
        if last_timer_mode == 'bpm':
            seconds_value = 60 / timer_speed_bpm.get()
            timer_speed_seconds.set(seconds_value)

        # Timer speed slider inside the new window
        timer_speed_slider = tk.Scale(settings_window, from_=1, to=20,
                                    orient=tk.HORIZONTAL, variable=timer_speed_seconds,
                                    resolution=1, length=200)
        timer_speed_slider.pack(pady=20)

        # Update the last timer mode to seconds when this window is used
        last_timer_mode = 'seconds'
        # print(f"timer_speed seconds: {timer_speed_seconds.get()}")

    def play_audio(note_audio_file):
        try:
            pygame.mixer.music.load(note_audio_file)  # Load the audio file
            pygame.mixer.music.play()  # Play the audio file
        except pygame.error as e:
            log_debug_message(f"Error playing audio: {e}")

    def stop_audio():
        if pygame.mixer.music.get_busy():  # Check if any audio is playing
            pygame.mixer.music.stop()
            log_debug_message("Audio stopped")

    def display_note(available_notes: list):
        global last_note
        try:
            if not available_notes:  # Check if available_notes is empty
                if debug_mode.get():
                    log_debug_message(f'Error: No note types were chosen.')
                return  # Exit the function if there are no notes to choose from

            # Assign note before entering while loop
            note = random.choice(available_notes)
            if alternate_fcharts.get():
                refresh_notes()
                # print(f'refreshing {note['finger_chart']}, picking {random.choice(note['finger_chart'].split(';'))}')
            else:
                note = random.choice(available_notes)  # Assign note before entering while loop


            if debug_mode.get():
                log_debug_message(f"Info: Displayed note: {note['note']}, Last note: {last_note}")
            
            # Ensure note is different from the last_note
            while note["note"] == last_note:
                note = random.choice(available_notes)

            if click_enabled.get():  # Use the actual value of the BooleanVar
                note_sound.play()
            else:
                note_sound.stop()  # Stop the sound when the metronome is disabled

            # label.config(text=note["note"])
            if show_note_label.get():
                if dim_note_label.get():
                    label.config(text=note["note"], bg=main_colour, fg='#424242', font=('Helvetica', 32))
                else:
                    label.config(text=note["note"], bg=main_colour, fg='white', font=('Helvetica', 32))
            else:
                label.config(text='', bg=main_colour, fg='white', font=('Helvetica', 32))
            last_note = note["note"]
        
        except IndexError:
            if debug_mode.get():
                log_debug_message(f'Error: No note types were chosen.')

        if fchart_enabled.get():
            try:
                fchart_path = note["finger_chart"]
                window.geometry("250x550")

                # Clear any existing image widgets before displaying the new one
                for widget in window.winfo_children():
                    if isinstance(widget, tk.Label) and widget != label:
                        widget.destroy()

                # Load the image using PIL
                try:
                    img = Image.open(fchart_path)
                    # Get window size and resize the image to fit the window
                    window_width = 180
                    window_height = 420
                    img = img.resize((window_width, window_height), Image.Resampling.LANCZOS)  # Use LANCZOS instead of ANTIALIAS

                    # Convert the PIL image to a PhotoImage to display in tkinter
                    fchart_img = ImageTk.PhotoImage(img)

                    # Display the fingering chart
                    fchart_label = tk.Label(window, image=fchart_img, bg=main_colour)
                    fchart_label.image = fchart_img  # Keep a reference to avoid garbage collection
                    fchart_label.pack(pady=10)
                except FileNotFoundError:
                    log_debug_message(f'no image for {note['note']}')

            except KeyError:
                if debug_mode.get():
                    log_debug_message(f"Error: No fingering chart available for {note['note']}")
        else:
            # Clear the window if no fingering chart is shown
            for widget in window.winfo_children():
                if isinstance(widget, tk.Label) and widget != label:
                    widget.destroy()

            # Reset the window size when fingering chart is disabled
            window.geometry("200x200")  # Default window size
        
        if backtrack_enabled.get():
            play_audio(note['audio'])  # Play audio if enabled
        else:
            stop_audio()  # Stop the audio if backtrack is disabled

    # Function to update available notes whenever flags are changed
    def refresh_notes():
        # print('refresh')
        global available_notes
        selected_octaves = get_selected_octaves()
        available_notes = update_notes(notes_data, resources_data, selected_octaves, include_natural, include_sharp, include_enharmonic)
        # print(len(available_notes))
    
    def open_about_window():
        about_window = tk.Toplevel()  # Create a new window
        about_window.title("About Saxonator 3000")
        about_window.geometry("500x200")  # Set window size
        
        with open('license.txt', 'r') as file:
            file_content = file.read()
        # About information
        about_text = file_content

        # Create a Text widget for selectable and copyable text
        text_widget = tk.Text(about_window, wrap="word", padx=10, pady=10)
        text_widget.insert(tk.END, about_text)
        text_widget.config(state="disabled")  # Make the text read-only, but selectable
        text_widget.pack(expand=True, fill="both")
    
    # Function to toggle the debug terminal in a separate window
    def toggle_debug_terminal():
        global debug_terminal, debug_terminal_window

        if debug_mode.get():
            # If debug mode is enabled, create a new window for the debug terminal
            if debug_terminal is None:
                debug_terminal_window = tk.Toplevel(window)  # Create new window for debug terminal
                debug_terminal_window.title("Debug Console")
                debug_terminal_window.geometry("400x200")
                debug_terminal_window.protocol("WM_DELETE_WINDOW", lambda: toggle_debug_terminal())  # Handle close event

                # Create the Text widget for displaying debug messages
                debug_terminal = tk.Text(debug_terminal_window, height=10, state='disabled')  # Set the height
                debug_terminal.pack(fill=tk.BOTH, expand=True)
            else:
                debug_terminal_window.deiconify()  # Show the window again if it was hidden
        else:
            # If debug mode is disabled, destroy the debug terminal window if it exists
            if debug_terminal is not None:
                debug_terminal_window = debug_terminal.winfo_toplevel()
                debug_terminal_window.withdraw()  # Hide the window instead of destroying it
                debug_terminal = None  # Reset debug_terminal to None

    # Menu bar setup
    menubar = tk.Menu(window)

    # Note settings tab
    note_menu = tk.Menu(menubar, tearoff=0)

    # Adding checkable items to the Note settings tab
    note_menu.add_checkbutton(label="Include natural", onvalue=True, offvalue=False, variable=include_natural, command=refresh_notes)
    note_menu.add_checkbutton(label="Include sharp", onvalue=True, offvalue=False, variable=include_sharp, command=refresh_notes)
    note_menu.add_checkbutton(label="Include enharmonic", onvalue=True, offvalue=False, variable=include_enharmonic, command=refresh_notes)

    # Add Note settings tab to menu bar
    menubar.add_cascade(label="Notes", menu=note_menu)

    octave_menu = tk.Menu(menubar, tearoff=0)
    # Adding checkable items to the Note settings tab
    octave_menu.add_checkbutton(label="Third", onvalue=True, offvalue=False, variable=octave_3, command=refresh_notes)
    octave_menu.add_checkbutton(label="Fourth", onvalue=True, offvalue=False, variable=octave_4, command=refresh_notes)
    octave_menu.add_checkbutton(label="Fifth", onvalue=True, offvalue=False, variable=octave_5, command=refresh_notes)
    octave_menu.add_checkbutton(label="Sixth", onvalue=True, offvalue=False, variable=octave_6, command=refresh_notes)

    # Add Note settings tab to menu bar
    menubar.add_cascade(label="Octaves", menu=octave_menu)

    # Timer tab in the menu
    mode_menu = tk.Menu(menubar, tearoff=0)

    # Adding radio buttons to the menu for mutual exclusivity
    mode_menu.add_command(label="Set timer speed (BPM)", command=open_bpm_timer_settings)
    mode_menu.add_command(label="Set timer speed (s)", command=open_s_timer_settings)

    menubar.add_cascade(label="Timers", menu=mode_menu)

    # Settings tab for debug flag
    settings_menu = tk.Menu(menubar, tearoff=0)
    settings_menu.add_checkbutton(label="Enable metronome", onvalue=True, offvalue=False, variable=click_enabled)
    settings_menu.add_checkbutton(label="Show fingering chart", onvalue=True, offvalue=False, variable=fchart_enabled)
    settings_menu.add_checkbutton(label="Enable alternative fingering charts", onvalue=True, offvalue=False, variable=alternate_fcharts)
    settings_menu.add_checkbutton(label="Enable backtrack", onvalue=True, offvalue=False, variable=backtrack_enabled)
    settings_menu.add_checkbutton(label="Show note label", onvalue=True, offvalue=False, variable=show_note_label)
    settings_menu.add_checkbutton(label="Dim note label", onvalue=True, offvalue=False, variable=dim_note_label)
    settings_menu.add_checkbutton(label="Enable debug", onvalue=True, offvalue=False, variable=debug_mode, command=toggle_debug_terminal)

    # Add Settings tab to menu bar
    menubar.add_cascade(label="Settings", menu=settings_menu)

    # Adding the About menu to the menu bar
    help_menu = tk.Menu(menubar, tearoff=0)
    help_menu.add_command(label="About", command=open_about_window)
    menubar.add_cascade(label="Help", menu=help_menu)

    # Display the menu bar in the window
    window.config(menu=menubar)

    # Display area for notes
    global label
    label = tk.Label(window, text="Press space", bg=main_colour, fg="white", font=("Helvetica", 32))
    label.pack(pady=5)

    # Create a frame to hold the buttons
    button_frame = tk.Frame(window, bg=main_colour)
    button_frame.pack(side=tk.BOTTOM, pady=10)

    # Create and pack the "Next Note" button inside the same frame
    button = ttk.Button(button_frame, text="Next Note", command=lambda: display_note(available_notes), style="TButton")
    button.pack(side=tk.LEFT, padx=5)
    button['takefocus'] = 0

    # Create and pack the timer button inside the frame
    timer_button = ttk.Button(button_frame, text="Start timer", command=toggle_timer, style="TButton")
    timer_button.pack(side=tk.RIGHT, padx=5)


    # Bind the spacebar key to the button's action
    window.bind("<space>", lambda event: (display_note(available_notes), 'break'))

    # Initial note calculation based on default flags
    refresh_notes()

    window.mainloop()

if __name__ == "__main__":
    pygame.mixer.init()
    data = init_jsons()  # Load JSON data for notes and resources
    start_gui(data[0], data[1])  # Start the GUI
