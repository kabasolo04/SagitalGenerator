import os
import sys
import json
import math
import colorsys
import numpy as np

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# PASTEL COLOR PALETTE
COLOR_BG = "#F4F6F9"         # Soft light blue-gray background
COLOR_CARD = "#FFFFFF"       # Pure white for cards
COLOR_TEXT = "#2D3748"       # Elegant dark gray for text
COLOR_MUTED = "#718096"      # Secondary gray

# Pastel button colors
COLOR_PRIMARY_BG = "#B3C5FF" # Pastel lavender blue
COLOR_PRIMARY_FG = "#1A237E"
COLOR_SUCCESS_BG = "#C8E6C9" # Pastel mint green
COLOR_SUCCESS_FG = "#1B5E20"
COLOR_PURPLE_BG = "#E1BEE7"  # Pastel purple for PNG Export
COLOR_PURPLE_FG = "#4A148C"
COLOR_DANGER_BG = "#FFCDD2"  # Pastel pink
COLOR_DANGER_FG = "#B71C1C"
COLOR_DEFAULT_BTN = "#E2E8F0"# Soft slate gray
COLOR_LOOP_ARROW = "#E57373" # Soft pastel red for self-loops


def val_to_hex(val):
    """Converts slider value (0-100) to hex color. 0 = Black (#000000)."""
    val = float(val)
    if val <= 0:
        return "#000000"
    h = (val - 1.0) / 99.0
    h = max(0.0, min(1.0, h))
    r, g, b = colorsys.hsv_to_rgb(h, 0.75, 0.85)
    return f"#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}"


def hex_to_val(hex_str):
    """Converts hex color string back to closest slider value (0-100)."""
    if not hex_str or hex_str.lower() in ("#000000", "#000"):
        return 0.0
    try:
        hex_str = hex_str.lstrip("#")
        r = int(hex_str[0:2], 16) / 255.0
        g = int(hex_str[2:4], 16) / 255.0
        b = int(hex_str[4:6], 16) / 255.0
        h, s, v = colorsys.rgb_to_hsv(r, g, b)
        if v < 0.15:
            return 0.0
        return 1.0 + h * 99.0
    except Exception:
        return 0.0


class GradientColorSlider(tk.Canvas):
    """Custom slider widget with a visible color gradient background spectrum."""
    def __init__(self, master, width=220, height=22, initial_val=0, command=None, **kwargs):
        super().__init__(
            master, width=width, height=height, 
            highlightthickness=1, highlightbackground="#CBD5E0", 
            cursor="hand2", **kwargs
        )
        self.slider_width = width
        self.slider_height = height
        self.val = initial_val
        self.command = command

        self.bind("<B1-Motion>", self._on_drag)
        self.bind("<Button-1>", self._on_drag)

        self.draw_spectrum()
        self.set(initial_val)

    def draw_spectrum(self):
        """Draws the color spectrum directly onto the slider track."""
        for x in range(self.slider_width):
            val = (x / max(1, self.slider_width - 1)) * 100.0
            color = val_to_hex(val)
            self.create_line(x, 0, x, self.slider_height, fill=color)

    def draw_thumb(self):
        """Draws the indicator thumb position over the gradient."""
        self.delete("thumb")
        x = (self.val / 100.0) * (self.slider_width - 1)
        self.create_rectangle(
            x - 3, 0, x + 3, self.slider_height,
            fill="#FFFFFF", outline="#1A202C", width=1.5, tags="thumb"
        )

    def _on_drag(self, event):
        x = max(0, min(self.slider_width - 1, event.x))
        self.val = (x / (self.slider_width - 1)) * 100.0
        self.draw_thumb()
        if self.command:
            self.command(self.val)

    def set(self, val):
        self.val = max(0.0, min(100.0, float(val)))
        self.draw_thumb()


