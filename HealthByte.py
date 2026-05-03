import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pymongo import MongoClient
import re
import datetime
CONFIG = {"sugar_limit": 15, "sodium_limit": 400, "fat_limit": 20, "energy_limit": 400}
WHO_DAILY = {"energy": 2000, "sugar": 50, "sodium": 2000, "fat": 70}
CONDITIONS_LIST = ["None", "Diabetes", "Hypertension", "Heart Disease", "Asthma", "Kidney Disease", "Obesity"]
ADDITIVES_DATA = [
    {"code": "102", "name": "Tartrazine", "risk": "HIGH", "issues": "Hyperactivity, asthma"},
    {"code": "110", "name": "Sunset Yellow FCF", "risk": "HIGH", "issues": "Hyperactivity, allergies, asthma"},
    {"code": "123", "name": "Amaranth", "risk": "HIGH", "issues": "Possible carcinogen"},
    {"code": "124", "name": "Ponceau 4R", "risk": "HIGH", "issues": "Hyperactivity, allergic reactions"},
    {"code": "127", "name": "Erythrosine", "risk": "HIGH", "issues": "Thyroid problems, hyperactivity"},
    {"code": "128", "name": "Red 2G", "risk": "VERY HIGH", "issues": "Carcinogenic"},
    {"code": "171", "name": "Titanium Dioxide", "risk": "HIGH", "issues": "Possible carcinogen, banned in EU"},
    {"code": "211", "name": "Sodium Benzoate", "risk": "MEDIUM-HIGH", "issues": "Benzene risk with Vit C"},
    {"code": "249", "name": "Potassium Nitrite", "risk": "HIGH", "issues": "Forms carcinogenic nitrosamines"},
    {"code": "250", "name": "Sodium Nitrite", "risk": "HIGH", "issues": "Carcinogenic nitrosamines"},
    {"code": "320", "name": "BHA", "risk": "HIGH", "issues": "Possible carcinogen, hormone disruptor"},
    {"code": "951", "name": "Aspartame", "risk": "HIGH", "issues": "Headaches, neurological effects"},
    {"code": "924", "name": "Potassium Bromate", "risk": "VERY HIGH", "issues": "CARCINOGENIC - BANNED"},
    {"code": "927", "name": "Azodicarbonamide", "risk": "HIGH", "issues": "Asthma, banned in EU"}
]
df_additives = pd.DataFrame(ADDITIVES_DATA)
try:
    client = MongoClient("mongodb://localhost:27017", serverSelectionTimeoutMS=2000)
    client.admin.command('ping')
    db = client["health_project_db"]
    users_col = db["users"]
    logs_col = db["logs"]
except Exception:
    db = None
    users_col = None
    logs_col = None
def add_user():
    if db is None:
        messagebox.showerror("Error", "MongoDB is not connected")
        return
    name = u_name_box.get()
    age = u_age_box.get()
    weight = u_weight_box.get()
    height = u_height_box.get()
    cond = u_cond_box.get()
    if name and age and weight and height and cond:
        users_col.insert_one({"name": name, "age": age, "weight": weight, "height": height, "condition": cond})
        messagebox.showinfo("Success", "User Profile Added Successfully")
        u_name_box.delete(0, tk.END)
        u_age_box.delete(0, tk.END)
        u_weight_box.delete(0, tk.END)
        u_height_box.delete(0, tk.END)
        u_cond_box.current(0)
    else:
        messagebox.showwarning("Warning", "Please fill all user profile fields")
