import tkinter as tk
import tkinter.filedialog
import docutils.nodes
from docutils.core import publish_doctree
from PIL import Image, ImageTk


# https://stackoverflow.com/questions/12305142/issue-with-singleton-python-call-two-times-init
def singleton(cls):
    singletons = {}
    def getinstance(*args, **kwargs):
        if cls not in singletons:
            singletons[cls] = cls(*args, **kwargs)
        return singletons[cls]
    return getinstance


class CreateToolTip:
    activeToolTip = None
    def __init__(self, widget, text='widget info', delay=500):
        self.waittime = delay  # Delay in milliseconds (default: 500ms)
        self.widget = widget
        self.text = self._unindent(text)

        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        if event and self.tw:
            window_x = self.tw.winfo_rootx()
            window_y = self.tw.winfo_rooty()
            _window_x = self.tw.winfo_width()
            _window_y = self.tw.winfo_height()
            cursor_x = event.x_root
            cursor_y = event.y_root
            if window_x <= cursor_x <= window_x + _window_x and window_y <= cursor_y <= window_y + _window_y:
                return
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.hidetip)

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        idx = self.id
        self.id = None
        if idx:
            self.widget.after_cancel(idx)

    def showtip(self):
        if CreateToolTip.activeToolTip:
            return
        else:
            CreateToolTip.activeToolTip = self
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20

        self.tw = tk.Toplevel(self.widget)
        self.tw.bind("<Leave>", self.leave)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))

        width = len(max(self.text.splitlines(), key=len))
        height = len(self.text.splitlines())

        text = tk.Text(self.tw, height=height, width=width, wrap=tk.WORD,
                       bg="#ffffff", relief=tk.FLAT, borderwidth=10)
        text.pack(ipadx=1)

        self.parse_and_display(text)

    def parse_and_display(self, text):
        text.tag_configure("normal", font=("Arial", 12))
        text.tag_configure("bold", font=("Arial", 12, "bold"))
        text.tag_configure("italic", font=("Arial", 12, "italic"))
        text.tag_configure("link", font=("Arial", 12), foreground="blue", underline=True)
        text.tag_configure("document heading", font=("Arial", 16, "bold"))
        text.tag_configure("subtitle", font=("Arial", 14, "bold"))
        text.tag_configure("subheading", font=("Arial", 12, "bold"))

        document = publish_doctree(self.text)

        self.walk(document, text)

        text.configure(state=tk.DISABLED)

    def walk(self, document, text, title = 16):
        for child in document.children:
            if isinstance(child, docutils.nodes.Text):
                text.insert("end", child.astext(), "normal")
            elif isinstance(child, docutils.nodes.paragraph):
                self.walk(child, text)
                text.insert("end", "\n")
            elif isinstance(child, docutils.nodes.title):
                _heading = "heading_" + str(title)
                text.tag_configure(_heading, font=("Arial", title, "bold"))
                text.insert("end", child.astext(), _heading)
                text.insert("end", "\n")
            elif isinstance(child, docutils.nodes.subtitle):
                text.insert("end", child.astext(), "subtitle")
                text.insert("end", "\n")
            elif isinstance(child, docutils.nodes.section):
                self.walk(child, text, title=title-4)
            elif isinstance(child, docutils.nodes.strong):
                text.insert("end", child.astext(), "bold")
            elif isinstance(child, docutils.nodes.emphasis):
                text.insert("end", child.astext(), "italic")
            elif isinstance(child, docutils.nodes.reference):
                text.insert("end", child.astext(), "link")
                text.tag_bind("link", "<Button-1>", lambda event, node=child: self.open_url(event, node))
            elif isinstance(child, docutils.nodes.image):
                image_path = child["uri"]
                try:
                    image = Image.open(image_path)
                    image = image.resize((100, 100))  # Adjust the size as needed
                    photo = ImageTk.PhotoImage(image)

                    # Insert the image into the text widget
                    text.image_create("end", image=photo)
                    text.insert("end", "\n")

                    # Keep a reference to the PhotoImage to prevent it from being garbage collected
                    text.image = photo

                except Exception as e:
                    print(f"Error loading image: {e}")
            elif isinstance(child, docutils.nodes.bullet_list):
                for item_node in child.children:
                    text.insert("end", "".join(["• ", item_node.astext(), "\n"]), "normal")

    def hidetip(self):
        if CreateToolTip.activeToolTip == self and not self.check_cursor_above_tooltip():
            tw = self.tw
            self.tw = None
            if tw:
                tw.destroy()
            CreateToolTip.activeToolTip = None

    def open_url(self, event, node):
        if "refuri" in node.attributes:
            url = node.attributes["refuri"]
            # Open the URL in a web browser or handle it as desired
            print("Opening URL:", url)

    def check_cursor_above_tooltip(self):
        cursor_x, cursor_y = self.tw.winfo_pointerxy()
        window_x = self.tw.winfo_rootx()
        window_y = self.tw.winfo_rooty()
        window_w = self.tw.winfo_width()
        window_h = self.tw.winfo_height()
        if window_x <= cursor_x <= window_x + window_w and window_y <= cursor_y <= window_y + window_h:
            return True
        else:
            return False

    @staticmethod
    def _unindent(text: str) -> str:
        """
        Unindents the given text if every line starts with the same indentation.

        Args:
            text (str): The text to unindent.

        Returns:
            str: The unindented text.
        """
        lines = text.split("\n")
        indentation = None

        for line in lines:
            if not line.strip():
                continue

            line_indentation = len(line) - len(line.lstrip())

            if indentation is None:
                indentation = line_indentation
            elif line_indentation < indentation:
                indentation = line_indentation

        if indentation is not None and indentation > 0:
            unindented_lines = [line[indentation:] for line in lines]
            return "\n".join(unindented_lines)

        return text


