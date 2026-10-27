import os
import sys
import json
import math
import colorsys
import numpy as np
from collections import defaultdict

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.path import Path

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


def draw_loop(ax, x, y, angle_rad=-np.pi/2, color=COLOR_LOOP_ARROW, label="", scale=1.0):
    """Draws a round, balloon-shaped self-referential loop with a clear arrowhead separated from the node dot."""
    dir_x, dir_y = np.cos(angle_rad), np.sin(angle_rad)
    perp_x, perp_y = -np.sin(angle_rad), np.cos(angle_rad)

    r_dot_gap = 0.22 * scale
    r_start = 0.15 * scale

    start_x = x + perp_x * r_start + dir_x * r_dot_gap
    start_y = y + perp_y * r_start + dir_y * r_dot_gap

    end_x = x - perp_x * r_start + dir_x * r_dot_gap
    end_y = y - perp_y * r_start + dir_y * r_dot_gap

    r_spread = 0.95 * scale
    r_reach = 1.25 * scale

    c1_x = x + perp_x * r_spread + dir_x * r_reach
    c1_y = y + perp_y * r_spread + dir_y * r_reach

    c2_x = x - perp_x * r_spread + dir_x * r_reach
    c2_y = y - perp_y * r_spread + dir_y * r_reach

    path_data = [
        (Path.MOVETO, (start_x, start_y)),
        (Path.CURVE4, (c1_x, c1_y)),
        (Path.CURVE4, (c2_x, c2_y)),
        (Path.CURVE4, (end_x, end_y))
    ]

    codes, verts = zip(*path_data)
    path = Path(verts, codes)

    patch = patches.FancyArrowPatch(
        path=path,
        arrowstyle="-|>",
        mutation_scale=14 * scale,
        color=color,
        lw=2.0,
        shrinkA=4,
        shrinkB=4,
        zorder=4
    )
    ax.add_patch(patch)

    if label:
        lbl_x = x + dir_x * (r_reach + 0.30 * scale)
        lbl_y = y + dir_y * (r_reach + 0.30 * scale)
        ax.text(lbl_x, lbl_y, label, fontsize=int(9 * scale), color=color, ha='center', va='center', fontweight='bold', zorder=5)