def analyze_and_add():
    if db is None:
        messagebox.showerror("Error", "MongoDB is not connected")
        return
    name = a_name_box.get()
    ing = ing_box.get("1.0", tk.END).upper().strip()
    energy_str = energy_box.get()
    sugar_str = sugar_box.get()
    sodium_str = sodium_box.get()
    fat_str = fat_box.get()
    if name and ing and energy_str and sugar_str and sodium_str and fat_str:
        try:
            energy = float(energy_str)
            sugar = float(sugar_str)
            sodium = float(sodium_str)
            fat = float(fat_str)
            user_data = users_col.find_one({"name": name})
            cond = user_data["condition"] if user_data and "condition" in user_data else "None"
            score = 10.0
            details = f"User Name: {name}\nMedical Condition: {cond}\n\n"
            details += "INGREDIENTS ANALYSIS:\n"
            codes_found = re.findall(r'(?:INS|E)\s*(\d+)', ing)
            found_mask = df_additives['code'].isin(codes_found)
            for _, row in df_additives[found_mask].iterrows():
                details += f"• {row['name']} ({row['code']}): {row['issues']}\n"
                score -= 2.0 if "HIGH" in row['risk'] else 1.0
            if not any(found_mask):
                details += "No high-risk additives found in database.\n"
            details += "\nNUTRITIONAL ANALYSIS:\n"
            if energy > CONFIG['energy_limit']:
                score -= 1.0
                details += f"! HIGH CALORIES: {energy} kcal\n"
            if sugar > CONFIG['sugar_limit']:
                score -= 1.5
                details += f"! HIGH SUGAR: {sugar}g\n"
                if cond == "Diabetes":
                    score -= 2.0
                    details += "CRITICAL: Dangerous for Diabetes!\n"
            if sodium > CONFIG['sodium_limit']:
                score -= 1.0
                details += f"! HIGH SALT: {sodium}mg\n"
                if cond in ["Hypertension", "Heart Disease"]:
                    score -= 2.0
                    details += f"CRITICAL: Dangerous for {cond}!\n"
            score = max(0.0, min(10.0, score))
            details += f"\nFINAL SAFETY SCORE: {score}/10"
            date_str = datetime.datetime.now().strftime("%d-%m-%Y %H:%M")
            logs_col.insert_one({"user_name": name, "score": score, "date": date_str})
            res_text.delete("1.0", tk.END)
            res_text.insert(tk.END, details)
            clear_analyzer_fields()
            show_history()
            show_chart(energy, sugar, sodium, fat)
        except ValueError:
            messagebox.showerror("Error", "Nutritional values must be numbers")
    else:
        messagebox.showwarning("Warning", "Please fill all fields")
def clear_analyzer_fields():
    a_name_box.delete(0, tk.END)
    ing_box.delete("1.0", tk.END)
    energy_box.delete(0, tk.END)
    sugar_box.delete(0, tk.END)
    sodium_box.delete(0, tk.END)
    fat_box.delete(0, tk.END)
def show_history():
    if db is None: return
    for row in tree.get_children():
        tree.delete(row)
    data = list(logs_col.find().sort("date", -1))
    for item in data:
        tree.insert("", tk.END, values=(item.get("user_name", "Unknown"), item.get("score", 0.0), item.get("date", "")))
def show_chart(e, s, n, f):
    for widget in chart_area.winfo_children():
        widget.destroy()
    fig, ax = plt.subplots(figsize=(5, 4))
    categories = ['Energy', 'Sugar', 'Sodium', 'Fat']
    who_pct = [
        (e / WHO_DAILY['energy']) * 100,
        (s / WHO_DAILY['sugar']) * 100,
        (n / WHO_DAILY['sodium']) * 100,
        (f / WHO_DAILY['fat']) * 100
    ]
    serving_pct = [
        (e / CONFIG['energy_limit']) * 100,
        (s / CONFIG['sugar_limit']) * 100,
        (n / CONFIG['sodium_limit']) * 100,
        (f / CONFIG['fat_limit']) * 100
    ]
    x = np.arange(len(categories))
    width = 0.35
    ax.bar(x - width/2, serving_pct, width, label='Serving Limit', color='#3498db')
    ax.bar(x + width/2, who_pct, width, label='WHO Daily Limit', color='#2ecc71')
    ax.axhline(100, color='red', linestyle='--', linewidth=1, label='Max Threshold')
    ax.set_ylabel('% of Recommended Limit')
    ax.set_title('Nutritional Impact vs WHO Daily Guidelines')
    ax.set_xticks(x)
    ax.set_xticklabels(categories)
    ax.set_ylim(0, max(120, max(serving_pct + who_pct) + 10))
    ax.legend(fontsize='small')
    fig.tight_layout()
    canvas = FigureCanvasTkAgg(fig, master=chart_area)
    canvas.draw()
    canvas.get_tk_widget().pack()
