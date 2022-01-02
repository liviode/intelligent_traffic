import tkinter as tk
import tkinter.ttk as ttk


class TkSlot(tk.Frame):

    def __init__(self, tk_parent):
        tk.Frame.__init__(self, tk_parent)

        self.car = tk.Label(self, text='-', anchor="e", width=1, font=("Courier", 12))
        self.velocity = tk.Label(self, text='-', anchor="w", width=1, font=("Courier", 12))

        self.car.pack(ipadx=2, ipady=2, expand=True, fill='both', side='left')
        self.velocity.pack(ipadx=2, ipady=2, fill='both')
        self.tooltip = ToolTip(self, text='')

    def set_car(self, car):
        if car is None:
            self.car['text'] = '-'
            self.velocity['text'] = '-'
            self.car.config(bg='gray')
            self.velocity.config(bg='gray')
            self.tooltip.text = '-'

        else:
            self.car['text'] = car.nr
            self.velocity['text'] = car.velocity
            self.car.config(bg='white', borderwidth=1)
            self.velocity.config(bg='yellow')
            self.tooltip.text = 'Next street:' + car.next_street





class TkStreet(tk.LabelFrame):

    def __init__(self, tk_parent, street, **kw):
        super().__init__(tk_parent, padx=5, pady=5, **kw)
        self.tk_slots = []
        self.index = 0

        for i in range(street.length):
            tk_slot = TkSlot(self)
            self.tk_slots.append(tk_slot)
            tk_slot.grid(row=0, column=i)


class ToolTip:
    def __init__(self, widget, text=None):
        self.tooltip = None

        def on_enter(event):
            self.tooltip = tk.Toplevel()
            self.tooltip.overrideredirect(True)
            self.tooltip.geometry(f'+{event.x_root + 15}+{event.y_root + 10}')

            self.label = tk.Label(self.tooltip, text=self.text)
            self.label.pack()

        def on_leave():
            self.tooltip.destroy()

        self.widget = widget
        self.text = text

        self.widget.bind('<Enter>', on_enter)
        self.widget.bind('<Leave>', on_leave)


def get_html(env):
    html = '<html><body><h1>Configuration</h1>'
    config = '<table>'
    config += '<tr><td>cycles_per_action</td><td>' + str(env.cycles_per_action) + '</td></tr>'
    config += '<tr><td>sleep_per_step</td><td>' + str(env.sleep_per_step) + '</td></tr>'
    html += config + '</table>'

    html += '<table><tr><td>Action</td><td>Observation</td><td>Reward</td><td>Done</td></tr>'
    _range = min(len(env.last_step_info), 20)
    for i in range(_range):
        (action, observation, reward, done) = env.last_step_info[i - _range]
        html += f'<tr><td>{action}</td><td>{observation}</td><td>{reward}</td><td>{done}</td></tr>'
    html += '</table>'

    html += '</body></html>'
    return html


class CrossingButton(tk.Frame):
    def __init__(self, parent, text='-no text-', command=None):
        super().__init__(parent)

        self.label = tk.Label(self, text=text)
        self.label.grid(row=0, column=0, padx=4, pady=4)
        self.button = ttk.Button(self, text='activate', command=command)
        self.button.grid(row=0, column=1, padx=4, pady=4)
        # self.config(background='white')

    def set_green(self):
        self.label.config(bg='green')

    def set_red(self):
        self.label.config(bg='red')


"""Implementation of the scrollable frame widget."""

import sys