class SagittalCreatorMinimal(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Interactive Sagittal Diagram Creator")
        self.geometry("1180x740")
        self.configure(bg=COLOR_BG)

        self.setup_styles()

        self.sets_data = [
            {"id": "set_1", "name": "A", "elements": ["1", "2", "3", "4"], "color": "#000000", "scale": 1.0},
            {"id": "set_2", "name": "B", "elements": ["a", "b", "c"], "color": "#000000", "scale": 1.0}
        ]
        self.relations_data = [
            {"from_set": "set_1", "from": "1", "to_set": "set_2", "to": "a", "flipped": False},
            {"from_set": "set_1", "from": "2", "to_set": "set_2", "to": "b", "flipped": False}
        ]
        self.text_blocks_data = []

        self.selected_node = None         
        self.node_positions = {}          
        self.label_positions = {}         
        self.custom_node_positions = {}   
        self.custom_set_positions = {}    
        self.custom_label_angles = {}     
        self.title_positions = {}         
        self.text_block_positions = {}    
        self.arrow_midpoints = {}         # rel_idx -> (mid_x, mid_y) for click detection

        # Drag & drop state variables
        self.dragging_node = None
        self.dragging_set = None
        self.dragging_text = None
        self.dragging_label = None        
        self.drag_start_mouse = None
        self.drag_start_node_pos = None
        self.drag_start_set_pos = None
        self.drag_start_text_pos = None
        self.clicked_title = None
        self.clicked_node = None
        self.clicked_text = None
        self.has_dragged = False

        self.create_layout()
        self.redraw_diagram()

    def setup_styles(self):
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

    def _generate_unique_text_id(self):
        idx = 1
        existing_ids = {t["id"] for t in self.text_blocks_data}
        while f"text_{idx}" in existing_ids:
            idx += 1
        return f"text_{idx}"

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
        btn_new_set.pack(side="left", padx=(0, 6))

        btn_new_text = ttk.Button(left_group, text="+ Add Text", style="Primary.TButton", command=self.open_new_text_dialog)
        btn_new_text.pack(side="left", padx=(0, 15))

        lbl_help = ttk.Label(
            left_group,
            text="💡 Drag Nodes/Text | Drag Numbers = Rotate | Click 2 Nodes = Arrow | Click Arrow Curve = Flip side",
            style="Help.TLabel"
        )
        lbl_help.pack(side="left", padx=5)

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

        self.canvas.mpl_connect('button_press_event', self.on_press)
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.mpl_connect('button_release_event', self.on_release)

    # --- MOUSE EVENTS: DRAG & CLICK LOGIC ---
    def on_press(self, event):
        if event.xdata is None or event.ydata is None:
            return

        click_x, click_y = event.xdata, event.ydata

        self.has_dragged = False
        self.drag_start_mouse = (click_x, click_y)
        self.dragging_node = None
        self.dragging_set = None
        self.dragging_text = None
        self.dragging_label = None
        self.clicked_title = None
        self.clicked_node = None
        self.clicked_text = None

        num_sets = len(self.sets_data)

        # 1. Check Set Title Click
        for set_id, (tx, ty) in self.title_positions.items():
            if math.hypot(tx - click_x, ty - click_y) < 0.8:
                self.clicked_title = set_id
                if num_sets > 1:
                    self.dragging_set = set_id
                    self.drag_start_set_pos = self._get_set_center(set_id)
                return

        # 2. Check Free Text Block Click (Rectangular Bounding Box Hitbox)
        for t_obj in self.text_blocks_data:
            tx, ty = t_obj["x"], t_obj["y"]
            fs = float(t_obj.get("fontsize", 12))
            scale_font = fs / 12.0
            text_str = str(t_obj.get("text", ""))
            half_w = max(0.8, len(text_str) * 0.12 * scale_font)
            half_h = max(0.4, 0.35 * scale_font)

            if (tx - half_w <= click_x <= tx + half_w) and (ty - half_h <= click_y <= ty + half_h):
                self.clicked_text = t_obj["id"]
                self.dragging_text = t_obj["id"]
                self.drag_start_text_pos = (tx, ty)
                return

        # 3. Check Element Label Click
        for node_key, (lx, ly) in self.label_positions.items():
            if math.hypot(lx - click_x, ly - click_y) < 0.35:
                self.dragging_label = node_key
                return

        # 4. Check Node Click
        clicked_node = None
        min_dist = float("inf")

        for (set_id, elem_id), (nx, ny) in self.node_positions.items():
            dist = math.hypot(nx - click_x, ny - click_y)
            if dist < 0.35 and dist < min_dist:
                min_dist = dist
                clicked_node = (set_id, elem_id)

        if clicked_node:
            self.clicked_node = clicked_node
            if num_sets == 1:
                self.dragging_node = clicked_node
                self.drag_start_node_pos = self.node_positions.get(clicked_node, (click_x, click_y))
            else:
                s_id = clicked_node[0]
                self.dragging_set = s_id
                self.drag_start_set_pos = self._get_set_center(s_id)
            return

        # 5. Check Arrow Curve Click (TO FLIP CURVATURE SIDE)
        for idx_rel, (mx, my) in self.arrow_midpoints.items():
            if math.hypot(mx - click_x, my - click_y) < 0.45:
                rel = self.relations_data[idx_rel]
                rel["flipped"] = not rel.get("flipped", False)
                self.redraw_diagram()
                return

        # 6. Check Ellipse Click (when 2+ sets)
        if num_sets > 1:
            y_spacing, x_spacing, x_start = 1.2, 4.0, 2.0
            for idx, s in enumerate(self.sets_data):
                s_id = s["id"]
                scale = float(s.get("scale", 1.0))
                max_elems = max((len(s.get("elements", [])) for s in self.sets_data), default=1)
                height = max(max_elems * y_spacing * scale + 1.5 * scale, 3 * scale)
                cx, cy = self._get_set_center(s_id, idx)
                if ((click_x - cx) / (1.2 * scale))**2 + ((click_y - cy) / (height / 2.0))**2 <= 1.0:
                    self.dragging_set = s_id
                    self.drag_start_set_pos = (cx, cy)
                    return

    def _get_set_center(self, set_id, idx=0):
        if set_id in self.custom_set_positions:
            return self.custom_set_positions[set_id]
        x_spacing, x_start = 4.0, 2.0
        for i, s in enumerate(self.sets_data):
            if s["id"] == set_id:
                return (x_start + i * x_spacing, 0.0)
        return (x_start + idx * x_spacing, 0.0)

    def on_drag(self, event):
        if (self.dragging_node is None and self.dragging_set is None and 
            self.dragging_text is None and self.dragging_label is None) or event.xdata is None or event.ydata is None:
            return

        dx = event.xdata - self.drag_start_mouse[0]
        dy = event.ydata - self.drag_start_mouse[1]

        if math.hypot(dx, dy) > 0.05 or self.dragging_label is not None:
            self.has_dragged = True

        if self.has_dragged:
            if self.dragging_label is not None:
                nx, ny = self.node_positions[self.dragging_label]
                angle = math.atan2(event.ydata - ny, event.xdata - nx)
                self.custom_label_angles[self.dragging_label] = angle
                self.redraw_diagram()
            elif self.dragging_text is not None and self.drag_start_text_pos is not None:
                orig_x, orig_y = self.drag_start_text_pos
                t_obj = next((t for t in self.text_blocks_data if t["id"] == self.dragging_text), None)
                if t_obj:
                    t_obj["x"] = orig_x + dx
                    t_obj["y"] = orig_y + dy
                    self.redraw_diagram()
            elif self.dragging_node is not None and self.drag_start_node_pos is not None:
                orig_x, orig_y = self.drag_start_node_pos
                self.custom_node_positions[self.dragging_node] = (orig_x + dx, orig_y + dy)
                self.redraw_diagram()
            elif self.dragging_set is not None and self.drag_start_set_pos is not None:
                orig_x, orig_y = self.drag_start_set_pos
                self.custom_set_positions[self.dragging_set] = (orig_x + dx, orig_y + dy)
                self.redraw_diagram()

    def on_release(self, event):
        if not self.has_dragged:
            if self.clicked_title is not None:
                self.open_edit_set_dialog(self.clicked_title)
            elif self.clicked_text is not None:
                self.open_edit_text_dialog(self.clicked_text)
            elif self.clicked_node is not None:
                clicked_node = self.clicked_node
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
                            "to": dst_elem,
                            "flipped": False
                        })

                    self.selected_node = None
                self.redraw_diagram()

        self.dragging_node = None
        self.dragging_set = None
        self.dragging_text = None
        self.dragging_label = None
        self.drag_start_mouse = None
        self.drag_start_node_pos = None
        self.drag_start_set_pos = None
        self.drag_start_text_pos = None
        self.clicked_title = None
        self.clicked_node = None
        self.clicked_text = None
        self.has_dragged = False

    def _compute_smart_relation_curvatures(self):
        """Calculates dynamic curvatures (rad) per relation grouped by unordered pair (A,B) to guarantee ZERO overlaps."""
        default_src_set = self.sets_data[0]["id"] if self.sets_data else "set_1"
        default_dst_set = self.sets_data[-1]["id"] if self.sets_data else "set_2"

        pair_groups = defaultdict(lambda: {"fwd": [], "bwd": []})

        for idx, rel in enumerate(self.relations_data):
            f_set = str(rel.get("from_set", default_src_set))
            t_set = str(rel.get("to_set", default_dst_set))
            src = str(rel.get("from"))
            dst = str(rel.get("to"))

            k_src = (f_set, src)
            k_dst = (t_set, dst)

            if k_src == k_dst:
                continue

            pair_key = tuple(sorted([k_src, k_dst]))
            if k_src == pair_key[0]:
                pair_groups[pair_key]["fwd"].append(idx)
            else:
                pair_groups[pair_key]["bwd"].append(idx)

        rad_dict = {}
        is_single_set = (len(self.sets_data) == 1)

        for pair_key, edges in pair_groups.items():
            fwd_indices = edges["fwd"]
            bwd_indices = edges["bwd"]

            base_rad = -0.32 if is_single_set else -0.28

            for i, idx in enumerate(fwd_indices):
                calc_rad = base_rad - i * 0.22
                if self.relations_data[idx].get("flipped", False):
                    calc_rad = -calc_rad
                rad_dict[idx] = calc_rad

            for j, idx in enumerate(bwd_indices):
                calc_rad = base_rad - j * 0.22
                if self.relations_data[idx].get("flipped", False):
                    calc_rad = -calc_rad
                rad_dict[idx] = calc_rad

        return rad_dict

    def redraw_diagram(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        ax.set_facecolor(COLOR_CARD)
        self.node_positions.clear()
        self.label_positions.clear()
        self.title_positions.clear()
        self.text_block_positions.clear()
        self.arrow_midpoints.clear()

        num_sets = len(self.sets_data)
        if num_sets == 0 and not self.text_blocks_data:
            ax.text(0.5, 0.5, "Click '+ Add Set' or '+ Add Text' to start", ha='center', va='center', fontsize=12, color=COLOR_MUTED)
            ax.axis('off')
            self.canvas.draw()
            return

        all_min_y, all_max_y = [], []
        all_min_x, all_max_x = [], []

        # MODE: 1 SET (Radial Cloud)
        if num_sets == 1:
            s = self.sets_data[0]
            elements = s.get("elements", [])
            color = s.get("color", "#000000")
            name = s.get("name", "Set 1")
            scale = float(s.get("scale", 1.0))

            n = len(elements)
            radius = 3.0 * scale

            if n == 2:
                angles = np.array([np.pi, 0.0])
            elif n == 4:
                angles = np.array([3 * np.pi / 4.0, np.pi / 4.0, 7 * np.pi / 4.0, 5 * np.pi / 4.0])
            elif n > 0:
                angles = 3 * np.pi / 4.0 - np.linspace(0, 2 * np.pi, n, endpoint=False)
            else:
                angles = np.array([])

            for i, elem in enumerate(elements):
                node_key = (s["id"], str(elem))
                if node_key in self.custom_node_positions:
                    x, y = self.custom_node_positions[node_key]
                else:
                    angle = angles[i]
                    x = radius * np.cos(angle)
                    y = radius * np.sin(angle)

                self.node_positions[node_key] = (x, y)
                all_min_x.append(x - 0.5 * scale)
                all_max_x.append(x + 0.5 * scale)
                all_min_y.append(y - 0.5 * scale)
                all_max_y.append(y + 0.5 * scale)

                if self.selected_node == node_key:
                    ax.plot(x, y, 'o', color='#FFB74D', markersize=16 * scale, zorder=3, alpha=0.6)

                ax.plot(x, y, 'o', color=color, markersize=8 * scale, zorder=4)
                
                default_angle = angles[i] if i < len(angles) else 0.0
                angle_lbl = self.custom_label_angles.get(node_key, default_angle)

                r_offset = 0.50 * scale
                lbl_x = x + r_offset * np.cos(angle_lbl)
                lbl_y = y + r_offset * np.sin(angle_lbl)

                self.label_positions[node_key] = (lbl_x, lbl_y)
                all_min_x.append(lbl_x - 0.3 * scale)
                all_max_x.append(lbl_x + 0.3 * scale)
                all_min_y.append(lbl_y - 0.3 * scale)
                all_max_y.append(lbl_y + 0.3 * scale)

                ax.text(lbl_x, lbl_y, str(elem), fontsize=int(12 * scale), fontweight='bold',
                        ha='center', va='center', color=COLOR_TEXT, zorder=5)

            title_y = radius + 1.1 * scale
            ax.text(0, title_y, name, fontsize=int(14 * scale), fontweight='bold', ha='center', color=color)
            self.title_positions[s["id"]] = (0, title_y)
            all_max_y.append(title_y + 0.5 * scale)
            all_min_y.append(-radius - 1.2 * scale)
            all_min_x.append(-radius - 1.2 * scale)
            all_max_x.append(radius + 1.2 * scale)

            smart_rads = self._compute_smart_relation_curvatures()

            for idx_rel, rel in enumerate(self.relations_data):
                src, dst = str(rel.get("from")), str(rel.get("to"))
                lbl = rel.get("label", "")
                k_src, k_dst = (s["id"], src), (s["id"], dst)

                if k_src in self.node_positions and k_dst in self.node_positions:
                    x1, y1 = self.node_positions[k_src]
                    x2, y2 = self.node_positions[k_dst]
                    idx_src = elements.index(src) if src in elements else 0
                    default_angle = angles[idx_src] if idx_src < len(angles) else 0.0

                    if src == dst:
                        ang_loop = self.custom_label_angles.get(k_src, default_angle)
                        draw_loop(ax, x1, y1, angle_rad=ang_loop, color=COLOR_LOOP_ARROW, label=lbl, scale=scale)
                        all_min_x.append(x1 - 1.5 * scale)
                        all_max_x.append(x1 + 1.5 * scale)
                        all_min_y.append(y1 - 1.5 * scale)
                        all_max_y.append(y1 + 1.5 * scale)
                    else:
                        rad = smart_rads.get(idx_rel, -0.32)
                        ax.annotate(
                            '', xy=(x2, y2), xytext=(x1, y1),
                            arrowprops=dict(
                                arrowstyle="->,head_width=0.35,head_length=0.50",
                                color="#4A5568", lw=1.8, shrinkA=10 * scale, shrinkB=10 * scale,
                                connectionstyle=f"arc3,rad={rad:.2f}"
                            ),
                            zorder=2
                        )
                        V = np.array([x2 - x1, y2 - y1])
                        dist = np.linalg.norm(V)
                        if dist > 1e-6:
                            u = V / dist
                            n_left = np.array([-u[1], u[0]])
                            curve_mid = np.array([(x1 + x2)/2.0, (y1 + y2)/2.0]) - 0.5 * rad * dist * n_left
                            self.arrow_midpoints[idx_rel] = (curve_mid[0], curve_mid[1])

                        if lbl:
                            mid_x, mid_y = (x1 + x2) / 2, (y1 + y2) / 2
                            ax.text(mid_x, mid_y, lbl, fontsize=9, color=COLOR_MUTED, ha='center')

        # MODE: 2+ SETS (Vertical Ellipses)
        elif num_sets > 1:
            y_spacing_base, x_spacing, x_start = 1.2, 4.0, 2.0

            for idx, s in enumerate(self.sets_data):
                set_id = s.get("id", str(idx))
                set_name = s.get("name", set_id)
                elements = s.get("elements", [])
                color = s.get("color", "#000000")
                scale = float(s.get("scale", 1.0))

                x_pos, y_center = self._get_set_center(set_id, idx)
                y_spacing = y_spacing_base * scale
                height = max(len(elements) * y_spacing + 1.5 * scale, 3.0 * scale)
                width = 2.4 * scale

                all_min_y.append(y_center - height / 2.0)
                all_max_y.append(y_center + height / 2.0 + 0.4 * scale)
                all_min_x.append(x_pos - width / 2.0 - 0.2)
                all_max_x.append(x_pos + width / 2.0 + 0.2)

                ellipse = patches.Ellipse(
                    (x_pos, y_center), width=width, height=height,
                    edgecolor=color, facecolor=color + '12', linewidth=2, zorder=1
                )
                ax.add_patch(ellipse)

                title_y = y_center + height/2 + 0.35 * scale
                ax.text(x_pos, title_y, set_name, fontsize=int(13 * scale), fontweight='bold', ha='center', color=color)
                self.title_positions[set_id] = (x_pos, title_y)

                if elements:
                    y_start = y_center + (len(elements) - 1) * y_spacing / 2
                    for i, elem in enumerate(elements):
                        node_key = (set_id, str(elem))
                        x_elem = x_pos
                        y_elem = y_start - i * y_spacing

                        self.node_positions[node_key] = (x_elem, y_elem)

                        if self.selected_node == node_key:
                            ax.plot(x_elem, y_elem, 'o', color='#FFB74D', markersize=14 * scale, zorder=3, alpha=0.6)

                        ax.plot(x_elem, y_elem, 'o', color=color, markersize=6 * scale, zorder=3)

                        if idx == 0:
                            default_angle = np.pi
                        elif idx == num_sets - 1:
                            default_angle = 0.0
                        else:
                            default_angle = np.pi / 2

                        angle_lbl = self.custom_label_angles.get(node_key, default_angle)
                        r_offset = 0.40 * scale

                        lbl_x = x_elem + r_offset * np.cos(angle_lbl)
                        lbl_y = y_elem + r_offset * np.sin(angle_lbl)

                        self.label_positions[node_key] = (lbl_x, lbl_y)
                        all_min_x.append(lbl_x - 0.3 * scale)
                        all_max_x.append(lbl_x + 0.3 * scale)
                        all_min_y.append(lbl_y - 0.3 * scale)
                        all_max_y.append(lbl_y + 0.3 * scale)

                        ax.text(lbl_x, lbl_y, str(elem), fontsize=int(11 * scale), ha='center', va='center', fontweight='bold', zorder=5)

            smart_rads = self._compute_smart_relation_curvatures()

            for idx_rel, rel in enumerate(self.relations_data):
                from_set = str(rel.get("from_set", self.sets_data[0].get("id")))
                to_set = str(rel.get("to_set", self.sets_data[-1].get("id")))
                src, dst = str(rel.get("from")), str(rel.get("to"))
                lbl = rel.get("label", "")

                k_src, k_dst = (from_set, src), (to_set, dst)
                if k_src in self.node_positions and k_dst in self.node_positions:
                    start = self.node_positions[k_src]
                    end = self.node_positions[k_dst]

                    if from_set == to_set and src == dst:
                        s_idx = next((i for i, s_item in enumerate(self.sets_data) if s_item["id"] == from_set), 0)
                        set_obj = self.sets_data[s_idx]
                        sc = float(set_obj.get("scale", 1.0)) * 0.75

                        if s_idx == 0:
                            default_angle = np.pi
                        elif s_idx == num_sets - 1:
                            default_angle = 0.0
                        else:
                            default_angle = np.pi / 2

                        ang_loop = self.custom_label_angles.get(k_src, default_angle)
                        draw_loop(ax, start[0], start[1], angle_rad=ang_loop, color=COLOR_LOOP_ARROW, label=lbl, scale=sc)
                        all_min_x.append(start[0] - 1.2 * sc)
                        all_max_x.append(start[0] + 1.2 * sc)
                        all_min_y.append(start[1] - 1.2 * sc)
                        all_max_y.append(start[1] + 1.2 * sc)
                    else:
                        is_forward = start[0] <= end[0]
                        rad = smart_rads.get(idx_rel, -0.28)

                        ax.annotate(
                            '', xy=(end[0], end[1]), xytext=(start[0], start[1]),
                            arrowprops=dict(
                                arrowstyle="->,head_width=0.30,head_length=0.45",
                                color="#4A5568", lw=1.5, shrinkA=8, shrinkB=8,
                                connectionstyle=f"arc3,rad={rad:.2f}"
                            ),
                            zorder=2
                        )
                        V = np.array([end[0] - start[0], end[1] - start[1]])
                        dist = np.linalg.norm(V)
                        if dist > 1e-6:
                            u = V / dist
                            n_left = np.array([-u[1], u[0]])
                            curve_mid = np.array([(start[0] + end[0])/2.0, (start[1] + end[1])/2.0]) - 0.5 * rad * dist * n_left
                            self.arrow_midpoints[idx_rel] = (curve_mid[0], curve_mid[1])

                        if lbl:
                            mid_x = (start[0] + end[0]) / 2
                            offset_y = 0.35 if is_forward else -0.35
                            mid_y = (start[1] + end[1]) / 2 + offset_y
                            ax.text(mid_x, mid_y, lbl, fontsize=9, color=COLOR_MUTED, ha='center', va='center')

        # DRAW FREE TEXT BLOCKS
        for t_obj in self.text_blocks_data:
            tx, ty = t_obj["x"], t_obj["y"]
            t_txt = t_obj.get("text", "")
            t_col = t_obj.get("color", COLOR_TEXT)
            t_fs = float(t_obj.get("fontsize", 12))
            t_id = t_obj["id"]

            self.text_block_positions[t_id] = (tx, ty)
            margin_x = (t_fs / 12.0) * 0.8
            margin_y = (t_fs / 12.0) * 0.5
            all_min_x.append(tx - margin_x)
            all_max_x.append(tx + margin_x)
            all_min_y.append(ty - margin_y)
            all_max_y.append(ty + margin_y)

            ax.text(
                tx, ty, t_txt, fontsize=int(t_fs), color=t_col, fontweight='bold',
                ha='center', va='center', zorder=10
            )

        ax.set_aspect('equal')
        ax.axis('off')
        
        if all_min_x and all_min_y:
            ax.set_xlim(min(all_min_x) - 0.5, max(all_max_x) + 0.5)
            ax.set_ylim(min(all_min_y) - 0.6, max(all_max_y) + 0.4)

        self.fig.tight_layout()
        self.canvas.draw()

    # --- TEXT BLOCK DIALOGS ---
    def open_new_text_dialog(self):
        dialog = tk.Toplevel(self)
        dialog.title("New Text Block")
        dialog.geometry("360x310")
        dialog.configure(bg=COLOR_CARD)
        dialog.transient(self)

        ttk.Label(dialog, text="Text Content:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(15, 2))
        entry_text = ttk.Entry(dialog)
        entry_text.pack(fill="x", padx=20)
        entry_text.insert(0, "G ⊆ A × B")

        ttk.Label(dialog, text="Font Size:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        size_frame = ttk.Frame(dialog, style="Card.TFrame")
        size_frame.pack(fill="x", padx=20, pady=2)

        lbl_size = ttk.Label(size_frame, text="12 pt", background=COLOR_CARD, font=("Segoe UI", 9, "bold"))
        lbl_size.pack(side="right", padx=(5, 0))

        font_size_val = [12]
        def on_size_change(val):
            fs = int(float(val))
            font_size_val[0] = fs
            lbl_size.config(text=f"{fs} pt")

        slider_size = ttk.Scale(size_frame, from_=8, to=48, value=12, command=on_size_change)
        slider_size.pack(side="left", fill="x", expand=True)

        color_hex = [COLOR_TEXT]
        initial_val = hex_to_val(COLOR_TEXT)

        ttk.Label(dialog, text="Text Color:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        slider_frame = ttk.Frame(dialog, style="Card.TFrame")
        slider_frame.pack(fill="x", padx=20, pady=2)

        color_preview = tk.Frame(slider_frame, width=22, height=22, bg=COLOR_TEXT, highlightbackground="#CBD5E0", highlightthickness=1)
        color_preview.pack(side="left", padx=(0, 8))

        lbl_hex = ttk.Label(slider_frame, text=COLOR_TEXT, background=COLOR_CARD, font=("Segoe UI", 9, "bold"))
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

        def save():
            txt = entry_text.get().strip()
            if not txt:
                messagebox.showerror("Error", "Please enter some text.", parent=dialog)
                return

            t_id = self._generate_unique_text_id()
            # Default coordinates placed cleanly in the top-left corner
            default_x = 0.8 if len(self.sets_data) > 1 else -3.2
            default_y = 3.2 if len(self.sets_data) > 1 else 3.8

            self.text_blocks_data.append({
                "id": t_id,
                "text": txt,
                "x": default_x,
                "y": default_y,
                "color": color_hex[0],
                "fontsize": font_size_val[0]
            })
            self.redraw_diagram()
            dialog.destroy()

        frame_btns = ttk.Frame(dialog, style="Card.TFrame")
        frame_btns.pack(fill="x", padx=20, pady=15)

        btn_cancel = ttk.Button(frame_btns, text="Cancel", style="TButton", command=dialog.destroy)
        btn_cancel.pack(side="left")

        btn_accept = ttk.Button(frame_btns, text="➕ Create Text", style="Primary.TButton", command=save)
        btn_accept.pack(side="right")

        dialog.wait_visibility()
        dialog.grab_set()

    def open_edit_text_dialog(self, text_id):
        t_obj = next((t for t in self.text_blocks_data if t["id"] == text_id), None)
        if not t_obj:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Edit Text Block")
        dialog.geometry("360x310")
        dialog.configure(bg=COLOR_CARD)
        dialog.transient(self)

        ttk.Label(dialog, text="Text Content:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(15, 2))
        entry_text = ttk.Entry(dialog)
        entry_text.pack(fill="x", padx=20)
        entry_text.insert(0, t_obj.get("text", ""))

        current_fs = int(t_obj.get("fontsize", 12))
        font_size_val = [current_fs]

        ttk.Label(dialog, text="Font Size:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        size_frame = ttk.Frame(dialog, style="Card.TFrame")
        size_frame.pack(fill="x", padx=20, pady=2)

        lbl_size = ttk.Label(size_frame, text=f"{current_fs} pt", background=COLOR_CARD, font=("Segoe UI", 9, "bold"))
        lbl_size.pack(side="right", padx=(5, 0))

        def on_size_change(val):
            fs = int(float(val))
            font_size_val[0] = fs
            lbl_size.config(text=f"{fs} pt")

        slider_size = ttk.Scale(size_frame, from_=8, to=48, value=current_fs, command=on_size_change)
        slider_size.pack(side="left", fill="x", expand=True)

        current_color = t_obj.get("color", COLOR_TEXT)
        color_hex = [current_color]
        initial_val = hex_to_val(current_color)

        ttk.Label(dialog, text="Text Color:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
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

        def delete_this_text():
            self.text_blocks_data = [t for t in self.text_blocks_data if t["id"] != text_id]
            self.redraw_diagram()
            dialog.destroy()

        def save_changes():
            txt = entry_text.get().strip()
            if not txt:
                messagebox.showerror("Error", "Please enter some text.", parent=dialog)
                return

            t_obj["text"] = txt
            t_obj["color"] = color_hex[0]
            t_obj["fontsize"] = font_size_val[0]

            self.redraw_diagram()
            dialog.destroy()

        btn_del = ttk.Button(frame_btns, text="🗑️ Delete Text", style="Danger.TButton", command=delete_this_text)
        btn_del.pack(side="left")

        btn_save = ttk.Button(frame_btns, text="💾 Save", style="Success.TButton", command=save_changes)
        btn_save.pack(side="right")

        dialog.wait_visibility()
        dialog.grab_set()

    # --- EDIT & CREATE SET DIALOGS ---
    def open_edit_set_dialog(self, set_id):
        set_obj = next((s for s in self.sets_data if s["id"] == set_id), None)
        if not set_obj:
            return

        dialog = tk.Toplevel(self)
        dialog.title("Edit Set")
        dialog.geometry("360x350")
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

        current_scale = float(set_obj.get("scale", 1.0))
        set_scale_val = [current_scale]

        ttk.Label(dialog, text="Set Size (Scale):", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        scale_frame = ttk.Frame(dialog, style="Card.TFrame")
        scale_frame.pack(fill="x", padx=20, pady=2)

        lbl_scale = ttk.Label(scale_frame, text=f"{current_scale:.1f}x", background=COLOR_CARD, font=("Segoe UI", 9, "bold"))
        lbl_scale.pack(side="right", padx=(5, 0))

        def on_scale_change(val):
            sc = round(float(val), 1)
            set_scale_val[0] = sc
            lbl_scale.config(text=f"{sc:.1f}x")

        slider_scale = ttk.Scale(scale_frame, from_=0.5, to=2.0, value=current_scale, command=on_scale_change)
        slider_scale.pack(side="left", fill="x", expand=True)

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
                self.custom_node_positions = {
                    k: v for k, v in self.custom_node_positions.items() if k[0] != target_id
                }
                self.custom_label_angles = {
                    k: v for k, v in self.custom_label_angles.items() if k[0] != target_id
                }
                if target_id in self.custom_set_positions:
                    del self.custom_set_positions[target_id]
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
            set_obj["scale"] = set_scale_val[0]

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
        dialog.geometry("360x350")
        dialog.configure(bg=COLOR_CARD)
        dialog.transient(self)

        ttk.Label(dialog, text="Set Display Name:", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(15, 2))
        entry_name = ttk.Entry(dialog)
        entry_name.pack(fill="x", padx=20)

        ttk.Label(dialog, text="Elements (comma separated):", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        entry_elems = ttk.Entry(dialog)
        entry_elems.pack(fill="x", padx=20)

        set_scale_val = [1.0]

        ttk.Label(dialog, text="Set Size (Scale):", background=COLOR_CARD).pack(anchor="w", padx=20, pady=(10, 2))
        scale_frame = ttk.Frame(dialog, style="Card.TFrame")
        scale_frame.pack(fill="x", padx=20, pady=2)

        lbl_scale = ttk.Label(scale_frame, text="1.0x", background=COLOR_CARD, font=("Segoe UI", 9, "bold"))
        lbl_scale.pack(side="right", padx=(5, 0))

        def on_scale_change(val):
            sc = round(float(val), 1)
            set_scale_val[0] = sc
            lbl_scale.config(text=f"{sc:.1f}x")

        slider_scale = ttk.Scale(scale_frame, from_=0.5, to=2.0, value=1.0, command=on_scale_change)
        slider_scale.pack(side="left", fill="x", expand=True)

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

            self.sets_data.append({
                "id": s_id, 
                "name": s_name, 
                "elements": elems, 
                "color": color_hex[0],
                "scale": set_scale_val[0]
            })
            self.redraw_diagram()
            dialog.destroy()

        frame_btns = ttk.Frame(dialog, style="Card.TFrame")
        frame_btns.pack(fill="x", padx=20, pady=15)

        btn_cancel = ttk.Button(frame_btns, text="Cancel", style="TButton", command=dialog.destroy)
        btn_cancel.pack(side="left")

        btn_accept = ttk.Button(frame_btns, text="➕ Create Text", style="Primary.TButton", command=save)
        btn_accept.pack(side="right")

        dialog.wait_visibility()
        dialog.grab_set()

    # --- FILE EXPORT & I/O LOGIC ---
    def export_png(self):
        if not self.sets_data and not self.text_blocks_data:
            messagebox.showerror("Error", "No elements available to export.")
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
        if not self.sets_data and not self.text_blocks_data:
            messagebox.showerror("Error", "No elements available to save.")
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
                node_pos_dict = {f"{k[0]}::{k[1]}": list(v) for k, v in self.custom_node_positions.items()}
                label_angles_dict = {f"{k[0]}::{k[1]}": float(v) for k, v in self.custom_label_angles.items()}
                set_pos_dict = {k: list(v) for k, v in self.custom_set_positions.items()}

                config = {
                    "sets": self.sets_data,
                    "relations": self.relations_data,
                    "custom_node_positions": node_pos_dict,
                    "custom_label_angles": label_angles_dict,
                    "custom_set_positions": set_pos_dict,
                    "text_blocks": self.text_blocks_data
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

                self.sets_data = data.get("sets", [])
                self.relations_data = data.get("relations", [])
                self.text_blocks_data = data.get("text_blocks", [])

                raw_node_pos = data.get("custom_node_positions", {})
                self.custom_node_positions = {}
                for k, v in raw_node_pos.items():
                    parts = k.split("::")
                    if len(parts) == 2:
                        self.custom_node_positions[(parts[0], parts[1])] = (v[0], v[1])

                raw_label_angles = data.get("custom_label_angles", {})
                self.custom_label_angles = {}
                for k, v in raw_label_angles.items():
                    parts = k.split("::")
                    if len(parts) == 2:
                        self.custom_label_angles[(parts[0], parts[1])] = float(v)

                raw_set_pos = data.get("custom_set_positions", {})
                self.custom_set_positions = {k: (v[0], v[1]) for k, v in raw_set_pos.items() if len(v) == 2}

                self.selected_node = None
                self.redraw_diagram()
                messagebox.showinfo("Success", f"Diagram loaded successfully:\n{os.path.basename(filepath)}")
            except Exception as e:
                messagebox.showerror("Error", f"Could not open JSON file:\n{e}")


if __name__ == "__main__":
    app = SagittalCreatorMinimal()
    app.mainloop()