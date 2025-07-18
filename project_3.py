import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
import folium
import webbrowser
import difflib
class Mosque:
    def __init__(self, ID, name, type_, address, coordinates, imam_name):
        self.ID = ID
        self.name = name
        self.type = type_
        self.address = address
        self.coordinates = coordinates
        self.imam_name = imam_name
class MosqueDB:
    def __init__(self):
        self.conn = sqlite3.connect("mosques.db")
        self.cursor = self.conn.cursor()
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS Mosq (
                                ID INTEGER PRIMARY KEY,
                                name TEXT,
                                type TEXT,
                                address TEXT,
                                coordinates TEXT,
                                imam_name TEXT)''')
        self.conn.commit()
    def Display(self):
        self.cursor.execute("SELECT * FROM Mosq")
        return self.cursor.fetchall()

    def Search(self, identifier):
        self.cursor.execute("SELECT * FROM Mosq WHERE ID=? OR name=?", (identifier, identifier))
        return self.cursor.fetchone()

    def Insert(self, ID, name, type_, address, coordinates, imam_name):
        self.cursor.execute("INSERT INTO Mosq VALUES (?, ?, ?, ?, ?, ?)",
                            (ID, name, type_, address, coordinates, imam_name))
        self.conn.commit()

    def Delete(self, ID):
        self.cursor.execute("DELETE FROM Mosq WHERE ID=?", (ID,))
        self.conn.commit()

    def Update_Imam(self, ID, new_imam):
        self.cursor.execute("UPDATE Mosq SET imam_name=? WHERE ID=?", (new_imam, ID))
        self.conn.commit()

    def __del__(self):
        self.conn.close()
db = MosqueDB()
root = tk.Tk()
root.title("🕌 Mosque Management System")
root.geometry("1000x600")
root.configure(bg="#fdf6e3")
style = ttk.Style()
style.theme_use("clam")
style.configure("TButton", background="#c3a995", foreground="black", padding=10, font=("Segoe UI", 10, "bold"))
style.configure("TLabel", background="#fdf6e3", font=("Segoe UI", 10))
style.configure("TEntry", padding=6)
fields = {}
labels = ["ID", "Name", "Type", "Address", "Coordinates", "Imam Name"]
input_frame = tk.LabelFrame(root, text="Mosque Information", padx=10, pady=10, bg="#fdf6e3", font=("Segoe UI", 12, "bold"))
input_frame.grid(row=0, column=0, sticky="nw", padx=10, pady=10)
for idx, label in enumerate(labels):
    ttk.Label(input_frame, text=label).grid(row=idx, column=0, sticky="w", pady=5)
    if label == "Type":
        var = tk.StringVar()
        fields[label] = var
        ttk.OptionMenu(input_frame, var, "", "Masjid", "Jame'", "Musalla").grid(row=idx, column=1, pady=5, sticky="ew")
    else:
        entry = ttk.Entry(input_frame, width=30)
        fields[label] = entry
        entry.grid(row=idx, column=1, pady=5, sticky="ew")
listbox_frame = tk.LabelFrame(root, text="Database Records", bg="#fdf6e3", padx=5, pady=5)
listbox_frame.grid(row=0, column=1, rowspan=2, padx=10, pady=10, sticky="n")
scrollbar = tk.Scrollbar(listbox_frame)
scrollbar.pack(side="right", fill="y")
listbox = tk.Listbox(listbox_frame, width=60, height=20, font=("Courier New", 10), yscrollcommand=scrollbar.set, bg="#fffaf0")
listbox.pack()
scrollbar.config(command=listbox.yview)

def validate_fields():
    try:
        if not all(fields[label].get() if isinstance(fields[label], tk.StringVar) else fields[label].get() for label in labels):
            raise ValueError("All fields are required.")
        int(fields["ID"].get())
        coords = fields["Coordinates"].get().split(",")
        if len(coords) != 2 or not all(c.strip().replace('.', '', 1).replace('-', '', 1).isdigit() for c in coords):
            raise ValueError("Coordinates must be in format: '24.7136,46.6753'")
        return True
    except Exception as e:
        messagebox.showerror("Validation Error", str(e))
        return False

def display_all():
    listbox.delete(0, tk.END)
    for row in db.Display():
        listbox.insert(tk.END, row)

def search():
    identifier = fields["ID"].get() or fields["Name"].get()
    result = db.Search(identifier)
    listbox.delete(0, tk.END)
    if result:
        listbox.insert(tk.END, result)
    else:
        close_matches = difflib.get_close_matches(identifier, [str(r[0]) for r in db.Display()] + [r[1] for r in db.Display()])
        if close_matches:
            listbox.insert(tk.END, f"Did you mean: {close_matches[0]}?")
        else:
            listbox.insert(tk.END, "Mosque not found")

def add_entry():
    if not validate_fields():
        return
    try:
        mosque = Mosque(
            int(fields["ID"].get()),
            fields["Name"].get(),
            fields["Type"].get(),
            fields["Address"].get(),
            fields["Coordinates"].get(),
            fields["Imam Name"].get(),
        )
        db.Insert(mosque.ID, mosque.name, mosque.type, mosque.address, mosque.coordinates, mosque.imam_name)
        display_all()
        clear_fields()  # Clear the input fields after adding
        messagebox.showinfo("Success", "Mosque added successfully!")  # Confirmation message
    except Exception as e:
        messagebox.showerror("Error", str(e))

def delete_entry():
    try:
        db.Delete(int(fields["ID"].get()))
        display_all()
        clear_fields()  # Clear the input fields after deletion
        messagebox.showinfo("Success", "Mosque deleted successfully!")  # Confirmation message
    except Exception as e:
        messagebox.showerror("Error", str(e))

def update_imam():
    try:
        db.Update_Imam(int(fields["ID"].get()), fields["Imam Name"].get())
        display_all()
        messagebox.showinfo("Success", "Imam name updated successfully.")
    except Exception as e:
        messagebox.showerror("Error", str(e))

def display_on_map():
    try:
        identifier = fields["ID"].get() or fields["Name"].get()
        result = db.Search(identifier)
        if result:
            coords = result[4].split(",")
            lat, lon = float(coords[0]), float(coords[1])
            m = folium.Map(location=[lat, lon], zoom_start=15)
            folium.Marker([lat, lon], popup=result[1]).add_to(m)
            m.save("map.html")
            webbrowser.open("map.html")
        else:
            messagebox.showinfo("Info", "Mosque not found")
    except Exception as e:
        messagebox.showerror("Map Error", str(e))

def on_select_record(event):
    selected = listbox.curselection()
    if selected:
        record = listbox.get(selected[0])
        for field in fields.values():
            if isinstance(field, tk.StringVar):
                field.set("")
            else:
                field.delete(0, tk.END)
        values = record if isinstance(record, tuple) else eval(record)
        for i, key in enumerate(labels):
            if isinstance(fields[key], tk.StringVar):
                fields[key].set(values[i])
            else:
                fields[key].insert(0, str(values[i]))

def clear_fields():
    for field in fields.values():
        if isinstance(field, tk.StringVar):
            field.set("")
        else:
            field.delete(0, tk.END)
button_frame = tk.Frame(root, bg="#fdf6e3")
button_frame.grid(row=2, column=0, columnspan=2, pady=40)
btns = [
    ("📋 Display All", display_all),
    ("🔍 Search", search),
    ("➕ Add Entry", add_entry),
    ("❌ Delete Entry", delete_entry),
    ("📝 Update Imam", update_imam),
    ("🗺️ Show on Map", display_on_map),
]
for idx, (text, cmd) in enumerate(btns):
    ttk.Button(button_frame, text=text, command=cmd).grid(row=0, column=idx, padx=5)
listbox.bind("<<ListboxSelect>>", on_select_record)
root.mainloop()