class ScrolledFrame(tk.Frame):
    """Scrollable Frame widget.
    Use display_widget() to set the interior widget. For example,
    to display a Label with the text "Hello, world!", you can say:
        sf = ScrolledFrame(self)
        sf.pack()
        sf.display_widget(Label, text="Hello, world!")
    The constructor accepts the usual Tkinter keyword arguments, plus
    a handful of its own:
      scrollbars (str; default: "both")
        Which scrollbars to provide.
        Must be one of "vertical", "horizontal," "both", or "neither".
      use_ttk (bool; default: False)
        Whether to use ttk widgets if available.
        The default is to use standard Tk widgets. This setting has
        no effect if ttk is not available on your system.
    """

    def __init__(self, master=None, **kw):
        """Return a new scrollable frame widget."""

        tk.Frame.__init__(self, master)

        # Hold these names for the interior widget
        self._interior = None
        self._interior_id = None

        # Whether to fit the interior widget's width to the canvas
        self._fit_width = False

        # Which scrollbars to provide
        if "scrollbars" in kw:
            scrollbars = kw["scrollbars"]
            del kw["scrollbars"]

            if not scrollbars:
                scrollbars = self._DEFAULT_SCROLLBARS
            elif not scrollbars in self._VALID_SCROLLBARS:
                raise ValueError("scrollbars parameter must be one of "
                                 "'vertical', 'horizontal', 'both', or "
                                 "'neither'")
        else:
            scrollbars = self._DEFAULT_SCROLLBARS

        # Whether to use ttk widgets if available
        if "use_ttk" in kw:
            if ttk and kw["use_ttk"]:
                Scrollbar = ttk.Scrollbar
            else:
                Scrollbar = tk.Scrollbar
            del kw["use_ttk"]
        else:
            Scrollbar = tk.Scrollbar

        # Default to a 1px sunken border
        if not "borderwidth" in kw:
            kw["borderwidth"] = 1
        if not "relief" in kw:
            kw["relief"] = "sunken"

        # Set up the grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Canvas to hold the interior widget
        c = self._canvas = tk.Canvas(self,
                                     borderwidth=0,
                                     highlightthickness=0,
                                     takefocus=0)

        # Enable scrolling when the canvas has the focus
        self.bind_arrow_keys(c)
        self.bind_scroll_wheel(c)

        # Call _resize_interior() when the canvas widget is updated
        c.bind("<Configure>", self._resize_interior)

        # Scrollbars
        xs = self._x_scrollbar = Scrollbar(self,
                                           orient="horizontal",
                                           command=c.xview)
        ys = self._y_scrollbar = Scrollbar(self,
                                           orient="vertical",
                                           command=c.yview)
        c.configure(xscrollcommand=xs.set, yscrollcommand=ys.set)

        # Lay out our widgets
        c.grid(row=0, column=0, sticky="nsew")
        if scrollbars == "vertical" or scrollbars == "both":
            ys.grid(row=0, column=1, sticky="ns")
        if scrollbars == "horizontal" or scrollbars == "both":
            xs.grid(row=1, column=0, sticky="we")

        # Forward these to the canvas widget
        self.bind = c.bind
        self.focus_set = c.focus_set
        self.unbind = c.unbind
        self.xview = c.xview
        self.xview_moveto = c.xview_moveto
        self.yview = c.yview
        self.yview_moveto = c.yview_moveto

        # Process our remaining configuration options
        self.configure(**kw)

    def __setitem__(self, key, value):
        """Configure resources of a widget."""

        if key in self._CANVAS_KEYS:
            # Forward these to the canvas widget
            self._canvas.configure(**{key: value})

        else:
            # Handle everything else normally
            tk.Frame.configure(self, **{key: value})

    # ------------------------------------------------------------------------

    def bind_arrow_keys(self, widget):
        """Bind the specified widget's arrow key events to the canvas."""

        widget.bind("<Up>",
                    lambda event: self._canvas.yview_scroll(-1, "units"))

        widget.bind("<Down>",
                    lambda event: self._canvas.yview_scroll(1, "units"))

        widget.bind("<Left>",
                    lambda event: self._canvas.xview_scroll(-1, "units"))

        widget.bind("<Right>",
                    lambda event: self._canvas.xview_scroll(1, "units"))

    def bind_scroll_wheel(self, widget):
        """Bind the specified widget's mouse scroll event to the canvas."""

        widget.bind("<MouseWheel>", self._scroll_canvas)
        widget.bind("<Button-4>", self._scroll_canvas)
        widget.bind("<Button-5>", self._scroll_canvas)

    def cget(self, key):
        """Return the resource value for a KEY given as string."""

        if key in self._CANVAS_KEYS:
            return self._canvas.cget(key)

        else:
            return tk.Frame.cget(self, key)

    # Also override this alias for cget()
    __getitem__ = cget

    def configure(self, cnf=None, **kw):
        """Configure resources of a widget."""

        # This is overridden so we can use our custom __setitem__()
        # to pass certain options directly to the canvas.
        if cnf:
            for key in cnf:
                self[key] = cnf[key]

        for key in kw:
            self[key] = kw[key]

    # Also override this alias for configure()
    config = configure

    def display_widget(self, widget_class, fit_width=False, **kw):
        """Create and display a new widget.
        If fit_width == True, the interior widget will be stretched as
        needed to fit the width of the frame.
        Keyword arguments are passed to the widget_class constructor.
        Returns the new widget.
        """

        # Blank the canvas
        self.erase()

        # Set width fitting
        self._fit_width = fit_width

        # Set the new interior widget
        self._interior = widget_class(self._canvas, **kw)

        # Add the interior widget to the canvas, and save its widget ID
        # for use in _resize_interior()
        self._interior_id = self._canvas.create_window(0, 0,
                                                       anchor="nw",
                                                       window=self._interior)

        # Call _update_scroll_region() when the interior widget is resized
        self._interior.bind("<Configure>", self._update_scroll_region)

        # Fit the interior widget to the canvas if requested
        # We don't need to check fit_width here since _resize_interior()
        # already does.
        self._resize_interior()

        # Scroll to the top-left corner of the canvas
        self.scroll_to_top()

        return self._interior

    def erase(self):
        """Erase the displayed widget."""

        # Clear the canvas
        self._canvas.delete("all")

        # Delete the interior widget
        del self._interior
        del self._interior_id

        # Save these names
        self._interior = None
        self._interior_id = None

        # Reset width fitting
        self._fit_width = False

    def scroll_to_top(self):
        """Scroll to the top-left corner of the canvas."""

        self._canvas.xview_moveto(0)
        self._canvas.yview_moveto(0)

    # ------------------------------------------------------------------------

    def _resize_interior(self, event=None):
        """Resize the interior widget to fit the canvas."""

        if self._fit_width and self._interior_id:
            # The current width of the canvas
            canvas_width = self._canvas.winfo_width()

            # The interior widget's requested width
            requested_width = self._interior.winfo_reqwidth()

            if requested_width != canvas_width:
                # Resize the interior widget
                new_width = max(canvas_width, requested_width)
                self._canvas.itemconfigure(self._interior_id, width=new_width)

    def _scroll_canvas(self, event):
        """Scroll the canvas."""

        c = self._canvas

        if sys.platform.startswith("darwin"):
            # macOS
            c.yview_scroll(-1 * event.delta, "units")

        elif event.num == 4:
            # Unix - scroll up
            c.yview_scroll(-1, "units")

        elif event.num == 5:
            # Unix - scroll down
            c.yview_scroll(1, "units")

        else:
            # Windows
            c.yview_scroll(-1 * (event.delta // 120), "units")

    def _update_scroll_region(self, event):
        """Update the scroll region when the interior widget is resized."""

        # The interior widget's requested width and height
        req_width = self._interior.winfo_reqwidth()
        req_height = self._interior.winfo_reqheight()

        # Set the scroll region to fit the interior widget
        self._canvas.configure(scrollregion=(0, 0, req_width, req_height))

    # ------------------------------------------------------------------------

    # Keys for configure() to forward to the canvas widget
    _CANVAS_KEYS = "width", "height", "takefocus"

    # Scrollbar-related configuration
    _DEFAULT_SCROLLBARS = "both"
    _VALID_SCROLLBARS = "vertical", "horizontal", "both", "neither"