def draw_loop(ax, x, y, angle_rad=-np.pi/2, color=COLOR_LOOP_ARROW, label=""):
    """Draws a curved self-referential loop for an element connected to itself."""
    dir_x, dir_y = np.cos(angle_rad), np.sin(angle_rad)
    perp_x, perp_y = -np.sin(angle_rad), np.cos(angle_rad)

    offset_radial = 0.08
    offset_perp = 0.14

    start_x = x + dir_x * offset_radial - perp_x * offset_perp
    start_y = y + dir_y * offset_radial - perp_y * offset_perp

    end_x = x + dir_x * offset_radial + perp_x * offset_perp
    end_y = y + dir_y * offset_radial + perp_y * offset_perp

    ax.annotate(
        '', xy=(end_x, end_y), xytext=(start_x, start_y),
        arrowprops=dict(
            arrowstyle="->,head_width=0.25,head_length=0.4",
            color=color,
            lw=1.5,
            connectionstyle="arc3,rad=2.2"
        ),
        zorder=3
    )

    if label:
        lbl_x = x + dir_x * 0.65
        lbl_y = y + dir_y * 0.65
        ax.text(lbl_x, lbl_y, label, fontsize=9, color=color, ha='center', va='center', fontweight='bold')


class SagittalCreatorMinimal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Sagittal Diagram Creator")
        self.geometry("1180x740")
        self.configure(bg=COLOR_BG)

        # Configure TTK pastel styles
        self.setup_styles()

        # Initial default data (black #000000)
        self.diagram_title = ""
        self.sets_data = [
            {"id": "set_1", "name": "A", "elements": ["1", "2", "3", "4"], "color": "#000000"},
            {"id": "set_2", "name": "B", "elements": ["a", "b", "c"], "color": "#000000"}
        ]
        self.relations_data = [
            {"from_set": "set_1", "from": "1", "to_set": "set_2", "to": "a"},
            {"from_set": "set_1", "from": "2", "to_set": "set_2", "to": "b"}
        ]

        self.selected_node = None     # (set_id, elem_id)
        self.node_positions = {}      # (set_id, elem_id) -> (x, y)
        self.title_positions = {}     # set_id -> (x, y)

        self.create_layout()
        self.redraw_diagram()

    def setup_styles(self):
        """Configures global TTK styles with pastel tones."""
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 10))
        self.style.configure("TFrame", background=COLOR_BG)
        self.style.configure("Card.TFrame", background=COLOR_CARD, relief="flat")
        self.style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT)
        self.style.configure("Help.TLabel", background=COLOR_CARD, foreground=COLOR_MUTED, font=("Segoe UI", 9, "italic"))

        self.style.configure("TButton", font=("Segoe UI", 10, "bold"), background=COLOR_DEFAULT_BTN, 
                             foreground=COLOR_TEXT, borderwidth=0, focuscolor="none", padding=6)
        self.style.map("TButton", background=[("active", "#CBD5E0")])

        self.style.configure("Primary.TButton", background=COLOR_PRIMARY_BG, foreground=COLOR_PRIMARY_FG)
        self.style.map("Primary.TButton", background=[("active", "#9FA8DA")])

        self.style.configure("Success.TButton", background=COLOR_SUCCESS_BG, foreground=COLOR_SUCCESS_FG)
        self.style.map("Success.TButton", background=[("active", "#A5D6A7")])

        self.style.configure("Purple.TButton", background=COLOR_PURPLE_BG, foreground=COLOR_PURPLE_FG)
        self.style.map("Purple.TButton", background=[("active", "#D1C4E9")])

        self.style.configure("Danger.TButton", background=COLOR_DANGER_BG, foreground=COLOR_DANGER_FG)
        self.style.map("Danger.TButton", background=[("active", "#EF9A9A")])

        self.style.configure("TEntry", fieldbackground="#F8FAFC", borderwidth=1, padding=5)

    def _generate_unique_id(self):
        idx = 1
        existing_ids = {s["id"] for s in self.sets_data}
        while f"set_{idx}" in existing_ids:
            idx += 1
        return f"set_{idx}"

    def _get_default_filename(self, extension=".json", prefix="diagram"):
        idx = 1
        filename = f"{prefix}_{idx}{extension}"
        while os.path.exists(filename):
            idx += 1
            filename = f"{prefix}_{idx}{extension}"
        return filename

    def create_layout(self):
        toolbar_card = ttk.Frame(self, style="Card.TFrame", padding=10)
        toolbar_card.pack(side="top", fill="x", padx=15, pady=(15, 5))

        left_group = ttk.Frame(toolbar_card, style="Card.TFrame")
        left_group.pack(side="left", fill="y")

        btn_new_set = ttk.Button(left_group, text="+ Add Set", style="Primary.TButton", command=self.open_new_set_dialog)
        btn_new_set.pack(side="left", padx=(0, 10))

        ttk.Label(left_group, text="Title:", background=COLOR_CARD, font=("Segoe UI", 9, "bold")).pack(side="left", padx=(5, 2))
        self.title_var = tk.StringVar(value=self.diagram_title)
        self.title_var.trace_add("write", self.on_title_change)
        entry_title = ttk.Entry(left_group, textvariable=self.title_var, width=18)
        entry_title.pack(side="left", padx=(0, 15))

        file_group = ttk.Frame(toolbar_card, style="Card.TFrame")
        file_group.pack(side="right", fill="y")

        separator = ttk.Separator(toolbar_card, orient="vertical")
        separator.pack(side="right", fill="y", padx=15)

        btn_open = ttk.Button(file_group, text="📂 Open", style="TButton", command=self.open_json)
        btn_open.pack(side="left", padx=3)

        btn_save = ttk.Button(file_group, text="💾 Save", style="Success.TButton", command=self.save_json)
        btn_save.pack(side="left", padx=3)

        btn_export = ttk.Button(file_group, text="🖼️ PNG", style="Purple.TButton", command=self.export_png)
        btn_export.pack(side="left", padx=(3, 0))

        canvas_card = ttk.Frame(self, style="Card.TFrame", padding=10)
        canvas_card.pack(side="top", fill="both", expand=True, padx=15, pady=(5, 15))

        self.fig = plt.Figure(figsize=(8, 6), dpi=100, facecolor=COLOR_CARD)
        self.canvas = FigureCanvasTkAgg(self.fig, master=canvas_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.canvas.mpl_connect('button_press_event', self.on_canvas_click)

    def on_title_change(self, *args):
        self.diagram_title = self.title_var.get()
        self.redraw_diagram()

    def on_canvas_click(self, event):
        if event.xdata is None or event.ydata is None:
            return

        click_x, click_y = event.xdata, event.ydata

        for set_id, (tx, ty) in self.title_positions.items():
            if math.hypot(tx - click_x, ty - click_y) < 0.8:
                self.selected_node = None
                self.open_edit_set_dialog(set_id)
                return

        clicked_node = None
        min_dist = float("inf")

        for (set_id, elem_id), (nx, ny) in self.node_positions.items():
            dist = math.hypot(nx - click_x, ny - click_y)
            if dist < 0.4 and dist < min_dist:
                min_dist = dist
                clicked_node = (set_id, elem_id)

        if clicked_node:
            if self.selected_node is None:
                self.selected_node = clicked_node
            else:
                src_set, src_elem = self.selected_node
                dst_set, dst_elem = clicked_node

                existing_idx = None
                default_src_set = self.sets_data[0]["id"] if self.sets_data else "set_1"
                default_dst_set = self.sets_data[-1]["id"] if self.sets_data else "set_2"

                for idx, rel in enumerate(self.relations_data):
                    r_fset = rel.get("from_set", default_src_set)
                    r_tset = rel.get("to_set", default_dst_set)
                    if (r_fset == src_set and str(rel.get("from")) == str(src_elem) and
                        r_tset == dst_set and str(rel.get("to")) == str(dst_elem)):
                        existing_idx = idx
                        break

                if existing_idx is not None:
                    del self.relations_data[existing_idx]
                else:
                    self.relations_data.append({
                        "from_set": src_set,
                        "from": src_elem,
                        "to_set": dst_set,
                        "to": dst_elem
                    })

                self.selected_node = None
        else:
            self.selected_node = None

        self.redraw_diagram()

    def redraw_diagram(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(COLOR_CARD)
        self.node_positions.clear()
        self.title_positions.clear()

        if self.diagram_title.strip():
            ax.set_title(self.diagram_title.strip(), fontsize=16, fontweight='bold', color=COLOR_TEXT, pad=15)

        num_sets = len(self.sets_data)
        if num_sets == 0:
            ax.text(0.5, 0.5, "Click '+ Add Set' to start", ha='center', va='center', fontsize=12, color=COLOR_MUTED)
            ax.axis('off')
            self.canvas.draw()
            return

        # MODE: 1 SET (Radial Cloud)
        if num_sets == 1:
            s = self.sets_data[0]
            elements = s.get("elements", [])
            color = s.get("color", "#000000")
            name = s.get("name", "Set 1")

            n = len(elements)
            radius = 3.0
            angles = np.linspace(0, 2 * np.pi, n, endpoint=False) if n > 0 else []

            for i, elem in enumerate(elements):
                angle = angles[i] + np.pi / 2
                x = radius * np.cos(angle)
                y = radius * np.sin(angle)
                self.node_positions[(s["id"], str(elem))] = (x, y)

                if self.selected_node == (s["id"], str(elem)):
                    ax.plot(x, y, 'o', color='#FFB74D', markersize=16, zorder=3, alpha=0.6)

                ax.plot(x, y, 'o', color=color, markersize=8, zorder=4)
                off_x = 0.45 * np.cos(angle)
                off_y = 0.45 * np.sin(angle)
                ax.text(x + off_x, y + off_y, str(elem), fontsize=12, fontweight='bold',
                        ha='center', va='center', color=COLOR_TEXT, zorder=5)

            title_y = radius + 1.1
            ax.text(0, title_y, name, fontsize=14, fontweight='bold', ha='center', color=color)
            self.title_positions[s["id"]] = (0, title_y)

            for rel in self.relations_data:
                src, dst = str(rel.get("from")), str(rel.get("to"))
                lbl = rel.get("label", "")
                k_src, k_dst = (s["id"], src), (s["id"], dst)

                if k_src in self.node_positions and k_dst in self.node_positions:
                    x1, y1 = self.node_positions[k_src]
                    x2, y2 = self.node_positions[k_dst]
                    idx_src = elements.index(src) if src in elements else 0
                    ang_src = angles[idx_src] + np.pi / 2

                    if src == dst:
                        ang_loop = ang_src + np.radians(45)
                        draw_loop(ax, x1, y1, angle_rad=ang_loop, color=COLOR_LOOP_ARROW, label=lbl)
                    else:
                        ax.annotate(
                            '', xy=(x2, y2), xytext=(x1, y1),
                            arrowprops=dict(
                                arrowstyle="->,head_width=0.25,head_length=0.4",
                                color="#4A5568", lw=1.5, shrinkA=9, shrinkB=9, connectionstyle="arc3,rad=-0.2"
                            ),
                            zorder=2
                        )
                        if lbl:
                            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                            ax.text(mid_x, mid_y, lbl, fontsize=9, color=COLOR_MUTED, ha='center')

            ax.set_aspect('equal')
            ax.axis('off')
            ax.set_xlim(-radius - 1.5, radius + 1.5)
            ax.set_ylim(-radius - 1.5, radius + 1.5)

        # MODE: 2+ SETS (Vertical Ellipses)
        else:
            y_spacing, x_spacing, x_start = 1.2, 4.0, 2.0
            max_elems = max((len(s.get("elements", [])) for s in self.sets_data), default=1)
            height = max(max_elems * y_spacing + 1.5, 3)
            y_center = 0

            for idx, s in enumerate(self.sets_data):
                set_id = s.get("id", str(idx))
                set_name = s.get("name", set_id)
                elements = s.get("elements", [])
                color = s.get("color", "#000000")
                x_pos = x_start + idx * x_spacing

                ellipse = patches.Ellipse(
                    (x_pos, y_center), width=2.4, height=height,
                    edgecolor=color, facecolor=color + '12', linewidth=2, zorder=1
                )
                ax.add_patch(ellipse)

                title_y = y_center + height/2 + 0.35
                ax.text(x_pos, title_y, set_name, fontsize=13, fontweight='bold', ha='center', color=color)
                self.title_positions[set_id] = (x_pos, title_y)

                if elements:
                    y_start = y_center + (len(elements) - 1) * y_spacing / 2
                    for i, elem in enumerate(elements):
                        y_elem = y_start - i * y_spacing
                        self.node_positions[(set_id, str(elem))] = (x_pos, y_elem)

                        if self.selected_node == (set_id, str(elem)):
                            ax.plot(x_pos, y_elem, 'o', color='#FFB74D', markersize=14, zorder=3, alpha=0.6)

                        ax.plot(x_pos, y_elem, 'o', color=color, markersize=6, zorder=3)

                        if idx == 0:
                            ax.text(x_pos - 0.25, y_elem, str(elem), fontsize=11, ha='right', va='center', fontweight='bold', zorder=3)
                        elif idx == num_sets - 1:
                            ax.text(x_pos + 0.25, y_elem, str(elem), fontsize=11, ha='left', va='center', fontweight='bold', zorder=3)
                        else:
                            ax.text(x_pos, y_elem + 0.25, str(elem), fontsize=11, ha='center', va='bottom', fontweight='bold', zorder=3)

            for rel in self.relations_data:
                from_set = str(rel.get("from_set", self.sets_data[0].get("id")))
                to_set = str(rel.get("to_set", self.sets_data[-1].get("id")))
                src, dst = str(rel.get("from")), str(rel.get("to"))
                lbl = rel.get("label", "")

                k_src, k_dst = (from_set, src), (to_set, dst)
                if k_src in self.node_positions and k_dst in self.node_positions:
                    start = self.node_positions[k_src]
                    end = self.node_positions[k_dst]

                    if from_set == to_set and src == dst:
                        draw_loop(ax, start[0], start[1], angle_rad=-np.pi/2, color=COLOR_LOOP_ARROW, label=lbl)
                    else:
                        is_forward = start[0] <= end[0]
                        rad = -0.25
                        
                        dx_start = 0.15 if start[0] < end[0] else (-0.15 if start[0] > end[0] else 0)
                        dx_end = -0.15 if start[0] < end[0] else (0.15 if start[0] > end[0] else 0)

                        ax.annotate(
                            '', xy=(end[0] + dx_end, end[1]), xytext=(start[0] + dx_start, start[1]),
                            arrowprops=dict(
                                arrowstyle="->,head_width=0.25,head_length=0.4",
                                color="#4A5568", lw=1.5, connectionstyle=f"arc3,rad={rad}"
                            ),
                            zorder=2
                        )
                        if lbl:
                            mid_x = (start[0] + end[0]) / 2
                            offset_y = 0.35 if is_forward else -0.35
                            mid_y = (start[1] + end[1]) / 2 + offset_y
                            ax.text(mid_x, mid_y, lbl, fontsize=9, color=COLOR_MUTED, ha='center', va='center')

            ax.set_aspect('equal')
            ax.axis('off')
            x_max = x_start + (num_sets - 1) * x_spacing
            padding_y = height / 2 + 1.2
            ax.set_xlim(0, x_max + 2.5)
            ax.set_ylim(-padding_y, padding_y)

        self.fig.tight_layout()
        self.canvas.draw()

    def open_edit_set_dialog(self, set_id):
        set_obj = next((s for s in self.sets_data if s["id"] == set_id), None)
        if not set_obj:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Edit Set")
        dialog.geometry("360x280")
        dialog.configure(bg=COLOR_CARD)
        dialog.transient(self)

        ttk.Label(dialog, text="Set Display Name:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(15, 2))
        entry_name = ttk.Entry(dialog)
        entry_name.pack(fill="x", padx=20)
        entry_name.insert(0, set_obj.get("name", ""))

        ttk.Label(dialog, text="Elements (comma separated):", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        entry_elems = ttk.Entry(dialog)
        entry_elems.pack(fill="x", padx=20)
        entry_elems.insert(0, ", ".join(set_obj.get("elements", [])))

        current_color = set_obj.get("color", "#000000")
        color_hex = [current_color]
        initial_val = hex_to_val(current_color)

        ttk.Label(dialog, text="Set Color:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        slider_frame = ttk.Frame(dialog, style="Card.TFrame")
        slider_frame.pack(fill="x", padx=20, pady=2)

        color_preview = tk.Frame(slider_frame, width=22, height=22, bg=current_color, highlightbackground="#CBD5E0", highlightthickness=1)
        color_preview.pack(side="left", padx=(0, 8))

        lbl_hex = ttk.Label(slider_frame, text=current_color, background=COLOR_CARD, font=("Segoe UI", 9, "bold"))
        lbl_hex.pack(side="right", padx=(8, 0))

        def on_slider_move(val):
            hex_code = val_to_hex(val)
            color_hex[0] = hex_code
            color_preview.config(bg=hex_code)
            lbl_hex.config(text=hex_code)

        color_slider = GradientColorSlider(
            slider_frame, width=210, height=22, initial_val=initial_val, command=on_slider_move
        )
        color_slider.pack(side="left", fill="x", expand=True)

        frame_btns = ttk.Frame(dialog, style="Card.TFrame")
        frame_btns.pack(fill="x", padx=20, pady=15)

        def delete_this_set():
            target_id = set_obj["id"]
            if messagebox.askyesno("Confirm Deletion", f"Do you want to delete '{set_obj.get('name')}' and its relations?", parent=dialog):
                self.sets_data = [s for s in self.sets_data if s["id"] != target_id]
                self.relations_data = [
                    r for r in self.relations_data 
                    if r.get("from_set") != target_id and r.get("to_set") != target_id
                ]
                self.selected_node = None
                self.redraw_diagram()
                dialog.destroy()

        def save_changes():
            new_name = entry_name.get().strip() or "Untitled"
            raw = entry_elems.get().strip()
            if not raw:
                messagebox.showerror("Error", "Please enter at least one element.", parent=dialog)
                return
            new_elems = [e.strip() for e in raw.split(",") if e.strip()]

            set_obj["name"] = new_name
            set_obj["elements"] = new_elems
            set_obj["color"] = color_hex[0]

            self.redraw_diagram()
            dialog.destroy()

        btn_del = ttk.Button(frame_btns, text="🗑️ Delete Set", style="Danger.TButton", command=delete_this_set)
        btn_del.pack(side="left")

        btn_save = ttk.Button(frame_btns, text="💾 Save", style="Success.TButton", command=save_changes)
        btn_save.pack(side="right")

        dialog.wait_visibility()
        dialog.grab_set()

    def open_new_set_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("New Set")
        dialog.geometry("360x280")
        dialog.configure(bg=COLOR_CARD)
        dialog.transient(self)

        ttk.Label(dialog, text="Set Display Name:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(15, 2))
        entry_name = ttk.Entry(dialog)
        entry_name.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Elements (comma separated):", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        entry_elems = ttk.Entry(dialog)
        entry_elems.pack(fill="x", padx=20)

        color_hex = ["#000000"]

        ttk.Label(dialog, text="Set Color:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        slider_frame = ttk.Frame(dialog, style="Card.TFrame")
        slider_frame.pack(fill="x", padx=20, pady=2)

        color_preview = tk.Frame(slider_frame, width=22, height=22, bg="#000000", highlightbackground="#CBD5E0", highlightthickness=1)
        color_preview.pack(side="left", padx=(0, 8))

        lbl_hex = ttk.Label(slider_frame, text="#000000", background=COLOR_CARD, font=("Segoe UI", 9, "bold"))
        lbl_hex.pack(side="right", padx=(8, 0))

        def on_slider_move(val):
            hex_code = val_to_hex(val)
            color_hex[0] = hex_code
            color_preview.config(bg=hex_code)
            lbl_hex.config(text=hex_code)

        color_slider = GradientColorSlider(
            slider_frame, width=210, height=22, initial_val=0, command=on_slider_move
        )
        color_slider.pack(side="left", fill="x", expand=True)

        def save():
            s_name = entry_name.get().strip() or f"Set {len(self.sets_data)+1}"
            raw = entry_elems.get().strip()

            if not raw:
                messagebox.showerror("Error", "Please enter at least one element.", parent=dialog)
                return

            elems = [e.strip() for e in raw.split(",") if e.strip()]
            s_id = self._generate_unique_id()

            self.sets_data.append({"id": s_id, "name": s_name, "elements": elems, "color": color_hex[0]})
            self.redraw_diagram()
            dialog.destroy()

        frame_btns = ttk.Frame(dialog, style="Card.TFrame")
        frame_btns.pack(fill="x", padx=20, pady=15)

        btn_cancel = ttk.Button(frame_btns, text="Cancel", style="TButton", command=dialog.destroy)
        btn_cancel.pack(side="left")

        btn_accept = ttk.Button(frame_btns, text="➕ Create Set", style="Primary.TButton", command=save)
        btn_accept.pack(side="right")

        dialog.wait_visibility()
        dialog.grab_set()

    def export_png(self):
        if not self.sets_data:
            messagebox.showerror("Error", "No sets available to export.")
            return

        default_png_name = self._get_default_filename(extension=".png", prefix="diagram")
        filepath = filedialog.asksaveasfilename(
            title="Export Diagram as PNG",
            initialfile=default_png_name,
            defaultextension=".png",
            filetypes=[("PNG Image", "*.png"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                self.fig.savefig(filepath, dpi=300, bbox_inches='tight', facecolor=self.fig.get_facecolor())
                messagebox.showinfo("Success", f"Diagram exported successfully to:\n{os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not export PNG image:\n{e}")

    def save_json(self):
        if not self.sets_data:
            messagebox.showerror("Error", "No sets available to save.")
            return

        default_json_name = self._get_default_filename(extension=".json", prefix="diagram")
        filepath = filedialog.asksaveasfilename(
            title="Save JSON File",
            initialfile=default_json_name,
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                config = {
                    "title": self.diagram_title,
                    "sets": self.sets_data,
                    "relations": self.relations_data
                }
                with open(filepath, "w", encoding="utf-8") as f:
                    json.dump(config, f, indent=2, ensure_ascii=False)
                messagebox.showinfo("Success", f"Diagram saved to:\n{os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\n{e}")

    def open_json(self):
        filepath = filedialog.askopenfilename(
            title="Open JSON File",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")]
        )
        if filepath:
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)

                self.diagram_title = data.get("title", "")
                self.title_var.set(self.diagram_title)
                self.sets_data = data.get("sets", [])
                self.relations_data = data.get("relations", [])
                self.selected_node = None
                self.redraw_diagram()
                messagebox.showinfo("Success", f"Diagram loaded successfully:\n{os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open JSON file:\n{e}")


if __name__ == "__main__":
    app = SagittalCreatorMinimal()
    app.mainloop()