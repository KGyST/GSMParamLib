import tkinter as tk
import tkinter.filedialog


# https://stackoverflow.com/questions/12305142/issue-with-singleton-python-call-two-times-init
def singleton(cls):
    singletons = {}
    def getinstance():
        if cls not in singletons:
            singletons[cls] = cls()
        return singletons[cls]
    return getinstance


class CreateToolTip:
    def __init__(self, widget, text='widget info'):
        self.waittime = 500
        self.wraplength = 180
        self.widget = widget
        self.text = text

        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        idx = self.id
        self.id = None
        if idx:
            self.widget.after_cancel(idx)

    def showtip(self, event=None):
        x, y, cx, cy = self.widget.bbox("insert")
        x += self.widget.winfo_rootx() + 25
        y += self.widget.winfo_rooty() + 20
        # creates a toplevel window
        self.tw = tk.Toplevel(self.widget)
        # Leaves only the label and removes the app window
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffff", relief='solid', borderwidth=1,
                       wraplength = self.wraplength)
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()


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