class InputDirPlusText:
    def __init__(self, top, text, target, tooltip='', row=0, column=0, func=tkinter.filedialog.askdirectory, title="Select folder"):
        self.target = target
        self.filename = ''
        self._frame = tk.Frame(top)
        self._frame.grid({"row": row, "column": column})

        self._frame.columnconfigure(1, weight=1)

        self.buttonDirName = tk.Button(self._frame, {"text": text, "command": self.getFunc(func, title) })
        self.buttonDirName.grid({"sticky": tk.W + tk.E, "row": 0, "column": 0, })

        self.entryName = tk.Entry(self._frame, {"width": 30, "textvariable": target})
        self.entryName.grid({"row": 0, "column": 1, "sticky": tk.E + tk.W, })

        if tooltip:
            CreateToolTip(self._frame, tooltip)

    def getFunc(self, func, title):
        def inputDirName():
            self.filename = func(initialdir="/", title=title)
            self.target.set(self.filename)
            self.entryName.delete(0, tk.END)
            self.entryName.insert(0, self.filename)
        return inputDirName

    def config(self, *args, **kwargs):
        return self.entryName.config(*args, **kwargs)


# class InputDirPlusRadio():
#     def __init__(self, top, text, target, var, varValue, tooltip='', row=0, column=0, **kwargs):
#         top.columnconfigure(1, weight=1)
#
#         self.frame = tk.Frame(top)
#         self.frame.grid({"row": row, "column": column, "sticky": tk.E + tk.W})
#
#         self._var = var
#         self._varValue = varValue
#
#         self.radio = tk.Radiobutton(self.frame, {"variable": self._var, "value": varValue})
#         self.radio.grid({"sticky": tk.W, "row": 0, "column": 0})
#
#         self.idpt = InputDirPlusText(self.frame, text, target, row=0, column=1, **kwargs)
#
#         if varValue:
#             self.idpt.entryName.config(state=tk.DISABLED)
#             self.idpt.buttonDirName.config(state=tk.DISABLED)
#
#         self.bCBobserver = self._var.trace_variable("w", self.radioModified)
#
#         if tooltip:
#             CreateToolTip(self.frame, tooltip)
#
#     def radioModified(self, *_):
#         if not self._var.get() == self._varValue:
#             self.idpt.entryName.config(state=tk.DISABLED)
#             self.idpt.buttonDirName.config(state=tk.DISABLED)
#         else:
#             self.idpt.entryName.config(state=tk.NORMAL)
#             self.idpt.buttonDirName.config(state=tk.NORMAL)