root = tk.Tk()
root.title("Personal Health & Food Analyzer")
root.geometry("1000x750")
tabs = ttk.Notebook(root)
tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
tab_profile = tk.Frame(tabs)
tab_analyzer = tk.Frame(tabs)
tab_history = tk.Frame(tabs)
tabs.add(tab_profile, text=" User Profile ")
tabs.add(tab_analyzer, text=" Food Analyzer ")
tabs.add(tab_history, text=" Analysis History ")
tk.Label(tab_profile, text="User Name").grid(row=0, column=0, padx=20, pady=10, sticky="w")
u_name_box = tk.Entry(tab_profile, width=40)
u_name_box.grid(row=0, column=1, padx=20, pady=10)
tk.Label(tab_profile, text="Age").grid(row=1, column=0, padx=20, pady=10, sticky="w")
u_age_box = tk.Entry(tab_profile, width=40)
u_age_box.grid(row=1, column=1, padx=20, pady=10)
tk.Label(tab_profile, text="Weight (kg)").grid(row=2, column=0, padx=20, pady=10, sticky="w")
u_weight_box = tk.Entry(tab_profile, width=40)
u_weight_box.grid(row=2, column=1, padx=20, pady=10)
tk.Label(tab_profile, text="Height (cm)").grid(row=3, column=0, padx=20, pady=10, sticky="w")
u_height_box = tk.Entry(tab_profile, width=40)
u_height_box.grid(row=3, column=1, padx=20, pady=10)
tk.Label(tab_profile, text="Condition").grid(row=4, column=0, padx=20, pady=10, sticky="w")
u_cond_box = ttk.Combobox(tab_profile, values=CONDITIONS_LIST, state="readonly", width=37)
u_cond_box.current(0)
u_cond_box.grid(row=4, column=1, padx=20, pady=10)
tk.Button(tab_profile, text="Save User Profile", command=add_user).grid(row=5, column=1, pady=20, sticky="e")
analyzer_main = tk.Frame(tab_analyzer)
analyzer_main.pack(fill=tk.BOTH, expand=True)
left_side = tk.Frame(analyzer_main)
left_side.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
tk.Label(left_side, text="User Name").grid(row=0, column=0, sticky="w", pady=2)
a_name_box = tk.Entry(left_side, width=30)
a_name_box.grid(row=0, column=1, pady=2)
tk.Label(left_side, text="Energy (kcal)").grid(row=1, column=0, sticky="w", pady=2)
energy_box = tk.Entry(left_side, width=30)
energy_box.grid(row=1, column=1, pady=2)
tk.Label(left_side, text="Sugar (g)").grid(row=2, column=0, sticky="w", pady=2)
sugar_box = tk.Entry(left_side, width=30)
sugar_box.grid(row=2, column=1, pady=2)
tk.Label(left_side, text="Sodium (mg)").grid(row=3, column=0, sticky="w", pady=2)
sodium_box = tk.Entry(left_side, width=30)
sodium_box.grid(row=3, column=1, pady=2)
tk.Label(left_side, text="Fat (g)").grid(row=4, column=0, sticky="w", pady=2)
fat_box = tk.Entry(left_side, width=30)
fat_box.grid(row=4, column=1, pady=2)
tk.Label(left_side, text="Ingredients").grid(row=5, column=0, sticky="nw", pady=2)
ing_box = tk.Text(left_side, height=4, width=25)
ing_box.grid(row=5, column=1, pady=2)
tk.Button(left_side, text="Analyze Food", command=analyze_and_add).grid(row=6, column=0, columnspan=2, pady=10)
res_text = tk.Text(left_side, height=12, width=45)
res_text.grid(row=8, column=0, columnspan=2, pady=5)
chart_area = tk.Frame(analyzer_main, width=400, height=400)
chart_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
tree = ttk.Treeview(tab_history, columns=("User", "Score", "Date"), show="headings")
for col in ("User", "Score", "Date"):
    tree.heading(col, text=col)
    tree.column(col, width=150)
tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
show_history()
root.mainloop()
